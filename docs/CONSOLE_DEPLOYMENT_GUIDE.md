# Nova Pro Dashboard - AWS Console Deployment Guide

## 🚨 Fixing "Resource Already Exists" Error

When you see this error in CloudFormation:
- `Dashboard 'NovaProMonitoring' already exists`
- `Resource of type 'AWS::SNS::Topic' with identifier 'NovaProMonitoring-AlarmTopic' already exists`

Here's how to fix it using the AWS Console:

## ✅ **Solution 1: Use Different Names (Recommended)**

### Step 1: Check Existing Resources
1. **Go to CloudWatch Console** → **Dashboards**
2. **Look for**: `NovaProMonitoring` dashboard
3. **If it exists**: Note it down, we'll use a different name

### Step 2: Deploy with Unique Names
1. **Go to CloudFormation Console**
2. **Click**: "Create stack" → "With new resources (standard)"
3. **Upload template**: `nova-pro-dashboard-compact.yaml`
4. **Stack name**: `nova-pro-dashboard-v2` (different from before)
5. **Parameters**:
   - **DashboardName**: `NovaProMonitoring-v2` ← **Change this**
   - **MonitoringRegion**: `us-east-1` (or your region)
   - **ModelId**: `amazon.nova-pro-v1:0`
   - **AlarmEmail**: `your-email@company.com` (optional)
   - **Environment**: `prod`
   - **Owner**: `DevOps`
   - **CostCenter**: `AI-OPERATIONS`

6. **Click**: "Next" → "Next" → "Create stack"

### Result:
- ✅ **New Dashboard**: `NovaProMonitoring-v2`
- ✅ **New SNS Topic**: `NovaProMonitoring-v2-AlarmTopic`
- ✅ **No conflicts** with existing resources

---

## 🔧 **Solution 2: Delete Existing Resources First**

⚠️ **WARNING**: This will delete your existing monitoring setup!

### Step 1: Delete Existing Dashboard
1. **Go to CloudWatch Console** → **Dashboards**
2. **Find**: `NovaProMonitoring` dashboard
3. **Select it** → **Actions** → **Delete**
4. **Confirm deletion**

### Step 2: Delete Existing SNS Topic
1. **Go to SNS Console** → **Topics**
2. **Find**: `NovaProMonitoring-AlarmTopic`
3. **Select it** → **Delete**
4. **Type**: `delete me` → **Delete**

### Step 3: Delete Failed CloudFormation Stack (if exists)
1. **Go to CloudFormation Console**
2. **Find**: Any failed stacks (status: `ROLLBACK_COMPLETE` or `CREATE_FAILED`)
3. **Select stack** → **Delete**
4. **Wait** for deletion to complete

### Step 4: Retry Deployment
1. **Create new stack** with original parameters
2. **Use original names**: `NovaProMonitoring`

---

## 📋 **Console Deployment Steps**

### 1. Access CloudFormation
- **AWS Console** → **CloudFormation** → **Create stack**

### 2. Upload Template
- **Choose**: "Upload a template file"
- **Select**: `nova-pro-dashboard-compact.yaml`
- **Click**: "Next"

### 3. Configure Stack
- **Stack name**: `nova-pro-dashboard-v2`
- **Parameters**:

| Parameter | Value | Notes |
|-----------|-------|-------|
| **DashboardName** | `NovaProMonitoring-v2` | Use unique name to avoid conflicts |
| **MonitoringRegion** | `us-east-1` | Your deployment region |
| **ModelId** | `amazon.nova-pro-v1:0` | Default Nova Pro model |
| **AlarmEmail** | `your-email@company.com` | Optional - leave empty if no email alerts |
| **Environment** | `prod` | Environment tag |
| **Owner** | `DevOps` | Owner tag |
| **CostCenter** | `AI-OPERATIONS` | Cost center tag |

### 4. Configure Options
- **Tags**: (Optional) Add additional tags
- **Permissions**: Use default
- **Advanced options**: Leave defaults
- **Click**: "Next"

### 5. Review and Deploy
- **Review** all settings
- **Acknowledge**: IAM capabilities (if prompted)
- **Click**: "Create stack"

### 6. Monitor Deployment
- **Watch** the "Events" tab for progress
- **Wait** for status: `CREATE_COMPLETE` (usually 2-3 minutes)

---

## 🎯 **After Successful Deployment**

### 1. Access Your Dashboard
1. **Go to CloudWatch Console** → **Dashboards**
2. **Click**: `NovaProMonitoring-v2`
3. **Verify**: All widgets load properly

### 2. Confirm Email Subscription (if provided)
1. **Check your email** for SNS confirmation
2. **Click**: "Confirm subscription" link

### 3. Test Alarms
1. **Go to CloudWatch** → **Alarms**
2. **Verify**: 4 alarms created:
   - `NovaProMonitoring-v2-HighErrorRate`
   - `NovaProMonitoring-v2-HighP99Latency`
   - `NovaProMonitoring-v2-DailyCostLimit`
   - `NovaProMonitoring-v2-HighThrottlingRate`

---

## 🔑 **Required IAM Permissions**

**IMPORTANT**: Add this policy to your IAM role before accessing the dashboard:

### Console Steps:
1. **Go to IAM Console** → **Roles**
2. **Find your role** → **Add permissions** → **Create inline policy**
3. **JSON tab** → **Paste this policy**:

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
        "arn:aws:cloudwatch:*:*:dashboard/NovaProMonitoring-v2",
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

4. **Name**: `NovaProDashboardAccess`
5. **Click**: "Create policy"

---

## 🛠️ **Troubleshooting**

### Dashboard Not Loading
- **Check**: IAM permissions are added to your role
- **Verify**: You're in the correct AWS region
- **Confirm**: Dashboard name matches what you deployed

### Metrics Not Showing
- **Enable**: Bedrock model invocation logging
- **Go to**: Bedrock Console → Settings → Model invocation logging
- **Configure**: CloudWatch Logs destination

### Email Notifications Not Working
- **Check**: Email confirmation in your inbox
- **Verify**: SNS subscription is confirmed
- **Test**: Trigger an alarm manually

---

## 💡 **Pro Tips**

1. **Use unique names** to avoid conflicts with existing resources
2. **Start with no email** for initial testing, add email later
3. **Enable Bedrock logging** for full dashboard functionality
4. **Bookmark the dashboard URL** for easy access
5. **Monitor costs** - dashboard costs ~$4/month

---

## 📞 **Need Help?**

If you encounter issues:
1. **Check CloudFormation Events** tab for specific error messages
2. **Verify IAM permissions** are correctly added
3. **Ensure Bedrock is available** in your selected region
4. **Try different resource names** if conflicts persist

**Dashboard URL Format**: 
`https://REGION.console.aws.amazon.com/cloudwatch/home?region=REGION#dashboards:name=DASHBOARD_NAME`