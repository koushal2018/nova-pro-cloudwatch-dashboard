#!/bin/bash

# Setup User and Application Tracking for Nova Pro Dashboard
# This script enables the required logging and shows how to include metadata

set -e

echo "🚀 Setting up User and Application Tracking for Nova Pro Dashboard"
echo

# Check if we're in the right AWS account/region
CURRENT_REGION=$(aws configure get region 2>/dev/null || echo "us-east-1")
echo "Current AWS Region: $CURRENT_REGION"
echo

# Step 1: Create IAM role for Bedrock logging (if it doesn't exist)
echo "📋 Step 1: Creating IAM role for Bedrock logging..."

ROLE_NAME="BedrockLoggingRole"
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
        --description "Role for Bedrock model invocation logging"
    
    aws iam put-role-policy \
        --role-name $ROLE_NAME \
        --policy-name BedrockLoggingPolicy \
        --policy-document "$LOGGING_POLICY"
    
    echo "✅ Created IAM role $ROLE_NAME"
fi

# Get account ID for ARN construction
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"

echo "Role ARN: $ROLE_ARN"
echo

# Step 2: Enable Bedrock model invocation logging
echo "📋 Step 2: Enabling Bedrock model invocation logging..."

LOG_GROUP_NAME="/aws/bedrock/modelinvocations"

# Create log group if it doesn't exist
if aws logs describe-log-groups --log-group-name-prefix $LOG_GROUP_NAME --query 'logGroups[?logGroupName==`'$LOG_GROUP_NAME'`]' --output text | grep -q $LOG_GROUP_NAME; then
    echo "✅ Log group $LOG_GROUP_NAME already exists"
else
    echo "Creating log group $LOG_GROUP_NAME..."
    aws logs create-log-group --log-group-name $LOG_GROUP_NAME
    echo "✅ Created log group $LOG_GROUP_NAME"
fi

# Configure Bedrock logging
echo "Configuring Bedrock model invocation logging..."
aws bedrock put-model-invocation-logging-configuration \
    --logging-config "destinationConfig={cloudWatchConfig={logGroupName=$LOG_GROUP_NAME,roleArn=$ROLE_ARN}}" \
    --region $CURRENT_REGION

echo "✅ Bedrock model invocation logging enabled"
echo

# Step 3: Show example of how to include metadata
echo "📋 Step 3: Example Nova Pro request with metadata"
echo
echo "To see user/application data in your dashboard, include metadata in your Bedrock requests:"
echo
cat << 'EOF'
# Python example using boto3:
import boto3
import json

bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

response = bedrock.invoke_model(
    modelId='amazon.nova-pro-v1:0',
    contentType='application/json',
    body=json.dumps({
        "messages": [
            {
                "role": "user", 
                "content": [{"text": "Hello, how are you?"}]
            }
        ],
        "inferenceConfig": {
            "max_new_tokens": 100,
            "temperature": 0.7
        },
        # 🔑 THIS IS THE KEY - Include metadata for tracking
        "metadata": {
            "userId": "john.doe@company.com",
            "applicationName": "customer-chatbot",
            "department": "sales",
            "costCenter": "CC-12345"
        }
    })
)
EOF

echo
echo "📋 Step 4: Test the setup"
echo
echo "Run this command to test with metadata:"
cat << 'EOF'

# Test command (replace with your actual values):
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
            "userId": "test-user",
            "applicationName": "dashboard-test"
        }
    })
)

print("✅ Test request sent with metadata!")
print("Response:", json.loads(response['body'].read())['output']['message']['content'][0]['text'][:100] + "...")
PYTHON

EOF

echo
echo "📋 Step 5: Verify in CloudWatch"
echo
echo "After sending requests with metadata:"
echo "1. Wait 2-5 minutes for logs to appear"
echo "2. Check CloudWatch Logs: /aws/bedrock/modelinvocations"
echo "3. View your dashboard - user/app widgets should show data"
echo
echo "Dashboard URL:"
aws cloudformation describe-stacks \
    --stack-name nova-pro-dashboard \
    --query 'Stacks[0].Outputs[?OutputKey==`DashboardURL`].OutputValue' \
    --output text 2>/dev/null || echo "Run: aws cloudformation describe-stacks --stack-name nova-pro-dashboard"

echo
echo "🎉 Setup complete! Send Nova Pro requests with metadata to see tracking data."