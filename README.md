# Nova Pro CloudWatch Dashboard

> **Disclaimer**: This is a personal open-source project and is **NOT** affiliated with, endorsed by, or sponsored by Amazon Web Services (AWS) or any of its subsidiaries. The author created this project independently to help the community monitor their Bedrock Nova Pro usage.

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

## 🔐 Security Validation

Run security validation tests to verify hardening measures:

```bash
# Run comprehensive security validation
python -c "
from test_template_properties import *
test_iam_trust_policy_restrictions()
test_cloudwatch_permission_region_scoping()
test_logs_permission_model_scoping()
test_resource_protection_policies()
test_sns_topic_access_policy()
print('All security validations passed!')
"

# Validate IAM policies with AWS IAM Policy Simulator
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::ACCOUNT:role/DASHBOARD-ViewerRole \
  --action-names cloudwatch:GetDashboard \
  --resource-arns arn:aws:cloudwatch:REGION:ACCOUNT:dashboard/DASHBOARD

# Check for security findings with AWS Config (if enabled)
aws configservice get-compliance-details-by-config-rule \
  --config-rule-name iam-role-managed-policy-check

# Scan for security issues with AWS Security Hub (if enabled)
aws securityhub get-findings \
  --filters '{"ResourceId":[{"Value":"STACK-NAME","Comparison":"EQUALS"}]}'
```

## 🚨 Incident Response

### Security Event Detection

Monitor for these security events:

```bash
# CloudTrail: Unusual IAM role assumptions
aws logs filter-log-events \
  --log-group-name CloudTrail/SecurityEvents \
  --filter-pattern '{ $.eventName = "AssumeRole" && $.sourceIPAddress != "EXPECTED_IP" }'

# CloudWatch: Suspicious metric access patterns
aws logs filter-log-events \
  --log-group-name /aws/cloudwatch/api \
  --filter-pattern '{ $.eventName = "GetMetricData" && $.errorCode exists }'

# Config: Unauthorized resource changes
aws configservice get-compliance-details-by-config-rule \
  --config-rule-name cloudformation-stack-drift-detection-check
```

### Emergency Response Actions

If security breach detected:

```bash
# 1. Immediately disable the IAM role
aws iam attach-role-policy \
  --role-name DASHBOARD-ViewerRole \
  --policy-arn arn:aws:iam::aws:policy/AWSDenyAll

# 2. Isolate SNS topic (if compromised)
aws sns set-topic-attributes \
  --topic-arn arn:aws:sns:REGION:ACCOUNT:TOPIC \
  --attribute-name Policy \
  --attribute-value '{"Statement":[{"Effect":"Deny","Principal":"*","Action":"*"}]}'

# 3. Enable detailed CloudTrail logging
aws cloudtrail put-event-selectors \
  --trail-name SecurityAuditTrail \
  --event-selectors ReadWriteType=All,IncludeManagementEvents=true

# 4. Create security incident ticket
echo "Security incident detected at $(date)" > incident-$(date +%Y%m%d-%H%M%S).log
```

### Recovery Procedures

After incident resolution:

```bash
# 1. Restore IAM role with updated trust policy
aws iam detach-role-policy \
  --role-name DASHBOARD-ViewerRole \
  --policy-arn arn:aws:iam::aws:policy/AWSDenyAll

# 2. Update stack with enhanced security
aws cloudformation update-stack \
  --stack-name nova-pro-dashboard \
  --template-body file://nova-pro-dashboard-template.yaml \
  --capabilities CAPABILITY_NAMED_IAM

# 3. Verify security controls
python -c "from test_template_properties import *; test_security_validation_property_based()"

# 4. Document lessons learned
echo "Incident resolved. Updated security controls verified." >> incident-$(date +%Y%m%d-%H%M%S).log
```

## 📚 Documentation

- [Deployment Guide](DEPLOYMENT.md) - Production deployment checklist and security hardening
- [Contributing Guide](CONTRIBUTING.md) - How to contribute to this project

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests (`python test_template_properties.py`)
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

- Create an [Issue](../../issues) for bug reports or feature requests
- Check [Deployment Guide](DEPLOYMENT.md) for troubleshooting
- Review [Security Recommendations](DEPLOYMENT.md#security-best-practices) for production deployment

## ⚠️ Disclaimer

This project is provided "as is" without warranty of any kind. This is a personal project created by the author and is:

- **NOT** an official AWS product or service
- **NOT** affiliated with, endorsed by, or sponsored by Amazon Web Services
- **NOT** supported by AWS Support

Use at your own risk. Always review CloudFormation templates before deploying to your AWS account.

---

**Author**: Koushal Dalal
**Version**: 1.0.0 (December 2025)
**Pricing Update**: December 2025 (Nova Pro pricing embedded in cost calculations)