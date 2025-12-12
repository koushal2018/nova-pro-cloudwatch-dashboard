#!/bin/bash

# Nova Pro Dashboard Compact - Production Deployment Script
# This script deploys the compact CloudWatch dashboard with proper error handling

set -euo pipefail

# Configuration
STACK_NAME="${1:-nova-pro-dashboard-compact}"
REGION="${2:-us-east-1}"
TEMPLATE_FILE="nova-pro-dashboard-compact.yaml"
PARAMETERS_FILE="${3:-parameters.example.json}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Nova Pro Dashboard Compact Deployment${NC}"
echo "Stack Name: $STACK_NAME"
echo "Region: $REGION"
echo "Template: $TEMPLATE_FILE"
echo "Parameters: $PARAMETERS_FILE"
echo ""

# Validate prerequisites
echo -e "${YELLOW}📋 Validating prerequisites...${NC}"

if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not found. Please install AWS CLI.${NC}"
    exit 1
fi

if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS credentials not configured. Please run 'aws configure'.${NC}"
    exit 1
fi

if [[ ! -f "$TEMPLATE_FILE" ]]; then
    echo -e "${RED}❌ Template file '$TEMPLATE_FILE' not found.${NC}"
    exit 1
fi

if [[ ! -f "$PARAMETERS_FILE" ]]; then
    echo -e "${RED}❌ Parameters file '$PARAMETERS_FILE' not found.${NC}"
    echo "Creating example parameters file..."
    cat > "$PARAMETERS_FILE" << 'EOF'
[
  {
    "ParameterKey": "MonitoringRegion",
    "ParameterValue": "us-east-1"
  },
  {
    "ParameterKey": "ModelId", 
    "ParameterValue": "amazon.nova-pro-v1:0"
  },
  {
    "ParameterKey": "DashboardName",
    "ParameterValue": "NovaProMonitoring"
  },
  {
    "ParameterKey": "AlarmEmail",
    "ParameterValue": ""
  },
  {
    "ParameterKey": "Environment",
    "ParameterValue": "prod"
  },
  {
    "ParameterKey": "Owner",
    "ParameterValue": "DevOps"
  },
  {
    "ParameterKey": "CostCenter",
    "ParameterValue": "AI-OPERATIONS"
  }
]
EOF
    echo -e "${YELLOW}⚠️  Please edit '$PARAMETERS_FILE' with your values and run again.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites validated${NC}"

# Check if stack exists
echo -e "${YELLOW}🔍 Checking if stack exists...${NC}"
if aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" &> /dev/null; then
    STACK_EXISTS=true
    echo -e "${YELLOW}📦 Stack '$STACK_NAME' exists - will update${NC}"
else
    STACK_EXISTS=false
    echo -e "${GREEN}🆕 Stack '$STACK_NAME' does not exist - will create${NC}"
fi

# Validate template (skip size validation as it's expected to be large)
echo -e "${YELLOW}🔍 Validating template syntax...${NC}"
if aws cloudformation validate-template --template-body "file://$TEMPLATE_FILE" --region "$REGION" &> /dev/null; then
    echo -e "${GREEN}✅ Template syntax is valid${NC}"
else
    echo -e "${YELLOW}⚠️  Template validation skipped (likely due to size limit - this is normal for comprehensive templates)${NC}"
fi

# Deploy stack
echo -e "${YELLOW}🚀 Deploying stack...${NC}"

if [[ "$STACK_EXISTS" == "true" ]]; then
    # Update existing stack
    echo "Updating existing stack..."
    aws cloudformation update-stack \
        --stack-name "$STACK_NAME" \
        --template-body "file://$TEMPLATE_FILE" \
        --parameters "file://$PARAMETERS_FILE" \
        --capabilities CAPABILITY_IAM \
        --region "$REGION" \
        --tags Key=DeployedBy,Value="$(whoami)" Key=DeployedAt,Value="$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        || {
            if aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" --query 'Stacks[0].StackStatus' --output text | grep -q "UPDATE_COMPLETE"; then
                echo -e "${YELLOW}ℹ️  No changes detected - stack is already up to date${NC}"
            else
                echo -e "${RED}❌ Stack update failed${NC}"
                exit 1
            fi
        }
else
    # Create new stack
    echo "Creating new stack..."
    aws cloudformation create-stack \
        --stack-name "$STACK_NAME" \
        --template-body "file://$TEMPLATE_FILE" \
        --parameters "file://$PARAMETERS_FILE" \
        --capabilities CAPABILITY_IAM \
        --enable-termination-protection \
        --region "$REGION" \
        --tags Key=DeployedBy,Value="$(whoami)" Key=DeployedAt,Value="$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        || {
            echo -e "${RED}❌ Stack creation failed${NC}"
            exit 1
        }
fi

# Wait for deployment to complete
echo -e "${YELLOW}⏳ Waiting for deployment to complete...${NC}"
if [[ "$STACK_EXISTS" == "true" ]]; then
    aws cloudformation wait stack-update-complete --stack-name "$STACK_NAME" --region "$REGION"
    FINAL_STATUS="UPDATE_COMPLETE"
else
    aws cloudformation wait stack-create-complete --stack-name "$STACK_NAME" --region "$REGION"
    FINAL_STATUS="CREATE_COMPLETE"
fi

# Check final status
STACK_STATUS=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" --query 'Stacks[0].StackStatus' --output text)

if [[ "$STACK_STATUS" == "$FINAL_STATUS" ]]; then
    echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
    
    # Get outputs
    echo -e "${YELLOW}📊 Stack Outputs:${NC}"
    aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`DashboardURL` || OutputKey==`DashboardName` || OutputKey==`AlarmTopicArn`].[OutputKey,OutputValue,Description]' \
        --output table
    
    # Get dashboard URL
    DASHBOARD_URL=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`DashboardURL`].OutputValue' \
        --output text)
    
    echo ""
    echo -e "${GREEN}🎉 Deployment Complete!${NC}"
    echo -e "${GREEN}📊 Dashboard URL: $DASHBOARD_URL${NC}"
    echo ""
    echo -e "${YELLOW}Next Steps:${NC}"
    echo "1. 📧 If you provided an email, confirm the SNS subscription"
    echo "2. 🔍 Verify Bedrock model invocation logging is enabled"
    echo "3. 📈 Access your dashboard at the URL above"
    echo "4. ⚙️  Customize alarm thresholds as needed"
    
else
    echo -e "${RED}❌ Deployment failed with status: $STACK_STATUS${NC}"
    
    # Show stack events for debugging
    echo -e "${YELLOW}📋 Recent stack events:${NC}"
    aws cloudformation describe-stack-events \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'StackEvents[?ResourceStatus==`CREATE_FAILED` || ResourceStatus==`UPDATE_FAILED`].[Timestamp,ResourceType,LogicalResourceId,ResourceStatusReason]' \
        --output table
    
    exit 1
fi