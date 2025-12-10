# Design Document: Nova Pro CloudWatch Dashboard

## Overview

This design document outlines a comprehensive CloudWatch monitoring solution for Amazon Bedrock's Nova Pro Model, delivered as a CloudFormation template. The solution provides enterprise-grade observability for usage patterns, performance metrics, cost tracking, and operational health through a pre-configured dashboard that can be deployed in minutes.

The system leverages native AWS CloudWatch metrics published by Amazon Bedrock under the `AWS/Bedrock` namespace, organizing them into logical widget groups that address specific monitoring concerns for different stakeholder roles (operations, finance, reliability, security).

## Architecture

### High-Level Architecture

The solution consists of a single CloudFormation template that provisions:

1. **CloudWatch Dashboard**: Main visualization component with multiple widget sections
2. **CloudWatch Alarms**: Configurable threshold-based alerts for critical metrics
3. **SNS Topic** (optional): Notification delivery mechanism for alarm triggers
4. **IAM Permissions**: Least-privilege access policies for dashboard viewing

### Component Interaction Flow

```
CloudFormation Template Deployment
         |
         v
    [Parameters Input]
    - Region
    - Dashboard Name
    - Alarm Thresholds
    - SNS Email (optional)
         |
         v
    [Resource Creation]
    - Dashboard with Widgets
    - CloudWatch Alarms
    - SNS Topic & Subscription
         |
         v
    [Metric Collection]
    Amazon Bedrock → CloudWatch Metrics (AWS/Bedrock namespace)
         |
         v
    [Dashboard Visualization]
    Real-time metric display across widget sections
         |
         v
    [Alarm Evaluation]
    Threshold breaches → SNS Notifications
```

### Deployment Model

- **Single-Region Deployment**: Dashboard monitors Nova Pro metrics in one specified AWS region
- **Cross-Account Support**: Template can be deployed in any AWS account with Bedrock access
- **Update-Safe**: CloudFormation stack updates preserve dashboard configuration and alarm history

## Components and Interfaces

### 1. CloudFormation Template Structure

**Template Parameters:**
- `DashboardName` (String): Name for the CloudWatch dashboard (default: "NovaProMonitoring")
- `MonitoringRegion` (String): AWS region to monitor for Bedrock metrics (required)
- `ModelId` (String): Nova Pro model identifier (default: "amazon.nova-pro-v1:0")
- `ErrorRateThreshold` (Number): Percentage threshold for error rate alarms (default: 5)
- `P99LatencyThreshold` (Number): Milliseconds threshold for p99 latency alarms (default: 5000)
- `DailyCostThreshold` (Number): USD threshold for daily cost alarms (default: 1000)
- `ThrottleRateThreshold` (Number): Percentage threshold for throttling alarms (default: 10)
- `AlarmEmail` (String): Email address for alarm notifications (optional)

**Template Outputs:**
- `DashboardURL`: Direct link to the created CloudWatch dashboard
- `DashboardName`: Name of the created dashboard
- `AlarmTopicArn`: ARN of the SNS topic for alarm notifications (if created)

### 2. Dashboard Widget Organization

The dashboard is organized into logical sections, each addressing specific monitoring requirements:

#### Section 1: Usage Overview (Top Row)
- **Widget 1.1**: Total Invocations (Number widget)
  - Metric: `Invocations` (Sum statistic)
  - Time range: Last 24 hours
  
- **Widget 1.2**: Requests Per Minute (Line graph)
  - Metric: `Invocations` (Rate per minute)
  - Time range: Last 6 hours
  
- **Widget 1.3**: Service TPM (Tokens Per Minute for Quota) (Line graph)
  - Calculated metric: `(InputTokenCount + CacheWriteInputTokenCount + (OutputTokenCount × 5)) / period × 60`
  - Note: This is the TPM calculation used by the service team for quota enforcement
  - Note: Output tokens weighted 5x per Bedrock TPM calculation
  - Time range: Last 6 hours

- **Widget 1.4**: Customer TPM (Traditional Token Count) (Line graph)
  - Calculated metric: `(InputTokenCount + OutputTokenCount) / period × 60`
  - Note: This is the traditional TPM calculation customers typically use for monitoring
  - Time range: Last 6 hours

#### Section 2: Cost Tracking (Second Row)
- **Widget 2.1**: Estimated Daily Cost (Number widget with trend)
  - Calculated metric: `(InputTokenCount * 0.0008/1000) + (CacheWriteInputTokenCount * 0.0008/1000) + (CacheReadInputTokenCount * 0.00008/1000) + (OutputTokenCount * 0.0032/1000)`
  - Note: Prices embedded as constants based on Nova Pro pricing (December 2025)
  - Time range: Last 24 hours
  
- **Widget 2.2**: Cost Per Request (Line graph)
  - Calculated metric: `Total Cost / Invocations`
  - Time range: Last 7 days
  
- **Widget 2.3**: Token Cost Breakdown (Stacked area chart)
  - Metrics: Input token cost, Cache write cost, Cache read cost, Output token cost
  - Shows cost distribution across different token types
  - Time range: Last 30 days

- **Widget 2.4**: Cache Efficiency (Line graph)
  - Calculated metric: `CacheReadInputTokenCount / (InputTokenCount + CacheWriteInputTokenCount + CacheReadInputTokenCount) * 100`
  - Shows percentage of tokens served from cache (cache hit rate)
  - Time range: Last 7 days

#### Section 3: Performance Metrics (Third Row)
- **Widget 3.1**: Latency Percentiles (Line graph)
  - Metrics: `InvocationLatency` (p50, p90, p95, p99)
  - Time range: Last 6 hours
  
- **Widget 3.2**: Average Latency Comparison (Number widgets)
  - Current hour vs previous hour average latency
  
- **Widget 3.3**: Latency by Request Size (Line graph)
  - Metric: `InvocationLatency` grouped by input token ranges
  - Time range: Last 24 hours

#### Section 4: Error and Reliability (Fourth Row)
- **Widget 4.1**: Error Rate (Gauge widget)
  - Calculated metric: `(InvocationClientErrors + InvocationServerErrors) / Invocations * 100`
  - Threshold markers at alarm levels
  
- **Widget 4.2**: Error Breakdown (Stacked bar chart)
  - Metrics: `InvocationClientErrors`, `InvocationServerErrors`, `InvocationThrottles`
  - Time range: Last 24 hours
  
- **Widget 4.3**: Recent Errors (Log widget)
  - CloudWatch Logs Insights query for recent error messages
  - Requires model invocation logging enabled

#### Section 5: Invocation Patterns (Fifth Row)
- **Widget 5.1**: Success vs Failed Invocations (Pie chart)
  - Metrics: Successful invocations vs errors
  - Time range: Last 24 hours
  
- **Widget 5.2**: Token Distribution (Histogram)
  - Metrics: Distribution of input and output token counts
  - Time range: Last 7 days
  
- **Widget 5.3**: Concurrent Invocations (Line graph)
  - Metric: Active concurrent invocations
  - Time range: Last 6 hours

#### Section 6: Guardrails (Sixth Row - Optional)
- **Widget 6.1**: Guardrail Interventions (Number widget)
  - Metric: `InvocationsIntervened` from AWS/Bedrock/Guardrails namespace
  - Time range: Last 24 hours
  
- **Widget 6.2**: Intervention Rate (Line graph)
  - Calculated metric: `InvocationsIntervened / Invocations * 100`
  - Time range: Last 7 days
  
- **Widget 6.3**: Interventions by Type (Stacked bar chart)
  - Metric: `FindingCounts` grouped by `GuardrailPolicyType` dimension
  - Time range: Last 24 hours

### 3. CloudWatch Alarms

**Alarm 1: High Error Rate**
- Metric: `(InvocationClientErrors + InvocationServerErrors) / Invocations * 100`
- Threshold: Configurable via `ErrorRateThreshold` parameter
- Evaluation: 2 consecutive periods of 5 minutes
- Action: Publish to SNS topic

**Alarm 2: High P99 Latency**
- Metric: `InvocationLatency` (p99 statistic)
- Threshold: Configurable via `P99LatencyThreshold` parameter
- Evaluation: 3 consecutive periods of 5 minutes
- Action: Publish to SNS topic

**Alarm 3: Daily Cost Limit**
- Metric: Calculated daily cost
- Threshold: Configurable via `DailyCostThreshold` parameter
- Evaluation: 1 period of 24 hours
- Action: Publish to SNS topic

**Alarm 4: High Throttling Rate**
- Metric: `InvocationThrottles / (Invocations + InvocationThrottles) * 100`
- Threshold: Configurable via `ThrottleRateThreshold` parameter
- Evaluation: 2 consecutive periods of 5 minutes
- Action: Publish to SNS topic

### 4. IAM Permissions

**Dashboard Viewer Role** (Optional):
```
Permissions:
- cloudwatch:GetDashboard
- cloudwatch:ListDashboards
- cloudwatch:GetMetricData
- cloudwatch:GetMetricStatistics
- cloudwatch:ListMetrics
- logs:StartQuery
- logs:GetQueryResults
```

**Alarm Publisher Role** (Created automatically):
```
Permissions:
- sns:Publish (scoped to created SNS topic)
```

## Data Models

### CloudWatch Metric Schema

**Primary Metrics (AWS/Bedrock namespace):**
```
Invocations
  - Dimension: ModelId
  - Unit: Count
  - Statistic: Sum, Rate

InvocationLatency
  - Dimension: ModelId
  - Unit: Milliseconds
  - Statistic: Average, p50, p90, p95, p99

InvocationClientErrors
  - Dimension: ModelId
  - Unit: Count
  - Statistic: Sum

InvocationServerErrors
  - Dimension: ModelId
  - Unit: Count
  - Statistic: Sum

InvocationThrottles
  - Dimension: ModelId
  - Unit: Count
  - Statistic: Sum

InputTokenCount
  - Dimension: ModelId
  - Unit: Count
  - Statistic: Sum

CacheWriteInputTokenCount
  - Dimension: ModelId
  - Unit: Count
  - Statistic: Sum
  - Note: Tokens written to prompt cache (first request)

CacheReadInputTokenCount
  - Dimension: ModelId
  - Unit: Count
  - Statistic: Sum
  - Note: Tokens read from prompt cache (subsequent requests with cache hit)

OutputTokenCount
  - Dimension: ModelId
  - Unit: Count
  - Statistic: Sum
```

**Guardrail Metrics (AWS/Bedrock/Guardrails namespace):**
```
InvocationsIntervened
  - Dimensions: GuardrailArn, GuardrailVersion
  - Unit: Count
  - Statistic: Sum

FindingCounts
  - Dimensions: GuardrailArn, GuardrailPolicyType, FindingType
  - Unit: Count
  - Statistic: Sum
```

### Dashboard Body JSON Structure

```json
{
  "widgets": [
    {
      "type": "metric|text|log",
      "x": <grid-x-position>,
      "y": <grid-y-position>,
      "width": <grid-width>,
      "height": <grid-height>,
      "properties": {
        "metrics": [
          ["Namespace", "MetricName", "DimensionName", "DimensionValue", {"stat": "Statistic"}]
        ],
        "period": <seconds>,
        "stat": "Average|Sum|p99|etc",
        "region": "<aws-region>",
        "title": "<widget-title>",
        "yAxis": {
          "left": {"min": 0}
        }
      }
    }
  ]
}
```

### Cost Calculation Model

**Nova Pro Pricing (as of design - December 2025):**
- Input tokens: $0.0008 per 1,000 tokens
- Output tokens: $0.0032 per 1,000 tokens
- Cache write tokens: $0.0008 per 1,000 tokens (same as input)
- Cache read tokens: $0.00008 per 1,000 tokens (90% discount from input)

**Cost Formulas:**
```
Input Cost = (InputTokenCount / 1000) * 0.0008
Cache Write Cost = (CacheWriteInputTokenCount / 1000) * 0.0008
Cache Read Cost = (CacheReadInputTokenCount / 1000) * 0.00008
Output Cost = (OutputTokenCount / 1000) * 0.0032

Total Cost = Input Cost + Cache Write Cost + Cache Read Cost + Output Cost
Cost Per Request = Total Cost / Invocations
Daily Cost = Sum(Total Cost) over 24 hours
Monthly Projection = Daily Cost * 30
```

**TPM Calculations:**

There are two TPM calculations to be aware of:

1. **Service TPM (for quota enforcement):**
   ```
   Service TPM = (InputTokenCount + CacheWriteInputTokenCount + (OutputTokenCount × 5)) / period × 60
   ```
   This is what the Bedrock service team uses for quota limits. Output tokens are weighted 5x.

2. **Customer TPM (traditional monitoring):**
   ```
   Customer TPM = (InputTokenCount + OutputTokenCount) / period × 60
   ```
   This is the traditional calculation customers use to understand their token consumption rate.

## 
Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

After analyzing the acceptance criteria, most requirements are specific examples that validate the presence and configuration of particular dashboard widgets, alarms, and template parameters. However, several universal properties emerge that should hold across all components:

**Property 1: Region consistency across all metrics**
*For any* widget in the dashboard that contains CloudWatch metrics, all metric definitions within that widget should reference the same region parameter value.
**Validates: Requirements 1.3**

**Property 2: Model dimension inclusion**
*For any* CloudWatch metric query in the dashboard that queries the AWS/Bedrock namespace, the metric should include the ModelId dimension to segment data by model version.
**Validates: Requirements 2.5**

**Property 3: Optional parameters have defaults**
*For any* CloudFormation parameter marked as optional (not required), the parameter definition should include a Default value.
**Validates: Requirements 8.2**

**Property 4: Update-safe resource configuration**
*For any* resource in the CloudFormation template, the resource should not have properties that would force replacement during stack updates (e.g., changing DashboardName should update, not replace).
**Validates: Requirements 8.5**

**Property 5: Least-privilege IAM permissions**
*For any* IAM policy statement in the template, the actions granted should be scoped to the minimum necessary permissions and resources should be constrained where possible.
**Validates: Requirements 9.1**

**Property 6: Scoped CloudWatch permissions**
*For any* IAM policy statement granting CloudWatch permissions, the statement should include resource constraints or conditions limiting access to Bedrock-related metrics.
**Validates: Requirements 9.2**

**Property 7: Alarm SNS integration**
*For any* CloudWatch alarm resource in the template, if the AlarmEmail parameter is provided, the alarm should have an AlarmActions property referencing the SNS topic.
**Validates: Requirements 10.5**

## Error Handling

### CloudFormation Deployment Errors

**Missing Permissions:**
- Error: CloudFormation fails with "Access Denied" during resource creation
- Handling: Template includes detailed parameter descriptions indicating required IAM permissions
- User Action: Grant necessary CloudWatch, SNS, and IAM permissions to the deploying principal

**Invalid Region:**
- Error: Region parameter specifies a region where Bedrock is not available
- Handling: Parameter description warns about Bedrock availability
- User Action: Select a region where Amazon Bedrock is supported

**Resource Limits:**
- Error: Account has reached CloudWatch dashboard or alarm limits
- Handling: CloudFormation rollback with clear error message
- User Action: Delete unused dashboards/alarms or request limit increase

### Runtime Errors

**No Metric Data:**
- Scenario: Dashboard displays "No data available" for widgets
- Cause: Nova Pro model has not been invoked in the monitored region
- Resolution: Widgets show empty state; data appears once invocations occur

**Missing Guardrail Metrics:**
- Scenario: Guardrail widgets show no data
- Cause: No guardrails configured for the Nova Pro model
- Resolution: Guardrail section remains empty; no errors displayed

**Cost Calculation Inaccuracy:**
- Scenario: Displayed costs don't match AWS billing
- Cause: Pricing constants in template are outdated
- Resolution: Template includes comments indicating pricing update dates; users can update constants

### Alarm False Positives

**Low Traffic Periods:**
- Scenario: Error rate alarm triggers during low-traffic periods
- Cause: Small sample size makes percentage calculations volatile
- Mitigation: Alarms use "M out of N" evaluation periods to reduce noise

**Cold Start Latency:**
- Scenario: Latency alarm triggers after idle periods
- Cause: First invocations after idle time have higher latency
- Mitigation: P99 latency alarm uses 3 consecutive periods to avoid single-spike triggers

## Testing Strategy

### Unit Testing Approach

The CloudFormation template itself is the primary artifact, so testing focuses on template validation and structure verification:

**Template Validation Tests:**
- Validate CloudFormation template syntax using `cfn-lint`
- Verify all required parameters are defined
- Verify all outputs are properly formatted
- Check that all resource references are valid

**Dashboard JSON Structure Tests:**
- Parse dashboard body JSON and verify it's valid JSON
- Verify all widgets have required properties (type, x, y, width, height)
- Verify metric widgets have valid metric arrays
- Check that widget positions don't overlap

**Alarm Configuration Tests:**
- Verify each alarm has required properties (MetricName, Threshold, ComparisonOperator)
- Verify alarm thresholds reference parameters correctly
- Verify alarm actions reference the SNS topic when email is provided

**IAM Policy Tests:**
- Parse IAM policy documents and verify valid JSON
- Verify policy statements have required fields (Effect, Action, Resource)
- Check that actions are scoped appropriately

### Property-Based Testing Approach

Property-based tests will use `cfn-python-lint` and custom Python scripts with a property testing library (Hypothesis) to verify universal properties across the template:

**Test Configuration:**
- Minimum 100 iterations per property test
- Use Hypothesis for Python-based property tests
- Generate variations of template parameters to test properties

**Property Test 1: Region Consistency**
- **Feature: nova-cloudwatch-dashboard, Property 1: Region consistency across all metrics**
- Generator: Create dashboard JSON with random widget configurations
- Test: Parse all metric definitions and verify they all reference the same region
- Validates: All widgets use consistent region parameter

**Property Test 2: Model Dimension Inclusion**
- **Feature: nova-cloudwatch-dashboard, Property 2: Model dimension inclusion**
- Generator: Create metric definitions with various namespaces
- Test: For metrics in AWS/Bedrock namespace, verify ModelId dimension is present
- Validates: Bedrock metrics are properly segmented by model

**Property Test 3: Optional Parameters Have Defaults**
- **Feature: nova-cloudwatch-dashboard, Property 3: Optional parameters have defaults**
- Generator: Parse template parameters section
- Test: For each parameter without Required=true, verify Default field exists
- Validates: All optional parameters can be omitted during deployment

**Property Test 4: Update-Safe Resources**
- **Feature: nova-cloudwatch-dashboard, Property 4: Update-safe resource configuration**
- Generator: Parse all resource definitions
- Test: Verify resources don't have properties that force replacement (check CloudFormation docs)
- Validates: Stack updates don't cause unnecessary resource recreation

**Property Test 5: Least-Privilege IAM**
- **Feature: nova-cloudwatch-dashboard, Property 5: Least-privilege IAM permissions**
- Generator: Parse all IAM policy statements
- Test: Verify actions are minimal and resources are constrained
- Validates: IAM policies follow least-privilege principle

**Property Test 6: Scoped CloudWatch Permissions**
- **Feature: nova-cloudwatch-dashboard, Property 6: Scoped CloudWatch permissions**
- Generator: Parse IAM policies for CloudWatch actions
- Test: Verify resource constraints or conditions are present
- Validates: CloudWatch permissions are appropriately scoped

**Property Test 7: Alarm SNS Integration**
- **Feature: nova-cloudwatch-dashboard, Property 7: Alarm SNS integration**
- Generator: Parse alarm resources
- Test: When AlarmEmail parameter is set, verify AlarmActions references SNS topic
- Validates: Alarms properly integrate with notification system

### Integration Testing

**Deployment Tests:**
- Deploy template to test AWS account
- Verify all resources are created successfully
- Verify dashboard is accessible via output URL
- Verify alarms are in OK state initially

**Metric Visualization Tests:**
- Invoke Nova Pro model to generate test metrics
- Wait for metrics to propagate to CloudWatch
- Verify dashboard widgets display data correctly
- Verify calculated metrics (cost, rates) show expected values

**Alarm Trigger Tests:**
- Generate conditions that should trigger alarms (high error rate, high latency)
- Verify alarms transition to ALARM state
- Verify SNS notifications are sent (if configured)
- Verify alarm messages contain useful context

**Update Tests:**
- Deploy initial template version
- Modify parameters and update stack
- Verify updates complete without resource replacement
- Verify dashboard continues functioning after update

### Manual Testing Checklist

- [ ] Deploy template in fresh AWS account
- [ ] Verify dashboard loads without errors
- [ ] Generate test traffic to Nova Pro model
- [ ] Verify all widget sections display data
- [ ] Test alarm threshold adjustments
- [ ] Verify SNS email subscription confirmation
- [ ] Test stack update with parameter changes
- [ ] Verify cost calculations match expected values
- [ ] Test in multiple AWS regions
- [ ] Verify guardrail widgets (if guardrails configured)

## Implementation Notes

### CloudFormation Template Best Practices

1. **Use Intrinsic Functions**: Leverage `Fn::Sub`, `Fn::Join`, and `Ref` for dynamic value construction
2. **Parameterize Appropriately**: Balance flexibility with simplicity; don't over-parameterize
3. **Include Metadata**: Use `AWS::CloudFormation::Interface` for better parameter grouping in console
4. **Version Control**: Include template version in description for tracking
5. **Comments**: Use YAML format for better inline documentation support

### Dashboard JSON Construction

1. **Widget Grid System**: CloudWatch uses 24-column grid; plan widget layouts carefully
2. **Escape JSON**: When embedding JSON in CloudFormation, properly escape quotes and special characters
3. **Use Fn::Sub for Region**: Inject region parameter into dashboard JSON using CloudFormation functions
4. **Metric Math**: Use CloudWatch metric math for calculated metrics (cost, rates, percentages)
5. **Period Selection**: Choose appropriate periods based on metric resolution and retention

### Cost Optimization

1. **Dashboard Pricing**: CloudWatch dashboards cost $3/month; document this in template description
2. **Alarm Pricing**: Standard alarms cost $0.10/month; high-resolution alarms cost $0.30/month
3. **Metric Queries**: Dashboard metric queries are free; API calls for programmatic access are charged
4. **Log Insights**: Log widgets incur charges based on data scanned; limit query time ranges

### Maintenance Considerations

1. **Pricing Updates**: Nova Pro pricing may change; include pricing update date in comments
2. **Metric Changes**: AWS may add new Bedrock metrics; template should be updated to include them
3. **Region Expansion**: As Bedrock expands to new regions, update parameter descriptions
4. **Model Versions**: New Nova model versions may have different model IDs; parameterize model ID

## Security Considerations

### Security Review Findings (December 2025)

**CRITICAL SECURITY ISSUES IDENTIFIED:**

1. **IAM Trust Policy Over-Permissive** 
   - Current: Allows any principal in account (`arn:aws:iam::${AWS::AccountId}:root`)
   - Risk: Privilege escalation, unauthorized dashboard access
   - Fix: Restrict to specific users/roles with ExternalId for cross-account access

2. **CloudWatch Permissions Lack Region Scoping**
   - Current: Metrics permissions don't restrict region access
   - Risk: Access to CloudWatch metrics in other regions
   - Fix: Add `aws:RequestedRegion` condition to all CloudWatch permissions

3. **Logs Permissions Too Broad**
   - Current: Access to all Bedrock model logs (`/aws/bedrock/modelinvocations*`)
   - Risk: Access to other models' sensitive logs
   - Fix: Scope to specific model (`/aws/bedrock/modelinvocations/${ModelId}*`)

4. **Missing Resource Protection**
   - Current: Critical resources lack DeletionPolicy/UpdateReplacePolicy
   - Risk: Accidental resource deletion during stack operations
   - Fix: Add `DeletionPolicy: Retain` to all IAM and monitoring resources

### Security Architecture Principles

**Defense in Depth:**
- Multiple layers of access control (IAM policies, resource policies, conditions)
- Principle of least privilege at every level
- Encryption in transit and at rest for all data flows

**Zero Trust Model:**
- No implicit trust based on network location
- Explicit verification for every access request
- Continuous monitoring and validation of access patterns

**Secure by Default:**
- All sensitive parameters use NoEcho
- KMS encryption enabled for SNS topics
- IAM policies start with minimal permissions

### Detailed Security Controls

**1. Identity and Access Management**

```yaml
# SECURE IAM Trust Policy Template
AssumeRolePolicyDocument:
  Version: '2012-10-17'
  Statement:
    - Effect: Allow
      Principal:
        AWS:
          - 'arn:aws:iam::${AWS::AccountId}:user/dashboard-admin'
          - 'arn:aws:iam::${AWS::AccountId}:role/MonitoringTeamRole'
      Action: sts:AssumeRole
      Condition:
        StringEquals:
          'sts:ExternalId': !Ref ExternalId
        IpAddress:
          'aws:SourceIp': !Ref AllowedSourceIPs
        DateGreaterThan:
          'aws:CurrentTime': '2025-01-01T00:00:00Z'
        DateLessThan:
          'aws:CurrentTime': '2026-01-01T00:00:00Z'
```

**2. Resource-Level Security**

```yaml
# CloudWatch Permissions with Full Scoping
- Effect: Allow
  Action:
    - cloudwatch:GetMetricData
    - cloudwatch:GetMetricStatistics
    - cloudwatch:ListMetrics
  Resource: '*'
  Condition:
    StringEquals:
      'cloudwatch:namespace': 
        - 'AWS/Bedrock'
        - 'AWS/Bedrock/Guardrails'
      'aws:RequestedRegion': !Ref MonitoringRegion
    ForAllValues:StringLike:
      'cloudwatch:MetricName': 
        - 'Invocation*'
        - '*TokenCount'
        - '*Latency'
```

**3. Data Protection**

```yaml
# SNS Topic with Enhanced Security
AlarmTopic:
  Type: AWS::SNS::Topic
  Properties:
    KmsMasterKeyId: alias/aws/sns
    Policy:
      Statement:
        - Effect: Allow
          Principal:
            Service: cloudwatch.amazonaws.com
          Action: sns:Publish
          Resource: !Ref AlarmTopic
          Condition:
            StringEquals:
              'aws:SourceAccount': !Ref AWS::AccountId
        - Effect: Deny
          Principal: '*'
          Action: '*'
          Resource: !Ref AlarmTopic
          Condition:
            Bool:
              'aws:SecureTransport': 'false'
```

**4. Monitoring and Auditing**

```yaml
# CloudTrail Integration for Security Monitoring
SecurityAuditRole:
  Type: AWS::IAM::Role
  Properties:
    AssumeRolePolicyDocument:
      Statement:
        - Effect: Allow
          Principal:
            Service: cloudtrail.amazonaws.com
          Action: sts:AssumeRole
    Policies:
      - PolicyName: CloudTrailLogsPolicy
        PolicyDocument:
          Statement:
            - Effect: Allow
              Action:
                - logs:CreateLogGroup
                - logs:CreateLogStream
                - logs:PutLogEvents
              Resource: 
                - !Sub 'arn:aws:logs:${MonitoringRegion}:${AWS::AccountId}:log-group:/aws/cloudtrail/nova-dashboard*'
```

### Security Testing Strategy

**1. Automated Security Validation**

```python
def test_iam_policy_least_privilege():
    """Validate IAM policies follow least privilege principle."""
    policies = extract_iam_policies()
    for policy in policies:
        # Verify no wildcard actions
        assert not any('*' in action for action in policy.actions)
        # Verify resource constraints exist
        assert policy.has_resource_constraints or policy.has_conditions
        # Verify no privilege escalation paths
        assert not any(action.startswith('iam:') for action in policy.actions)

def test_cross_account_access_controls():
    """Validate cross-account access is properly restricted."""
    trust_policy = extract_trust_policy()
    # Verify ExternalId is required
    assert 'sts:ExternalId' in trust_policy.conditions
    # Verify source IP restrictions exist
    assert 'aws:SourceIp' in trust_policy.conditions
```

**2. Penetration Testing Scenarios**

- **Privilege Escalation**: Attempt to assume higher-privilege roles
- **Cross-Region Access**: Try to access metrics from unauthorized regions  
- **Data Exfiltration**: Attempt to access logs from other models
- **Denial of Service**: Try to delete or modify critical resources

**3. Security Compliance Validation**

```bash
# AWS Config Rules for Compliance
aws configservice put-config-rule \
  --config-rule '{
    "ConfigRuleName": "iam-role-managed-policy-check",
    "Source": {
      "Owner": "AWS",
      "SourceIdentifier": "IAM_ROLE_MANAGED_POLICY_CHECK"
    },
    "InputParameters": "{\"managedPolicyArns\":\"arn:aws:iam::aws:policy/ReadOnlyAccess\"}"
  }'

# Security Hub Integration
aws securityhub enable-security-hub \
  --enable-default-standards
```

### Incident Response Procedures

**1. Security Event Detection**
- CloudTrail logs unusual IAM role assumptions
- AWS Config detects policy changes
- CloudWatch alarms trigger on suspicious metric access patterns

**2. Immediate Response Actions**
```bash
# Emergency role disable
aws iam attach-role-policy \
  --role-name DashboardViewerRole \
  --policy-arn arn:aws:iam::aws:policy/AWSDenyAll

# Isolate SNS topic
aws sns set-topic-attributes \
  --topic-arn $TOPIC_ARN \
  --attribute-name Policy \
  --attribute-value '{"Statement":[{"Effect":"Deny","Principal":"*","Action":"*"}]}'
```

**3. Investigation and Recovery**
- Analyze CloudTrail logs for attack timeline
- Review IAM Access Analyzer findings
- Update security policies based on lessons learned
- Restore services with enhanced security controls

### Security Compliance Framework

**SOC 2 Type II Controls:**
- Access controls (CC6.1): IAM policies with least privilege
- Logical access (CC6.2): Multi-factor authentication requirements
- Data protection (CC6.7): Encryption in transit and at rest

**ISO 27001 Controls:**
- A.9.1.2: Access to networks and network services
- A.9.4.2: Secure log-on procedures  
- A.10.1.1: Policy on the use of cryptographic controls

**AWS Well-Architected Security Pillar:**
- Identity and access management
- Detective controls
- Infrastructure protection
- Data protection in transit and at rest
- Incident response

### Security Maintenance Schedule

**Daily:**
- Monitor CloudTrail logs for unusual access patterns
- Review CloudWatch alarms for security-related triggers

**Weekly:**
- Run IAM Access Analyzer to identify unused permissions
- Review SNS topic subscription changes

**Monthly:**
- Rotate IAM access keys (if any programmatic access)
- Review and update IP allowlists
- Test incident response procedures

**Quarterly:**
- Security policy review and updates
- Penetration testing of dashboard access controls
- Compliance audit against security frameworks

### Legacy Security Considerations

1. **SNS Topic Encryption**: ✅ KMS encryption enabled (`alias/aws/sns`)
2. **Dashboard Access**: ✅ IAM authentication required (no public access)
3. **Sensitive Data**: ✅ No PII in log widgets (filtered queries only)
4. **Cross-Account Access**: ⚠️ Needs ExternalId and IP restrictions
5. **Alarm Actions**: ⚠️ Needs SNS topic access policy validation

## Future Enhancements

1. **Multi-Model Support**: Extend template to monitor multiple models simultaneously
2. **Custom Metrics**: Add support for application-specific custom metrics
3. **Anomaly Detection**: Integrate CloudWatch Anomaly Detection for automatic threshold adjustment
4. **Cost Allocation Tags**: Add support for cost allocation by project/team using tags
5. **Composite Alarms**: Create composite alarms combining multiple conditions
6. **Lambda Integration**: Add Lambda functions for advanced metric calculations
7. **Cross-Region Dashboard**: Support monitoring multiple regions in single dashboard
8. **Automated Reporting**: Add EventBridge rules to generate periodic metric reports
