#!/bin/bash

# Configure Bedrock CloudWatch Logs IAM Role
# This script performs the manual IAM configuration steps for Bedrock logging

set -e

# Configuration - modify these values for your environment
ROLE_NAME="${BEDROCK_ROLE_NAME:-Bedrockcloudwatchlogs}"
POLICY_NAME="${BEDROCK_POLICY_NAME:-BedrockCloudWatchLogsAccess}"
ACCOUNT_ID="${AWS_ACCOUNT_ID:-$(aws sts get-caller-identity --query Account --output text)}"
REGION="${AWS_REGION:-us-east-1}"

echo "🔍 Checking if role '$ROLE_NAME' exists..."

# Check if role exists
if ! aws iam get-role --role-name "$ROLE_NAME" >/dev/null 2>&1; then
    echo "❌ Role '$ROLE_NAME' not found. Please create it first or check the role name."
    exit 1
fi

echo "✅ Role '$ROLE_NAME' found"

# Step 5: Review existing policies
echo "📋 Current policies attached to role '$ROLE_NAME':"
aws iam list-attached-role-policies --role-name "$ROLE_NAME" --query 'AttachedPolicies[].PolicyName' --output table
aws iam list-role-policies --role-name "$ROLE_NAME" --query 'PolicyNames' --output table

# Step 6-9: Create inline policy
echo "📝 Creating inline policy '$POLICY_NAME'..."

INLINE_POLICY='{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:'$REGION':'$ACCOUNT_ID':log-group:/aws/bedrock/modelinvocations:*"
    }
  ]
}'

aws iam put-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-name "$POLICY_NAME" \
    --policy-document "$INLINE_POLICY"

echo "✅ Inline policy '$POLICY_NAME' created successfully"

# Step 11: Check and update trust relationship
echo "🔐 Checking trust relationship for role '$ROLE_NAME'..."

TRUST_POLICY='{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "bedrock.amazonaws.com"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "aws:SourceAccount": "'$ACCOUNT_ID'"
        },
        "ArnLike": {
          "aws:SourceArn": "arn:aws:bedrock:'$REGION':'$ACCOUNT_ID':*"
        }
      }
    }
  ]
}'

# Get current trust policy
CURRENT_TRUST=$(aws iam get-role --role-name "$ROLE_NAME" --query 'Role.AssumeRolePolicyDocument')

echo "📄 Current trust policy:"
echo "$CURRENT_TRUST" | jq '.'

# Update trust policy
echo "🔄 Updating trust relationship..."
aws iam update-assume-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-document "$TRUST_POLICY"

echo "✅ Trust relationship updated successfully"

# Verify the configuration
echo "🔍 Verifying final configuration..."
echo ""
echo "📋 Final policies attached to role '$ROLE_NAME':"
aws iam list-attached-role-policies --role-name "$ROLE_NAME" --query 'AttachedPolicies[].PolicyName' --output table
aws iam list-role-policies --role-name "$ROLE_NAME" --query 'PolicyNames' --output table

echo ""
echo "🔐 Final trust relationship:"
aws iam get-role --role-name "$ROLE_NAME" --query 'Role.AssumeRolePolicyDocument' | jq '.'

echo ""
echo "✅ Configuration complete! You can now retry your Bedrock operation."
echo ""
echo "📝 Next steps:"
echo "   1. Return to the Bedrock console"
echo "   2. Retry the operation that caused the original error"
echo "   3. If issues persist, check CloudWatch Logs for detailed error messages"