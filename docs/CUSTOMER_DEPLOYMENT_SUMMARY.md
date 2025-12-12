# Nova Pro Dashboard - Customer Deployment Summary

## 🎯 What This Template Creates

The Nova Pro CloudWatch Dashboard template creates **monitoring infrastructure only** - no IAM roles or policies. You'll use your existing IAM role to access the dashboard.

### Resources Created:
- ✅ **CloudWatch Dashboard** - Nova Pro monitoring dashboard
- ✅ **CloudWatch Alarms** - 4 alarms for error rate, latency, cost, and throttling
- ✅ **SNS Topic** - For alarm notifications (optional, if email provided)
- ✅ **SNS Subscription** - Email subscription (optional, if email provided)

### Resources NOT Created:
- ❌ **No IAM Roles** - You'll use your existing role
- ❌ **No IAM Policies** - You'll add permissions to your existing role

## 🔑 Required IAM Permissions

Add this policy to your existing IAM role:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CloudWatchDashboardAccess",
      "Effect": "Allow",
      "Action": [
        "cloudwatch:GetDashboard",
        "cloudwatch:ListDashboards"
      ],
      "Resource": [
        "arn:aws:cloudwatch:*:*:dashboard/NovaProMonitoring",
        "arn:aws:cloudwatch:*:*:dashboard/*"
      ]
    },
    {
      "Sid": "CloudWatchMetricsAccess",
      "Effect": "Allow",
      "Action": [
        "cloudwatch:GetMetricData",
        "cloudwatch:GetMetricStatistics",
        "cloudwatch:ListMetrics"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "cloudwatch:namespace": [
            "AWS/Bedrock",
            "AWS/Bedrock/Guardrails"
          ]
        }
      }
    },
    {
      "Sid": "CloudWatchLogsAccess",
      "Effect": "Allow",
      "Action": [
        "logs:StartQuery",
        "logs:GetQueryResults",
        "logs:StopQuery",
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams",
        "logs:FilterLogEvents"
      ],
      "Resource": [
        "arn:aws:logs:*:*:log-group:/aws/bedrock/modelinvocations/amazon.nova-pro-v1:0*",
        "arn:aws:logs:*:*:log-group:/aws/bedrock/modelinvocations/amazon.nova-pro-v1:0:*"
      ]
    },
    {
      "Sid": "BedrockReadOnlyAccess",
      "Effect": "Allow",
      "Action": [
        "bedrock:GetModelInvocationLoggingConfiguration",
        "bedrock:ListFoundationModels"
      ],
      "Resource": "*"
    }
  ]
}
```

## 🚀 Deployment Steps

### 1. Deploy the Template
```bash
aws cloudformation create-stack \
  --stack-name nova-pro-dashboard \
  --template-body file://nova-pro-dashboard-compact.yaml \
  --parameters file://parameters.json \
  --region us-east-1
```

### 2. Configure Parameters
Create `parameters.json`:
```json
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
    "ParameterValue": "your-email@company.com"
  },
  {
    "ParameterKey": "Environment",
    "ParameterValue": "prod"
  }
]
```

### 3. Add IAM Permissions
Add the policy above to your existing IAM role.

### 4. Access Dashboard
Navigate to: CloudWatch → Dashboards → NovaProMonitoring

## 📊 What You'll See

### Dashboard Widgets:
- **Usage Metrics**: Invocations, TPM, concurrent requests
- **Cost Analysis**: Daily costs, cost per request, token cost breakdown
- **Performance**: Latency percentiles, cache efficiency
- **Error Monitoring**: Error rates, error breakdown, recent errors
- **Guardrail Analytics**: Intervention rates, intervention types
- **User/App Tracking**: Usage by user and application (requires metadata)

### Alarms Created:
1. **High Error Rate** - Triggers when error rate > 5%
2. **High P99 Latency** - Triggers when P99 latency > 5000ms
3. **Daily Cost Limit** - Triggers when daily cost > $1000
4. **High Throttling Rate** - Triggers when throttling > 10%

## 🔧 Post-Deployment

### Enable Bedrock Logging (Required for detailed analytics)
```bash
aws bedrock put-model-invocation-logging-configuration \
  --logging-config '{
    "cloudWatchConfig": {
      "logGroupName": "/aws/bedrock/modelinvocations",
      "roleArn": "arn:aws:iam::ACCOUNT:role/service-role/AmazonBedrockExecutionRoleForModelInvocationLogging"
    },
    "textDataDeliveryEnabled": true
  }'
```

### Confirm Email Subscription
If you provided an email, check for SNS confirmation and click the link.

### Test Dashboard Access
1. Navigate to CloudWatch console
2. Go to Dashboards
3. Click on "NovaProMonitoring"
4. Verify all widgets load properly

## 💰 Cost Estimate

- **Dashboard**: ~$3/month
- **Alarms**: ~$0.40/month (4 alarms × $0.10)
- **SNS**: ~$0.50/month (notifications)
- **Total**: ~$4/month

## 🛠️ Troubleshooting

### Dashboard Not Visible
- Check your IAM role has `cloudwatch:GetDashboard` permission
- Verify you're in the correct region

### Metrics Not Loading
- Ensure `cloudwatch:GetMetricData` permission is granted
- Check the namespace condition includes "AWS/Bedrock"

### Log Widgets Empty
- Verify Bedrock model invocation logging is enabled
- Check `logs:StartQuery` permission is granted
- Ensure log group resources match your model ID

### Access Denied Errors
- Verify all required actions are in your IAM policy
- Check resource ARNs match your account and region
- Ensure conditions (namespace, etc.) are correctly configured

## 📞 Support

For issues:
1. Check IAM permissions match the policy above
2. Verify Bedrock logging is enabled
3. Confirm dashboard name matches your parameters
4. Check you're in the correct AWS region

---

**Template Status**: ✅ **Production Ready**  
**IAM Resources**: ❌ **None Created** (Use existing role)  
**Required Action**: Add IAM policy to your existing role