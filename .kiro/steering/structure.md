# Project Structure

## Directory Organization

```
.kiro/
├── hooks/                          # Agent hooks for automated workflows
│   ├── aws-parameter-validation.kiro.hook
│   ├── cloudformation-stack-management.kiro.hook
│   ├── security-first-cloudformation.kiro.hook
│   ├── iac-best-practices.kiro.hook
│   ├── cfn-validate-test.kiro.hook
│   └── git-best-practices-reminder.kiro.hook
├── specs/                          # Feature specifications
│   └── nova-cloudwatch-dashboard/
│       ├── requirements.md         # User stories and acceptance criteria
│       ├── design.md              # Architecture and technical design
│       └── tasks.md               # Implementation checklist
└── steering/                       # AI assistant guidance documents
    ├── product.md                 # Product overview
    ├── tech.md                    # Tech stack and commands
    └── structure.md               # This file
```

## File Naming Conventions

- CloudFormation templates: `*.yaml` or `*.yml` (YAML preferred)
- Template files may include: `*template*.yaml`, `*cloudformation*.yaml`, `*cfn*.yaml`
- Hook files: `*.kiro.hook` (JSON format)
- Specification files: `requirements.md`, `design.md`, `tasks.md`
- Steering files: `*.md` (Markdown)

## CloudFormation Template Structure

When creating CloudFormation templates, follow this organization:

1. **AWSTemplateFormatVersion**: Always "2010-09-09"
2. **Description**: Comprehensive template description with version
3. **Metadata**: AWS::CloudFormation::Interface for parameter grouping
4. **Parameters**: Required parameters first, then optional with defaults
5. **Conditions**: Conditional resource creation logic
6. **Resources**: Grouped logically (SNS, Dashboard, Alarms, IAM)
7. **Outputs**: Dashboard URL, resource ARNs, useful references

## Specification Structure

Each feature spec follows a three-document pattern:

- **requirements.md**: User stories with acceptance criteria (WHEN/THEN format)
- **design.md**: Architecture, components, data models, testing strategy, correctness properties
- **tasks.md**: Granular implementation checklist with requirement traceability

## Hook Patterns

Hooks monitor file changes and trigger automated validations:

- **Security checks**: Embedded credentials, NoEcho parameters, IAM least privilege
- **Operational safety**: DeletionPolicy, UpdateReplacePolicy, resource protection
- **AWS best practices**: Parameter types, stack policies, tagging, drift detection
- **Validation**: Template syntax, structure, and CloudFormation compliance

## Design Principles

- **Update-safe resources**: Avoid properties that force replacement during stack updates
- **Least-privilege IAM**: Scope permissions to minimum necessary actions and resources
- **Inline documentation**: Use YAML comments to explain complex logic and pricing
- **Property-based testing**: Universal correctness properties validated across template variations
- **Parameterization balance**: Flexibility without over-complication
