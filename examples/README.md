# Examples

This directory contains example configuration files and templates for deploying the Nova Pro Dashboard.

## 📋 Files

### `parameters.example.json`
Basic parameter configuration for CloudFormation deployment.
- Copy and customize for your environment
- Update email, region, and other settings as needed

### `parameters-unique.json`
Example parameters using unique resource names to avoid conflicts.
- Use when you have existing resources with the same names
- Demonstrates how to deploy multiple dashboard instances

### `required-iam-policy.json`
Complete IAM policy that needs to be added to your existing role.
- Copy this policy to your IAM role
- Provides all necessary permissions for dashboard access
- Follows least-privilege security principles

## 🚀 Usage

### Basic Deployment
```bash
# Copy and customize parameters
cp examples/parameters.example.json my-parameters.json
# Edit my-parameters.json with your values

# Deploy via CLI
aws cloudformation create-stack \
  --stack-name nova-pro-dashboard \
  --template-body file://nova-pro-dashboard-compact.yaml \
  --parameters file://my-parameters.json \
  --region us-east-1
```

### Avoiding Resource Conflicts
```bash
# Use unique names to avoid conflicts
aws cloudformation create-stack \
  --stack-name nova-pro-dashboard-v2 \
  --template-body file://nova-pro-dashboard-compact.yaml \
  --parameters file://examples/parameters-unique.json \
  --region us-east-1
```

### IAM Policy Setup
1. Go to IAM Console → Roles
2. Find your role → Add permissions → Create inline policy
3. Copy content from `required-iam-policy.json`
4. Paste in JSON tab → Review → Create policy

## 🔧 Customization

### Parameter Descriptions

| Parameter | Description | Example |
|-----------|-------------|---------|
| `DashboardName` | Name for CloudWatch dashboard | `NovaProMonitoring` |
| `MonitoringRegion` | AWS region for monitoring | `us-east-1` |
| `ModelId` | Bedrock Nova Pro model ID | `amazon.nova-pro-v1:0` |
| `AlarmEmail` | Email for notifications (optional) | `admin@company.com` |
| `Environment` | Environment tag | `prod`, `staging`, `dev` |
| `Owner` | Owner tag | `DevOps`, `AI-Team` |
| `CostCenter` | Cost center for billing | `AI-OPERATIONS` |

### Common Customizations

#### Different Model
```json
{
  "ParameterKey": "ModelId",
  "ParameterValue": "amazon.nova-lite-v1:0"
}
```

#### Multiple Environments
```json
{
  "ParameterKey": "DashboardName",
  "ParameterValue": "NovaProMonitoring-Staging"
},
{
  "ParameterKey": "Environment",
  "ParameterValue": "staging"
}
```

#### Custom Alarm Thresholds
```json
{
  "ParameterKey": "ErrorRateThreshold",
  "ParameterValue": "2"
},
{
  "ParameterKey": "DailyCostThreshold",
  "ParameterValue": "500"
}
```

## 🛡️ Security Notes

- **Never commit** actual parameter files with sensitive data
- **Use different names** for production vs development
- **Review IAM policies** before applying
- **Test in non-production** environments first

## 📚 Additional Resources

- [Console Deployment Guide](../docs/CONSOLE_DEPLOYMENT_GUIDE.md)
- [IAM Requirements](../docs/CUSTOMER_IAM_REQUIREMENTS.md)
- [Troubleshooting](../docs/TROUBLESHOOTING.md)