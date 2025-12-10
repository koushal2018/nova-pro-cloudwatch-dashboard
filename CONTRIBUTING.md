# Contributing to Nova Pro CloudWatch Dashboard

Thank you for your interest in contributing to the Nova Pro CloudWatch Dashboard project! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites

- AWS CLI configured with appropriate permissions
- Python 3.8+ for running tests
- `cfn-lint` for CloudFormation template validation
- Git for version control

### Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/nova-pro-cloudwatch-dashboard.git
   cd nova-pro-cloudwatch-dashboard
   ```
3. Install development dependencies:
   ```bash
   pip install cfn-lint hypothesis pytest
   ```

## 🔧 Development Workflow

### Branch Naming Convention

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `test/description` - Test improvements
- `security/description` - Security enhancements

### Making Changes

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes following our coding standards

3. Run tests to ensure everything works:
   ```bash
   python test_template_properties.py
   cfn-lint nova-pro-dashboard-template.yaml
   ```

4. Commit your changes with clear messages:
   ```bash
   git commit -m "feat: add new dashboard widget for cache metrics
   
   - Add cache hit rate visualization
   - Include cache efficiency calculations
   - Update cost tracking to include cache savings"
   ```

## 📋 Contribution Guidelines

### CloudFormation Template Changes

- **Always validate**: Run `cfn-lint` before committing
- **Test thoroughly**: Ensure property-based tests pass
- **Document pricing**: Update cost calculations with current pricing dates
- **Security first**: Follow least-privilege IAM principles
- **Update-safe**: Avoid properties that force resource replacement

### Code Quality Standards

- **Property-based testing**: Add tests for new correctness properties
- **Documentation**: Update inline comments for complex logic
- **Parameterization**: Balance flexibility with simplicity
- **Resource protection**: Add `DeletionPolicy: Retain` for critical resources

### Commit Message Format

Follow conventional commits:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test additions/modifications
- `refactor`: Code refactoring
- `security`: Security improvements
- `perf`: Performance improvements

Examples:
```bash
feat(dashboard): add guardrail intervention widgets
fix(alarms): correct P99 latency threshold calculation
docs(readme): update deployment instructions
test(properties): add region consistency validation
security(iam): scope CloudWatch permissions to Bedrock namespace
```

## 🧪 Testing Requirements

### Required Tests

All contributions must include appropriate tests:

1. **Property-based tests** for universal correctness properties
2. **Template validation** using `cfn-lint`
3. **AWS validation** using `aws cloudformation validate-template`

### Running Tests

```bash
# Run all property-based tests
python test_template_properties.py

# Validate CloudFormation template
cfn-lint nova-pro-dashboard-template.yaml

# AWS template validation (requires AWS CLI configured)
aws cloudformation validate-template --template-body file://nova-pro-dashboard-template.yaml
```

### Test Coverage

New features should include:
- Unit tests for parsing functions
- Property tests for correctness properties
- Integration tests for AWS resource creation (if applicable)

## 📚 Documentation Standards

### Inline Documentation

- **YAML comments**: Explain complex CloudFormation logic
- **Pricing updates**: Include dates for cost calculations
- **Security notes**: Document IAM permissions and constraints
- **Operational notes**: Include deployment and maintenance guidance

### External Documentation

- Update `README.md` for user-facing changes
- Update `DEPLOYMENT.md` for operational changes
- Update design documents for architectural changes

## 🔒 Security Guidelines

### Security Review Checklist

- [ ] IAM policies follow least-privilege principle
- [ ] No hardcoded credentials or sensitive data
- [ ] Resource-scoped permissions where possible
- [ ] Proper encryption for data in transit and at rest
- [ ] Input validation for all parameters

### Security-Sensitive Changes

Changes affecting security require:
1. Detailed security impact analysis
2. Review by security-focused maintainers
3. Testing of security controls
4. Documentation of security implications

## 📝 Pull Request Process

### Before Submitting

1. **Rebase** your branch on the latest main:
   ```bash
   git fetch origin
   git rebase origin/main
   ```

2. **Run all tests** and ensure they pass

3. **Update documentation** as needed

4. **Self-review** your changes

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Security enhancement
- [ ] Performance improvement

## Testing
- [ ] Property-based tests pass
- [ ] CloudFormation template validates
- [ ] Manual testing completed (if applicable)

## Security Impact
Describe any security implications

## Documentation
- [ ] README updated
- [ ] Inline comments added
- [ ] Design docs updated (if needed)

## Checklist
- [ ] Code follows project conventions
- [ ] Self-review completed
- [ ] Tests added/updated
- [ ] Documentation updated
```

### Review Process

1. **Automated checks**: CI/CD pipeline runs tests
2. **Peer review**: At least one maintainer review required
3. **Security review**: Required for security-sensitive changes
4. **Final approval**: Maintainer approval required for merge

## 🏷️ Issue Guidelines

### Bug Reports

Include:
- CloudFormation template version
- AWS region and account details (sanitized)
- Steps to reproduce
- Expected vs actual behavior
- Error messages and logs
- Environment details

### Feature Requests

Include:
- Use case description
- Proposed solution
- Alternative solutions considered
- Impact on existing functionality
- Implementation complexity estimate

### Security Issues

**Do not** create public issues for security vulnerabilities. Instead:
1. Email security concerns to maintainers
2. Provide detailed vulnerability description
3. Include proof of concept (if safe)
4. Allow time for responsible disclosure

## 🤝 Community Guidelines

### Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Maintain professional communication

### Getting Help

- Check existing issues and documentation first
- Ask questions in issue discussions
- Provide context and details when asking for help
- Be patient with response times

## 📊 Metrics and Monitoring

### Contribution Metrics

We track:
- Code quality improvements
- Test coverage increases
- Documentation completeness
- Security enhancements
- Performance optimizations

### Recognition

Contributors are recognized through:
- GitHub contributor graphs
- Release notes acknowledgments
- Community highlights
- Maintainer nominations

## 🔄 Release Process

### Versioning

We follow semantic versioning (SemVer):
- `MAJOR.MINOR.PATCH`
- Major: Breaking changes
- Minor: New features (backward compatible)
- Patch: Bug fixes (backward compatible)

### Release Cycle

- **Patch releases**: As needed for critical fixes
- **Minor releases**: Monthly for new features
- **Major releases**: Quarterly for significant changes

Thank you for contributing to Nova Pro CloudWatch Dashboard! 🎉