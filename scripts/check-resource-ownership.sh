#!/bin/bash

# Check Resource Ownership - Determine if resources were created by CloudFormation

set -euo pipefail

DASHBOARD_NAME="${1:-NovaProMonitoring}"
REGION="${2:-us-east-1}"

echo "🔍 Checking Resource Ownership"
echo "Dashboard: $DASHBOARD_NAME"
echo "Region: $REGION"
echo ""

# Get account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Check dashboard
echo "📊 Checking Dashboard..."
if aws cloudwatch get-dashboard --dashboard-name "$DASHBOARD_NAME" --region "$REGION" &> /dev/null; then
    echo "✅ Dashboard '$DASHBOARD_NAME' exists"
    
    # Try to find which stack owns it
    STACK_NAME=$(aws cloudformation list-stack-resources \
        --region "$REGION" \
        --query "StackResourceSummaries[?ResourceType=='AWS::CloudWatch::Dashboard' && PhysicalResourceId=='$DASHBOARD_NAME'].StackName" \
        --output text 2>/dev/null || echo "")
    
    if [[ -n "$STACK_NAME" && "$STACK_NAME" != "None" ]]; then
        echo "🏗️  Dashboard is managed by CloudFormation stack: $STACK_NAME"
        
        # Check stack status
        STACK_STATUS=$(aws cloudformation describe-stacks \
            --stack-name "$STACK_NAME" \
            --region "$REGION" \
            --query 'Stacks[0].StackStatus' \
            --output text 2>/dev/null || echo "UNKNOWN")
        echo "📋 Stack status: $STACK_STATUS"
        
        # Check deletion policy
        echo "🛡️  Checking deletion policy..."
        DELETION_POLICY=$(aws cloudformation describe-stack-resources \
            --stack-name "$STACK_NAME" \
            --region "$REGION" \
            --query "StackResources[?LogicalResourceId=='NovaProDashboard'].Metadata" \
            --output text 2>/dev/null || echo "")
        
        if [[ "$DELETION_POLICY" == *"Retain"* ]]; then
            echo "⚠️  Dashboard has DeletionPolicy: Retain (will NOT be deleted with stack)"
        else
            echo "🗑️  Dashboard will be deleted when stack is deleted"
        fi
    else
        echo "⚠️  Dashboard was created manually (not by CloudFormation)"
    fi
else
    echo "❌ Dashboard '$DASHBOARD_NAME' does not exist"
fi

echo ""

# Check SNS Topic
echo "📧 Checking SNS Topic..."
TOPIC_NAME="${DASHBOARD_NAME}-AlarmTopic"
TOPIC_ARN="arn:aws:sns:$REGION:$ACCOUNT_ID:$TOPIC_NAME"

if aws sns get-topic-attributes --topic-arn "$TOPIC_ARN" --region "$REGION" &> /dev/null; then
    echo "✅ SNS Topic '$TOPIC_NAME' exists"
    
    # Try to find which stack owns it
    STACK_NAME=$(aws cloudformation list-stack-resources \
        --region "$REGION" \
        --query "StackResourceSummaries[?ResourceType=='AWS::SNS::Topic' && PhysicalResourceId=='$TOPIC_ARN'].StackName" \
        --output text 2>/dev/null || echo "")
    
    if [[ -n "$STACK_NAME" && "$STACK_NAME" != "None" ]]; then
        echo "🏗️  SNS Topic is managed by CloudFormation stack: $STACK_NAME"
        
        # Check deletion policy
        DELETION_POLICY=$(aws cloudformation describe-stack-resources \
            --stack-name "$STACK_NAME" \
            --region "$REGION" \
            --query "StackResources[?LogicalResourceId=='AlarmTopic'].Metadata" \
            --output text 2>/dev/null || echo "")
        
        if [[ "$DELETION_POLICY" == *"Retain"* ]]; then
            echo "⚠️  SNS Topic has DeletionPolicy: Retain (will NOT be deleted with stack)"
        else
            echo "🗑️  SNS Topic will be deleted when stack is deleted"
        fi
    else
        echo "⚠️  SNS Topic was created manually (not by CloudFormation)"
    fi
else
    echo "❌ SNS Topic '$TOPIC_NAME' does not exist"
fi

echo ""

# Check for any existing stacks
echo "🏗️  Checking for existing CloudFormation stacks..."
STACKS=$(aws cloudformation list-stacks \
    --region "$REGION" \
    --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE ROLLBACK_COMPLETE CREATE_FAILED \
    --query "StackSummaries[?contains(StackName, 'nova') || contains(StackName, 'Nova')].{Name:StackName,Status:StackStatus}" \
    --output table 2>/dev/null || echo "")

if [[ -n "$STACKS" ]]; then
    echo "$STACKS"
else
    echo "No Nova-related stacks found"
fi

echo ""
echo "🎯 Summary & Recommendations:"
echo ""

# Provide recommendations based on findings
if aws cloudwatch get-dashboard --dashboard-name "$DASHBOARD_NAME" --region "$REGION" &> /dev/null; then
    STACK_NAME=$(aws cloudformation list-stack-resources \
        --region "$REGION" \
        --query "StackResourceSummaries[?ResourceType=='AWS::CloudWatch::Dashboard' && PhysicalResourceId=='$DASHBOARD_NAME'].StackName" \
        --output text 2>/dev/null || echo "")
    
    if [[ -n "$STACK_NAME" && "$STACK_NAME" != "None" ]]; then
        echo "✅ Resources are managed by CloudFormation"
        echo "💡 Recommendation: Delete the existing stack first, then redeploy"
        echo ""
        echo "Commands:"
        echo "aws cloudformation delete-stack --stack-name '$STACK_NAME' --region $REGION"
        echo "aws cloudformation wait stack-delete-complete --stack-name '$STACK_NAME' --region $REGION"
        echo ""
        echo "Note: Resources with DeletionPolicy: Retain will be preserved"
    else
        echo "⚠️  Resources were created manually"
        echo "💡 Recommendation: Use different names or manually delete existing resources"
        echo ""
        echo "Option 1 - Use different names (safest):"
        echo "Deploy with DashboardName: 'NovaProMonitoring-v2'"
        echo ""
        echo "Option 2 - Delete manually:"
        echo "aws cloudwatch delete-dashboards --dashboard-names '$DASHBOARD_NAME' --region $REGION"
        echo "aws sns delete-topic --topic-arn '$TOPIC_ARN' --region $REGION"
    fi
else
    echo "✅ No conflicting resources found"
    echo "💡 You can proceed with deployment using original names"
fi