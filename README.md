# Nova Pro CloudWatch Dashboard

A comprehensive CloudFormation-based monitoring solution for Amazon Bedrock's Nova Pro foundation model. Provides enterprise-grade observability for AI workload operations through pre-configured CloudWatch dashboards.

## 🚀 Quick Start

Deploy the monitoring dashboard in minutes:

```bash
aws cloudformation create-stack \
  --stack-name nova-pro-dashboard \
  --template-body file://nova-pro-dashboard-template.yaml \
  --parameters ParameterKey=MonitoringRegion,ParameterValue=us-east-1 \
             ParameterKey=AlarmEmail,ParameterValue=alerts@company.com \
  --capabilities CAPABILITY_NAMED_IAM \
  --enable-termination-protection
```

## 📊 Features

- **Real-time Usage Monitoring**: Track invocations, TPM (tokens per minute), and request patterns
- **Cost Tracking**: Monitor daily costs with cache efficiency analysis (December 2025 pricing)
- **Performance Metrics**: Latency percentiles, error rates, and throughput monitoring
- **Guardrail Compliance**: Content safety intervention tracking and reporting
- **Operational Alerts**: Pre-configured CloudWatch alarms with SNS notifications
- **Security**: Least-privilege IAM roles and encrypted SNS topics

## 🏗️ Architecture

The solution deploys:
- **CloudWatch Dashboard**: 42 widgets across 7 monitoring sections
- **CloudWatch Alarms**: 4 configurable threshold-based alerts
- **SNS Integration**: Optional email notifications for alarm triggers
- **IAM Permissions**: Read-only dashboard viewer role with scoped access

## 📋 Prerequisites

- AWS account with Amazon Bedrock access
- Nova Pro model available in target region
- IAM permissions for CloudFormation, CloudWatch, SNS, IAM
- AWS CLI configured (for deployment)

## 🔧 Configuration

### Required Parameters
- `MonitoringRegion`: AWS region where Nova Pro metrics are monitored

### Optional Parameters (with defaults)
- `DashboardName`: "NovaProMonitoring"
- `ModelId`: "amazon.nova-pro-v1:0"
- `ErrorRateThreshold`: 5%
- `P99LatencyThreshold`: 5000ms
- `DailyCostThreshold`: $1000
- `ThrottleRateThreshold`: 10%
- `AlarmEmail`: "" (optional email for notifications)

## 📈 Dashboard Sections

1. **Usage Overview**: Total invocations, requests/min, service TPM, customer TPM
2. **Cost Tracking**: Daily cost estimation, cost per request, token cost breakdown, cache efficiency
3. **Performance**: Latency percentiles, latency comparisons, request size correlation
4. **Error Monitoring**: Error rate gauge, error breakdown, recent error logs
5. **Invocation Patterns**: Success vs failed ratio, token distribution, concurrent invocations
6. **Guardrails**: Intervention tracking, intervention rates, policy type breakdown

## 💰 Cost Estimate

- CloudWatch Dashboard: $3.00/month
- CloudWatch Alarms: $0.40/month (4 alarms)
- SNS Notifications: $0.00 (first 1,000 free)
- **Total Infrastructure**: ~$3.40/month (excluding Nova Pro usage)

## 🔒 Security

- Least-privilege IAM policies scoped to Bedrock metrics
- KMS-encrypted SNS topics
- No public dashboard access (IAM authentication required)
- Resource protection policies prevent accidental deletion

## 🧪 Testing

Run property-based tests to validate template correctness:

```bash
python test_template_properties.py
```

Validate CloudFormation template:

```bash
cfn-lint nova-pro-dashboard-template.yaml
aws cloudformation validate-template --template-body file://nova-pro-dashboard-template.yaml
```

## 📚 Documentation

- [Deployment Guide](DEPLOYMENT.md) - Production deployment checklist and security hardening
- [Design Document](.kiro/specs/nova-cloudwatch-dashboard/design.md) - Architecture and technical design
- [Requirements](.kiro/specs/nova-cloudwatch-dashboard/requirements.md) - User stories and acceptance criteria
- [Implementation Tasks](.kiro/specs/nova-cloudwatch-dashboard/tasks.md) - Development checklist

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests (`python test_template_properties.py`)
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🏷️ Tags

`aws` `cloudformation` `cloudwatch` `bedrock` `nova-pro` `monitoring` `dashboard` `infrastructure-as-code` `observability` `ai-monitoring`

## 📞 Support

- Create an [Issue](../../issues) for bug reports or feature requests
- Check [Deployment Guide](DEPLOYMENT.md) for troubleshooting
- Review [Security Recommendations](DEPLOYMENT.md#security-best-practices) for production deployment

---

**Version**: 1.0.0 (December 2025)  
**Pricing Update**: December 2025 (Nova Pro pricing embedded in cost calculations)