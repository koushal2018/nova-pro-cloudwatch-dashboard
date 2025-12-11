#!/bin/bash

# Nova Pro Dashboard - Drift Detection and Compliance Setup
# This script sets up automated drift detection and AWS Config monitoring

set -e

STACK_NAME="${1:-nova-pro-dashboard-prod}"
REGION="${2:-us-east-1}"
CONFIG_BUCKET="${3:-your-aws-config-bucket}"

echo "Setting up drift detection and compliance monitoring for stack: $STACK_NAME in region: $REGION"

# 1. Enable AWS Config (if not already enabled)
echo "Checking AWS Config status..."
if ! aws configservice describe-configuration-recorders --region $REGION --query 'ConfigurationRecorders[0].name' --output text 2>/dev/null; then
    echo "Enabling AWS Config..."
    
    # Create Config service role
    aws iam create-role \
        --role-name AWSConfigRole \
        --assume-role-policy-document '{
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "config.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }' \
        --region $REGION || true
    
    aws iam attach-role-policy \
        --role-name AWSConfigRole \
        --policy-arn arn:aws:iam::aws:policy/service-role/ConfigRole \
        --region $REGION || true
    
    # Create Config recorder
    aws configservice put-configuration-recorder \
        --configuration-recorder name=default,roleARN=arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/AWSConfigRole \
        --region $REGION
    
    # Create delivery channel
    aws configservice put-delivery-channel \
        --delivery-channel name=default,s3BucketName=$CONFIG_BUCKET \
        --region $REGION
    
    # Start Config recorder
    aws configservice start-configuration-recorder \
        --configuration-recorder-name default \
        --region $REGION
fi

# 2. Create Config rules for CloudFormation stack compliance
echo "Creating Config rules for stack compliance..."

# Rule: Check if stack has termination protection enabled
aws configservice put-config-rule \
    --config-rule '{
        "ConfigRuleName": "cloudformation-stack-termination-protection-enabled",
        "Description": "Checks if CloudFormation stacks have termination protection enabled",
        "Source": {
            "Owner": "AWS",
            "SourceIdentifier": "CLOUDFORMATION_STACK_TERMINATION_PROTECTION_ENABLED"
        },
        "InputParameters": "{\"stackNames\":\"'$STACK_NAME'\"}"
    }' \
    --region $REGION || true

# Rule: Check if resources have required tags
aws configservice put-config-rule \
    --config-rule '{
        "ConfigRuleName": "required-tags-nova-dashboard",
        "Description": "Checks if Nova Dashboard resources have required tags",
        "Source": {
            "Owner": "AWS",
            "SourceIdentifier": "REQUIRED_TAGS"
        },
        "InputParameters": "{\"requiredTagKeys\":\"Environment,Owner,CostCenter,Purpose\"}"
    }' \
    --region $REGION || true

# 3. Create CloudWatch alarm for drift detection
echo "Creating CloudWatch alarm for drift detection..."

# Create custom metric for drift detection
aws logs create-log-group \
    --log-group-name /aws/lambda/drift-detection \
    --region $REGION || true

# Create Lambda function for automated drift detection
cat > drift-detection-lambda.py << 'EOF'
import json
import boto3
import os

def lambda_handler(event, context):
    cf_client = boto3.client('cloudformation')
    cw_client = boto3.client('cloudwatch')
    
    stack_name = os.environ['STACK_NAME']
    region = os.environ['AWS_REGION']
    
    try:
        # Start drift detection
        response = cf_client.detect_stack_drift(StackName=stack_name)
        drift_id = response['StackDriftDetectionId']
        
        # Wait for completion (simplified - in production use Step Functions)
        import time
        time.sleep(30)
        
        # Get drift results
        drift_result = cf_client.describe_stack_drift_detection_status(
            StackDriftDetectionId=drift_id
        )
        
        # Send metric to CloudWatch
        drift_status = drift_result['StackDriftStatus']
        metric_value = 1 if drift_status == 'DRIFTED' else 0
        
        cw_client.put_metric_data(
            Namespace='Custom/StackManagement',
            MetricData=[
                {
                    'MetricName': 'StackDrift',
                    'Dimensions': [
                        {
                            'Name': 'StackName',
                            'Value': stack_name
                        }
                    ],
                    'Value': metric_value,
                    'Unit': 'Count'
                }
            ]
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps(f'Drift detection completed. Status: {drift_status}')
        }
        
    except Exception as e:
        print(f'Error: {str(e)}')
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }
EOF

# Package and deploy Lambda function
zip drift-detection-lambda.zip drift-detection-lambda.py

aws lambda create-function \
    --function-name nova-dashboard-drift-detection \
    --runtime python3.9 \
    --role arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/lambda-execution-role \
    --handler drift-detection-lambda.lambda_handler \
    --zip-file fileb://drift-detection-lambda.zip \
    --environment Variables="{STACK_NAME=$STACK_NAME}" \
    --region $REGION || true

# 4. Create EventBridge rule for weekly drift detection
echo "Setting up weekly drift detection schedule..."

aws events put-rule \
    --name nova-dashboard-weekly-drift-check \
    --schedule-expression "cron(0 2 ? * MON *)" \
    --description "Weekly drift detection for Nova Dashboard stack" \
    --region $REGION || true

aws events put-targets \
    --rule nova-dashboard-weekly-drift-check \
    --targets "Id"="1","Arn"="arn:aws:lambda:$REGION:$(aws sts get-caller-identity --query Account --output text):function:nova-dashboard-drift-detection" \
    --region $REGION || true

# 5. Create CloudWatch alarm for drift detection
aws cloudwatch put-metric-alarm \
    --alarm-name "NovaProDashboard-StackDrift" \
    --alarm-description "Detects configuration drift in Nova Pro Dashboard stack" \
    --metric-name StackDrift \
    --namespace Custom/StackManagement \
    --statistic Maximum \
    --period 86400 \
    --threshold 0 \
    --comparison-operator GreaterThanThreshold \
    --dimensions Name=StackName,Value=$STACK_NAME \
    --evaluation-periods 1 \
    --alarm-actions arn:aws:sns:$REGION:$(aws sts get-caller-identity --query Account --output text):${STACK_NAME}-AlarmTopic \
    --region $REGION || true

echo "Drift detection and compliance monitoring setup complete!"
echo ""
echo "Next steps:"
echo "1. Verify AWS Config is recording: aws configservice get-status --region $REGION"
echo "2. Check Config rules: aws configservice describe-config-rules --region $REGION"
echo "3. Test drift detection: aws cloudformation detect-stack-drift --stack-name $STACK_NAME --region $REGION"
echo "4. Monitor compliance: aws configservice get-compliance-details-by-config-rule --config-rule-name required-tags-nova-dashboard --region $REGION"

# Cleanup
rm -f drift-detection-lambda.py drift-detection-lambda.zip