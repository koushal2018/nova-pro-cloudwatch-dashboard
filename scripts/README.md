# Scripts

This directory contains utility scripts for deploying, validating, and managing the Nova Pro Dashboard.

## 📋 Scripts Overview

### `validate-template.py`
Comprehensive validation script for the CloudFormation template.
- Validates YAML structure and CloudFormation syntax
- Checks SNS policy actions and conditions
- Verifies security best practices
- Validates production readiness criteria

### `deploy-compact-dashboard.sh`
Automated deployment script with error handling and validation.
- Validates prerequisites and AWS credentials
- Handles stack creation and updates
- Provides detailed deployment status and outputs
- Includes rollback and error handling

### `fix-existing-resources.sh`
Diagnostic and resolution script for resource conflicts.
- Identifies existing resources that cause deployment conflicts
- Provides specific resolution commands
- Offers multiple resolution strategies
- Helps with resource cleanup

### `check-resource-ownership.sh`
Determines ownership and management of existing AWS resources.
- Checks if resources were created by CloudFormation
- Identifies which stack manages resources
- Provides recommendations based on resource ownership
- Helps plan resource cleanup strategy

### `assume-dashboard-role.sh` (Legacy)
Helper script for assuming IAM roles (when template created roles).
- **Note**: Template no longer creates IAM roles
- Kept for reference and backward compatibility
- Use existing IAM role with required permissions instead

## 🚀 Usage

### Template Validation
```bash
# Validate template before deployment
python3 scripts/validate-template.py nova-pro-dashboard-compact.yaml
```

### Automated Deployment
```bash
# Deploy with default settings
./scripts/deploy-compact-dashboard.sh

# Deploy with custom parameters
./scripts/deploy-compact-dashboard.sh my-stack us-west-2 my-parameters.json
```

### Resource Conflict Resolution
```bash
# Check for existing resources and get resolution options
./scripts/fix-existing-resources.sh

# Check resource ownership
./scripts/check-resource-ownership.sh NovaProMonitoring us-east-1
```

## 🔧 Prerequisites

### Python Scripts
- **Python 3.7+**
- **PyYAML** (for YAML parsing): `pip install pyyaml`
- **AWS CLI** configured with appropriate permissions

### Bash Scripts
- **Bash 4.0+** (macOS/Linux)
- **AWS CLI** installed and configured
- **jq** (for JSON parsing): `brew install jq` or `apt-get install jq`

### AWS Permissions
Scripts require these AWS permissions:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudformation:*",
        "cloudwatch:*",
        "sns:*",
        "sts:GetCallerIdentity"
      ],
      "Resource": "*"
    }
  ]
}
```

## 📚 Script Details

### validate-template.py
**Purpose**: Comprehensive template validation

**Features**:
- YAML syntax validation
- CloudFormation structure checks
- SNS policy validation (checks for valid actions)
- Security best practices verification
- Production readiness assessment

**Output**:
- ✅ Passed checks
- ⚠️ Warnings (non-blocking issues)
- ❌ Errors (must be fixed)

### deploy-compact-dashboard.sh
**Purpose**: Automated deployment with error handling

**Features**:
- Prerequisites validation
- Stack existence detection
- Parameter file validation
- Deployment progress monitoring
- Output extraction and display

**Parameters**:
1. Stack name (default: `nova-pro-dashboard-compact`)
2. AWS region (default: `us-east-1`)
3. Parameters file (default: `parameters.example.json`)

### fix-existing-resources.sh
**Purpose**: Resolve resource naming conflicts

**Features**:
- Detects existing dashboards and SNS topics
- Provides multiple resolution strategies
- Generates specific AWS CLI commands
- Recommends safest resolution approach

**Resolution Options**:
1. Use different names (recommended)
2. Delete existing resources
3. Import existing resources

### check-resource-ownership.sh
**Purpose**: Determine resource management status

**Features**:
- Identifies CloudFormation-managed resources
- Checks deletion policies
- Finds owning stacks
- Provides cleanup recommendations

**Output**:
- Resource existence status
- CloudFormation ownership
- Deletion policy information
- Recommended actions

## 🛡️ Security Considerations

### Script Security
- **Review scripts** before execution
- **Use least-privilege** AWS credentials
- **Test in non-production** environments first
- **Avoid hardcoded credentials**

### AWS Permissions
- Scripts use **read-only operations** where possible
- **Destructive operations** require explicit confirmation
- **CloudFormation permissions** are scoped to stack operations
- **No permanent credential storage**

## 🔍 Troubleshooting

### Common Issues

#### Permission Denied
```bash
# Make scripts executable
chmod +x scripts/*.sh
```

#### AWS CLI Not Found
```bash
# Install AWS CLI
pip install awscli
# or
brew install awscli
```

#### Python Dependencies Missing
```bash
# Install required packages
pip install pyyaml
```

#### jq Not Found
```bash
# macOS
brew install jq

# Ubuntu/Debian
sudo apt-get install jq

# CentOS/RHEL
sudo yum install jq
```

### Script Debugging
```bash
# Run with debug output
bash -x scripts/deploy-compact-dashboard.sh

# Check script syntax
bash -n scripts/deploy-compact-dashboard.sh
```

## 📝 Contributing

When adding new scripts:
1. **Follow existing patterns** and error handling
2. **Add comprehensive help text**
3. **Include parameter validation**
4. **Test on multiple platforms**
5. **Update this README**

### Script Template
```bash
#!/bin/bash
set -euo pipefail

# Script description and usage
SCRIPT_NAME="$(basename "$0")"
usage() {
    echo "Usage: $SCRIPT_NAME [options]"
    echo "Description of what the script does"
    exit 1
}

# Parameter validation
if [[ $# -lt 1 ]]; then
    usage
fi

# Main script logic with error handling
```

## 🔗 Related Documentation

- [Console Deployment Guide](../docs/CONSOLE_DEPLOYMENT_GUIDE.md)
- [Troubleshooting Guide](../docs/TROUBLESHOOTING.md)
- [Contributing Guidelines](../CONTRIBUTING.md)