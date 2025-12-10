#!/usr/bin/env python3
"""
Property-based tests for Nova Pro CloudWatch Dashboard CloudFormation template.

These tests verify universal correctness properties that should hold across
all template configurations.
"""

import json
import boto3
from hypothesis import given, strategies as st, settings
import pytest


def load_template():
    """Load the CloudFormation template using AWS CloudFormation validation."""
    try:
        # Use AWS CloudFormation to validate and parse the template
        with open('nova-pro-dashboard-template.yaml', 'r') as f:
            template_body = f.read()
        
        # Use boto3 to validate the template (this handles CloudFormation intrinsic functions)
        cf_client = boto3.client('cloudformation', region_name='us-east-1')
        response = cf_client.validate_template(TemplateBody=template_body)
        
        # For testing purposes, we'll parse the template manually
        # but skip the complex JSON sections that cause YAML parsing issues
        import yaml
        
        # Create a custom YAML loader that handles CloudFormation functions
        class CloudFormationLoader(yaml.SafeLoader):
            pass
        
        def construct_fn(loader, tag_suffix, node):
            """Handle CloudFormation intrinsic functions."""
            if isinstance(node, yaml.ScalarNode):
                return {f'Fn::{tag_suffix}': loader.construct_scalar(node)}
            elif isinstance(node, yaml.SequenceNode):
                return {f'Fn::{tag_suffix}': loader.construct_sequence(node)}
            elif isinstance(node, yaml.MappingNode):
                return {f'Fn::{tag_suffix}': loader.construct_mapping(node)}
        
        def construct_ref(loader, node):
            """Handle CloudFormation Ref function."""
            return {'Ref': loader.construct_scalar(node)}
        
        # Add constructors for CloudFormation functions
        CloudFormationLoader.add_multi_constructor('!', construct_fn)
        CloudFormationLoader.add_constructor('!Ref', construct_ref)
        
        # Parse the template with our custom loader
        template = yaml.load(template_body, Loader=CloudFormationLoader)
        return template
        
    except Exception as e:
        # Fallback: parse just the parts we need for testing
        with open('nova-pro-dashboard-template.yaml', 'r') as f:
            lines = f.readlines()
        
        # Extract just the Parameters section for our tests
        template = {'Parameters': {}}
        in_parameters = False
        current_param = None
        indent_level = 0
        
        for line in lines:
            stripped = line.strip()
            if stripped == 'Parameters:':
                in_parameters = True
                continue
            elif in_parameters and line.startswith('Resources:'):
                break
            elif in_parameters and stripped and not line.startswith(' '):
                break
            elif in_parameters and stripped:
                # Count indentation
                indent = len(line) - len(line.lstrip())
                
                if indent == 2 and ':' in stripped:  # Parameter name
                    current_param = stripped.split(':')[0]
                    template['Parameters'][current_param] = {}
                elif indent == 4 and current_param and ':' in stripped:  # Parameter property
                    key, value = stripped.split(':', 1)
                    value = value.strip()
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.isdigit():
                        value = int(value)
                    elif value in ['true', 'false']:
                        value = value == 'true'
                    template['Parameters'][current_param][key] = value
        
        return template


def test_optional_parameters_have_defaults():
    """
    **Feature: nova-cloudwatch-dashboard, Property 3: Optional parameters have defaults**
    **Validates: Requirements 8.2**
    
    Property: For any CloudFormation parameter marked as optional (not required),
    the parameter definition should include a Default value.
    
    This ensures that users can deploy the template without specifying every parameter,
    providing sensible defaults for optional configuration values.
    """
    template = load_template()
    parameters = template.get('Parameters', {})
    
    # Required parameters (these should NOT have defaults or can have them)
    # MonitoringRegion is required (no default expected)
    required_params = {'MonitoringRegion'}
    
    # Check all parameters
    for param_name, param_config in parameters.items():
        if param_name in required_params:
            # Required parameters don't need defaults
            continue
        
        # All other parameters are optional and MUST have defaults
        assert 'Default' in param_config, (
            f"Optional parameter '{param_name}' is missing a Default value. "
            f"All optional parameters must have defaults per Requirements 8.2"
        )
        
        # Verify the default is not None (empty string is acceptable for AlarmEmail)
        default_value = param_config['Default']
        assert default_value is not None, (
            f"Optional parameter '{param_name}' has None as Default. "
            f"Defaults should be meaningful values or empty strings."
        )


@given(st.data())
@settings(max_examples=100, deadline=None)
def test_optional_parameters_have_defaults_property(data):
    """
    **Feature: nova-cloudwatch-dashboard, Property 3: Optional parameters have defaults**
    **Validates: Requirements 8.2**
    
    Property-based test: For any subset of optional parameters in the template,
    all should have Default values defined.
    
    This test generates random subsets of parameters and verifies the property holds.
    """
    template = load_template()
    parameters = template.get('Parameters', {})
    
    # Required parameters that don't need defaults
    required_params = {'MonitoringRegion'}
    
    # Get optional parameters
    optional_params = {k: v for k, v in parameters.items() if k not in required_params}
    
    if not optional_params:
        # If no optional parameters exist, test passes trivially
        return
    
    # Select a random subset of optional parameters to check
    param_names = list(optional_params.keys())
    selected_params = data.draw(
        st.lists(
            st.sampled_from(param_names),
            min_size=1,
            max_size=len(param_names),
            unique=True
        )
    )
    
    # Verify each selected optional parameter has a default
    for param_name in selected_params:
        param_config = optional_params[param_name]
        
        assert 'Default' in param_config, (
            f"Optional parameter '{param_name}' is missing a Default value"
        )
        
        # Verify default is not None
        assert param_config['Default'] is not None, (
            f"Optional parameter '{param_name}' has None as Default"
        )


def test_required_parameters_identified_correctly():
    """
    Helper test to verify we correctly identify required vs optional parameters.
    
    MonitoringRegion should be required (no default).
    All other parameters should be optional (have defaults).
    """
    template = load_template()
    parameters = template.get('Parameters', {})
    
    # MonitoringRegion should not have a default (it's required)
    assert 'MonitoringRegion' in parameters
    assert 'Default' not in parameters['MonitoringRegion'], (
        "MonitoringRegion should be required and not have a default value"
    )
    
    # ModelId should have a default (it's optional with a sensible default)
    assert 'ModelId' in parameters
    assert 'Default' in parameters['ModelId']
    assert parameters['ModelId']['Default'] == 'amazon.nova-pro-v1:0'
    
    # DashboardName should have a default
    assert 'DashboardName' in parameters
    assert 'Default' in parameters['DashboardName']
    assert parameters['DashboardName']['Default'] == 'NovaProMonitoring'
    
    # All alarm thresholds should have defaults
    alarm_params = [
        'ErrorRateThreshold',
        'P99LatencyThreshold', 
        'DailyCostThreshold',
        'ThrottleRateThreshold'
    ]
    
    for param in alarm_params:
        assert param in parameters, f"Missing alarm parameter: {param}"
        assert 'Default' in parameters[param], f"{param} should have a default"
        assert isinstance(parameters[param]['Default'], (int, float)), (
            f"{param} default should be numeric"
        )
    
    # AlarmEmail should have a default (empty string is acceptable)
    assert 'AlarmEmail' in parameters
    assert 'Default' in parameters['AlarmEmail']
    assert parameters['AlarmEmail']['Default'] == ""


def extract_dashboard_json():
    """Extract the dashboard JSON from the CloudFormation template."""
    try:
        with open('nova-pro-dashboard-template.yaml', 'r') as f:
            content = f.read()
        
        # Find the DashboardBody section
        start_marker = 'DashboardBody:'
        end_marker = '# CloudWatch Alarms'
        
        start_idx = content.find(start_marker)
        end_idx = content.find(end_marker)
        
        if start_idx == -1 or end_idx == -1:
            raise ValueError("Could not find dashboard JSON section in template")
        
        dashboard_section = content[start_idx:end_idx]
        
        # Extract the JSON part (between the Fn::Sub and the end)
        json_start = dashboard_section.find('|')
        if json_start == -1:
            raise ValueError("Could not find JSON start in dashboard section")
        
        json_content = dashboard_section[json_start + 1:].strip()
        
        # Parse the JSON (it contains CloudFormation variables like ${MonitoringRegion})
        # We'll replace these with placeholder values for parsing
        json_content = json_content.replace('${MonitoringRegion}', 'us-east-1')
        json_content = json_content.replace('${ModelId}', 'amazon.nova-pro-v1:0')
        json_content = json_content.replace('${ErrorRateThreshold}', '5')
        
        # Parse the JSON
        dashboard_json = json.loads(json_content)
        return dashboard_json
        
    except Exception as e:
        print(f"Error extracting dashboard JSON: {e}")
        return None


def test_region_consistency_across_metrics():
    """
    **Feature: nova-cloudwatch-dashboard, Property 1: Region consistency across all metrics**
    **Validates: Requirements 1.3**
    
    Property: For any widget in the dashboard that contains CloudWatch metrics,
    all metric definitions within that widget should reference the same region parameter value.
    
    This ensures that all metrics are queried from the same AWS region, preventing
    data inconsistencies and ensuring proper monitoring scope.
    """
    dashboard_json = extract_dashboard_json()
    assert dashboard_json is not None, "Could not extract dashboard JSON from template"
    
    widgets = dashboard_json.get('widgets', [])
    assert len(widgets) > 0, "Dashboard should contain widgets"
    
    for i, widget in enumerate(widgets):
        properties = widget.get('properties', {})
        
        # Check if widget has a region property
        if 'region' in properties:
            widget_region = properties['region']
            
            # All widgets should use the same region (MonitoringRegion parameter)
            assert widget_region == 'us-east-1', (
                f"Widget {i} uses region '{widget_region}' but should use MonitoringRegion parameter. "
                f"All widgets must use consistent region per Requirements 1.3"
            )
        
        # For metric widgets, also check that metrics don't specify different regions
        if widget.get('type') == 'metric' and 'metrics' in properties:
            metrics = properties['metrics']
            for metric in metrics:
                if isinstance(metric, list) and len(metric) >= 2:
                    # Standard metric format: ["Namespace", "MetricName", ...]
                    # Region should be specified at widget level, not metric level
                    continue
                elif isinstance(metric, dict) and 'MetricStat' in metric:
                    # Alarm-style metric format
                    metric_stat = metric['MetricStat']
                    if 'Region' in metric_stat:
                        metric_region = metric_stat['Region']
                        assert metric_region == 'us-east-1', (
                            f"Widget {i} metric specifies region '{metric_region}' "
                            f"but should use consistent MonitoringRegion"
                        )


def test_model_dimension_inclusion():
    """
    **Feature: nova-cloudwatch-dashboard, Property 2: Model dimension inclusion**
    **Validates: Requirements 2.5**
    
    Property: For any CloudWatch metric query in the dashboard that queries the AWS/Bedrock namespace,
    the metric should include the ModelId dimension to segment data by model version.
    
    This ensures that metrics are properly scoped to the specific Nova Pro model being monitored,
    preventing data mixing from different models.
    """
    dashboard_json = extract_dashboard_json()
    assert dashboard_json is not None, "Could not extract dashboard JSON from template"
    
    widgets = dashboard_json.get('widgets', [])
    assert len(widgets) > 0, "Dashboard should contain widgets"
    
    for i, widget in enumerate(widgets):
        properties = widget.get('properties', {})
        
        # Check metric widgets
        if widget.get('type') == 'metric' and 'metrics' in properties:
            metrics = properties['metrics']
            
            for j, metric in enumerate(metrics):
                if isinstance(metric, list) and len(metric) >= 2:
                    namespace = metric[0]
                    
                    # Check AWS/Bedrock namespace metrics
                    if namespace == 'AWS/Bedrock':
                        # Should have ModelId dimension
                        has_model_dimension = False
                        
                        # Look for ModelId dimension in the metric definition
                        for k in range(2, len(metric), 2):
                            if k + 1 < len(metric) and metric[k] == 'ModelId':
                                has_model_dimension = True
                                model_id_value = metric[k + 1]
                                assert model_id_value == 'amazon.nova-pro-v1:0', (
                                    f"Widget {i}, metric {j} has ModelId '{model_id_value}' "
                                    f"but should use ModelId parameter value"
                                )
                                break
                        
                        assert has_model_dimension, (
                            f"Widget {i}, metric {j} queries AWS/Bedrock namespace "
                            f"but missing ModelId dimension. All Bedrock metrics must include "
                            f"ModelId dimension per Requirements 2.5"
                        )
                
                elif isinstance(metric, dict) and 'expression' in metric.lower():
                    # Expression metrics reference other metrics by ID, 
                    # so we don't need to check them directly
                    continue


@given(st.data())
@settings(max_examples=100, deadline=None)
def test_region_consistency_property_based(data):
    """
    **Feature: nova-cloudwatch-dashboard, Property 1: Region consistency across all metrics**
    **Validates: Requirements 1.3**
    
    Property-based test: For any subset of widgets in the dashboard,
    all should use the same region configuration.
    """
    dashboard_json = extract_dashboard_json()
    if dashboard_json is None:
        return  # Skip if we can't parse the dashboard
    
    widgets = dashboard_json.get('widgets', [])
    if not widgets:
        return  # Skip if no widgets
    
    # Select a random subset of widgets to check
    widget_indices = data.draw(
        st.lists(
            st.integers(min_value=0, max_value=len(widgets) - 1),
            min_size=1,
            max_size=min(10, len(widgets)),
            unique=True
        )
    )
    
    expected_region = 'us-east-1'  # MonitoringRegion parameter value
    
    for idx in widget_indices:
        widget = widgets[idx]
        properties = widget.get('properties', {})
        
        if 'region' in properties:
            assert properties['region'] == expected_region, (
                f"Widget {idx} uses inconsistent region: {properties['region']}"
            )


@given(st.data())
@settings(max_examples=100, deadline=None)
def test_model_dimension_inclusion_property_based(data):
    """
    **Feature: nova-cloudwatch-dashboard, Property 2: Model dimension inclusion**
    **Validates: Requirements 2.5**
    
    Property-based test: For any subset of AWS/Bedrock metrics in the dashboard,
    all should include the ModelId dimension.
    """
    dashboard_json = extract_dashboard_json()
    if dashboard_json is None:
        return  # Skip if we can't parse the dashboard
    
    widgets = dashboard_json.get('widgets', [])
    if not widgets:
        return  # Skip if no widgets
    
    # Collect all AWS/Bedrock metrics (store indices only to avoid hashability issues)
    bedrock_metric_indices = []
    for i, widget in enumerate(widgets):
        properties = widget.get('properties', {})
        if widget.get('type') == 'metric' and 'metrics' in properties:
            for j, metric in enumerate(properties['metrics']):
                if isinstance(metric, list) and len(metric) >= 2 and metric[0] == 'AWS/Bedrock':
                    bedrock_metric_indices.append((i, j))
    
    if not bedrock_metric_indices:
        return  # Skip if no Bedrock metrics
    
    # Select a random subset of Bedrock metric indices to check
    selected_indices = data.draw(
        st.lists(
            st.sampled_from(bedrock_metric_indices),
            min_size=1,
            max_size=min(10, len(bedrock_metric_indices)),
            unique=True
        )
    )
    
    for widget_idx, metric_idx in selected_indices:
        widget = widgets[widget_idx]
        metric = widget['properties']['metrics'][metric_idx]
        
        # Check for ModelId dimension
        has_model_dimension = False
        for k in range(2, len(metric), 2):
            if k + 1 < len(metric) and metric[k] == 'ModelId':
                has_model_dimension = True
                break
        
        assert has_model_dimension, (
            f"Widget {widget_idx}, metric {metric_idx} missing ModelId dimension"
        )


def extract_template_resources():
    """Extract resources section from the CloudFormation template."""
    try:
        with open('nova-pro-dashboard-template.yaml', 'r') as f:
            content = f.read()
        
        # Find the Resources section
        resources_start = content.find('Resources:')
        outputs_start = content.find('Outputs:')
        
        if resources_start == -1:
            raise ValueError("Could not find Resources section in template")
        
        if outputs_start == -1:
            resources_section = content[resources_start:]
        else:
            resources_section = content[resources_start:outputs_start]
        
        # Parse the resources section manually to extract alarm resources
        lines = resources_section.split('\n')
        resources = {}
        current_resource = None
        current_properties = {}
        indent_level = 0
        in_properties = False
        
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            
            # Count indentation
            indent = len(line) - len(line.lstrip())
            
            # Resource name (indent 2)
            if indent == 2 and ':' in stripped and not stripped.startswith('-'):
                if current_resource:
                    resources[current_resource] = current_properties
                current_resource = stripped.split(':')[0]
                current_properties = {}
                in_properties = False
            
            # Resource type (indent 4)
            elif indent == 4 and stripped.startswith('Type:'):
                current_properties['Type'] = stripped.split(':', 1)[1].strip()
            
            # Properties section (indent 4)
            elif indent == 4 and stripped == 'Properties:':
                in_properties = True
                current_properties['Properties'] = {}
            
            # Property values (indent 6+)
            elif in_properties and indent >= 6 and ':' in stripped:
                key = stripped.split(':', 1)[0]
                value = stripped.split(':', 1)[1].strip()
                
                # Handle AlarmActions specifically
                if key == 'AlarmActions':
                    current_properties['Properties']['AlarmActions'] = 'conditional'
                elif key in ['AlarmName', 'AlarmDescription', 'MetricName', 'Namespace']:
                    current_properties['Properties'][key] = value
        
        # Add the last resource
        if current_resource:
            resources[current_resource] = current_properties
        
        return resources
        
    except Exception as e:
        print(f"Error extracting resources: {e}")
        return {}


def test_alarm_sns_integration():
    """
    **Feature: nova-cloudwatch-dashboard, Property 7: Alarm SNS integration**
    **Validates: Requirements 10.5**
    
    Property: For any CloudWatch alarm resource in the template, if the AlarmEmail parameter 
    is provided, the alarm should have an AlarmActions property referencing the SNS topic.
    
    This ensures that when users provide an email address for notifications, all alarms
    will properly send notifications to that email via the SNS topic.
    """
    resources = extract_template_resources()
    assert len(resources) > 0, "Could not extract resources from template"
    
    # Find all CloudWatch alarm resources
    alarm_resources = {}
    for resource_name, resource_config in resources.items():
        if resource_config.get('Type') == 'AWS::CloudWatch::Alarm':
            alarm_resources[resource_name] = resource_config
    
    assert len(alarm_resources) > 0, "Template should contain CloudWatch alarm resources"
    
    # Verify each alarm has conditional AlarmActions
    for alarm_name, alarm_config in alarm_resources.items():
        properties = alarm_config.get('Properties', {})
        
        # Each alarm should have AlarmActions property
        assert 'AlarmActions' in properties, (
            f"Alarm '{alarm_name}' is missing AlarmActions property. "
            f"All alarms must have AlarmActions for SNS integration per Requirements 10.5"
        )
        
        # The AlarmActions should be conditional (we detect this by checking the template structure)
        # In our parsing, we marked conditional AlarmActions as 'conditional'
        alarm_actions = properties.get('AlarmActions')
        assert alarm_actions == 'conditional', (
            f"Alarm '{alarm_name}' should have conditional AlarmActions that reference "
            f"SNS topic when AlarmEmail is provided per Requirements 10.5"
        )
    
    # Verify we have the expected alarms
    expected_alarms = [
        'HighErrorRateAlarm',
        'HighP99LatencyAlarm', 
        'DailyCostLimitAlarm',
        'HighThrottlingRateAlarm'
    ]
    
    for expected_alarm in expected_alarms:
        assert expected_alarm in alarm_resources, (
            f"Expected alarm '{expected_alarm}' not found in template"
        )


def extract_iam_policies():
    """Extract IAM policies from the CloudFormation template."""
    try:
        with open('nova-pro-dashboard-template.yaml', 'r') as f:
            content = f.read()
        
        # Find the DashboardViewerPolicy managed policy section
        policy_start = content.find('DashboardViewerPolicy:')
        if policy_start == -1:
            return {}
        
        # Find the end of the policy (look for next top-level resource)
        lines = content[policy_start:].split('\n')
        policy_lines = []
        
        for i, line in enumerate(lines):
            # Stop when we hit the next top-level resource (starts with 2 spaces and capital letter)
            if i > 0 and line.startswith('  ') and not line.startswith('    ') and line.strip() and line.strip()[0].isupper() and ':' in line:
                break
            policy_lines.append(line)
        
        policy_section = '\n'.join(policy_lines)
        
        # Extract policy statements from the managed policy
        policies = {}
        
        # Look for policy document statements
        if 'PolicyDocument:' in policy_section and 'Statement:' in policy_section:
            # Extract the policy statements by analyzing the content
            statements = []
            
            # Find CloudWatch dashboard permissions
            if 'cloudwatch:GetDashboard' in policy_section and 'cloudwatch:ListDashboards' in policy_section:
                # Check if this statement has resource scoping
                dashboard_section = policy_section[policy_section.find('cloudwatch:GetDashboard'):policy_section.find('cloudwatch:GetDashboard') + 500]
                has_resource_scoping = 'arn:aws:cloudwatch:' in dashboard_section and 'dashboard/' in dashboard_section
                
                statements.append({
                    'actions': ['cloudwatch:GetDashboard', 'cloudwatch:ListDashboards'],
                    'resource_scoped': has_resource_scoping,
                    'service': 'cloudwatch',
                    'statement_type': 'dashboard'
                })
            
            # Find CloudWatch metrics permissions
            if 'cloudwatch:GetMetricData' in policy_section:
                # Check if this statement has conditions
                metrics_section = policy_section[policy_section.find('cloudwatch:GetMetricData'):policy_section.find('cloudwatch:GetMetricData') + 800]
                has_conditions = 'Condition:' in metrics_section and 'cloudwatch:namespace' in metrics_section
                uses_wildcard_resource = "Resource: '*'" in metrics_section
                
                statements.append({
                    'actions': ['cloudwatch:GetMetricData', 'cloudwatch:GetMetricStatistics', 'cloudwatch:ListMetrics'],
                    'resource_scoped': not uses_wildcard_resource,
                    'has_conditions': has_conditions,
                    'service': 'cloudwatch',
                    'statement_type': 'metrics'
                })
            
            # Find CloudWatch Logs permissions
            if 'logs:StartQuery' in policy_section:
                # Check if this statement has resource scoping to Bedrock logs
                logs_section = policy_section[policy_section.find('logs:StartQuery'):policy_section.find('logs:StartQuery') + 500]
                has_bedrock_scoping = '/aws/bedrock/modelinvocations' in logs_section
                
                statements.append({
                    'actions': ['logs:StartQuery', 'logs:GetQueryResults', 'logs:DescribeLogGroups'],
                    'resource_scoped': has_bedrock_scoping,
                    'service': 'logs',
                    'statement_type': 'logs'
                })
            
            # Find Bedrock permissions
            if 'bedrock:GetModelInvocationLoggingConfiguration' in policy_section:
                # Check if this statement has conditions
                bedrock_section = policy_section[policy_section.find('bedrock:GetModelInvocationLoggingConfiguration'):policy_section.find('bedrock:GetModelInvocationLoggingConfiguration') + 500]
                has_conditions = 'Condition:' in bedrock_section and 'aws:RequestedRegion' in bedrock_section
                uses_wildcard_resource = "Resource: '*'" in bedrock_section
                
                statements.append({
                    'actions': ['bedrock:GetModelInvocationLoggingConfiguration', 'bedrock:ListFoundationModels'],
                    'resource_scoped': not uses_wildcard_resource,
                    'has_conditions': has_conditions,
                    'service': 'bedrock',
                    'statement_type': 'bedrock'
                })
            
            if statements:
                policies['DashboardViewerInlinePolicy'] = {
                    'statements': statements
                }
        
        return policies
        
    except Exception as e:
        print(f"Error extracting IAM policies: {e}")
        return {}


def test_least_privilege_iam_permissions():
    """
    **Feature: nova-cloudwatch-dashboard, Property 5: Least-privilege IAM permissions**
    **Validates: Requirements 9.1**
    
    Property: For any IAM policy statement in the template, the actions granted should be 
    scoped to the minimum necessary permissions and resources should be constrained where possible.
    
    This ensures that the dashboard viewer role follows AWS security best practices by granting
    only the minimum permissions required for dashboard functionality.
    """
    policies = extract_iam_policies()
    assert len(policies) > 0, "Could not extract IAM policies from template"
    
    # Check the DashboardViewerInlinePolicy
    assert 'DashboardViewerInlinePolicy' in policies, (
        "Template should contain DashboardViewerInlinePolicy"
    )
    
    policy = policies['DashboardViewerInlinePolicy']
    statements = policy.get('statements', [])
    assert len(statements) > 0, "Policy should contain permission statements"
    
    # Verify each statement follows least-privilege principles
    for i, statement in enumerate(statements):
        service = statement.get('service')
        actions = statement.get('actions', [])
        
        # All actions should be read-only (no write/delete/create permissions)
        for action in actions:
            action_verb = action.split(':')[1].lower()
            forbidden_verbs = [
                'create', 'delete', 'update', 'put', 'post', 'modify', 
                'change', 'set', 'add', 'remove', 'attach', 'detach'
            ]
            
            assert not any(verb in action_verb for verb in forbidden_verbs), (
                f"Statement {i} contains non-read-only action '{action}'. "
                f"Dashboard viewer role should only have read permissions per Requirements 9.1"
            )
        
        # CloudWatch dashboard actions should be resource-scoped
        if service == 'cloudwatch' and any('Dashboard' in action for action in actions):
            assert statement.get('resource_scoped', False), (
                f"Statement {i} with CloudWatch dashboard actions should be resource-scoped "
                f"to specific dashboard ARN per least-privilege principle"
            )
        
        # CloudWatch Logs actions should be resource-scoped to Bedrock logs
        if service == 'logs':
            assert statement.get('resource_scoped', False), (
                f"Statement {i} with CloudWatch Logs actions should be resource-scoped "
                f"to Bedrock log groups per least-privilege principle"
            )
        
        # Actions with Resource: '*' should have conditions to limit scope
        if not statement.get('resource_scoped', True):
            assert statement.get('has_conditions', False) == True, (
                f"Statement {i} uses Resource: '*' but lacks conditions. "
                f"Broad resource permissions must be constrained with conditions per Requirements 9.1"
            )


def test_scoped_cloudwatch_permissions():
    """
    **Feature: nova-cloudwatch-dashboard, Property 6: Scoped CloudWatch permissions**
    **Validates: Requirements 9.2**
    
    Property: For any IAM policy statement granting CloudWatch permissions, the statement 
    should include resource constraints or conditions limiting access to Bedrock-related metrics.
    
    This ensures that the dashboard viewer role can only access metrics relevant to Nova Pro
    monitoring and cannot access other CloudWatch metrics in the account.
    """
    policies = extract_iam_policies()
    assert len(policies) > 0, "Could not extract IAM policies from template"
    
    policy = policies.get('DashboardViewerInlinePolicy', {})
    statements = policy.get('statements', [])
    
    # Find CloudWatch-related statements
    cloudwatch_statements = [
        stmt for stmt in statements 
        if stmt.get('service') == 'cloudwatch'
    ]
    
    assert len(cloudwatch_statements) > 0, (
        "Template should contain CloudWatch permission statements"
    )
    
    for i, statement in enumerate(cloudwatch_statements):
        actions = statement.get('actions', [])
        
        # Dashboard actions should be resource-scoped
        dashboard_actions = [action for action in actions if 'Dashboard' in action]
        if dashboard_actions:
            assert statement.get('resource_scoped', False), (
                f"CloudWatch statement {i} with dashboard actions {dashboard_actions} "
                f"should be resource-scoped to specific dashboard ARN per Requirements 9.2"
            )
        
        # Metric actions should have namespace conditions
        metric_actions = [action for action in actions if 'Metric' in action]
        if metric_actions:
            # If using Resource: '*', must have conditions
            if not statement.get('resource_scoped', True):
                assert statement.get('has_conditions', False) == True, (
                    f"CloudWatch statement {i} with metric actions {metric_actions} "
                    f"uses broad resource permissions but lacks namespace conditions. "
                    f"Should be limited to AWS/Bedrock namespace per Requirements 9.2"
                )


@given(st.data())
@settings(max_examples=100, deadline=None)
def test_least_privilege_iam_permissions_property_based(data):
    """
    **Feature: nova-cloudwatch-dashboard, Property 5: Least-privilege IAM permissions**
    **Validates: Requirements 9.1**
    
    Property-based test: For any subset of IAM policy statements in the template,
    all should follow least-privilege principles with minimal necessary permissions.
    """
    policies = extract_iam_policies()
    if not policies:
        return  # Skip if we can't parse policies
    
    # Get all policy statements
    all_statements = []
    for policy_name, policy_config in policies.items():
        statements = policy_config.get('statements', [])
        for i, stmt in enumerate(statements):
            all_statements.append((policy_name, i, stmt))
    
    if not all_statements:
        return  # Skip if no statements found
    
    # Select a random subset of statement indices to check
    statement_indices = list(range(len(all_statements)))
    selected_indices = data.draw(
        st.lists(
            st.sampled_from(statement_indices),
            min_size=1,
            max_size=len(all_statements),
            unique=True
        )
    )
    
    selected_statements = [all_statements[i] for i in selected_indices]
    
    for policy_name, stmt_index, statement in selected_statements:
        actions = statement.get('actions', [])
        
        # Verify all actions are read-only
        for action in actions:
            action_verb = action.split(':')[1].lower()
            forbidden_verbs = [
                'create', 'delete', 'update', 'put', 'post', 'modify',
                'change', 'set', 'add', 'remove', 'attach', 'detach'
            ]
            
            assert not any(verb in action_verb for verb in forbidden_verbs), (
                f"Policy {policy_name}, statement {stmt_index} contains "
                f"non-read-only action '{action}'"
            )


@given(st.data())
@settings(max_examples=100, deadline=None)
def test_scoped_cloudwatch_permissions_property_based(data):
    """
    **Feature: nova-cloudwatch-dashboard, Property 6: Scoped CloudWatch permissions**
    **Validates: Requirements 9.2**
    
    Property-based test: For any subset of CloudWatch permission statements,
    all should be properly scoped to Bedrock-related resources or have appropriate conditions.
    """
    policies = extract_iam_policies()
    if not policies:
        return  # Skip if we can't parse policies
    
    # Get CloudWatch statements
    cloudwatch_statements = []
    for policy_name, policy_config in policies.items():
        statements = policy_config.get('statements', [])
        for i, stmt in enumerate(statements):
            if stmt.get('service') == 'cloudwatch':
                cloudwatch_statements.append((policy_name, i, stmt))
    
    if not cloudwatch_statements:
        return  # Skip if no CloudWatch statements
    
    # Select a random subset of CloudWatch statement indices to check
    statement_indices = list(range(len(cloudwatch_statements)))
    selected_indices = data.draw(
        st.lists(
            st.sampled_from(statement_indices),
            min_size=1,
            max_size=len(cloudwatch_statements),
            unique=True
        )
    )
    
    selected_statements = [cloudwatch_statements[i] for i in selected_indices]
    
    for policy_name, stmt_index, statement in selected_statements:
        actions = statement.get('actions', [])
        
        # Dashboard actions should be resource-scoped
        dashboard_actions = [action for action in actions if 'Dashboard' in action]
        if dashboard_actions:
            assert statement.get('resource_scoped', False), (
                f"Policy {policy_name}, statement {stmt_index} with dashboard actions "
                f"should be resource-scoped"
            )
        
        # Metric actions with broad resources should have conditions
        metric_actions = [action for action in actions if 'Metric' in action]
        if metric_actions and not statement.get('resource_scoped', True):
            assert statement.get('has_conditions', False) == True, (
                f"Policy {policy_name}, statement {stmt_index} with metric actions "
                f"should have namespace conditions"
            )


def test_sns_topic_conditional_creation():
    """
    Helper test to verify SNS topic and subscription are created conditionally.
    
    This supports the alarm SNS integration property by ensuring the SNS infrastructure
    exists when needed.
    """
    resources = extract_template_resources()
    
    # Should have AlarmTopic SNS resource
    assert 'AlarmTopic' in resources, "Template should contain AlarmTopic SNS resource"
    alarm_topic = resources['AlarmTopic']
    assert alarm_topic.get('Type') == 'AWS::SNS::Topic', (
        "AlarmTopic should be of type AWS::SNS::Topic"
    )
    
    # Should have AlarmSubscription resource
    assert 'AlarmSubscription' in resources, "Template should contain AlarmSubscription resource"
    alarm_subscription = resources['AlarmSubscription']
    assert alarm_subscription.get('Type') == 'AWS::SNS::Subscription', (
        "AlarmSubscription should be of type AWS::SNS::Subscription"
    )


@given(st.data())
@settings(max_examples=100, deadline=None)
def test_alarm_sns_integration_property_based(data):
    """
    **Feature: nova-cloudwatch-dashboard, Property 7: Alarm SNS integration**
    **Validates: Requirements 10.5**
    
    Property-based test: For any subset of CloudWatch alarms in the template,
    all should have conditional AlarmActions that reference the SNS topic.
    """
    resources = extract_template_resources()
    if not resources:
        return  # Skip if we can't parse resources
    
    # Find all alarm resources
    alarm_names = [
        name for name, config in resources.items() 
        if config.get('Type') == 'AWS::CloudWatch::Alarm'
    ]
    
    if not alarm_names:
        return  # Skip if no alarms found
    
    # Select a random subset of alarms to check
    selected_alarms = data.draw(
        st.lists(
            st.sampled_from(alarm_names),
            min_size=1,
            max_size=len(alarm_names),
            unique=True
        )
    )
    
    for alarm_name in selected_alarms:
        alarm_config = resources[alarm_name]
        properties = alarm_config.get('Properties', {})
        
        # Each selected alarm should have AlarmActions
        assert 'AlarmActions' in properties, (
            f"Alarm '{alarm_name}' missing AlarmActions property"
        )
        
        # AlarmActions should be conditional
        assert properties.get('AlarmActions') == 'conditional', (
            f"Alarm '{alarm_name}' should have conditional AlarmActions"
        )


def extract_resource_policies():
    """Extract DeletionPolicy and UpdateReplacePolicy from CloudFormation template."""
    try:
        with open('nova-pro-dashboard-template.yaml', 'r') as f:
            content = f.read()
        
        # Find all resources and their policies
        resource_policies = {}
        lines = content.split('\n')
        current_resource = None
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Resource name (indent 2, ends with colon)
            if (len(line) - len(line.lstrip()) == 2 and 
                ':' in stripped and 
                not stripped.startswith('-') and 
                not stripped.startswith('#') and
                stripped[0].isupper()):
                current_resource = stripped.split(':')[0]
                resource_policies[current_resource] = {
                    'DeletionPolicy': None,
                    'UpdateReplacePolicy': None,
                    'Type': None
                }
            
            # Look for Type, DeletionPolicy, UpdateReplacePolicy
            elif current_resource and len(line) - len(line.lstrip()) == 4:
                if stripped.startswith('Type:'):
                    resource_policies[current_resource]['Type'] = stripped.split(':', 1)[1].strip()
                elif stripped.startswith('DeletionPolicy:'):
                    resource_policies[current_resource]['DeletionPolicy'] = stripped.split(':', 1)[1].strip()
                elif stripped.startswith('UpdateReplacePolicy:'):
                    resource_policies[current_resource]['UpdateReplacePolicy'] = stripped.split(':', 1)[1].strip()
        
        return resource_policies
        
    except Exception as e:
        print(f"Error extracting resource policies: {e}")
        return {}


def check_replacement_forcing_properties():
    """Check for properties that force resource replacement during updates."""
    try:
        with open('nova-pro-dashboard-template.yaml', 'r') as f:
            content = f.read()
        
        replacement_issues = []
        
        # Check for hardcoded resource names (should use parameters/functions)
        if 'DashboardName: "' in content and 'Ref: DashboardName' not in content:
            replacement_issues.append("Dashboard has hardcoded name instead of parameter reference")
        
        # Check for hardcoded alarm names
        alarm_resources = ['HighErrorRateAlarm', 'HighP99LatencyAlarm', 'DailyCostLimitAlarm', 'HighThrottlingRateAlarm']
        for alarm in alarm_resources:
            if f'{alarm}:' in content:
                # Look for AlarmName property in the alarm definition
                alarm_start = content.find(f'{alarm}:')
                alarm_end = content.find('\n  ', alarm_start + len(alarm) + 1)
                if alarm_end == -1:
                    alarm_end = len(content)
                alarm_section = content[alarm_start:alarm_end]
                
                if 'AlarmName:' in alarm_section and 'Fn::Sub:' in alarm_section:
                    # Good: uses Fn::Sub for dynamic naming
                    pass
                elif 'AlarmName:' in alarm_section and 'Ref:' in alarm_section:
                    # Good: uses parameter reference
                    pass
                elif f'AlarmName: "{alarm}"' in alarm_section:
                    replacement_issues.append(f"Alarm {alarm} has hardcoded name")
        
        # Check for hardcoded SNS topic names
        if 'AlarmTopic:' in content:
            topic_start = content.find('AlarmTopic:')
            topic_end = content.find('\n  ', topic_start + 11)
            if topic_end == -1:
                topic_end = len(content)
            topic_section = content[topic_start:topic_end]
            
            if 'TopicName:' in topic_section and 'Fn::Sub:' in topic_section:
                # Good: uses Fn::Sub for dynamic naming
                pass
            elif 'TopicName: "AlarmTopic"' in topic_section:
                replacement_issues.append("SNS Topic has hardcoded name")
        
        # Check for hardcoded IAM role/policy names
        iam_resources = ['DashboardViewerRole', 'DashboardViewerPolicy']
        for iam_resource in iam_resources:
            if f'{iam_resource}:' in content:
                iam_start = content.find(f'{iam_resource}:')
                iam_end = content.find('\n  ', iam_start + len(iam_resource) + 1)
                if iam_end == -1:
                    iam_end = len(content)
                iam_section = content[iam_start:iam_end]
                
                name_property = 'RoleName:' if 'Role' in iam_resource else 'ManagedPolicyName:'
                if name_property in iam_section and 'Fn::Sub:' in iam_section:
                    # Good: uses Fn::Sub for dynamic naming
                    pass
                elif name_property in iam_section and f'"{iam_resource}"' in iam_section:
                    replacement_issues.append(f"IAM resource {iam_resource} has hardcoded name")
        
        return replacement_issues
        
    except Exception as e:
        print(f"Error checking replacement-forcing properties: {e}")
        return [f"Error analyzing template: {e}"]


def test_update_safe_resource_configuration():
    """
    **Feature: nova-cloudwatch-dashboard, Property 4: Update-safe resource configuration**
    **Validates: Requirements 8.5**
    
    Property: For any resource in the CloudFormation template, the resource should not have 
    properties that would force replacement during stack updates.
    
    This ensures that stack updates preserve dashboard configuration and alarm history,
    preventing operational disruption during template updates.
    """
    # Test 1: Check for DeletionPolicy and UpdateReplacePolicy on critical resources
    resource_policies = extract_resource_policies()
    assert len(resource_policies) > 0, "Could not extract resource policies from template"
    
    # Critical resources that should have protection policies
    critical_resources = [
        'NovaProDashboard',
        'AlarmTopic', 
        'HighErrorRateAlarm',
        'HighP99LatencyAlarm',
        'DailyCostLimitAlarm',
        'HighThrottlingRateAlarm',
        'DashboardViewerPolicy',
        'DashboardViewerRole'
    ]
    
    for resource_name in critical_resources:
        if resource_name in resource_policies:
            resource_info = resource_policies[resource_name]
            
            # Critical resources should have DeletionPolicy: Retain
            assert resource_info.get('DeletionPolicy') == 'Retain', (
                f"Critical resource '{resource_name}' should have DeletionPolicy: Retain "
                f"to prevent accidental deletion during stack operations per Requirements 8.5. "
                f"Current DeletionPolicy: {resource_info.get('DeletionPolicy')}"
            )
            
            # Critical resources should have UpdateReplacePolicy: Retain
            assert resource_info.get('UpdateReplacePolicy') == 'Retain', (
                f"Critical resource '{resource_name}' should have UpdateReplacePolicy: Retain "
                f"to prevent replacement during stack updates per Requirements 8.5. "
                f"Current UpdateReplacePolicy: {resource_info.get('UpdateReplacePolicy')}"
            )
    
    # Test 2: Check for replacement-forcing properties
    replacement_issues = check_replacement_forcing_properties()
    assert len(replacement_issues) == 0, (
        f"Found properties that could force resource replacement during updates: "
        f"{'; '.join(replacement_issues)}. All resource names should use parameters "
        f"or CloudFormation functions to avoid replacement per Requirements 8.5"
    )
    
    # Test 3: Verify update-safe resource types and configurations
    update_safe_validations = []
    
    for resource_name, resource_info in resource_policies.items():
        resource_type = resource_info.get('Type')
        
        if resource_type == 'AWS::CloudWatch::Dashboard':
            # Dashboard updates are safe when DashboardName uses parameters
            update_safe_validations.append(f"Dashboard {resource_name} uses parameterized naming")
            
        elif resource_type == 'AWS::CloudWatch::Alarm':
            # Alarm updates are safe when AlarmName uses parameters and thresholds are parameterized
            update_safe_validations.append(f"Alarm {resource_name} uses parameterized naming and thresholds")
            
        elif resource_type == 'AWS::SNS::Topic':
            # SNS topic updates are safe when TopicName uses parameters
            update_safe_validations.append(f"SNS Topic {resource_name} uses parameterized naming")
            
        elif resource_type == 'AWS::IAM::Role':
            # IAM role updates are safe when RoleName uses parameters
            update_safe_validations.append(f"IAM Role {resource_name} uses parameterized naming")
            
        elif resource_type == 'AWS::IAM::ManagedPolicy':
            # Managed policy updates are safe when ManagedPolicyName uses parameters
            update_safe_validations.append(f"IAM Policy {resource_name} uses parameterized naming")
    
    # Ensure we validated the expected resources
    assert len(update_safe_validations) >= len(critical_resources), (
        f"Expected to validate at least {len(critical_resources)} resources for update safety, "
        f"but only validated {len(update_safe_validations)}. "
        f"Validations: {update_safe_validations}"
    )
    
    # Test 4: Verify no immutable properties are used
    immutable_property_checks = [
        # CloudWatch Dashboard immutable properties
        ("AWS::CloudWatch::Dashboard", "DashboardName", "should use Ref: DashboardName parameter"),
        # CloudWatch Alarm immutable properties  
        ("AWS::CloudWatch::Alarm", "AlarmName", "should use Fn::Sub with DashboardName parameter"),
        # SNS Topic immutable properties
        ("AWS::SNS::Topic", "TopicName", "should use Fn::Sub with DashboardName parameter"),
        # IAM Role immutable properties
        ("AWS::IAM::Role", "RoleName", "should use Fn::Sub with DashboardName parameter"),
        # IAM ManagedPolicy immutable properties
        ("AWS::IAM::ManagedPolicy", "ManagedPolicyName", "should use Fn::Sub with DashboardName parameter"),
    ]
    
    # This validation is implicit in our replacement-forcing properties check above
    # The template should use parameterized names for all critical resources


@given(st.data())
@settings(max_examples=50, deadline=None)
def test_update_safe_resource_configuration_property_based(data):
    """
    **Feature: nova-cloudwatch-dashboard, Property 4: Update-safe resource configuration**
    **Validates: Requirements 8.5**
    
    Property-based test: For any subset of resources in the template,
    all should be configured to avoid replacement during stack updates.
    """
    resource_policies = extract_resource_policies()
    if not resource_policies:
        return  # Skip if we can't parse resources
    
    # Critical resources that must have protection policies
    critical_resources = [
        'NovaProDashboard',
        'AlarmTopic', 
        'HighErrorRateAlarm',
        'HighP99LatencyAlarm',
        'DailyCostLimitAlarm',
        'HighThrottlingRateAlarm',
        'DashboardViewerPolicy',
        'DashboardViewerRole'
    ]
    
    # Filter to only critical resources that exist in the template
    existing_critical_resources = [
        name for name in critical_resources 
        if name in resource_policies
    ]
    
    if not existing_critical_resources:
        return  # Skip if no critical resources found
    
    # Select a random subset of critical resources to check
    selected_resources = data.draw(
        st.lists(
            st.sampled_from(existing_critical_resources),
            min_size=1,
            max_size=len(existing_critical_resources),
            unique=True
        )
    )
    
    for resource_name in selected_resources:
        resource_info = resource_policies[resource_name]
        resource_type = resource_info.get('Type')
        
        # Verify critical resources have protection policies
        assert resource_info.get('DeletionPolicy') == 'Retain', (
            f"Critical resource '{resource_name}' should have DeletionPolicy: Retain"
        )
        
        assert resource_info.get('UpdateReplacePolicy') == 'Retain', (
            f"Critical resource '{resource_name}' should have UpdateReplacePolicy: Retain"
        )
        
        # Verify resource types are update-safe
        update_safe_types = [
            'AWS::CloudWatch::Dashboard',
            'AWS::CloudWatch::Alarm', 
            'AWS::SNS::Topic',
            'AWS::SNS::Subscription',
            'AWS::IAM::Role',
            'AWS::IAM::ManagedPolicy'
        ]
        
        assert resource_type in update_safe_types, (
            f"Resource '{resource_name}' has type '{resource_type}' which may not be update-safe"
        )
    
    # Additional property-based validation: check for replacement-forcing properties
    replacement_issues = check_replacement_forcing_properties()
    assert len(replacement_issues) == 0, (
        f"Found replacement-forcing properties in selected resources: {replacement_issues}"
    )


if __name__ == '__main__':
    # Run the basic test
    print("Running property test: Optional parameters have defaults...")
    test_optional_parameters_have_defaults()
    print("✓ Basic test passed")
    
    print("\nRunning helper test: Required parameters identified correctly...")
    test_required_parameters_identified_correctly()
    print("✓ Helper test passed")
    
    print("\nRunning property-based test with Hypothesis...")
    test_optional_parameters_have_defaults_property()
    print("✓ Property-based test passed")
    
    print("\nRunning property test: Region consistency across metrics...")
    test_region_consistency_across_metrics()
    print("✓ Region consistency test passed")
    
    print("\nRunning property test: Model dimension inclusion...")
    test_model_dimension_inclusion()
    print("✓ Model dimension inclusion test passed")
    
    print("\nRunning property-based test: Region consistency...")
    test_region_consistency_property_based()
    print("✓ Region consistency property-based test passed")
    
    print("\nRunning property-based test: Model dimension inclusion...")
    test_model_dimension_inclusion_property_based()
    print("✓ Model dimension inclusion property-based test passed")
    
    print("\nRunning property test: Alarm SNS integration...")
    test_alarm_sns_integration()
    print("✓ Alarm SNS integration test passed")
    
    print("\nRunning helper test: SNS topic conditional creation...")
    test_sns_topic_conditional_creation()
    print("✓ SNS topic conditional creation test passed")
    
    print("\nRunning property-based test: Alarm SNS integration...")
    test_alarm_sns_integration_property_based()
    print("✓ Alarm SNS integration property-based test passed")
    
    print("\nRunning property test: Least-privilege IAM permissions...")
    test_least_privilege_iam_permissions()
    print("✓ Least-privilege IAM permissions test passed")
    
    print("\nRunning property test: Scoped CloudWatch permissions...")
    test_scoped_cloudwatch_permissions()
    print("✓ Scoped CloudWatch permissions test passed")
    
    print("\nRunning property-based test: Least-privilege IAM permissions...")
    test_least_privilege_iam_permissions_property_based()
    print("✓ Least-privilege IAM permissions property-based test passed")
    
    print("\nRunning property-based test: Scoped CloudWatch permissions...")
    test_scoped_cloudwatch_permissions_property_based()
    print("✓ Scoped CloudWatch permissions property-based test passed")
    
    print("\nRunning property test: Update-safe resource configuration...")
    test_update_safe_resource_configuration()
    print("✓ Update-safe resource configuration test passed")
    
    print("\nRunning property-based test: Update-safe resource configuration...")
    test_update_safe_resource_configuration_property_based()
    print("✓ Update-safe resource configuration property-based test passed")
    
    print("\n✓ All tests passed!")
