#!/bin/bash

# Switch Bedrock logging from S3 to CloudWatch Logs for dashboard compatibility

set -e

echo "🔄 Switching Bedrock logging from S3 to CloudWatch Logs"
echo

# Get current configuration
echo "Current Bedrock logging configuration:"
aws bedrock get-model-invocation-logging-configuration
echo

# Check if we're in the right AWS account/region
CURRENT_REGION=$(aws configure get region 2>/dev/null || echo "us-east-1")
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "Current AWS Region: $CURRENT_REGION"
echo "Account ID: $ACCOUNT_ID"
echo

# Create IAM role for Bedrock logging (if it doesn't exist)
ROLE_NAME="BedrockLoggingRole"
ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"

echo "📋 Step 1: Ensuring IAM role exists..."

TRUST_POLICY='{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "bedrock.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}'

LOGGING_POLICY='{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:log-group:/aws/bedrock/modelinvocations*"
    }
  ]
}'

# Check if role exists
if aws iam get-role --role-name $ROLE_NAME >/dev/null 2>&1; then
    echo "✅ IAM role $ROLE_NAME already exists"
else
    echo "Creating IAM role $ROLE_NAME..."
    aws iam create-role \
        --role-name $ROLE_NAME \
        --assume-role-policy-document "$TRUST_POLICY" \
        --description "Role for Bedrock model invocation logging to CloudWatch"
    
    aws iam put-role-policy \
        --role-name $ROLE_NAME \
        --policy-name BedrockLoggingPolicy \
        --policy-document "$LOGGING_POLICY"
    
    echo "✅ Created IAM role $ROLE_NAME"
fi

echo "Role ARN: $ROLE_ARN"
echo

# Create CloudWatch log group
LOG_GROUP_NAME="/aws/bedrock/modelinvocations"

echo "📋 Step 2: Creating CloudWatch log group..."

if aws logs describe-log-groups --log-group-name-prefix $LOG_GROUP_NAME --query 'logGroups[?logGroupName==`'$LOG_GROUP_NAME'`]' --output text | grep -q $LOG_GROUP_NAME; then
    echo "✅ Log group $LOG_GROUP_NAME already exists"
else
    echo "Creating log group $LOG_GROUP_NAME..."
    aws logs create-log-group --log-group-name $LOG_GROUP_NAME
    echo "✅ Created log group $LOG_GROUP_NAME"
fi

# Switch Bedrock logging to CloudWatch Logs
echo "📋 Step 3: Switching Bedrock logging to CloudWatch Logs..."

aws bedrock put-model-invocation-logging-configuration \
    --logging-config "cloudWatchConfig={logGroupName=$LOG_GROUP_NAME,roleArn=$ROLE_ARN},textDataDeliveryEnabled=true,imageDataDeliveryEnabled=true,embeddingDataDeliveryEnabled=true,videoDataDeliveryEnabled=true" \
    --region $CURRENT_REGION

echo "✅ Bedrock logging switched to CloudWatch Logs"
echo

# Verify new configuration
echo "📋 Step 4: Verifying new configuration..."
aws bedrock get-model-invocation-logging-configuration
echo

echo "🎉 Setup complete!"
echo
echo "Next steps:"
echo "1. Send Nova Pro requests with metadata (see example below)"
echo "2. Wait 2-5 minutes for logs to appear in CloudWatch"
echo "3. Check your dashboard - user/app widgets should show data"
echo
echo "Example request with metadata:"
cat << 'EOF'

python3 << 'PYTHON'
import boto3
import json

bedrock = boto3.client('bedrock-runtime')

response = bedrock.invoke_model(
    modelId='amazon.nova-pro-v1:0',
    contentType='application/json',
    body=json.dumps({
        "messages": [{"role": "user", "content": [{"text": "Test message for tracking"}]}],
        "inferenceConfig": {"max_new_tokens": 50},
        "metadata": {
            "userId": "test-user@company.com",
            "applicationName": "dashboard-test"
        }
    })
)

print("✅ Test request sent with metadata!")
PYTHON

EOF

echo
echo "Dashboard URL:"
aws cloudformation describe-stacks \
    --stack-name nova-pro-dashboard \
    --query 'Stacks[0].Outputs[?OutputKey==`DashboardURL`].OutputValue' \
    --output text 2>/dev/null || echo "Check CloudFormation outputs for dashboard URL"