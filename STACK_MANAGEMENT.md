# Nova Pro Dashboard - Stack Management Best Practices

## Overview

This document provides comprehensive guidance for managing the Nova Pro CloudWatch Dashboard CloudFormation stack according to AWS best practices for production environments.

## Stack Protection Strategy

### 1. Stack Policies

**Purpose**: Prevent accidental deletion or replacement of critical resources during stack updates.

**Implementation**: The stack includes a comprehensive stack policy (`stack-policy.json`) that:
- Denies replacement of critical resources (Dashboard, SNS Topic, Alarms, IAM Role/Policy)
- Denies deletion of critical resources
- Allows safe parameter and property updates
- Permits stack-level operations

**Application**:
```bash
# Apply stack policy after stack creation
aws cloudformation set-stack-policy \
  --stack-name nova-pro-dashboard-prod \
  --stack-policy-body file://stack-policy.json \
  --region us-east-1
```

### 2. Termination Protection

**Purpose**: Prevent accidental stack deletion.

**Implementation**:
```bash
# Enable termination protection
aws cloudformation update-termination-protection \
  --stack-name nova-pro-dashboard-prod \
  --enable-termination-protection \
  --region us-east-1
```

### 3. Resource Protection Policies

**Purpose**: Retain critical resources even if stack is deleted.

**Implementation**: All critical resources include:
```yaml
DeletionPolicy: Retain
UpdateReplacePolicy: Retain
```

## Rollback Configuration

### Automatic Rollback Triggers

The stack supports automatic rollback based on CloudWatch alarms:

```bash
# Deploy with rollback triggers
aws cloudformation create-stack \
  --stack-name nova-pro-dashboard-prod \
  --template-body file://nova-pro-dashboard-template.yaml \
  --parameters file://parameters.json \
  --capabilities CAPABILITY_NAMED_IAM \
  --rollback-configuration \
    RollbackTriggers='[
      {
        "Arn":"arn:aws:cloudwatch:us-east-1:123456789012:alarm:NovaProMonitoring-HighErrorRate",
        "Type":"AWS::CloudWatch::Alarm"
      },
      {
        "Arn":"arn:aws:cloudwatch:us-east-1:123456789012:alarm:NovaProMonitoring-HighP99Latency",
        "Type":"AWS::CloudWatch::Alarm"
      }
    ]',MonitoringTimeInMinutes=10 \
  --enable-termination-protection \
  --region us-east-1
```

### Manual Rollback Procedures

If issues are detected after deployment:

```bash
# Cancel stack update (if in progress)
aws cloudformation cancel-update-stack \
  --stack-name nova-pro-dashboard-prod \
  --region us-east-1

# Continue rollback (if stack is in UPDATE_ROLLBACK_FAILED state)
aws cloudformation continue-update-rollback \
  --stack-name nova-pro-dashboard-prod \
  --region us-east-1
```

## Drift Detection

### Automated Drift Detection

Use the provided script to set up automated drift detection:

```bash
# Set up automated drift detection and compliance monitoring
./drift-detection-setup.sh nova-pro-dashboard-prod us-east-1 your-config-bucket
```

### Manual Drift Detection

```bash
# Start drift detection
DRIFT_ID=$(aws cloudformation detect-stack-drift \
  --stack-name nova-pro-dashboard-prod \
  --region us-east-1 \
  --query 'StackDriftDetectionId' \
  --output text)

# Check drift status
aws cloudformation describe-stack-drift-detection-status \
  --stack-drift-detection-id $DRIFT_ID \
  --region us-east-1

# Get detailed drift results
aws cloudformation describe-stack-resource-drifts \
  --stack-name nova-pro-dashboard-prod \
  --region us-east-1
```

### Drift Remediation

When drift is detected:

1. **Assess Impact**: Review drift details to understand changes
2. **Update Template**: Incorporate legitimate changes into template
3. **Revert Changes**: Use AWS CLI to revert unauthorized changes
4. **Update Stack**: Deploy corrected template

```bash
# Example: Revert dashboard configuration drift
aws cloudwatch put-dashboard \
  --dashboard-name NovaProMonitoring \
  --dashboard-body file://correct-dashboard-config.json \
  --region us-east-1
```

## Comprehensive Tagging Strategy

### Required Tags

All resources must include these tags for proper management:

- **Environment**: prod, staging, dev, test
- **Owner**: Team or individual responsible
- **CostCenter**: Billing allocation code
- **Purpose**: NovaProMonitoring
- **Component**: Specific component (Dashboard, Alarm, etc.)

### Tag Compliance Monitoring

Use AWS Config to monitor tag compliance:

```bash
# Check tag compliance
aws configservice get-compliance-details-by-config-rule \
  --config-rule-name required-tags-nova-dashboard \
  --region us-east-1
```

## Backup and Recovery

### Template and Configuration Backup

```bash
# Export current template
aws cloudformation get-template \
  --stack-name nova-pro-dashboard-prod \
  --region us-east-1 \
  --template-stage Processed > backup-template-$(date +%Y%m%d).json

# Export current parameters
aws cloudformation describe-stacks \
  --stack-name nova-pro-dashboard-prod \
  --region us-east-1 \
  --query 'Stacks[0].Parameters' > backup-parameters-$(date +%Y%m%d).json

# Export dashboard configuration
aws cloudwatch get-dashboard \
  --dashboard-name NovaProMonitoring \
  --region us-east-1 > backup-dashboard-$(date +%Y%m%d).json

# Export alarm configurations
aws cloudwatch describe-alarms \
  --alarm-names \
    "NovaProMonitoring-HighErrorRate" \
    "NovaProMonitoring-HighP99Latency" \
    "NovaProMonitoring-DailyCostLimit" \
    "NovaProMonitoring-HighThrottlingRate" \
  --region us-east-1 > backup-alarms-$(date +%Y%m%d).json
```

### Disaster Recovery Procedures

1. **Complete Stack Recreation**:
   ```bash
   # Delete stack (if necessary)
   aws cloudformation delete-stack \
     --stack-name nova-pro-dashboard-prod \
     --region us-east-1
   
   # Recreate from backup
   aws cloudformation create-stack \
     --stack-name nova-pro-dashboard-prod \
     --template-body file://backup-template-YYYYMMDD.json \
     --parameters file://backup-parameters-YYYYMMDD.json \
     --capabilities CAPABILITY_NAMED_IAM \
     --enable-termination-protection \
     --region us-east-1
   ```

2. **Individual Resource Recovery**:
   ```bash
   # Restore dashboard from backup
   aws cloudwatch put-dashboard \
     --dashboard-name NovaProMonitoring \
     --dashboard-body file://backup-dashboard-YYYYMMDD.json \
     --region us-east-1
   ```

## Monitoring Stack Health

### Stack Status Monitoring

```bash
# Check stack status
aws cloudformation describe-stacks \
  --stack-name nova-pro-dashboard-prod \
  --region us-east-1 \
  --query 'Stacks[0].StackStatus'

# Monitor stack events
aws cloudformation describe-stack-events \
  --stack-name nova-pro-dashboard-prod \
  --region us-east-1 \
  --query 'StackEvents[0:10].[Timestamp,ResourceStatus,ResourceType,LogicalResourceId]' \
  --output table
```

### Resource Health Checks

```bash
# Verify dashboard accessibility
DASHBOARD_URL=$(aws cloudformation describe-stacks \
  --stack-name nova-pro-dashboard-prod \
  --region us-east-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`DashboardURL`].OutputValue' \
  --output text)

# Check alarm states
aws cloudwatch describe-alarms \
  --state-value ALARM \
  --region us-east-1

# Verify SNS topic health
aws sns get-topic-attributes \
  --topic-arn $(aws cloudformation describe-stacks \
    --stack-name nova-pro-dashboard-prod \
    --region us-east-1 \
    --query 'Stacks[0].Outputs[?OutputKey==`AlarmTopicArn`].OutputValue' \
    --output text) \
  --region us-east-1
```

## Update Management

### Safe Update Procedures

1. **Pre-Update Validation**:
   ```bash
   # Validate new template
   aws cloudformation validate-template \
     --template-body file://nova-pro-dashboard-template-new.yaml
   
   # Create change set
   aws cloudformation create-change-set \
     --stack-name nova-pro-dashboard-prod \
     --template-body file://nova-pro-dashboard-template-new.yaml \
     --parameters file://parameters-new.json \
     --change-set-name update-$(date +%Y%m%d-%H%M%S) \
     --capabilities CAPABILITY_NAMED_IAM \
     --region us-east-1
   
   # Review change set
   aws cloudformation describe-change-set \
     --stack-name nova-pro-dashboard-prod \
     --change-set-name update-$(date +%Y%m%d-%H%M%S) \
     --region us-east-1
   ```

2. **Execute Update**:
   ```bash
   # Execute change set
   aws cloudformation execute-change-set \
     --stack-name nova-pro-dashboard-prod \
     --change-set-name update-$(date +%Y%m%d-%H%M%S) \
     --region us-east-1
   
   # Monitor update progress
   aws cloudformation wait stack-update-complete \
     --stack-name nova-pro-dashboard-prod \
     --region us-east-1
   ```

### Parameter-Only Updates

For threshold adjustments and other parameter changes:

```bash
# Safe parameter update
aws cloudformation update-stack \
  --stack-name nova-pro-dashboard-prod \
  --use-previous-template \
  --parameters \
    ParameterKey=ErrorRateThreshold,ParameterValue=3 \
    ParameterKey=P99LatencyThreshold,ParameterValue=4000 \
  --region us-east-1
```

## Compliance and Governance

### AWS Config Integration

Monitor stack compliance with organizational policies:

```bash
# Check CloudFormation stack compliance
aws configservice get-compliance-details-by-config-rule \
  --config-rule-name cloudformation-stack-termination-protection-enabled \
  --region us-east-1

# Check resource tagging compliance
aws configservice get-compliance-details-by-config-rule \
  --config-rule-name required-tags-nova-dashboard \
  --region us-east-1
```

### Service Quotas Monitoring

Monitor AWS service quotas to prevent deployment failures:

```bash
# Check CloudWatch quotas
aws service-quotas get-service-quota \
  --service-code cloudwatch \
  --quota-code L-5E141212 \
  --region us-east-1  # Dashboards per region

aws service-quotas get-service-quota \
  --service-code cloudwatch \
  --quota-code L-F678F1CE \
  --region us-east-1  # Alarms per region

# Check SNS quotas
aws service-quotas get-service-quota \
  --service-code sns \
  --quota-code L-309BEFB2 \
  --region us-east-1  # Topics per region
```

## Incident Response

### Stack Failure Response

1. **Immediate Assessment**:
   ```bash
   # Check stack status
   aws cloudformation describe-stacks \
     --stack-name nova-pro-dashboard-prod \
     --region us-east-1
   
   # Review recent events
   aws cloudformation describe-stack-events \
     --stack-name nova-pro-dashboard-prod \
     --region us-east-1 \
     --query 'StackEvents[?ResourceStatus==`CREATE_FAILED` || ResourceStatus==`UPDATE_FAILED`]'
   ```

2. **Resource-Level Investigation**:
   ```bash
   # Check individual resource status
   aws cloudformation list-stack-resources \
     --stack-name nova-pro-dashboard-prod \
     --region us-east-1
   
   # Get detailed resource information
   aws cloudformation describe-stack-resource \
     --stack-name nova-pro-dashboard-prod \
     --logical-resource-id NovaProDashboard \
     --region us-east-1
   ```

3. **Recovery Actions**:
   - Review CloudTrail logs for unauthorized changes
   - Check IAM permissions for deployment principal
   - Verify service quotas haven't been exceeded
   - Execute rollback procedures if necessary

### Communication Templates

**Incident Notification**:
```
SUBJECT: Nova Pro Dashboard Stack Issue - [SEVERITY]

Stack Name: nova-pro-dashboard-prod
Region: us-east-1
Status: [CURRENT_STATUS]
Issue: [DESCRIPTION]
Impact: [IMPACT_ASSESSMENT]
ETA: [ESTIMATED_RESOLUTION_TIME]

Actions Taken:
- [ACTION_1]
- [ACTION_2]

Next Steps:
- [NEXT_STEP_1]
- [NEXT_STEP_2]
```

## Maintenance Schedule

### Daily
- Monitor stack status and alarm states
- Review CloudWatch costs and usage

### Weekly
- Run drift detection
- Review stack events and changes
- Backup current configuration

### Monthly
- Review and update alarm thresholds based on usage patterns
- Audit IAM role usage and permissions
- Update Nova Pro pricing constants if changed
- Review service quota utilization

### Quarterly
- Test disaster recovery procedures
- Review and update stack policies
- Conduct security review of IAM policies
- Update documentation and runbooks

## Troubleshooting Guide

### Common Issues and Solutions

1. **Stack Update Fails with "No updates are to be performed"**:
   - Verify template changes are significant enough to trigger update
   - Check if parameters have actually changed
   - Use change sets to preview updates

2. **Resource Already Exists Error**:
   - Check for naming conflicts with existing resources
   - Verify stack wasn't partially created previously
   - Use unique naming patterns with stack name prefix

3. **IAM Permission Errors**:
   - Verify deployment principal has necessary permissions
   - Check resource-based policies (SNS topic policy)
   - Ensure cross-account trust relationships are correct

4. **Alarm Not Triggering**:
   - Verify metric data is being published
   - Check alarm threshold and evaluation settings
   - Confirm SNS subscription is active and confirmed

5. **Dashboard Shows No Data**:
   - Ensure Nova Pro model is being invoked in the region
   - Verify model ID parameter matches actual usage
   - Check CloudWatch metrics publication (5-15 minute delay)

### Support Escalation

For issues requiring AWS Support:

1. Gather diagnostic information:
   ```bash
   # Collect stack information
   aws cloudformation describe-stacks \
     --stack-name nova-pro-dashboard-prod \
     --region us-east-1 > support-stack-info.json
   
   # Collect recent events
   aws cloudformation describe-stack-events \
     --stack-name nova-pro-dashboard-prod \
     --region us-east-1 > support-stack-events.json
   
   # Collect resource details
   aws cloudformation list-stack-resources \
     --stack-name nova-pro-dashboard-prod \
     --region us-east-1 > support-resource-list.json
   ```

2. Include in support case:
   - Stack name and region
   - Template version and deployment method
   - Error messages and timestamps
   - Recent changes or updates
   - Diagnostic files collected above

This comprehensive stack management approach ensures the Nova Pro Dashboard maintains high availability, security, and operational excellence in production environments.