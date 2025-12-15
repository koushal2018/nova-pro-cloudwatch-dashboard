# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-12-12

### Added
- Initial release of Nova Pro CloudWatch Dashboard
- Comprehensive monitoring dashboard for Amazon Bedrock Nova Pro models
- Real-time usage metrics (invocations, TPM, concurrent requests)
- Cost analytics with token-level breakdown
- Performance monitoring with latency percentiles
- Error tracking and analysis
- Guardrail intervention monitoring
- User and application usage tracking
- Pre-configured CloudWatch alarms for key metrics
- SNS notifications for alarm events
- Production-ready CloudFormation template
- Comprehensive documentation and deployment guides
- IAM policy templates for secure access
- Support for 8 AWS regions
- Automated validation and deployment scripts

### Features
- **Dashboard Widgets**: 20+ pre-configured widgets covering all aspects of Nova Pro monitoring
- **Cost Tracking**: Real-time cost calculation based on December 2025 pricing
- **Cache Analytics**: Cache hit rate and efficiency monitoring
- **Log Analytics**: CloudWatch Logs Insights queries for detailed analysis
- **Security**: Least-privilege IAM policies and encrypted SNS topics
- **Flexibility**: Parameterized template for easy customization
- **Reliability**: Deletion protection and rollback triggers

### Documentation
- Console deployment guide for AWS Console users
- CLI deployment guide for automation
- Comprehensive IAM requirements documentation
- Troubleshooting guide with common issues and solutions
- Production deployment best practices
- Contributing guidelines for community contributions

### Security
- Least-privilege IAM policies
- Resource-scoped permissions
- Namespace-restricted CloudWatch access
- Encrypted SNS topics with AWS managed keys
- Secure transport enforcement
- Account-based access restrictions

### Supported Regions
- us-east-1 (US East - N. Virginia)
- us-west-2 (US West - Oregon)
- eu-west-1 (Europe - Ireland)
- eu-central-1 (Europe - Frankfurt)
- ap-southeast-1 (Asia Pacific - Singapore)
- ap-northeast-1 (Asia Pacific - Tokyo)
- ca-central-1 (Canada - Central)
- me-central-1 (Middle East - UAE)

### Technical Details
- CloudFormation template size: ~60KB (comprehensive monitoring)
- Estimated monthly cost: ~$4 (dashboard + alarms + SNS)
- Resource count: 34 resources (dashboard, alarms, SNS, policies)
- Validation: 29+ automated checks for production readiness

## [1.1.0] - 2025-12-15

### Fixed
- **CRITICAL**: Fixed cost calculation formulas that were dividing by 1000 twice
- Corrected all pricing expressions from `(tokens * rate/1000)` to `(tokens/1000 * rate)`
- Updated cost alarm calculations to use corrected formula
- Fixed daily cost threshold alarm to prevent false positives

### Added
- Enhanced cost tracking with `RUNNING_SUM` for daily totals
- Real-time cost tracking alongside daily cumulative costs

### Enhanced
- **Cost Widgets**: Improved layout with combined real-time and daily cost views
- **Token Tracking**: Added daily token consumption totals
- **User Analytics**: Enhanced cost calculation accuracy in log queries
- **Documentation**: Updated pricing formulas throughout all widgets and queries

### Changed
- Cost calculation methodology now correctly applies Nova Pro pricing rates
- Widget titles updated to indicate "Corrected Formula" where applicable
- Improved widget annotations with clearer pricing information
- Enhanced parameter organization with new "Inference Profile Tracking" group

### Technical Details
- Formula fix: `(m1 * 0.0008/1000)` → `(m1/1000 * 0.0008)`
- Updated 8 existing widgets with corrected formulas
- Simplified dashboard focus on core Nova Pro monitoring

## [Unreleased]

### Planned
- Additional AWS regions as Nova Pro becomes available
- Enhanced cost optimization recommendations
- Integration with AWS Cost Explorer
- Custom metric support
- Multi-model dashboard support
- Terraform version of the template
- Automated testing pipeline
- Performance optimization for large-scale deployments

---

## Release Notes Format

### Added
- New features and capabilities

### Changed
- Changes in existing functionality

### Deprecated
- Soon-to-be removed features

### Removed
- Removed features

### Fixed
- Bug fixes

### Security
- Security improvements and fixes