# Contributing to Nova Pro Dashboard

Thank you for your interest in contributing to the Nova Pro Dashboard project! We welcome contributions from the community.

## 🤝 How to Contribute

### Reporting Issues
- **Search existing issues** before creating new ones
- **Use issue templates** when available
- **Provide detailed information** including error messages, steps to reproduce, and environment details
- **Include CloudFormation events** and relevant logs

### Suggesting Features
- **Check existing feature requests** first
- **Describe the use case** and business value
- **Provide implementation ideas** if you have them
- **Consider backward compatibility**

### Code Contributions
1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Make your changes**
4. **Test thoroughly** (see Testing section)
5. **Commit with clear messages**
6. **Push to your branch** (`git push origin feature/amazing-feature`)
7. **Open a Pull Request**

## 🧪 Testing

### Template Validation
```bash
# Validate CloudFormation template
python3 scripts/validate-template.py nova-pro-dashboard-compact.yaml

# Test deployment (use test account)
aws cloudformation create-stack \
  --stack-name test-nova-dashboard \
  --template-body file://nova-pro-dashboard-compact.yaml \
  --parameters file://examples/parameters.example.json
```

### Documentation Testing
- **Test all commands** in documentation
- **Verify links** work correctly
- **Check formatting** in different viewers
- **Validate JSON/YAML** syntax

### Manual Testing Checklist
- [ ] Template deploys successfully
- [ ] Dashboard loads without errors
- [ ] All widgets display data (after enabling logging)
- [ ] Alarms are created and functional
- [ ] SNS notifications work (if configured)
- [ ] IAM permissions are minimal and functional
- [ ] Documentation is accurate and complete

## 📝 Code Standards

### CloudFormation Templates
- **Use consistent indentation** (2 spaces)
- **Add descriptive comments** for complex logic
- **Follow AWS naming conventions**
- **Include proper metadata** and descriptions
- **Use parameters** for configurable values
- **Add appropriate tags** to all resources

### Documentation
- **Use clear, concise language**
- **Include code examples** where helpful
- **Follow markdown best practices**
- **Keep README up to date**
- **Add troubleshooting info** for common issues

### Scripts
- **Include error handling** (`set -euo pipefail` for bash)
- **Add help text** and usage examples
- **Use consistent formatting**
- **Test on multiple platforms** when possible

## 🏗️ Development Setup

### Prerequisites
- AWS CLI configured
- Python 3.7+ (for validation scripts)
- Access to AWS account for testing
- Text editor with YAML/JSON support

### Local Development
```bash
# Clone the repository
git clone https://github.com/your-org/nova-pro-dashboard.git
cd nova-pro-dashboard

# Make scripts executable
chmod +x scripts/*.sh

# Validate template
python3 scripts/validate-template.py nova-pro-dashboard-compact.yaml
```

### Testing Environment
- **Use a dedicated test AWS account** or sandbox
- **Clean up resources** after testing
- **Test in multiple regions** if making region-specific changes
- **Verify cost implications** of changes

## 📋 Pull Request Guidelines

### Before Submitting
- [ ] **Test your changes** thoroughly
- [ ] **Update documentation** if needed
- [ ] **Add/update examples** if applicable
- [ ] **Check for breaking changes**
- [ ] **Validate all templates** and scripts
- [ ] **Review your own code** for issues

### PR Description
Include:
- **Summary of changes**
- **Motivation and context**
- **Testing performed**
- **Breaking changes** (if any)
- **Related issues** (if any)

### Review Process
1. **Automated checks** will run
2. **Maintainer review** for code quality and design
3. **Community feedback** period
4. **Final approval** and merge

## 🔄 Release Process

### Versioning
We use [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist
- [ ] Update version numbers
- [ ] Update CHANGELOG.md
- [ ] Test in multiple regions
- [ ] Update documentation
- [ ] Create release notes
- [ ] Tag release

## 🛡️ Security

### Reporting Security Issues
- **Do not** create public issues for security vulnerabilities
- **Email** security concerns to [security@yourorg.com]
- **Include** detailed information about the vulnerability
- **Allow time** for investigation and fix before disclosure

### Security Best Practices
- **Follow least privilege** principle
- **Avoid hardcoded credentials** or sensitive data
- **Use secure defaults** in templates
- **Document security implications** of changes
- **Test IAM policies** thoroughly

## 📚 Resources

### AWS Documentation
- [CloudFormation User Guide](https://docs.aws.amazon.com/cloudformation/)
- [CloudWatch User Guide](https://docs.aws.amazon.com/cloudwatch/)
- [Bedrock User Guide](https://docs.aws.amazon.com/bedrock/)
- [IAM User Guide](https://docs.aws.amazon.com/iam/)

### Tools
- [CloudFormation Linter](https://github.com/aws-cloudformation/cfn-lint)
- [AWS CLI](https://aws.amazon.com/cli/)
- [IAM Policy Simulator](https://policysim.aws.amazon.com/)

### Community
- [AWS CloudFormation GitHub](https://github.com/aws-cloudformation)
- [AWS Samples](https://github.com/aws-samples)
- [AWS Community](https://aws.amazon.com/developer/community/)

## 🏷️ Issue Labels

We use these labels to categorize issues:
- **bug**: Something isn't working
- **enhancement**: New feature or request
- **documentation**: Improvements or additions to docs
- **good first issue**: Good for newcomers
- **help wanted**: Extra attention is needed
- **question**: Further information is requested
- **security**: Security-related issue

## 💬 Communication

### Code of Conduct
Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

### Getting Help
- **GitHub Discussions**: For questions and community help
- **GitHub Issues**: For bugs and feature requests
- **Documentation**: Check docs/ folder first

### Stay Updated
- **Watch** the repository for notifications
- **Follow** releases for updates
- **Join** community discussions

## 🎉 Recognition

Contributors will be:
- **Listed** in CONTRIBUTORS.md
- **Mentioned** in release notes
- **Thanked** in the community

Thank you for contributing to make Nova Pro monitoring better for everyone! 🚀