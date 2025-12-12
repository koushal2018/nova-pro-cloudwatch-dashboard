#!/bin/bash

# Nova Pro Dashboard - Role Assumption Helper Script
# This script helps users assume the DashboardViewerRole for dashboard access

set -euo pipefail

# Configuration
STACK_NAME="${1:-nova-pro-dashboard-compact}"
REGION="${2:-us-east-1}"
SESSION_NAME="${3:-DashboardViewer-$(date +%s)}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔐 Nova Pro Dashboard Role Assumption${NC}"
echo "Stack Name: $STACK_NAME"
echo "Region: $REGION"
echo "Session Name: $SESSION_NAME"
echo ""

# Get current account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "Account ID: $ACCOUNT_ID"

# Get role ARN from stack outputs
echo -e "${YELLOW}📋 Getting role ARN from stack...${NC}"
ROLE_ARN=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --query 'Stacks[0].Outputs[?OutputKey==`DashboardViewerRoleArn`].OutputValue' \
  --output text 2>/dev/null || echo "")

if [[ -z "$ROLE_ARN" ]]; then
    echo -e "${RED}❌ Could not find DashboardViewerRoleArn output in stack '$STACK_NAME'${NC}"
    echo "Make sure the stack exists and has been deployed successfully."
    exit 1
fi

echo "Role ARN: $ROLE_ARN"

# Get dashboard name for external ID
DASHBOARD_NAME=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --query 'Stacks[0].Outputs[?OutputKey==`DashboardName`].OutputValue' \
  --output text 2>/dev/null || echo "NovaProMonitoring")

EXTERNAL_ID="${DASHBOARD_NAME}-${ACCOUNT_ID}"
echo "External ID: $EXTERNAL_ID"

# Assume the role
echo -e "${YELLOW}🔄 Assuming role...${NC}"
CREDENTIALS=$(aws sts assume-role \
  --role-arn "$ROLE_ARN" \
  --role-session-name "$SESSION_NAME" \
  --external-id "$EXTERNAL_ID" \
  --query 'Credentials.[AccessKeyId,SecretAccessKey,SessionToken]' \
  --output text 2>/dev/null || echo "")

if [[ -z "$CREDENTIALS" ]]; then
    echo -e "${RED}❌ Failed to assume role${NC}"
    echo ""
    echo -e "${YELLOW}Possible causes:${NC}"
    echo "1. Your current user/role doesn't have permission to assume the DashboardViewerRole"
    echo "2. The external ID is incorrect"
    echo "3. The role's time restrictions don't allow current access"
    echo ""
    echo -e "${YELLOW}To fix this, your administrator needs to grant you sts:AssumeRole permission:${NC}"
    cat << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "sts:AssumeRole",
      "Resource": "$ROLE_ARN",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "$EXTERNAL_ID"
        }
      }
    }
  ]
}
EOF
    exit 1
fi

# Parse credentials
read -r ACCESS_KEY SECRET_KEY SESSION_TOKEN <<< "$CREDENTIALS"

echo -e "${GREEN}✅ Successfully assumed role!${NC}"
echo ""

# Get dashboard URL
DASHBOARD_URL=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --query 'Stacks[0].Outputs[?OutputKey==`DashboardURL`].OutputValue' \
  --output text 2>/dev/null || echo "")

echo -e "${GREEN}🎉 Role Assumption Complete!${NC}"
echo ""
echo -e "${YELLOW}📊 Dashboard Access:${NC}"
if [[ -n "$DASHBOARD_URL" ]]; then
    echo "Dashboard URL: $DASHBOARD_URL"
else
    echo "Dashboard URL: Check CloudWatch console for dashboard named '$DASHBOARD_NAME'"
fi
echo ""

echo -e "${YELLOW}🔧 To use these credentials:${NC}"
echo ""
echo "Option 1 - Export environment variables:"
echo "export AWS_ACCESS_KEY_ID='$ACCESS_KEY'"
echo "export AWS_SECRET_ACCESS_KEY='$SECRET_KEY'"
echo "export AWS_SESSION_TOKEN='$SESSION_TOKEN'"
echo ""
echo "Option 2 - Use AWS CLI profile:"
echo "aws configure set aws_access_key_id '$ACCESS_KEY' --profile dashboard-viewer"
echo "aws configure set aws_secret_access_key '$SECRET_KEY' --profile dashboard-viewer"
echo "aws configure set aws_session_token '$SESSION_TOKEN' --profile dashboard-viewer"
echo "aws configure set region '$REGION' --profile dashboard-viewer"
echo ""
echo "Then use: aws cloudwatch get-dashboard --dashboard-name '$DASHBOARD_NAME' --profile dashboard-viewer"
echo ""

echo -e "${YELLOW}⏰ Session expires in 1 hour. Re-run this script to refresh.${NC}"