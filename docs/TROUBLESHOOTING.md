# Troubleshooting Guide

## Common Issues and Solutions

### 🚨 Deployment Issues

#### "Resource Already Exists" Error
**Error**: `Dashboard 'NovaProMonitoring' already exists`

**Solution**:
1. **Use different names** (recommended):
   - Change `DashboardName` parameter to `NovaProMonitoring-v2`
   - Use different stack name: `nova-pro-dashboard-v2`

2. **Delete existing resources**:
   - CloudWatch Console → Dashboards → Delete existing dashboard
   - SNS Console → Topics → Delete existing topic

#### "Invalid Principal in Policy" Error
**Error**: `Invalid principal in policy: "AWS":"arn:aws:iam::ACCOUNT:user/dashboard-admin"`

**Solution**: ✅ **FIXED** - Template no longer creates IAM roles. Use your existing role with required permissions.

#### Template Size Warning
**Warning**: Template exceeds CloudFormation validation limit

**Solution**: This is normal for comprehensive templates. Deploy directly without validation.

### 🔑 Access Issues

#### Dashboard Not Visible
**Symptoms**: Can't see dashboard in CloudWatch console

**Solutions**:
1. **Check IAM permissions**: Ensure `cloudwatch:GetDashboard` permission
2. **Verify region**: Confirm you're in the correct AWS region
3. **Check dashboard name**: Ensure name matches deployment parameters

#### Metrics Not Loading
**Symptoms**: Dashboard widgets show "No data available"

**Solutions**:
1. **Check IAM permissions**: Verify `cloudwatch:GetMetricData` permission
2. **Verify namespace condition**: Ensure IAM policy includes Bedrock namespaces
3. **Wait for data**: New deployments may take 5-10 minutes for first metrics
4. **Check model usage**: Ensure Nova Pro model is being used

#### Log Widgets Empty
**Symptoms**: Log-based widgets show no data

**Solutions**:
1. **Enable Bedrock logging**:
   ```bash
   aws bedrock put-model-invocation-logging-configuration \
     --logging-config '{
       "cloudWatchConfig": {
         "logGroupName": "/aws/bedrock/modelinvocations"
       },
       "textDataDeliveryEnabled": true
     }'
   ```
2. **Check log permissions**: Verify `logs:StartQuery` permission
3. **Verify log group**: Ensure log group exists and matches model ID

### 📧 Notification Issues

#### Email Notifications Not Working
**Symptoms**: Not receiving alarm emails

**Solutions**:
1. **Check email confirmation**: Look for SNS subscription confirmation email
2. **Confirm subscription**: Click confirmation link in email
3. **Check spam folder**: SNS emails may be filtered
4. **Verify SNS topic**: Ensure topic was created successfully

#### Alarms Not Triggering
**Symptoms**: Alarms stay in "Insufficient data" state

**Solutions**:
1. **Wait for data**: Alarms need metric data to evaluate
2. **Check thresholds**: Verify alarm thresholds are appropriate
3. **Test manually**: Temporarily lower thresholds to test
4. **Verify metrics**: Ensure underlying metrics are being generated

### 💰 Cost Issues

#### Unexpected Costs
**Symptoms**: Higher than expected AWS charges

**Solutions**:
1. **Review cost breakdown**: Check CloudWatch, SNS, and log storage costs
2. **Optimize log retention**: Reduce log group retention period
3. **Adjust alarm frequency**: Reduce alarm evaluation frequency
4. **Monitor usage**: Use cost widgets to track spending

#### Cost Calculations Incorrect
**Symptoms**: Dashboard cost estimates don't match billing

**Solutions**:
1. **Update pricing**: Modify cost calculations if AWS pricing changes
2. **Check regions**: Pricing may vary by region
3. **Verify token counts**: Ensure token metrics are accurate

### 🔧 Performance Issues

#### Dashboard Loading Slowly
**Symptoms**: Dashboard takes long time to load

**Solutions**:
1. **Reduce time range**: Use shorter time periods for widgets
2. **Optimize queries**: Simplify complex log queries
3. **Check region**: Ensure dashboard and data are in same region

#### High Memory Usage
**Symptoms**: Browser becomes slow when viewing dashboard

**Solutions**:
1. **Reduce widget count**: Remove unnecessary widgets
2. **Increase refresh interval**: Reduce auto-refresh frequency
3. **Use smaller time ranges**: Limit data volume per widget

### 🛡️ Security Issues

#### Access Denied Errors
**Symptoms**: "User is not authorized to perform" errors

**Solutions**:
1. **Check IAM policy**: Verify all required actions are included
2. **Verify resource ARNs**: Ensure ARNs match your account/region
3. **Check conditions**: Verify namespace and region conditions
4. **Test permissions**: Use IAM policy simulator

#### Cross-Account Access Issues
**Symptoms**: Can't access dashboard from different account

**Solutions**:
1. **Update resource ARNs**: Include cross-account resource ARNs
2. **Modify conditions**: Adjust region/account conditions
3. **Check trust policies**: Verify cross-account trust relationships

### 📊 Data Issues

#### Missing User/Application Data
**Symptoms**: User and application tracking widgets show no data

**Solutions**:
1. **Check metadata format**: Ensure requests include proper metadata:
   ```json
   {
     "metadata": {
       "userId": "john.doe",
       "applicationName": "chatbot"
     }
   }
   ```
2. **Verify field names**: Match `UserIdentityField` and `ApplicationIdentityField` parameters
3. **Check log parsing**: Verify log queries parse metadata correctly

#### Guardrail Data Missing
**Symptoms**: Guardrail widgets show no interventions

**Solutions**:
1. **Enable guardrails**: Ensure guardrails are configured for your model
2. **Check permissions**: Verify access to `AWS/Bedrock/Guardrails` namespace
3. **Test guardrails**: Trigger interventions to generate data

## 🔍 Diagnostic Steps

### 1. Check CloudFormation Events
1. Go to CloudFormation Console
2. Select your stack
3. Click "Events" tab
4. Look for error messages

### 2. Verify IAM Permissions
1. Go to IAM Console
2. Find your role
3. Check attached policies
4. Use IAM Policy Simulator to test

### 3. Check CloudWatch Logs
1. Go to CloudWatch Console
2. Click "Logs" → "Log groups"
3. Look for `/aws/bedrock/modelinvocations` logs
4. Verify log entries exist

### 4. Test Bedrock Access
```bash
# Test model access
aws bedrock list-foundation-models --region us-east-1

# Check logging configuration
aws bedrock get-model-invocation-logging-configuration --region us-east-1
```

### 5. Validate Template
```bash
# Use validation script
python3 scripts/validate-template.py nova-pro-dashboard-compact.yaml
```

## 📞 Getting Help

### Before Asking for Help
1. **Check this troubleshooting guide**
2. **Review CloudFormation events**
3. **Verify IAM permissions**
4. **Check AWS service status**

### When Reporting Issues
Include:
- **Error messages** (exact text)
- **CloudFormation events** (screenshots)
- **IAM policy** (redacted)
- **AWS region** and **account type**
- **Steps to reproduce**

### Support Channels
- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and community help
- **AWS Support**: For AWS service-specific issues

## 🔄 Recovery Procedures

### Complete Stack Recreation
If stack is corrupted:
1. **Export dashboard configuration**:
   ```bash
   aws cloudwatch get-dashboard --dashboard-name NovaProMonitoring > backup.json
   ```
2. **Delete stack**
3. **Wait for complete deletion**
4. **Redeploy with new stack name**
5. **Restore custom configurations**

### Partial Resource Recovery
If only some resources failed:
1. **Identify failed resources** in CloudFormation events
2. **Delete failed resources manually**
3. **Update stack** to recreate missing resources

### Data Recovery
If monitoring data is lost:
1. **Check CloudWatch metric retention** (15 months default)
2. **Review log group retention** settings
3. **Restore from backups** if available
4. **Reconfigure logging** if needed