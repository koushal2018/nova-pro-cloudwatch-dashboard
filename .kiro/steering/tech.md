# Technology Stack

## Infrastructure as Code

- **CloudFormation**: Primary IaC tool for AWS resource provisioning
- **YAML**: Template format (preferred over JSON for readability and inline comments)

## AWS Services

- **Amazon Bedrock**: Nova Pro foundation model (amazon.nova-pro-v1:0)
- **CloudWatch**: Metrics, dashboards, alarms, and Logs Insights
- **SNS**: Notification delivery for alarm triggers
- **IAM**: Least-privilege access control

## Metrics and Monitoring

- **Namespace**: AWS/Bedrock for model metrics, AWS/Bedrock/Guardrails for content safety
- **Key Metrics**: Invocations, InvocationLatency, InputTokenCount, OutputTokenCount, CacheReadInputTokenCount, CacheWriteInputTokenCount, InvocationClientErrors, InvocationServerErrors, InvocationThrottles
- **Calculated Metrics**: TPM (two variants: service quota and customer monitoring), cost per request, error rates, cache efficiency

## Development Tools

- **cfn-lint**: CloudFormation template validation and linting
- **Python + Hypothesis**: Property-based testing for template correctness
- **AWS CLI**: Template deployment and testing

## Common Commands

### Validate Template
```bash
cfn-lint template.yaml
```

### Deploy Stack
```bash
aws cloudformation create-stack \
  --stack-name nova-pro-dashboard \
  --template-body file://template.yaml \
  --parameters ParameterKey=MonitoringRegion,ParameterValue=us-east-1 \
  --capabilities CAPABILITY_IAM
```

### Update Stack
```bash
aws cloudformation update-stack \
  --stack-name nova-pro-dashboard \
  --template-body file://template.yaml \
  --parameters ParameterKey=MonitoringRegion,ParameterValue=us-east-1
```

### Delete Stack
```bash
aws cloudformation delete-stack --stack-name nova-pro-dashboard
```

### Validate Stack
```bash
aws cloudformation validate-template --template-body file://template.yaml
```

## Pricing Considerations

- CloudWatch dashboards: $3/month per dashboard
- Standard alarms: $0.10/month per alarm
- High-resolution alarms: $0.30/month per alarm
- Nova Pro pricing (December 2024):
  - Input tokens: $0.0008 per 1K tokens
  - Output tokens: $0.0032 per 1K tokens
  - Cache write: $0.0008 per 1K tokens
  - Cache read: $0.00008 per 1K tokens (90% discount)
