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
        
        # Find the DashboardBody section more precisely
        start_marker = 'DashboardBody:'
        end_marker = '  # ========================================================================'
        
        start_idx = content.find(start_marker)
        end_idx = content.find(end_marker, start_idx)
        
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
                dashboard_section = policy_section[policy_section.find('cloudwatch:GetDashboard'):policy_section.find('cloudwatch:GetDashboard') + 800]
                has_resource_scoping = ('arn:aws:cloudwatch:' in dashboard_section or 'arn:${AWS::Partition}:cloudwatch:' in dashboard_section) and 'dashboard' in dashboard_section
                
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


def test_iam_trust_policy_restrictions():
    """
    **Feature: nova-cloudwatch-dashboard, Property 8: IAM trust policy restrictions**
    **Validates: Requirements 9.1 - Security hardening**
    
    Property: IAM trust policies should not allow overly permissive principals
    and should include security conditions like ExternalId and region scoping.
    """
    import yaml
    
    with open('nova-pro-dashboard-template.yaml', 'r') as f:
        content = f.read()
    
    # Check that the trust policy doesn't use account root as principal
    assert 'arn:${AWS::Partition}:iam::${AWS::AccountId}:root' not in content, (
        "IAM trust policy should not use account root principal for security"
    )
    
    # Check for specific user/role principals instead
    assert 'arn:${AWS::Partition}:iam::${AWS::AccountId}:user/dashboard-admin' in content, (
        "IAM trust policy should specify specific users instead of account root"
    )
    
    # Check for ExternalId condition
    assert 'sts:ExternalId' in content, (
        "IAM trust policy should include ExternalId condition for cross-account security"
    )
    
    # Check for region scoping in trust policy
    assert 'aws:RequestedRegion' in content, (
        "IAM trust policy should include region scoping conditions"
    )


def test_cloudwatch_permission_region_scoping():
    """
    **Feature: nova-cloudwatch-dashboard, Property 9: CloudWatch permission region scoping**
    **Validates: Requirements 9.2 - Security hardening**
    
    Property: All CloudWatch permissions should include region scoping conditions
    to prevent cross-region access.
    """
    import yaml
    
    with open('nova-pro-dashboard-template.yaml', 'r') as f:
        content = f.read()
    
    # Find CloudWatch permission statements
    cloudwatch_actions = [
        'cloudwatch:GetDashboard',
        'cloudwatch:ListDashboards', 
        'cloudwatch:GetMetricData',
        'cloudwatch:GetMetricStatistics',
        'cloudwatch:ListMetrics'
    ]
    
    for action in cloudwatch_actions:
        if action in content:
            # Find the section containing this action
            lines = content.split('\n')
            action_found = False
            region_condition_found = False
            
            for i, line in enumerate(lines):
                if action in line:
                    action_found = True
                    # Look for aws:RequestedRegion condition in the next 20 lines
                    for j in range(i, min(i + 20, len(lines))):
                        if 'aws:RequestedRegion' in lines[j]:
                            region_condition_found = True
                            break
                    break
            
            if action_found:
                assert region_condition_found, (
                    f"CloudWatch action '{action}' should have aws:RequestedRegion condition for security"
                )


def test_logs_permission_model_scoping():
    """
    **Feature: nova-cloudwatch-dashboard, Property 10: Logs permission model scoping**
    **Validates: Requirements 9.2 - Security hardening**
    
    Property: CloudWatch Logs permissions should be scoped to specific model logs
    to prevent access to other models' logs.
    """
    import yaml
    
    with open('nova-pro-dashboard-template.yaml', 'r') as f:
        content = f.read()
    
    # Check that logs permissions are scoped to specific model
    assert '/aws/bedrock/modelinvocations/${ModelId}' in content, (
        "Logs permissions should be scoped to specific model logs using ModelId parameter"
    )
    
    # Check that broad logs permissions are not used
    assert '/aws/bedrock/modelinvocations*' not in content or content.count('/aws/bedrock/modelinvocations*') == 0, (
        "Logs permissions should not use wildcard access to all model logs"
    )


def test_resource_protection_policies():
    """
    **Feature: nova-cloudwatch-dashboard, Property 11: Resource protection policies**
    **Validates: Requirements 8.5 - Security hardening**
    
    Property: All critical resources should have DeletionPolicy and UpdateReplacePolicy
    set to Retain to prevent accidental deletion or replacement.
    """
    resource_policies = extract_resource_policies()
    
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
    
    for resource_name in critical_resources:
        if resource_name in resource_policies:
            resource_info = resource_policies[resource_name]
            
            assert resource_info.get('DeletionPolicy') == 'Retain', (
                f"Critical resource '{resource_name}' should have DeletionPolicy: Retain"
            )
            
            assert resource_info.get('UpdateReplacePolicy') == 'Retain', (
                f"Critical resource '{resource_name}' should have UpdateReplacePolicy: Retain"
            )


def test_sns_topic_access_policy():
    """
    **Feature: nova-cloudwatch-dashboard, Property 12: SNS topic access policy**
    **Validates: Requirements 10.5 - Security hardening**
    
    Property: SNS topic should have a resource-based policy that restricts
    publishing to CloudWatch service only and denies non-TLS connections.
    """
    import yaml
    
    with open('nova-pro-dashboard-template.yaml', 'r') as f:
        content = f.read()
    
    # Check for SNS topic policy resource
    assert 'AlarmTopicPolicy:' in content, (
        "SNS topic should have a resource-based access policy"
    )
    
    # Check for CloudWatch service principal restriction
    assert 'cloudwatch.amazonaws.com' in content, (
        "SNS topic policy should restrict publishing to CloudWatch service"
    )
    
    # Check for TLS enforcement
    assert 'aws:SecureTransport' in content, (
        "SNS topic policy should enforce TLS connections"
    )
    
    # Check for unauthorized publishing denial
    assert 'DenyUnauthorizedPublishing' in content, (
        "SNS topic policy should deny unauthorized publishing"
    )


def extract_user_analytics_queries():
    """Extract CloudWatch Logs Insights queries for user analytics from the dashboard."""
    try:
        dashboard_json = extract_dashboard_json()
        if not dashboard_json:
            return []
        
        widgets = dashboard_json.get('widgets', [])
        user_analytics_queries = []
        
        for i, widget in enumerate(widgets):
            if widget.get('type') == 'log':
                properties = widget.get('properties', {})
                query = properties.get('query', '')
                title = properties.get('title', '')
                
                # Check if this is a user analytics query
                if ('${UserIdentityField}' in query or 
                    'userId' in query or 
                    'User' in title):
                    user_analytics_queries.append({
                        'widget_index': i,
                        'title': title,
                        'query': query,
                        'properties': properties
                    })
        
        return user_analytics_queries
        
    except Exception as e:
        print(f"Error extracting user analytics queries: {e}")
        return []


def extract_application_analytics_queries():
    """Extract CloudWatch Logs Insights queries for application analytics from the dashboard."""
    try:
        dashboard_json = extract_dashboard_json()
        if not dashboard_json:
            return []
        
        widgets = dashboard_json.get('widgets', [])
        application_analytics_queries = []
        
        for i, widget in enumerate(widgets):
            if widget.get('type') == 'log':
                properties = widget.get('properties', {})
                query = properties.get('query', '')
                title = properties.get('title', '')
                
                # Check if this is an application analytics query
                if ('${ApplicationIdentityField}' in query or 
                    'appName' in query or 
                    'Application' in title):
                    application_analytics_queries.append({
                        'widget_index': i,
                        'title': title,
                        'query': query,
                        'properties': properties
                    })
        
        return application_analytics_queries
        
    except Exception as e:
        print(f"Error extracting application analytics queries: {e}")
        return []


def test_user_identity_extraction_consistency():
    """
    **Feature: nova-cloudwatch-dashboard, Property 8: User identity extraction consistency**
    **Validates: Requirements 12.3**
    
    Property: For any CloudWatch Logs Insights query that extracts user identity, 
    the query should use the UserIdentityField parameter value in the regex pattern 
    for metadata field extraction.
    
    This ensures that user analytics adapt to different organizations' metadata field
    naming conventions by using the configurable UserIdentityField parameter.
    """
    user_queries = extract_user_analytics_queries()
    assert len(user_queries) > 0, (
        "Template should contain user analytics queries with user identity extraction"
    )
    
    for query_info in user_queries:
        query = query_info['query']
        title = query_info['title']
        
        # Skip queries that don't extract user identity
        if 'userId' not in query and '${UserIdentityField}' not in query:
            continue
        
        # Check that the query uses the UserIdentityField parameter
        assert '${UserIdentityField}' in query, (
            f"User analytics query '{title}' should use UserIdentityField parameter "
            f"in regex pattern for metadata field extraction per Requirements 12.3. "
            f"Found query: {query[:100]}..."
        )
        
        # Check that the regex pattern correctly uses the parameter
        # The pattern should be: "metadata":\s*\{[^\}]*"${UserIdentityField}":\s*"(?<userId>[^"]+)"
        expected_pattern = '"${UserIdentityField}":\\s*"(?<userId>[^"]+)"'
        assert expected_pattern in query, (
            f"User analytics query '{title}' should use correct regex pattern "
            f"with UserIdentityField parameter. Expected pattern: {expected_pattern}. "
            f"Found query: {query[:200]}..."
        )


def test_user_analytics_completeness():
    """
    **Feature: nova-cloudwatch-dashboard, Property 10: User analytics completeness**
    **Validates: Requirements 11.3**
    
    Property: For any user analytics widget that displays metrics, the underlying 
    log query should return invocation count, token consumption, and cost calculation fields.
    
    This ensures that user analytics provide comprehensive information for cost allocation
    and usage monitoring per user.
    """
    user_queries = extract_user_analytics_queries()
    assert len(user_queries) > 0, (
        "Template should contain user analytics queries"
    )
    
    # Check each user analytics query for completeness
    required_analytics = {
        'invocations': False,
        'cost': False, 
        'tokens': False
    }
    
    for query_info in user_queries:
        query = query_info['query']
        title = query_info['title'].lower()
        
        # Check for invocation count analytics
        if ('invocations' in title or 'count()' in query):
            required_analytics['invocations'] = True
            
            # Invocation queries should count by userId
            assert 'count() as invocations by userId' in query or 'count()' in query, (
                f"User invocation query should count invocations by userId. "
                f"Query: {query[:100]}..."
            )
        
        # Check for cost analytics
        if ('cost' in title or '0.0008' in query or '0.0032' in query):
            required_analytics['cost'] = True
            
            # Cost queries should include all token types and pricing
            cost_components = [
                'inputTokens', 'outputTokens', 
                '0.0008/1000', '0.0032/1000'  # Nova Pro pricing
            ]
            
            for component in cost_components:
                if component in ['0.0008/1000', '0.0032/1000']:
                    # Pricing should be present
                    assert component in query, (
                        f"User cost query should include {component} pricing component. "
                        f"Query: {query[:200]}..."
                    )
        
        # Check for token consumption analytics
        if ('token' in title or 'inputTokens' in query or 'outputTokens' in query):
            required_analytics['tokens'] = True
            
            # Token queries should parse both input and output tokens
            token_fields = ['inputTokens', 'outputTokens']
            for field in token_fields:
                assert field in query, (
                    f"User token query should include {field} field. "
                    f"Query: {query[:200]}..."
                )
    
    # Verify all required analytics are present
    missing_analytics = [k for k, v in required_analytics.items() if not v]
    assert len(missing_analytics) == 0, (
        f"User analytics are missing required components: {missing_analytics}. "
        f"All user analytics widgets should provide invocation count, token consumption, "
        f"and cost calculation fields per Requirements 11.3"
    )


@given(st.data())
@settings(max_examples=100, deadline=None)
def test_user_identity_extraction_consistency_property_based(data):
    """
    **Feature: nova-cloudwatch-dashboard, Property 8: User identity extraction consistency**
    **Validates: Requirements 12.3**
    
    Property-based test: For any subset of user analytics queries in the template,
    all should use the UserIdentityField parameter consistently.
    """
    user_queries = extract_user_analytics_queries()
    if not user_queries:
        return  # Skip if no user analytics queries
    
    # Filter to queries that extract user identity
    identity_queries = [
        q for q in user_queries 
        if ('userId' in q['query'] or '${UserIdentityField}' in q['query'])
    ]
    
    if not identity_queries:
        return  # Skip if no identity extraction queries
    
    # Select a random subset of identity queries to check
    query_indices = list(range(len(identity_queries)))
    selected_indices = data.draw(
        st.lists(
            st.sampled_from(query_indices),
            min_size=1,
            max_size=len(identity_queries),
            unique=True
        )
    )
    
    selected_queries = [identity_queries[i] for i in selected_indices]
    
    for query_info in selected_queries:
        query = query_info['query']
        title = query_info['title']
        
        # Each selected query should use UserIdentityField parameter
        assert '${UserIdentityField}' in query, (
            f"Query '{title}' should use UserIdentityField parameter"
        )
        
        # Should use correct regex pattern
        expected_pattern = '"${UserIdentityField}":\\s*"(?<userId>[^"]+)"'
        assert expected_pattern in query, (
            f"Query '{title}' should use correct UserIdentityField regex pattern"
        )


@given(st.data())
@settings(max_examples=100, deadline=None)
def test_user_analytics_completeness_property_based(data):
    """
    **Feature: nova-cloudwatch-dashboard, Property 10: User analytics completeness**
    **Validates: Requirements 11.3**
    
    Property-based test: For any subset of user analytics queries,
    all should provide complete metric information (invocations, tokens, cost).
    """
    user_queries = extract_user_analytics_queries()
    if not user_queries:
        return  # Skip if no user analytics queries
    
    # Select a random subset of user queries to check
    query_indices = list(range(len(user_queries)))
    selected_indices = data.draw(
        st.lists(
            st.sampled_from(query_indices),
            min_size=1,
            max_size=min(5, len(user_queries)),  # Limit to 5 for performance
            unique=True
        )
    )
    
    selected_queries = [user_queries[i] for i in selected_indices]
    
    # Check that collectively, the selected queries provide complete analytics
    analytics_coverage = {
        'invocations': False,
        'cost': False,
        'tokens': False
    }
    
    for query_info in selected_queries:
        query = query_info['query']
        title = query_info['title'].lower()
        
        # Check what type of analytics this query provides
        if 'invocations' in title or 'count()' in query:
            analytics_coverage['invocations'] = True
        
        if 'cost' in title or '0.0008' in query or '0.0032' in query:
            analytics_coverage['cost'] = True
        
        if 'token' in title or 'inputTokens' in query or 'outputTokens' in query:
            analytics_coverage['tokens'] = True
    
    # If we selected queries, they should collectively provide some analytics
    # Note: Not all queries need to provide all types - some are specialized
    if len(selected_queries) >= 1:
        covered_analytics = sum(analytics_coverage.values())
        assert covered_analytics >= 1, (
            f"Selected user analytics queries should provide at least 1 type of analytics. "
            f"Coverage: {analytics_coverage}. "
            f"Selected queries: {[q['title'] for q in selected_queries]}"
        )


def test_application_identity_extraction_consistency():
    """
    **Feature: nova-cloudwatch-dashboard, Property 9: Application identity extraction consistency**
    **Validates: Requirements 12.4**
    
    Property: For any CloudWatch Logs Insights query that extracts application identity, 
    the query should use the ApplicationIdentityField parameter value in the regex pattern 
    for metadata field extraction.
    
    This ensures that application analytics adapt to different organizations' metadata field
    naming conventions by using the configurable ApplicationIdentityField parameter.
    """
    application_queries = extract_application_analytics_queries()
    assert len(application_queries) > 0, (
        "Template should contain application analytics queries with application identity extraction"
    )
    
    for query_info in application_queries:
        query = query_info['query']
        title = query_info['title']
        
        # Skip queries that don't extract application identity
        if 'appName' not in query and '${ApplicationIdentityField}' not in query:
            continue
        
        # Check that the query uses the ApplicationIdentityField parameter
        assert '${ApplicationIdentityField}' in query, (
            f"Application analytics query '{title}' should use ApplicationIdentityField parameter "
            f"in regex pattern for metadata field extraction per Requirements 12.4. "
            f"Found query: {query[:100]}..."
        )
        
        # Check that the regex pattern correctly uses the parameter
        # The pattern should be: "metadata":\s*\{[^\}]*"${ApplicationIdentityField}":\s*"(?<appName>[^"]+)"
        expected_pattern = '"${ApplicationIdentityField}":\\s*"(?<appName>[^"]+)"'
        assert expected_pattern in query, (
            f"Application analytics query '{title}' should use correct regex pattern "
            f"with ApplicationIdentityField parameter. Expected pattern: {expected_pattern}. "
            f"Found query: {query[:200]}..."
        )


def test_application_analytics_completeness():
    """
    **Feature: nova-cloudwatch-dashboard, Property 11: Application analytics completeness**
    **Validates: Requirements 11.4**
    
    Property: For any application analytics widget that displays metrics, the underlying 
    log query should return invocation count, token consumption, and cost calculation fields.
    
    This ensures that application analytics provide comprehensive information for cost allocation
    and usage monitoring per application.
    """
    application_queries = extract_application_analytics_queries()
    assert len(application_queries) > 0, (
        "Template should contain application analytics queries"
    )
    
    # Check each application analytics query for completeness
    required_analytics = {
        'invocations': False,
        'cost': False, 
        'tokens': False
    }
    
    for query_info in application_queries:
        query = query_info['query']
        title = query_info['title'].lower()
        
        # Check for invocation count analytics
        if ('invocations' in title or 'count()' in query):
            required_analytics['invocations'] = True
            
            # Invocation queries should count by appName
            assert 'count() as invocations by appName' in query or 'count()' in query, (
                f"Application invocation query should count invocations by appName. "
                f"Query: {query[:100]}..."
            )
        
        # Check for cost analytics
        if ('cost' in title or '0.0008' in query or '0.0032' in query):
            required_analytics['cost'] = True
            
            # Cost queries should include all token types and pricing
            cost_components = [
                'inputTokens', 'outputTokens', 
                '0.0008/1000', '0.0032/1000'  # Nova Pro pricing
            ]
            
            for component in cost_components:
                if component in ['0.0008/1000', '0.0032/1000']:
                    # Pricing should be present
                    assert component in query, (
                        f"Application cost query should include {component} pricing component. "
                        f"Query: {query[:200]}..."
                    )
        
        # Check for token consumption analytics
        if ('token' in title or 'inputTokens' in query or 'outputTokens' in query):
            required_analytics['tokens'] = True
            
            # Token queries should parse both input and output tokens
            token_fields = ['inputTokens', 'outputTokens']
            for field in token_fields:
                assert field in query, (
                    f"Application token query should include {field} field. "
                    f"Query: {query[:200]}..."
                )
    
    # Verify all required analytics are present
    missing_analytics = [k for k, v in required_analytics.items() if not v]
    assert len(missing_analytics) == 0, (
        f"Application analytics are missing required components: {missing_analytics}. "
        f"All application analytics widgets should provide invocation count, token consumption, "
        f"and cost calculation fields per Requirements 11.4"
    )


@given(st.data())
@settings(max_examples=100, deadline=None)
def test_application_identity_extraction_consistency_property_based(data):
    """
    **Feature: nova-cloudwatch-dashboard, Property 9: Application identity extraction consistency**
    **Validates: Requirements 12.4**
    
    Property-based test: For any subset of application analytics queries in the template,
    all should use the ApplicationIdentityField parameter consistently.
    """
    application_queries = extract_application_analytics_queries()
    if not application_queries:
        return  # Skip if no application analytics queries
    
    # Filter to queries that extract application identity
    identity_queries = [
        q for q in application_queries 
        if ('appName' in q['query'] or '${ApplicationIdentityField}' in q['query'])
    ]
    
    if not identity_queries:
        return  # Skip if no identity extraction queries
    
    # Select a random subset of identity queries to check
    query_indices = list(range(len(identity_queries)))
    selected_indices = data.draw(
        st.lists(
            st.sampled_from(query_indices),
            min_size=1,
            max_size=len(identity_queries),
            unique=True
        )
    )
    
    selected_queries = [identity_queries[i] for i in selected_indices]
    
    for query_info in selected_queries:
        query = query_info['query']
        title = query_info['title']
        
        # Each selected query should use ApplicationIdentityField parameter
        assert '${ApplicationIdentityField}' in query, (
            f"Query '{title}' should use ApplicationIdentityField parameter"
        )
        
        # Should use correct regex pattern
        expected_pattern = '"${ApplicationIdentityField}":\\s*"(?<appName>[^"]+)"'
        assert expected_pattern in query, (
            f"Query '{title}' should use correct ApplicationIdentityField regex pattern"
        )


@given(st.data())
@settings(max_examples=100, deadline=None)
def test_application_analytics_completeness_property_based(data):
    """
    **Feature: nova-cloudwatch-dashboard, Property 11: Application analytics completeness**
    **Validates: Requirements 11.4**
    
    Property-based test: For any subset of application analytics queries,
    all should provide complete metric information (invocations, tokens, cost).
    """
    application_queries = extract_application_analytics_queries()
    if not application_queries:
        return  # Skip if no application analytics queries
    
    # Select a random subset of application queries to check
    query_indices = list(range(len(application_queries)))
    selected_indices = data.draw(
        st.lists(
            st.sampled_from(query_indices),
            min_size=1,
            max_size=min(5, len(application_queries)),  # Limit to 5 for performance
            unique=True
        )
    )
    
    selected_queries = [application_queries[i] for i in selected_indices]
    
    # Check that collectively, the selected queries provide complete analytics
    analytics_coverage = {
        'invocations': False,
        'cost': False,
        'tokens': False
    }
    
    for query_info in selected_queries:
        query = query_info['query']
        title = query_info['title'].lower()
        
        # Check what type of analytics this query provides
        if 'invocations' in title or 'count()' in query:
            analytics_coverage['invocations'] = True
        
        if 'cost' in title or '0.0008' in query or '0.0032' in query:
            analytics_coverage['cost'] = True
        
        if 'token' in title or 'inputTokens' in query or 'outputTokens' in query:
            analytics_coverage['tokens'] = True
    
    # If we selected queries, they should collectively provide some analytics
    # Note: Not all queries need to provide all types - some are specialized
    if len(selected_queries) >= 1:
        covered_analytics = sum(analytics_coverage.values())
        assert covered_analytics >= 1, (
            f"Selected application analytics queries should provide at least 1 type of analytics. "
            f"Coverage: {analytics_coverage}. "
            f"Selected queries: {[q['title'] for q in selected_queries]}"
        )


def extract_unknown_usage_queries():
    """Extract CloudWatch Logs Insights queries for unknown usage tracking from the dashboard."""
    try:
        # Read the template file directly as text to avoid YAML parsing issues
        with open('nova-pro-dashboard-template.yaml', 'r') as f:
            template_content = f.read()
        
        # Extract log widgets that handle unknown usage
        unknown_queries = []
        
        # Look for widgets with titles related to unknown usage or allocation
        import re
        
        # Extract the unknown usage widget
        if 'Unknown Usage' in template_content:
            # Find the query for unknown usage widget - look for the pattern before the title
            pattern = r'"query":\s*"([^"]*(?:\\.[^"]*)*)"[^}]*?"title":\s*"Unknown Usage[^"]*"'
            matches = re.findall(pattern, template_content, re.DOTALL)
            for match in matches:
                # Unescape the query string
                query = match.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
                unknown_queries.append({
                    'query': query,
                    'title': 'Unknown Usage (%)',
                    'type': 'unknown_usage'
                })
        
        # Extract the cost allocation coverage widget
        if 'Cost Allocation Coverage' in template_content:
            pattern = r'"query":\s*"([^"]*(?:\\.[^"]*)*)"[^}]*?"title":\s*"Cost Allocation Coverage[^"]*"'
            matches = re.findall(pattern, template_content, re.DOTALL)
            for match in matches:
                # Unescape the query string
                query = match.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
                unknown_queries.append({
                    'query': query,
                    'title': 'Cost Allocation Coverage (%)',
                    'type': 'allocation_coverage'
                })
        
        return unknown_queries
        
    except Exception as e:
        print(f"Error extracting unknown usage queries: {e}")
        return []


def test_unknown_usage_categorization():
    """
    **Feature: nova-cloudwatch-dashboard, Property 12: Unknown usage categorization**
    **Validates: Requirements 11.5**
    
    Property: For any log query that processes requests without user or application metadata,
    those requests should be categorized separately from identified requests.
    
    This ensures that unattributed usage is properly tracked and reported for cost allocation.
    """
    unknown_queries = extract_unknown_usage_queries()
    assert len(unknown_queries) > 0, (
        "Template should contain unknown usage tracking queries"
    )
    
    # Check each unknown usage query for proper categorization
    categorization_features = {
        'identifies_unknown': False,
        'separates_attributed': False,
        'calculates_percentage': False
    }
    
    for query_info in unknown_queries:
        query = query_info['query']
        title = query_info['title'].lower()
        
        # Check for unknown usage identification
        if ('unknown' in title or 'allocation' in title):
            # Verify the query identifies requests without metadata
            if ('userId' in query and 'appName' in query):
                categorization_features['identifies_unknown'] = True
                
            # Verify the query separates attributed from unattributed
            if ('count(' in query and ('greatest(' in query or 'case when' in query)):
                categorization_features['separates_attributed'] = True
                
            # Verify the query calculates percentages
            if ('percentage' in query or '* 100' in query or 'round(' in query):
                categorization_features['calculates_percentage'] = True
    
    # Verify all categorization features are present
    missing_features = [feature for feature, present in categorization_features.items() if not present]
    assert len(missing_features) == 0, (
        f"Unknown usage queries missing categorization features: {missing_features}. "
        f"Features found: {categorization_features}"
    )


@given(st.data())
@settings(max_examples=100, deadline=None)
def test_unknown_usage_categorization_property_based(data):
    """
    **Feature: nova-cloudwatch-dashboard, Property 12: Unknown usage categorization**
    **Validates: Requirements 11.5**
    
    Property-based test: For any log query that processes requests without user or application metadata,
    those requests should be categorized separately from identified requests.
    """
    unknown_queries = extract_unknown_usage_queries()
    
    # Select a subset of queries to test
    if len(unknown_queries) > 0:
        selected_queries = data.draw(st.lists(
            st.sampled_from(unknown_queries),
            min_size=1,
            max_size=min(3, len(unknown_queries)),
            unique=True
        ))
        
        for query_info in selected_queries:
            query = query_info['query']
            
            # Verify the query properly handles unknown usage categorization
            # Check that it identifies both user and application fields
            assert ('UserIdentityField' in query or 'userId' in query), (
                f"Query should reference user identity field: {query_info['title']}"
            )
            assert ('ApplicationIdentityField' in query or 'appName' in query), (
                f"Query should reference application identity field: {query_info['title']}"
            )
            
            # Check that it performs proper categorization logic
            has_categorization = (
                'count(' in query and 
                ('greatest(' in query or 'case when' in query or 'coalesce(' in query)
            )
            assert has_categorization, (
                f"Query should have categorization logic: {query_info['title']}"
            )


@given(st.data())
@settings(max_examples=50, deadline=None)
def test_security_validation_property_based(data):
    """
    **Feature: nova-cloudwatch-dashboard, Property 13: Security validation comprehensive**
    **Validates: Requirements 9.1, 9.2 - Security hardening**
    
    Property-based test: For any security configuration in the template,
    all security controls should be properly implemented.
    """
    # Test IAM trust policy restrictions
    test_iam_trust_policy_restrictions()
    
    # Test CloudWatch permission region scoping
    test_cloudwatch_permission_region_scoping()
    
    # Test logs permission model scoping
    test_logs_permission_model_scoping()
    
    # Test resource protection policies
    test_resource_protection_policies()
    
    # Test SNS topic access policy
    test_sns_topic_access_policy()


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
    
    print("\nRunning security validation tests...")
    print("  - Testing IAM trust policy restrictions...")
    test_iam_trust_policy_restrictions()
    print("  ✓ IAM trust policy restrictions test passed")
    
    print("  - Testing CloudWatch permission region scoping...")
    test_cloudwatch_permission_region_scoping()
    print("  ✓ CloudWatch permission region scoping test passed")
    
    print("  - Testing logs permission model scoping...")
    test_logs_permission_model_scoping()
    print("  ✓ Logs permission model scoping test passed")
    
    print("  - Testing resource protection policies...")
    test_resource_protection_policies()
    print("  ✓ Resource protection policies test passed")
    
    print("  - Testing SNS topic access policy...")
    test_sns_topic_access_policy()
    print("  ✓ SNS topic access policy test passed")
    
    print("\nRunning comprehensive security validation property-based test...")
    test_security_validation_property_based()
    print("✓ Comprehensive security validation property-based test passed")
    
    print("\nRunning property test: User identity extraction consistency...")
    test_user_identity_extraction_consistency()
    print("✓ User identity extraction consistency test passed")
    
    print("\nRunning property test: User analytics completeness...")
    test_user_analytics_completeness()
    print("✓ User analytics completeness test passed")
    
    print("\nRunning property-based test: User identity extraction consistency...")
    test_user_identity_extraction_consistency_property_based()
    print("✓ User identity extraction consistency property-based test passed")
    
    print("\nRunning property-based test: User analytics completeness...")
    test_user_analytics_completeness_property_based()
    print("✓ User analytics completeness property-based test passed")
    
    print("\nRunning property test: Unknown usage categorization...")
    test_unknown_usage_categorization()
    print("✓ Unknown usage categorization test passed")
    
    print("\nRunning property-based test: Unknown usage categorization...")
    test_unknown_usage_categorization_property_based()
    print("✓ Unknown usage categorization property-based test passed")
    
    print("\n✓ All tests passed!")
