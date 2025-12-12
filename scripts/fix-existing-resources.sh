#!/bin/bash

# Nova Pro Dashboard - Fix Existing Resources Script
# This script helps resolve conflicts when resources already exist

set -euo pipefail

# Configuration
DASHBOARD_NAME="${1:-NovaProMonitoring}"
REGION="${2:-us-east-1}"
STACK_NAME="${3:-nova-pro-dashboard-compact}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔧 Nova Pro Dashboard - Resource Conflict Resolution${NC}"
echo "Dashboard Name: $DASHBOARD_NAME"
echo "Region: $REGION"
echo "Stack Name: $STACK_NAME"
echo ""

echo -e "${YELLOW}📋 Checking for existing resources...${NC}"

# Check for existing dashboard
echo "Checking for existing dashboard..."
if aws cloudwatch get-dashboard --dashboard-name "$DASHBOARD_NAME" --region "$REGION" &> /dev/null; then
    echo -e "${YELLOW}⚠️  Dashboard '$DASHBOARD_NAME' already exists${NC}"
    DASHBOARD_EXISTS=true
else
    echo -e "${GREEN}✅ Dashboard '$DASHBOARD_NAME' does not exist${NC}"
    DASHBOARD_EXISTS=false
fi

# Check for existing SNS topic
echo "Checking for existing SNS topic..."
TOPIC_NAME="${DASHBOARD_NAME}-AlarmTopic"
if aws sns get-topic-attributes --topic-arn "arn:aws:sns:$REGION:$(aws sts get-caller-identity --query Account --output text):$TOPIC_NAME" --region "$REGION" &> /dev/null; then
    echo -e "${YELLOW}⚠️  SNS Topic '$TOPIC_NAME' already exists${NC}"
    TOPIC_EXISTS=true
else
    echo -e "${GREEN}✅ SNS Topic '$TOPIC_NAME' does not exist${NC}"
    TOPIC_EXISTS=false
fi

# Check for existing stack
echo "Checking for existing CloudFormation stack..."
if aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" &> /dev/null; then
    STACK_STATUS=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" --query 'Stacks[0].StackStatus' --output text)
    echo -e "${YELLOW}⚠️  Stack '$STACK_NAME' exists with status: $STACK_STATUS${NC}"
    STACK_EXISTS=true
else
    echo -e "${GREEN}✅ Stack '$STACK_NAME' does not exist${NC}"
    STACK_EXISTS=false
fi

echo ""
echo -e "${YELLOW}🛠️  Resolution Options:${NC}"
echo ""

if [[ "$DASHBOARD_EXISTS" == "true" || "$TOPIC_EXISTS" == "true" ]]; then
    echo -e "${YELLOW}Option 1: Use Different Names (Recommended)${NC}"
    echo "Deploy with unique resource names to avoid conflicts:"
    echo ""
    echo "Update your parameters.json:"
    cat << 'EOF'
[
  {
    "ParameterKey": "DashboardName",
    "ParameterValue": "NovaProMonitoring-v2"
  }
]
EOF
    echo ""
    echo "Then deploy:"
    echo "aws cloudformation create-stack \\"
    echo "  --stack-name nova-pro-dashboard-v2 \\"
    echo "  --template-body file://nova-pro-dashboard-compact.yaml \\"
    echo "  --parameters file://parameters.json \\"
    echo "  --region $REGION"
    echo ""
    
    echo -e "${YELLOW}Option 2: Delete Existing Resources${NC}"
    echo "⚠️  WARNING: This will delete existing monitoring setup!"
    echo ""
    
    if [[ "$DASHBOARD_EXISTS" == "true" ]]; then
        echo "Delete existing dashboard:"
        echo "aws cloudwatch delete-dashboards --dashboard-names '$DASHBOARD_NAME' --region $REGION"
    fi
    
    if [[ "$TOPIC_EXISTS" == "true" ]]; then
        echo "Delete existing SNS topic:"
        echo "aws sns delete-topic --topic-arn 'arn:aws:sns:$REGION:$(aws sts get-caller-identity --query Account --output text):$TOPIC_NAME' --region $REGION"
    fi
    
    echo ""
    echo "Then retry deployment with original names."
    echo ""
    
    echo -e "${YELLOW}Option 3: Import Existing Resources${NC}"
    echo "If the existing resources were created by a previous version of this template,"
    echo "you can import them into a new stack. This is more complex and requires"
    echo "matching the exact resource configuration."
    echo ""
fi

if [[ "$STACK_EXISTS" == "true" ]]; then
    echo -e "${YELLOW}Stack Management:${NC}"
    
    if [[ "$STACK_STATUS" == "ROLLBACK_COMPLETE" || "$STACK_STATUS" == "CREATE_FAILED" ]]; then
        echo "Delete the failed stack first:"
        echo "aws cloudformation delete-stack --stack-name '$STACK_NAME' --region $REGION"
        echo ""
        echo "Wait for deletion to complete:"
        echo "aws cloudformation wait stack-delete-complete --stack-name '$STACK_NAME' --region $REGION"
        echo ""
        echo "Then retry deployment."
    elif [[ "$STACK_STATUS" == "CREATE_COMPLETE" || "$STACK_STATUS" == "UPDATE_COMPLETE" ]]; then
        echo "Stack exists and is healthy. Consider updating instead of creating:"
        echo "aws cloudformation update-stack \\"
        echo "  --stack-name '$STACK_NAME' \\"
        echo "  --template-body file://nova-pro-dashboard-compact.yaml \\"
        echo "  --parameters file://parameters.json \\"
        echo "  --region $REGION"
    fi
fi

echo ""
echo -e "${GREEN}💡 Recommended Solution:${NC}"
echo "1. Use Option 1 (different names) for quickest resolution"
echo "2. Update DashboardName parameter to 'NovaProMonitoring-v2'"
echo "3. Use a new stack name like 'nova-pro-dashboard-v2'"
echo "4. Deploy with the new names"
echo ""
echo "This avoids conflicts and gets you up and running quickly!"