# Nova Pro Dashboard - Customer IAM Requirements

## Overview

Since you'll be using your existing IAM role to access the Nova Pro CloudWatch Dashboard, you need to ensure your role has the necessary permissions. The dashboard template will **NOT** create any IAM roles or policies - it only creates the dashboard, alarms, and SNS topic.

## Required IAM Policy

Add this policy to your existing IAM role to access the Nova Pro dashboard:

### Policy JSON
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

## Permission Breakdown

### 1. CloudWatch Dashboard Access
- **Actions**: `GetDashboard`, `ListDashboards`
- **Purpose**: View and list CloudWatch dashboards
- **Resources**: Specific to Nova Pro dashboard and general dashboard access

### 2. CloudWatch Metrics Access
- **Actions**: `GetMetricData`, `GetMetricStatistics`, `ListMetrics`
- **Purpose**: Read Bedrock metrics for dashboard widgets
- **Condition**: Limited to AWS/Bedrock and AWS/Bedrock/Guardrails namespaces only

### 3. CloudWatch Logs Access
- **Actions**: Log query operations for detailed analytics
- **Purpose**: Run CloudWatch Logs Insights queries for user/application tracking
- **Resources**: Limited to Bedrock model invocation logs only

### 4. Bedrock Read-Only Access
- **Actions**: `GetModelInvocationLoggingConfiguration`, `ListFoundationModels`
- **Purpose**: Check logging configuration and available models
- **Resources**: All Bedrock resources (read-only)

## Customization Notes

### Dashboard Name
If you change the `DashboardName` parameter from the default `NovaProMonitoring`, update the policy resource:
```json
"arn:aws:cloudwatch:*:*:dashboard/YOUR_DASHBOARD_NAME"
```

### Model ID
If you use a different Nova Pro model ID, update the log group resources:
```json
"arn:aws:logs:*:*:log-group:/aws/bedrock/modelinvocations/YOUR_MODEL_ID*"
```

### Region Restrictions
To limit access to specific regions, add region conditions:
```json
"Condition": {
  "StringEquals": {
    "aws:RequestedRegion": ["us-east-1", "us-west-2"]
  }
}
```

## Minimal Permissions (Alternative)

If you want the absolute minimum permissions for basic dashboard viewing (without log analytics):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:GetDashboard",
        "cloudwatch:GetMetricData",
        "cloudwatch:GetMetricStatistics"
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
    }
  ]
}
```

## Verification

After adding the policy to your role, verify access by:

1. **Console Access**: Navigate to CloudWatch → Dashboards → NovaProMonitoring
2. **API Access**: `aws cloudwatch get-dashboard --dashboard-name NovaProMonitoring`
3. **Metrics Access**: Check that Bedrock metrics load in dashboard widgets

## Security Notes

- ✅ **Least Privilege**: Policy grants minimum required permissions
- ✅ **Resource Scoped**: Limited to specific dashboards and log groups
- ✅ **Namespace Restricted**: CloudWatch metrics limited to Bedrock only
- ✅ **Read-Only**: No write permissions granted

## Troubleshooting

### Common Issues

1. **Dashboard not visible**: Check `cloudwatch:GetDashboard` permission
2. **Metrics not loading**: Verify `cloudwatch:GetMetricData` permission and namespace condition
3. **Log widgets empty**: Check `logs:StartQuery` permission and log group resources
4. **Access denied errors**: Ensure all required actions are included in your role policy

### Support

If you encounter permission issues, check:
1. Policy is attached to your role
2. Dashboard name matches the policy resource
3. Model ID matches the log group resources
4. Region matches your deployment region