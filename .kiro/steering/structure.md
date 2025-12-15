# Project Structure & Organization

## Repository Layout

```
nova-pro-cloudwatch-dashboard/
├── nova-pro-dashboard-compact.yaml    # Main CloudFormation template
├── README.md                          # Primary documentation
├── PROJECT_STRUCTURE.md              # Detailed structure guide
├── CHANGELOG.md                       # Version history
├── CONTRIBUTING.md                    # Contribution guidelines
├── LICENSE                           # MIT license
├── .gitignore                        # Git exclusions
├── task_agent_mapping.json          # Agent configuration (empty)
├── registered_agents.json           # Agent registry (empty)
├── docs/                             # Documentation
├── examples/                         # Configuration examples
└── scripts/                          # Utility scripts
```

## Core Files

### Main Template
- **`nova-pro-dashboard-compact.yaml`**: Single CloudFormation template containing all resources
- **Size**: ~60KB with comprehensive monitoring configuration
- **Resources**: 34 AWS resources (dashboard, alarms, SNS, policies)

### Documentation Hierarchy
1. **`README.md`**: Entry point with quick start guide
2. **`docs/`**: Detailed guides for specific scenarios
3. **`examples/`**: Ready-to-use configuration files
4. **`scripts/README.md`**: Automation tool documentation

## Directory Conventions

### `/docs/` - User Documentation
- **Console guides**: Step-by-step AWS Console instructions
- **IAM requirements**: Detailed permission documentation
- **Production guides**: Best practices and security considerations
- **Troubleshooting**: Common issues and solutions

### `/examples/` - Configuration Templates
- **Parameter files**: JSON format CloudFormation parameters
- **IAM policies**: Required permissions for dashboard access
- **Multiple scenarios**: Different deployment configurations
- **Naming convention**: `*.example.json` for templates, `*-unique.json` for conflict resolution

### `/scripts/` - Automation Tools
- **Validation**: `validate-template.py` for template checking
- **Deployment**: `deploy-compact-dashboard.sh` for automated deployment
- **Troubleshooting**: Resource conflict resolution tools
- **Naming convention**: Descriptive names with `.sh` or `.py` extensions

## File Naming Patterns

### CloudFormation Templates
- **Main template**: `nova-pro-dashboard-compact.yaml`
- **Format**: Kebab-case with descriptive suffixes
- **Extension**: `.yaml` (not `.yml`)

### Parameter Files
- **Examples**: `parameters.example.json`
- **Environment-specific**: `parameters-{env}.json`
- **Conflict resolution**: `parameters-unique.json`

### Documentation
- **Guides**: `UPPERCASE_WITH_UNDERSCORES.md`
- **READMEs**: `README.md` in each directory
- **Descriptive names**: Clear purpose indication

### Scripts
- **Python**: `kebab-case.py`
- **Bash**: `kebab-case.sh`
- **Executable**: All scripts should be executable (`chmod +x`)

## Content Organization

### Template Structure
```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: # Comprehensive description with version
Metadata: # Stack policies and interface configuration
Parameters: # Grouped by functionality
Conditions: # Environment and feature toggles
Resources: # Organized by service type
Outputs: # Essential information for users
```

### Parameter Grouping
1. **Dashboard Configuration**: Core settings
2. **Alarm Thresholds**: Monitoring limits
3. **Notification Settings**: SNS configuration
4. **User/Application Tracking**: Analytics settings
5. **Resource Tagging**: Organizational metadata

### Resource Organization
- **CloudWatch Dashboard**: Main monitoring interface
- **CloudWatch Alarms**: Operational alerting (4 pre-configured)
- **SNS Topic & Subscription**: Notification system
- **Outputs**: Stack information and dashboard URLs

## Development Patterns

### Adding New Features
1. **Template changes**: Update `nova-pro-dashboard-compact.yaml`
2. **Parameter updates**: Add to appropriate parameter group
3. **Documentation**: Update relevant guides in `docs/`
4. **Examples**: Provide configuration examples
5. **Validation**: Update `validate-template.py` if needed

### Documentation Updates
1. **Primary**: Update `README.md` for user-facing changes
2. **Detailed**: Update specific guides in `docs/`
3. **Structure**: Update `PROJECT_STRUCTURE.md` for organizational changes
4. **Changelog**: Document all changes in `CHANGELOG.md`

### Script Development
1. **Error handling**: Use `set -euo pipefail` for bash scripts
2. **Help text**: Include usage information and examples
3. **Validation**: Check prerequisites and parameters
4. **Documentation**: Update `scripts/README.md`

## Quality Standards

### File Organization
- **Single responsibility**: Each file has a clear, focused purpose
- **Logical grouping**: Related files are co-located
- **Clear naming**: File names indicate content and purpose
- **Consistent structure**: Similar files follow the same patterns

### Documentation Standards
- **Comprehensive**: Cover all user scenarios and use cases
- **Up-to-date**: Maintain accuracy with template changes
- **Accessible**: Clear language for different skill levels
- **Examples**: Provide concrete, working examples

### Template Standards
- **Parameterized**: Flexible configuration without hardcoded values
- **Secure**: Least-privilege permissions and encryption
- **Production-ready**: Deletion protection and rollback triggers
- **Well-documented**: Clear descriptions and metadata