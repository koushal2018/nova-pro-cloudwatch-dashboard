# Technology Stack

## Core Technologies

- **Infrastructure as Code**: AWS CloudFormation (YAML format)
- **Monitoring Platform**: Amazon CloudWatch (dashboards, metrics, alarms, logs)
- **Notification System**: Amazon SNS with email subscriptions
- **Security**: AWS IAM policies with least-privilege access
- **Target Service**: Amazon Bedrock Nova Pro models

## Template Architecture

- **Single Template**: `nova-pro-dashboard-compact.yaml` (~60KB)
- **Resource Count**: 34 AWS resources per deployment
- **No Custom Code**: Pure CloudFormation, no Lambda functions
- **Parameterized**: Flexible configuration via CloudFormation parameters

## Build & Deployment Tools

### Validation
```bash
# Template validation
python3 scripts/validate-template.py nova-pro-dashboard-compact.yaml

# Prerequisites: Python 3.7+, PyYAML
pip install pyyaml
```

### Deployment Methods

#### AWS Console (Recommended for first-time users)
1. Upload `nova-pro-dashboard-compact.yaml` to CloudFormation Console
2. Configure parameters using `examples/parameters.example.json` as reference
3. Deploy and monitor stack creation

#### AWS CLI (Automation/CI-CD)
```bash
# Basic deployment
aws cloudformation create-stack \
  --stack-name nova-pro-dashboard \
  --template-body file://nova-pro-dashboard-compact.yaml \
  --parameters file://examples/parameters.example.json \
  --region us-east-1

# Automated deployment with validation
./scripts/deploy-compact-dashboard.sh
```

### Utility Scripts

All scripts require Bash 4.0+, AWS CLI, and jq:

```bash
# Make scripts executable
chmod +x scripts/*.sh

# Install dependencies (macOS)
brew install awscli jq
pip install pyyaml

# Install dependencies (Ubuntu)
sudo apt-get install awscli jq
pip install pyyaml
```

## Configuration Management

### Parameter Files
- **JSON format**: CloudFormation parameter arrays
- **Examples provided**: `examples/parameters.example.json`
- **Environment-specific**: Copy and customize for each deployment

### IAM Requirements
- **Policy template**: `examples/required-iam-policy.json`
- **Attach to existing role**: No new roles created by template
- **Scoped permissions**: CloudWatch, Bedrock, and SNS only

## Supported Regions

Template supports Nova Pro availability in:
- us-east-1, us-west-2
- eu-west-1, eu-central-1  
- ap-southeast-1, ap-northeast-1
- ca-central-1, me-central-1

## Development Workflow

### Template Changes
1. Edit `nova-pro-dashboard-compact.yaml`
2. Validate: `python3 scripts/validate-template.py nova-pro-dashboard-compact.yaml`
3. Test deployment in non-production environment
4. Update documentation if parameters or resources change

### Script Development
1. Follow existing error handling patterns (`set -euo pipefail`)
2. Include comprehensive help text and parameter validation
3. Test on macOS and Linux
4. Update `scripts/README.md` with new functionality

## Quality Assurance

### Automated Checks
- **YAML syntax validation**
- **CloudFormation structure verification**
- **Security best practices validation**
- **Production readiness assessment**

### Manual Testing
- Deploy in test environment
- Verify all dashboard widgets load correctly
- Test alarm functionality
- Validate IAM permissions work as expected