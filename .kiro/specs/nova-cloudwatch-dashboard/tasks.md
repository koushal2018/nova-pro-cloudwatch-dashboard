# Implementation Plan

## Current Status
The CloudFormation template foundation is complete with:
- ✅ Template structure, parameters, and SNS topic resources
- ✅ Complete dashboard with usage overview, cost tracking, performance, and error widgets
- ✅ CloudWatch alarms for error rate, P99 latency, daily cost, and throttling rate
- ✅ Property-based test for optional parameters
- ✅ Template validation passing (cfn-lint and AWS CloudFormation validate-template)
- ⚠️ Missing: Guardrail widgets, outputs, additional property tests

- [x] 1. Set up project structure and CloudFormation template skeleton
  - Create directory structure for the CloudFormation template
  - Create base CloudFormation template file with AWSTemplateFormatVersion and Description
  - Define template metadata section with AWS::CloudFormation::Interface for parameter grouping
  - _Requirements: 1.1, 8.1_

- [x] 2. Define CloudFormation parameters
  - [x] 2.1 Create required parameters (MonitoringRegion, ModelId)
    - Add MonitoringRegion parameter with description about Bedrock availability
    - Add ModelId parameter with default value for Nova Pro model
    - _Requirements: 1.2, 1.3_
  
  - [x] 2.2 Create optional parameters with defaults (DashboardName, alarm thresholds, AlarmEmail)
    - Add DashboardName parameter with default value
    - Add ErrorRateThreshold, P99LatencyThreshold, DailyCostThreshold, ThrottleRateThreshold parameters with defaults
    - Add AlarmEmail parameter (optional, no default)
    - _Requirements: 8.2, 10.1, 10.2, 10.3, 10.4_
  
  - [x] 2.3 Write property test for optional parameters having defaults
    - **Property 3: Optional parameters have defaults**
    - **Validates: Requirements 8.2**

- [x] 3. Create SNS topic for alarm notifications
  - [x] 3.1 Define conditional SNS topic resource
    - Create condition to check if AlarmEmail parameter is provided
    - Define AWS::SNS::Topic resource with KMS encryption enabled
    - Add DisplayName property for the topic
    - _Requirements: 9.3, 10.5_
  
  - [x] 3.2 Define SNS subscription resource
    - Create AWS::SNS::Subscription resource conditional on AlarmEmail
    - Set Protocol to email and Endpoint to AlarmEmail parameter
    - _Requirements: 10.5_

- [x] 4. Build dashboard JSON structure for usage overview widgets
  - [x] 4.1 Create total invocations number widget
    - Define widget with Invocations metric using Sum statistic
    - Set time range to 24 hours
    - Position at x:0, y:0
    - _Requirements: 2.1_
  
  - [x] 4.2 Create requests per minute line graph widget
    - Define widget with Invocations metric using rate per minute
    - Set time range to 6 hours
    - Position at x:8, y:0
    - _Requirements: 2.2_
  
  - [x] 4.3 Create service TPM (quota) line graph widget
    - Define calculated metric: (InputTokenCount + CacheWriteInputTokenCount + (OutputTokenCount × 5)) / period × 60
    - This matches the service team's TPM calculation for quota enforcement
    - Set time range to 6 hours
    - Position at x:16, y:0
    - _Requirements: 2.3, 2.4_
  
  - [x] 4.4 Create customer TPM (traditional) line graph widget
    - Define calculated metric: (InputTokenCount + OutputTokenCount) / period × 60
    - This is the traditional TPM customers use for monitoring
    - Set time range to 6 hours
    - Position at x:0, y:6
    - _Requirements: 2.3, 2.4_

- [x] 5. Build dashboard JSON structure for cost tracking widgets
  - [x] 5.1 Create estimated daily cost number widget
    - Define calculated metric: (InputTokenCount * 0.0008/1000) + (CacheWriteInputTokenCount * 0.0008/1000) + (CacheReadInputTokenCount * 0.00008/1000) + (OutputTokenCount * 0.0032/1000)
    - Add pricing update date in comments (December 2025)
    - Set time range to 24 hours
    - Position at x:8, y:6
    - _Requirements: 3.1_
  
  - [x] 5.2 Create cost per request line graph widget
    - Define calculated metric dividing total cost by invocations
    - Set time range to 7 days
    - Position at x:16, y:6
    - _Requirements: 3.2_
  
  - [x] 5.3 Create token cost breakdown stacked area chart widget
    - Define separate metrics for input token cost, cache write cost, cache read cost, and output token cost
    - Set time range to 30 days
    - Position at x:0, y:12
    - _Requirements: 3.3, 3.4, 3.5_
  
  - [x] 5.4 Create cache efficiency line graph widget
    - Define calculated metric: CacheReadInputTokenCount / (InputTokenCount + CacheWriteInputTokenCount + CacheReadInputTokenCount) * 100
    - Shows cache hit rate percentage
    - Set time range to 7 days
    - Position at x:8, y:12
    - _Requirements: 3.1_

- [x] 6. Build dashboard JSON structure for performance metrics widgets
  - [x] 6.1 Create latency percentiles line graph widget
    - Define InvocationLatency metric with p50, p90, p95, p99 statistics
    - Set time range to 6 hours
    - Position at x:16, y:12
    - _Requirements: 4.1, 4.2_
  
  - [x] 6.2 Create average latency comparison number widgets
    - Define two number widgets comparing current hour vs previous hour
    - Use Average statistic for InvocationLatency
    - Position at x:0, y:18
    - _Requirements: 4.4_
  
  - [x] 6.3 Create latency by request size line graph widget
    - Define InvocationLatency metric grouped by input token ranges
    - Set time range to 24 hours
    - Position at x:8, y:18
    - _Requirements: 4.5_

- [x] 7. Build dashboard JSON structure for error and reliability widgets
  - [x] 7.1 Create error rate gauge widget
    - Define calculated metric for error percentage
    - Add threshold markers at alarm levels
    - Position at x:16, y:18
    - _Requirements: 5.1_
  
  - [x] 7.2 Create error breakdown stacked bar chart widget
    - Define metrics for InvocationClientErrors, InvocationServerErrors, InvocationThrottles
    - Set time range to 24 hours
    - Position at x:0, y:24
    - _Requirements: 5.2, 5.3_
  
  - [x] 7.3 Create recent errors log widget
    - Define CloudWatch Logs Insights query for recent errors
    - Add note about requiring model invocation logging
    - Set time range to 24 hours
    - Position at x:8, y:24
    - _Requirements: 5.4, 5.5_

- [ ] 8. Build dashboard JSON structure for invocation patterns widgets
  - [x] 8.1 Create success vs failed invocations pie chart widget
    - Define metrics for successful invocations vs errors
    - Set time range to 24 hours
    - Position at x:16, y:24
    - _Requirements: 6.2_
  
  - [x] 8.2 Create token distribution widgets
    - Define histogram widgets for input and output token counts
    - Set time range to 7 days
    - Position at x:0, y:30
    - _Requirements: 6.4, 6.5_
  
  - [x] 8.3 Create concurrent invocations line graph widget
    - Define metric for active concurrent invocations
    - Set time range to 6 hours
    - Position at x:12, y:30
    - _Requirements: 6.1_

- [x] 9. Build dashboard JSON structure for guardrails widgets
  - [x] 9.1 Create guardrail interventions number widget
    - Define InvocationsIntervened metric from AWS/Bedrock/Guardrails namespace
    - Set time range to 24 hours
    - Position at x:0, y:36
    - _Requirements: 7.1, 7.4_
  
  - [x] 9.2 Create intervention rate line graph widget
    - Define calculated metric for intervention percentage
    - Set time range to 7 days
    - Position at x:8, y:36
    - _Requirements: 7.3_
  
  - [x] 9.3 Create interventions by type stacked bar chart widget
    - Define FindingCounts metric grouped by GuardrailPolicyType dimension
    - Set time range to 24 hours
    - Position at x:16, y:36
    - _Requirements: 7.2_

- [x] 10. Assemble complete dashboard resource
  - [x] 10.1 Combine all widget JSON sections into dashboard body
    - Merge all widget definitions into single widgets array
    - Properly escape JSON for CloudFormation embedding
    - Use Fn::Sub to inject MonitoringRegion parameter into dashboard JSON
    - _Requirements: 1.3_
  
  - [x] 10.2 Create AWS::CloudWatch::Dashboard resource
    - Define dashboard resource with DashboardName from parameter
    - Set DashboardBody property with complete JSON (currently has 4 usage overview widgets)
    - _Requirements: 1.1, 2.1, 2.2, 2.3_
  
  - [x] 10.3 Write property test for region consistency across metrics
    - **Property 1: Region consistency across all metrics**
    - **Validates: Requirements 1.3**
  
  - [x] 10.4 Write property test for model dimension inclusion
    - **Property 2: Model dimension inclusion**
    - **Validates: Requirements 2.5**

- [x] 11. Create CloudWatch alarms
  - [x] 11.1 Create high error rate alarm
    - Define AWS::CloudWatch::Alarm resource with calculated error rate metric
    - Set threshold from ErrorRateThreshold parameter
    - Configure 2 consecutive periods of 5 minutes evaluation
    - Add conditional AlarmActions referencing SNS topic
    - _Requirements: 10.1_
  
  - [x] 11.2 Create high P99 latency alarm
    - Define AWS::CloudWatch::Alarm resource with InvocationLatency p99 metric
    - Set threshold from P99LatencyThreshold parameter
    - Configure 3 consecutive periods of 5 minutes evaluation
    - Add conditional AlarmActions referencing SNS topic
    - _Requirements: 10.2_
  
  - [x] 11.3 Create daily cost limit alarm
    - Define AWS::CloudWatch::Alarm resource with calculated daily cost metric
    - Set threshold from DailyCostThreshold parameter
    - Configure 1 period of 24 hours evaluation
    - Add conditional AlarmActions referencing SNS topic
    - _Requirements: 10.3_
  
  - [x] 11.4 Create high throttling rate alarm
    - Define AWS::CloudWatch::Alarm resource with calculated throttling rate metric
    - Set threshold from ThrottleRateThreshold parameter
    - Configure 2 consecutive periods of 5 minutes evaluation
    - Add conditional AlarmActions referencing SNS topic
    - _Requirements: 10.4_
  
  - [x] 11.5 Write property test for alarm SNS integration
    - **Property 7: Alarm SNS integration**
    - **Validates: Requirements 10.5**

- [ ] 12. Define IAM permissions (optional viewer role)
  - [-] 12.1 Create IAM role for dashboard viewers
    - Define AWS::IAM::Role resource with trust policy
    - Add AssumeRole permissions for specified principals
    - _Requirements: 9.1_
  
  - [x] 12.2 Create IAM policy for dashboard access
    - Define inline policy with CloudWatch read permissions
    - Scope permissions to dashboard and Bedrock metrics
    - Add Logs permissions for log insights widgets
    - _Requirements: 9.1, 9.2_
  
  - [x] 12.3 Write property test for least-privilege IAM permissions
    - **Property 5: Least-privilege IAM permissions**
    - **Validates: Requirements 9.1**
  
  - [x] 12.4 Write property test for scoped CloudWatch permissions
    - **Property 6: Scoped CloudWatch permissions**
    - **Validates: Requirements 9.2**

- [ ] 13. Define CloudFormation outputs
  - [x] 13.1 Create dashboard URL output
    - Define output with Fn::Sub to construct CloudWatch console URL
    - Include region and dashboard name in URL
    - Add description for output
    - _Requirements: 1.4_
  
  - [x] 13.2 Create dashboard name output
    - Define output returning dashboard name
    - Add description for output
    - _Requirements: 1.4_
  
  - [x] 13.3 Create alarm topic ARN output (conditional)
    - Define conditional output for SNS topic ARN
    - Only output if AlarmEmail parameter is provided
    - Add description for output
    - _Requirements: 10.5_

- [x] 14. Add template documentation and metadata
  - Add comprehensive description to template
  - Document pricing considerations in comments
  - Add parameter grouping in metadata section
  - Include usage instructions in template comments
  - Document pricing update dates for cost calculations
  - _Requirements: 8.1, 8.3_

- [x] 15. Write property test for update-safe resource configuration
  - **Property 4: Update-safe resource configuration**
  - **Validates: Requirements 8.5**

- [ ] 16. Validate and test CloudFormation template
  - [-] 16.1 Run cfn-lint validation
    - Install and run cfn-lint on template
    - Fix any syntax or structural issues
    - Verify all resource types are valid
  
  - [ ] 16.2 Test template deployment in AWS account
    - Deploy template to test AWS account
    - Verify all resources are created successfully
    - Check dashboard is accessible via output URL
    - Verify alarms are created and in OK state
  
  - [ ] 16.3 Generate test metrics and verify dashboard
    - Invoke Nova Pro model to generate test data
    - Wait for metrics to propagate to CloudWatch
    - Verify all dashboard widgets display data correctly
    - Verify cost calculations show expected values
  
  - [ ] 16.4 Test alarm triggers
    - Generate conditions to trigger alarms (if possible)
    - Verify alarms transition to ALARM state appropriately
    - Verify SNS notifications are sent (if configured)
  
  - [ ] 16.5 Test stack updates
    - Modify parameters and update stack
    - Verify updates complete without resource replacement
    - Verify dashboard continues functioning after update

- [ ] 17. Security Hardening - Address Critical Security Findings
  - [ ] 17.1 Fix IAM Trust Policy Over-Permissiveness
    - Replace account root principal with specific users/roles
    - Add ExternalId condition for cross-account access
    - Add source IP restrictions where applicable
    - _Security Finding: CRITICAL - Current trust policy allows any principal in account_
  
  - [ ] 17.2 Add Region Scoping to CloudWatch Permissions
    - Add aws:RequestedRegion condition to all CloudWatch metric permissions
    - Ensure permissions are limited to MonitoringRegion parameter
    - _Security Finding: HIGH - Permissions lack region scoping_
  
  - [ ] 17.3 Scope Logs Permissions to Specific Model
    - Change logs resource from `/aws/bedrock/modelinvocations*` to `/aws/bedrock/modelinvocations/${ModelId}*`
    - Prevent access to other models' logs
    - _Security Finding: MEDIUM - Logs permissions too broad_
  
  - [ ] 17.4 Add Resource Protection Policies
    - Add DeletionPolicy: Retain to all critical resources
    - Add UpdateReplacePolicy: Retain to prevent accidental replacement
    - Apply to: Dashboard, SNS Topic, Alarms, IAM Role, IAM Policy
    - _Security Finding: MEDIUM - Missing resource protection_
  
  - [ ] 17.5 Add SNS Topic Access Policy
    - Create resource-based policy for SNS topic
    - Restrict publishing to CloudWatch service only
    - Deny non-TLS connections
    - _Security Enhancement: Prevent unauthorized SNS access_
  
  - [ ] 17.6 Create Security Validation Tests
    - Add property test for IAM trust policy restrictions
    - Add test for CloudWatch permission region scoping
    - Add test for logs permission model scoping
    - Add test for resource protection policies
    - _Requirements: Security validation and compliance_
  
  - [ ] 17.7 Update Security Documentation
    - ✅ Add security findings to DEPLOYMENT.md
    - ✅ Add security architecture to design.md
    - Add security validation commands to README
    - Document incident response procedures
    - _Requirements: Security documentation and compliance_

- [ ] 18. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 18. Create README documentation
  - Write comprehensive README with deployment instructions
  - Document all parameters and their purposes
  - Include prerequisites (AWS account, Bedrock access, IAM permissions)
  - Add troubleshooting section for common issues
  - Include cost estimates for running the dashboard
  - Add examples of customizing the template
  - _Requirements: 8.3_
