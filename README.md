# Amazon Bedrock Nova Pro CloudWatch Dashboard

A comprehensive CloudWatch dashboard template for monitoring Amazon Bedrock Nova Pro model usage, performance, costs, and guardrail interventions.

![Dashboard Preview](https://img.shields.io/badge/AWS-CloudFormation-orange) ![License](https://img.shields.io/badge/License-MIT-blue) ![Version](https://img.shields.io/badge/Version-1.0.0-green)

## 🎯 Overview

This CloudFormation template creates a production-ready monitoring dashboard for Amazon Bedrock Nova Pro models, providing:

- **Real-time Usage Metrics** - Invocations, TPM, concurrent requests
- **Cost Analytics** - Daily costs, cost per request, token cost breakdown  
- **Performance Monitoring** - Latency percentiles, cache efficiency
- **Error Tracking** - Error rates, error breakdown, recent errors
- **Guardrail Analytics** - Intervention rates and types
- **User/Application Tracking** - Usage analytics by user and application

## 🚀 Quick Start

### Prerequisites
- AWS Account with Bedrock Nova Pro access
- CloudFormation deployment permissions
- IAM role with required permissions (see [IAM Requirements](#iam-requirements))

### Deploy via AWS Console
1. **Download** the template: [`nova-pro-dashboard-compact.yaml`](nova-pro-dashboard-compact.yaml)
2. **Go to** CloudFormation Console → Create Stack
3. **Upload** the template file
4. **Configure** parameters (see [Parameters](#parameters))
5. **Deploy** and wait for completion

### Deploy via AWS CLI
```bash
aws cloudformation create-stack \
  --stack-name nova-pro-dashboard \
  --template-body file://nova-pro-dashboard-compact.yaml \
  --parameters file://parameters.example.json \
  --region us-east-1
```

## 📋 Parameters

| Parameter | Description | Default | Required |
|-----------|-------------|---------|----------|
| `DashboardName` | Name for the CloudWatch dashboard | `NovaProMonitoring` | Yes |
| `MonitoringRegion` | AWS region for monitoring | - | Yes |
| `ModelId` | Bedrock Nova Pro model ID | `amazon.nova-pro-v1:0` | Yes |
| `AlarmEmail` | Email for alarm notifications | (empty) | No |
| `Environment` | Environment tag | `prod` | Yes |
| `Owner` | Owner tag | `DevOps` | Yes |
| `CostCenter` | Cost center tag | `AI-OPERATIONS` | Yes |

## 🔑 IAM Requirements

Add this policy to your IAM role to access the dashboard:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:GetDashboard",
        "cloudwatch:ListDashboards",
        "cloudwatch:GetMetricData",
        "cloudwatch:GetMetricStatistics",
        "cloudwatch:ListMetrics"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "cloudwatch:namespace": ["AWS/Bedrock", "AWS/Bedrock/Guardrails"]
        }
      }
    },
    {
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
        "arn:aws:logs:*:*:log-group:/aws/bedrock/modelinvocations/amazon.nova-pro-v1:0*"
      ]
    },
    {
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

## 📊 What's Included

### Resources Created
- **CloudWatch Dashboard** - Comprehensive monitoring dashboard
- **CloudWatch Alarms** - 4 pre-configured alarms for key metrics
- **SNS Topic** - For alarm notifications (optional)
- **SNS Subscription** - Email notifications (optional)

### Dashboard Widgets
- Usage metrics (invocations, TPM, concurrent requests)
- Cost analysis (daily costs, cost per request, token breakdown)
- Performance metrics (latency percentiles, cache efficiency)
- Error monitoring (error rates, recent errors, success vs failed)
- Guardrail analytics (intervention rates and types)
- User/application tracking (requires metadata in requests)

### Alarms Configured
1. **High Error Rate** - Triggers when error rate > 5%
2. **High P99 Latency** - Triggers when P99 latency > 5000ms
3. **Daily Cost Limit** - Triggers when daily cost > $1000
4. **High Throttling Rate** - Triggers when throttling > 10%

## 🛠️ Advanced Configuration

### Enable Bedrock Logging
For detailed analytics, enable model invocation logging:

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

### User/Application Tracking
To enable user and application analytics, include metadata in your Bedrock requests:

```json
{
  "metadata": {
    "userId": "john.doe",
    "applicationName": "chatbot"
  }
}
```

## 💰 Cost Estimate

- **Dashboard**: ~$3/month
- **Alarms**: ~$0.40/month (4 alarms × $0.10)
- **SNS**: ~$0.50/month (notifications)
- **Total**: ~$4/month

## 🔧 Troubleshooting

### Common Issues

#### "Resource Already Exists" Error
If you get conflicts with existing resources:
1. Use different names in parameters (e.g., `DashboardName: NovaProMonitoring-v2`)
2. Or delete existing resources first

#### Dashboard Not Loading
- Verify IAM permissions are added to your role
- Check you're in the correct AWS region
- Confirm dashboard name matches deployment

#### Metrics Not Showing
- Enable Bedrock model invocation logging
- Verify namespace conditions in IAM policy

See [Console Deployment Guide](docs/CONSOLE_DEPLOYMENT_GUIDE.md) for detailed troubleshooting.

## 📚 Documentation

- [Console Deployment Guide](docs/CONSOLE_DEPLOYMENT_GUIDE.md) - Step-by-step AWS Console instructions
- [IAM Requirements](docs/CUSTOMER_IAM_REQUIREMENTS.md) - Detailed IAM policy requirements
- [Production Deployment](docs/PRODUCTION_DEPLOYMENT_GUIDE.md) - Production deployment best practices
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues and solutions

## 🛡️ Security

- **Least Privilege**: IAM policies grant minimum required permissions
- **Resource Scoped**: Access limited to specific dashboards and log groups
- **Namespace Restricted**: CloudWatch metrics limited to Bedrock only
- **Encryption**: SNS topics encrypted with AWS managed keys
- **Deletion Protection**: Critical resources protected from accidental deletion

## 🌍 Supported Regions

- `us-east-1` (US East - N. Virginia)
- `us-west-2` (US West - Oregon)
- `eu-west-1` (Europe - Ireland)
- `eu-central-1` (Europe - Frankfurt)
- `ap-southeast-1` (Asia Pacific - Singapore)
- `ap-northeast-1` (Asia Pacific - Tokyo)
- `ca-central-1` (Canada - Central)
- `me-central-1` (Middle East - UAE)

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🏷️ Tags

`aws` `cloudformation` `bedrock` `nova-pro` `monitoring` `cloudwatch` `dashboard` `observability` `ai` `ml`

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-org/nova-pro-dashboard/issues)
- **Documentation**: [Wiki](https://github.com/your-org/nova-pro-dashboard/wiki)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/nova-pro-dashboard/discussions)

---

**Made with ❤️ for the AWS Community**