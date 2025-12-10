# Nova Pro CloudWatch Dashboard - Deployment Guide

## Production Deployment Checklist

### Pre-Deployment Steps

1. **Validate Template**
   ```bash
   cfn-lint nova-pro-dashboard-template.yaml
   aws cloudformation validate-template --template-body file://nova-pro-dashboard-template.yaml
   ```

2. **Review Stack Policy**
   - Ensure `stack-policy.json` protects critical resources from replacement
   - Current policy protects: Dashboard, SNS Topic, Alarms, IAM Role

3. **Prepare Parameters**
   ```bash
   # Required parameters
   MONITORING_REGION="us-east-1"  # Region where Bedrock is available
   
   # Optional parameters (customize as needed)
   DASHBOARD_NAME="NovaProMonitoring"
   ERROR_RATE_THRESHOLD="5"
   P99_LATENCY_THRESHOLD="5000"
   DAILY_COST_THRESHOLD="1000"
   THROTTLE_RATE_THRESHOLD="10"
   ALARM_EMAIL="ops-team@company.com"  # Optional
   ENVIRONMENT="prod"
   OWNER="DevOps"
   COST_CENTER="AI-Operations"
   ```

### Production Deployment

```bash
# Deploy with full protection and rollback configuration
aws cloudformation create-stack \
  --stack-name nova-pro-dashboard-prod \
  --template-body file://nova-pro-dashboard-template.yaml \
  --parameters \
    ParameterKey=MonitoringRegion,ParameterValue=$MONITORING_REGION \
    ParameterKey=DashboardName,ParameterValue=$DASHBOARD_NAME \
    ParameterKey=ErrorRateThreshold,ParameterValue=$ERROR_RATE_THRESHOLD \
    ParameterKey=P99LatencyThreshold,ParameterValue=$P99_LATENCY_THRESHOLD \
    ParameterKey=DailyCostThreshold,ParameterValue=$DAILY_COST_THRESHOLD \
    ParameterKey=ThrottleRateThreshold,ParameterValue=$THROTTLE_RATE_THRESHOLD \
    ParameterKey=AlarmEmail,ParameterValue=$ALARM_EMAIL \
    ParameterKey=Environment,ParameterValue=$ENVIRONMENT \
    ParameterKey=Owner,ParameterValue=$OWNER \
    ParameterKey=CostCenter,ParameterValue=$COST_CENTER \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --rollback-configuration \
    RollbackTriggers='[
      {
        "Arn":"arn:aws:cloudwatch:'$MONITORING_REGION':'$(aws sts get-caller-identity --query Account --output text)':alarm:'$DASHBOARD_NAME'-HighErrorRate",
        "Type":"AWS::CloudWatch::Alarm"
      },
      {
        "Arn":"arn:aws:cloudwatch:'$MONITORING_REGION':'$(aws sts get-caller-identity --query Account --output text)':alarm:'$DASHBOARD_NAME'-HighP99Latency",
        "Type":"AWS::CloudWatch::Alarm"
      }
    ]',MonitoringTimeInMinutes=5 \
  --enable-termination-protection \
  --tags \
    Key=Environment,Value=$ENVIRONMENT \
    Key=Owner,Value=$OWNER \
    Key=CostCenter,Value=$COST_CENTER \
    Key=Purpose,Value=NovaProMonitoring \
  --region $MONITORING_REGION

# Apply stack policy immediately after creation
aws cloudformation set-stack-policy \
  --stack-name nova-pro-dashboard-prod \
  --stack-policy-body file://stack-policy.json \
  --region $MONITORING_REGION
```

### Post-Deployment Verification

1. **Verify Stack Creation**
   ```bash
   aws cloudformation describe-stacks \
     --stack-name nova-pro-dashboard-prod \
     --region $MONITORING_REGION \
     --query 'Stacks[0].StackStatus'
   ```

2. **Test Dashboard Access**
   ```bash
   # Get dashboard URL from stack outputs
   DASHBOARD_URL=$(aws cloudformation describe-stacks \
     --stack-name nova-pro-dashboard-prod \
     --region $MONITORING_REGION \
     --query 'Stacks[0].Outputs[?OutputKey==`DashboardURL`].OutputValue' \
     --output text)
   
   echo "Dashboard URL: $DASHBOARD_URL"
   ```

3. **Verify Alarm Configuration**
   ```bash
   aws cloudwatch describe-alarms \
     --alarm-names \
       "$DASHBOARD_NAME-HighErrorRate" \
       "$DASHBOARD_NAME-HighP99Latency" \
       "$DASHBOARD_NAME-DailyCostLimit" \
       "$DASHBOARD_NAME-HighThrottlingRate" \
     --region $MONITORING_REGION
   ```

4. **Test SNS Subscription** (if email provided)
   ```bash
   # Check SNS topic and subscription
   aws sns list-subscriptions-by-topic \
     --topic-arn $(aws cloudformation describe-stacks \
       --stack-name nova-pro-dashboard-prod \
       --region $MONITORING_REGION \
       --query 'Stacks[0].Outputs[?OutputKey==`AlarmTopicArn`].OutputValue' \
       --output text) \
     --region $MONITORING_REGION
   ```

## Stack Management Operations

### Drift Detection

```bash
# Start drift detection
DRIFT_ID=$(aws cloudformation detect-stack-drift \
  --stack-name nova-pro-dashboard-prod \
  --region $MONITORING_REGION \
  --query 'StackDriftDetectionId' \
  --output text)

# Check drift status
aws cloudformation describe-stack-drift-detection-status \
  --stack-drift-detection-id $DRIFT_ID \
  --region $MONITORING_REGION

# Get detailed drift results
aws cloudformation describe-stack-resource-drifts \
  --stack-name nova-pro-dashboard-prod \
  --region $MONITORING_REGION
```

### Stack Updates

```bash
# Update stack (parameters only - safe operation)
aws cloudformation update-stack \
  --stack-name nova-pro-dashboard-prod \
  --template-body file://nova-pro-dashboard-template.yaml \
  --parameters \
    ParameterKey=ErrorRateThreshold,ParameterValue=3 \
    ParameterKey=P99LatencyThreshold,ParameterValue=4000 \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --region $MONITORING_REGION

# Monitor update progress
aws cloudformation describe-stack-events \
  --stack-name nova-pro-dashboard-prod \
  --region $MONITORING_REGION \
  --query 'StackEvents[0:10].[Timestamp,ResourceStatus,ResourceType,LogicalResourceId]' \
  --output table
```

### Backup and Recovery

```bash
# Export current template
aws cloudformation get-template \
  --stack-name nova-pro-dashboard-prod \
  --region $MONITORING_REGION \
  --template-stage Processed \
  > current-template-backup.json

# Export current parameters
aws cloudformation describe-stacks \
  --stack-name nova-pro-dashboard-prod \
  --region $MONITORING_REGION \
  --query 'Stacks[0].Parameters' \
  > current-parameters-backup.json
```

## Security Best Practices

### Security Review Summary

**CRITICAL SECURITY FINDINGS** - Address before production deployment:

1. **IAM Trust Policy Too Permissive**: DashboardViewerRole allows any principal in the account
2. **CloudWatch Permissions Lack Region Scoping**: Metrics permissions don't restrict region access
3. **Logs Permissions Too Broad**: Access to all Bedrock model logs instead of specific model
4. **Missing Resource Protection**: Critical resources lack DeletionPolicy/UpdateReplacePolicy

### Pre-Deployment Security Hardening

**1. Fix IAM Trust Policy (CRITICAL)**

The current trust policy allows any principal in the account to assume the role:
```yaml
# CURRENT (INSECURE)
Principal:
  AWS: 'arn:aws:iam::${AWS::AccountId}:root'

# RECOMMENDED (SECURE)
Principal:
  AWS:
    - 'arn:aws:iam::${AWS::AccountId}:user/dashboard-admin'
    - 'arn:aws:iam::${AWS::AccountId}:role/MonitoringTeamRole'
```

**2. Add Region Scoping to CloudWatch Permissions**

Current CloudWatch permissions lack region restrictions:
```yaml
# ADD to CloudWatch metrics condition:
Condition:
  StringEquals:
    'cloudwatch:namespace': ['AWS/Bedrock', 'AWS/Bedrock/Guardrails']
    'aws:RequestedRegion': !Ref MonitoringRegion  # ADD THIS LINE
```

**3. Scope Logs Permissions to Specific Model**

Current logs permissions are too broad:
```yaml
# CURRENT (TOO BROAD)
Resource: 'arn:aws:logs:${MonitoringRegion}:${AWS::AccountId}:log-group:/aws/bedrock/modelinvocations*'

# RECOMMENDED (MODEL-SPECIFIC)
Resource: 'arn:aws:logs:${MonitoringRegion}:${AWS::AccountId}:log-group:/aws/bedrock/modelinvocations/${ModelId}*'
```

**4. Add Resource Protection Policies**

Add to all critical resources:
```yaml
DeletionPolicy: Retain
UpdateReplacePolicy: Retain
```

### IAM Access Management

```bash
# Use the dashboard viewer role for read-only access
VIEWER_ROLE_ARN=$(aws cloudformation describe-stacks \
  --stack-name nova-pro-dashboard-prod \
  --region $MONITORING_REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`DashboardViewerRoleArn`].OutputValue' \
  --output text)

# Assume role for dashboard access
aws sts assume-role \
  --role-arn $VIEWER_ROLE_ARN \
  --role-session-name dashboard-viewer-session
```

### Security Validation Commands

Run these after deployment to verify security configuration:

```bash
# 1. Verify IAM role permissions are scoped correctly
aws iam simulate-principal-policy \
  --policy-source-arn $VIEWER_ROLE_ARN \
  --action-names cloudwatch:GetMetricData \
  --resource-arns "*" \
  --context-entries ContextKeyName=aws:RequestedRegion,ContextKeyValues=$MONITORING_REGION,ContextKeyType=string

# 2. Test role assumption (should succeed for authorized principals only)
aws sts assume-role \
  --role-arn $VIEWER_ROLE_ARN \
  --role-session-name security-validation-test

# 3. Enable IAM Access Analyzer for unused permissions detection
aws accessanalyzer create-analyzer \
  --analyzer-name nova-dashboard-analyzer \
  --type ACCOUNT \
  --region $MONITORING_REGION

# 4. Check for security findings
aws accessanalyzer list-findings \
  --analyzer-arn arn:aws:access-analyzer:$MONITORING_REGION:$(aws sts get-caller-identity --query Account --output text):analyzer/nova-dashboard-analyzer \
  --region $MONITORING_REGION

# 5. Verify SNS topic encryption
aws sns get-topic-attributes \
  --topic-arn $(aws cloudformation describe-stacks \
    --stack-name nova-pro-dashboard-prod \
    --region $MONITORING_REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`AlarmTopicArn`].OutputValue' \
    --output text) \
  --region $MONITORING_REGION
```

### Monitoring Stack Security

```bash
# Enable CloudTrail for stack API monitoring
aws cloudtrail create-trail \
  --name nova-dashboard-audit-trail \
  --s3-bucket-name your-cloudtrail-bucket \
  --include-global-service-events \
  --is-multi-region-trail \
  --enable-log-file-validation \
  --region $MONITORING_REGION

# Create CloudWatch alarm for unauthorized stack modifications
aws cloudwatch put-metric-alarm \
  --alarm-name "UnauthorizedStackModification" \
  --alarm-description "Detects unauthorized CloudFormation stack modifications" \
  --metric-name "CloudFormationStackModification" \
  --namespace "Custom/Security" \
  --statistic "Sum" \
  --period 300 \
  --threshold 1 \
  --comparison-operator "GreaterThanOrEqualToThreshold" \
  --evaluation-periods 1 \
  --region $MONITORING_REGION

# Monitor IAM role usage with CloudTrail
aws logs create-log-group \
  --log-group-name /aws/cloudtrail/nova-dashboard-security \
  --region $MONITORING_REGION

# Create metric filter for role assumption events
aws logs put-metric-filter \
  --log-group-name /aws/cloudtrail/nova-dashboard-security \
  --filter-name "DashboardRoleAssumption" \
  --filter-pattern '{ ($.eventName = AssumeRole) && ($.responseElements.assumedRoleUser.arn = "*DashboardViewerRole*") }' \
  --metric-transformations \
    metricName=DashboardRoleAssumptions,metricNamespace=Security/IAM,metricValue=1 \
  --region $MONITORING_REGION
```

### Security Compliance Checklist

Before production deployment, verify:

- [ ] IAM trust policy restricts access to specific users/roles (not account root)
- [ ] CloudWatch permissions include region scoping conditions
- [ ] Logs permissions are scoped to specific model logs
- [ ] All critical resources have DeletionPolicy: Retain
- [ ] SNS topic uses KMS encryption (✅ already configured)
- [ ] No hardcoded credentials in template (✅ verified)
- [ ] AlarmEmail parameter uses NoEcho: true (✅ already configured)
- [ ] IAM Access Analyzer is enabled and monitoring for unused permissions
- [ ] CloudTrail is logging IAM role assumption events
- [ ] Security validation commands pass successfully

### Cross-Account Access Security

If sharing dashboard access across AWS accounts:

```bash
# Add external account to trust policy
# Modify DashboardViewerRole trust policy to include:
Principal:
  AWS:
    - 'arn:aws:iam::EXTERNAL-ACCOUNT-ID:root'
Condition:
  StringEquals:
    'sts:ExternalId': 'unique-external-id-here'
  IpAddress:
    'aws:SourceIp': ['203.0.113.0/24']  # Restrict source IP if needed
```

### Incident Response

If security issues are detected:

1. **Immediate Actions**:
   ```bash
   # Disable the IAM role temporarily
   aws iam attach-role-policy \
     --role-name ${DASHBOARD_NAME}-ViewerRole \
     --policy-arn arn:aws:iam::aws:policy/AWSDenyAll
   ```

2. **Investigation**:
   ```bash
   # Review CloudTrail logs for unauthorized access
   aws logs filter-log-events \
     --log-group-name /aws/cloudtrail/nova-dashboard-security \
     --start-time $(date -d '1 hour ago' +%s)000 \
     --filter-pattern '{ $.userIdentity.type = "AssumedRole" }'
   ```

3. **Recovery**:
   ```bash
   # Remove deny policy and update trust policy
   aws iam detach-role-policy \
     --role-name ${DASHBOARD_NAME}-ViewerRole \
     --policy-arn arn:aws:iam::aws:policy/AWSDenyAll
   
   # Update stack with corrected IAM policies
   aws cloudformation update-stack \
     --stack-name nova-pro-dashboard-prod \
     --template-body file://nova-pro-dashboard-template-secure.yaml
   ```

## Cost Optimization

### Monthly Cost Estimate

- **CloudWatch Dashboard**: $3.00/month
- **CloudWatch Alarms**: $0.40/month (4 alarms × $0.10)
- **SNS Topic**: $0.00 (first 1,000 notifications free)
- **Total**: ~$3.40/month

### Cost Monitoring

```bash
# Monitor CloudWatch costs
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=DIMENSION,Key=SERVICE \
  --filter file://cloudwatch-cost-filter.json
```

## Troubleshooting

### Common Issues

1. **Stack Creation Fails**
   - Check IAM permissions for CloudFormation, CloudWatch, SNS, IAM
   - Verify Bedrock is available in the specified region
   - Check parameter values are within allowed ranges

2. **Dashboard Shows No Data**
   - Ensure Nova Pro model has been invoked in the monitored region
   - Verify model ID parameter matches actual model being used
   - Check CloudWatch metrics are being published (may take 5-15 minutes)

3. **Alarms Not Triggering**
   - Verify alarm thresholds are appropriate for your usage patterns
   - Check alarm evaluation periods and missing data treatment
   - Ensure SNS topic subscription is confirmed (check email)

4. **Permission Denied Errors**
   - Use the DashboardViewerRole for read-only access
   - Verify IAM policies are correctly attached
   - Check resource-based policies on CloudWatch and SNS

### Support Commands

```bash
# Get stack status and events
aws cloudformation describe-stack-events \
  --stack-name nova-pro-dashboard-prod \
  --region $MONITORING_REGION \
  --query 'StackEvents[?ResourceStatus==`CREATE_FAILED` || ResourceStatus==`UPDATE_FAILED`]'

# Check resource status
aws cloudformation list-stack-resources \
  --stack-name nova-pro-dashboard-prod \
  --region $MONITORING_REGION

# Validate current template
aws cloudformation validate-template \
  --template-url $(aws cloudformation describe-stacks \
    --stack-name nova-pro-dashboard-prod \
    --region $MONITORING_REGION \
    --query 'Stacks[0].TemplateDescription')
```

## Maintenance Schedule

### Weekly
- Review drift detection results
- Check alarm states and recent triggers
- Monitor CloudWatch costs

### Monthly
- Update Nova Pro pricing constants if changed
- Review and rotate SNS topic access keys (if using programmatic access)
- Audit IAM role usage with Access Analyzer

### Quarterly
- Review alarm thresholds based on usage patterns
- Update template with new Bedrock metrics (if available)
- Test disaster recovery procedures