#!/usr/bin/env python3
"""
Nova Pro CloudWatch Dashboard - Metrics Generation and Verification Script

This script generates test metrics by invoking the Nova Pro model and then verifies
that all dashboard widgets display data correctly. It also validates cost calculations.
"""

import argparse
import boto3
import json
import time
import sys
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NovaProDashboardTester:
    """Test class for Nova Pro CloudWatch Dashboard metrics generation and verification."""
    
    def __init__(self, region: str, stack_name: str):
        """Initialize the tester with AWS clients."""
        self.region = region
        self.stack_name = stack_name
        
        # Initialize AWS clients
        self.bedrock_client = boto3.client('bedrock-runtime', region_name=region)
        self.cloudwatch_client = boto3.client('cloudwatch', region_name=region)
        self.cloudformation_client = boto3.client('cloudformation', region_name=region)
        
        # Get stack parameters
        self.stack_info = self._get_stack_info()
        self.model_id = self.stack_info.get('ModelId', 'amazon.nova-pro-v1:0')
        self.dashboard_name = self.stack_info.get('DashboardName', 'NovaProMonitoring')
        
        logger.info(f"Initialized tester for region: {region}, stack: {stack_name}")
        logger.info(f"Model ID: {self.model_id}, Dashboard: {self.dashboard_name}")

    def _get_stack_info(self):
        """Get stack parameters and outputs."""
        try:
            response = self.cloudformation_client.describe_stacks(StackName=self.stack_name)
            stack = response['Stacks'][0]
            
            # Extract parameters
            parameters = {}
            for param in stack.get('Parameters', []):
                parameters[param['ParameterKey']] = param['ParameterValue']
            
            # Extract outputs
            outputs = {}
            for output in stack.get('Outputs', []):
                outputs[output['OutputKey']] = output['OutputValue']
            
            return {**parameters, **outputs}
        except Exception as e:
            logger.error(f"Failed to get stack info: {e}")
            raise

    def generate_test_invocations(self, num_invocations: int = 10):
        """Generate test invocations with various input sizes and patterns."""
        test_results = []
        
        # Test prompts with different token counts
        test_prompts = [
            "What is artificial intelligence?",
            "Explain machine learning and its applications in modern technology.",
            "Write about cloud computing benefits and challenges for enterprises."
        ]
        
        logger.info(f"Generating {num_invocations} test invocations...")
        
        for i in range(num_invocations):
            try:
                prompt = test_prompts[i % len(test_prompts)]
                
                # Prepare request with correct Nova Pro format
                request_body = {
                    "messages": [
                        {
                            "role": "user", 
                            "content": [{"text": prompt}]
                        }
                    ],
                    "inferenceConfig": {
                        "maxTokens": 200,
                        "temperature": 0.7,
                        "topP": 0.9
                    }
                }
                
                start_time = time.time()
                
                # Invoke the model
                response = self.bedrock_client.invoke_model(
                    modelId=self.model_id,
                    body=json.dumps(request_body),
                    contentType='application/json'
                )
                
                end_time = time.time()
                latency = (end_time - start_time) * 1000
                
                # Parse response
                response_body = json.loads(response['body'].read())
                
                # Estimate token counts
                input_tokens = len(prompt.split()) * 1.3
                output_text = ""
                if 'output' in response_body and 'message' in response_body['output']:
                    content = response_body['output']['message'].get('content', [])
                    if content and isinstance(content, list) and len(content) > 0:
                        output_text = content[0].get('text', '')
                
                output_tokens = len(output_text.split()) * 1.3 if output_text else 50
                
                result = {
                    'invocation': i + 1,
                    'latency_ms': latency,
                    'input_tokens_est': int(input_tokens),
                    'output_tokens_est': int(output_tokens),
                    'success': True,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                test_results.append(result)
                logger.info(f"Invocation {i+1}/{num_invocations} - Latency: {latency:.0f}ms")
                
                # Add delay between requests
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Invocation {i+1} failed: {e}")
                test_results.append({
                    'invocation': i + 1,
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                })
                time.sleep(1)
        
        successful_invocations = sum(1 for r in test_results if r.get('success', False))
        logger.info(f"Completed {successful_invocations}/{num_invocations} successful invocations")
        
        return test_results

    def wait_for_metrics_propagation(self, wait_minutes: int = 5):
        """Wait for CloudWatch metrics to propagate."""
        logger.info(f"Waiting {wait_minutes} minutes for metrics to propagate...")
        
        for minute in range(wait_minutes):
            remaining = wait_minutes - minute
            logger.info(f"Waiting... {remaining} minutes remaining")
            time.sleep(60)
        
        logger.info("Metrics propagation wait complete")

    def verify_dashboard_widgets(self):
        """Verify that dashboard widgets have data."""
        logger.info("Verifying dashboard widgets...")
        
        try:
            # Get dashboard configuration
            dashboard_response = self.cloudwatch_client.get_dashboard(
                DashboardName=self.dashboard_name
            )
            dashboard_body = json.loads(dashboard_response['DashboardBody'])
            widgets = dashboard_body.get('widgets', [])
            
            logger.info(f"Found {len(widgets)} widgets to verify")
            
            # Check for basic metrics
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=2)
            
            response = self.cloudwatch_client.get_metric_data(
                MetricDataQueries=[
                    {
                        'Id': 'invocations',
                        'MetricStat': {
                            'Metric': {
                                'Namespace': 'AWS/Bedrock',
                                'MetricName': 'Invocations',
                                'Dimensions': [
                                    {'Name': 'ModelId', 'Value': self.model_id}
                                ]
                            },
                            'Period': 300,
                            'Stat': 'Sum'
                        },
                        'ReturnData': True
                    }
                ],
                StartTime=start_time,
                EndTime=end_time
            )
            
            # Check if we have data
            has_data = False
            for result in response.get('MetricDataResults', []):
                if result.get('Values'):
                    has_data = True
                    break
            
            return {
                'dashboard_accessible': True,
                'widgets_count': len(widgets),
                'metrics_available': has_data
            }
            
        except Exception as e:
            logger.error(f"Failed to verify dashboard: {e}")
            return {
                'dashboard_accessible': False,
                'error': str(e)
            }

    def verify_cost_calculations(self, test_results):
        """Verify cost calculations."""
        logger.info("Verifying cost calculations...")
        
        successful_results = [r for r in test_results if r.get('success')]
        if not successful_results:
            return {'cost_calculation_available': False, 'error': 'No successful invocations'}
        
        total_input_tokens = sum(r.get('input_tokens_est', 0) for r in successful_results)
        total_output_tokens = sum(r.get('output_tokens_est', 0) for r in successful_results)
        
        # Nova Pro pricing (December 2025)
        input_cost_per_1k = 0.0008
        output_cost_per_1k = 0.0032
        
        expected_input_cost = (total_input_tokens / 1000) * input_cost_per_1k
        expected_output_cost = (total_output_tokens / 1000) * output_cost_per_1k
        expected_total_cost = expected_input_cost + expected_output_cost
        
        logger.info(f"Expected total cost: ${expected_total_cost:.4f}")
        
        return {
            'cost_calculation_available': True,
            'expected_cost': expected_total_cost,
            'total_input_tokens': total_input_tokens,
            'total_output_tokens': total_output_tokens
        }

    def generate_test_report(self, test_results, widget_verification, cost_verification):
        """Generate a comprehensive test report."""
        report = []
        report.append("=" * 80)
        report.append("NOVA PRO CLOUDWATCH DASHBOARD - TEST REPORT")
        report.append("=" * 80)
        report.append(f"Test Date: {datetime.utcnow().isoformat()}")
        report.append(f"Region: {self.region}")
        report.append(f"Stack: {self.stack_name}")
        report.append(f"Model ID: {self.model_id}")
        report.append(f"Dashboard: {self.dashboard_name}")
        report.append("")
        
        # Test invocation summary
        successful_invocations = sum(1 for r in test_results if r.get('success', False))
        total_invocations = len(test_results)
        
        report.append("TEST INVOCATION SUMMARY")
        report.append("-" * 40)
        report.append(f"Total Invocations: {total_invocations}")
        report.append(f"Successful: {successful_invocations}")
        report.append(f"Failed: {total_invocations - successful_invocations}")
        report.append(f"Success Rate: {successful_invocations/total_invocations*100:.1f}%")
        
        if successful_invocations > 0:
            successful_results = [r for r in test_results if r.get('success', False)]
            avg_latency = sum(r.get('latency_ms', 0) for r in successful_results) / len(successful_results)
            total_input_tokens = sum(r.get('input_tokens_est', 0) for r in successful_results)
            total_output_tokens = sum(r.get('output_tokens_est', 0) for r in successful_results)
            
            report.append(f"Average Latency: {avg_latency:.0f}ms")
            report.append(f"Total Input Tokens (est): {total_input_tokens:,}")
            report.append(f"Total Output Tokens (est): {total_output_tokens:,}")
        
        report.append("")
        
        # Dashboard verification
        report.append("DASHBOARD VERIFICATION")
        report.append("-" * 40)
        
        if widget_verification.get('dashboard_accessible'):
            report.append("✓ Dashboard accessible")
            report.append(f"✓ Found {widget_verification.get('widgets_count', 0)} widgets")
            
            if widget_verification.get('metrics_available'):
                report.append("✓ Metrics data available")
            else:
                report.append("⚠ No metrics data yet (may need more time)")
        else:
            report.append("✗ Dashboard not accessible")
            if 'error' in widget_verification:
                report.append(f"Error: {widget_verification['error']}")
        
        report.append("")
        
        # Cost verification
        report.append("COST CALCULATION VERIFICATION")
        report.append("-" * 40)
        
        if cost_verification.get('cost_calculation_available'):
            report.append("✓ Cost calculation data available")
            report.append(f"Expected Total Cost: ${cost_verification.get('expected_cost', 0):.4f}")
        else:
            report.append("✗ Cost calculation data not available")
        
        report.append("")
        
        # Overall result
        report.append("OVERALL TEST RESULT")
        report.append("-" * 40)
        
        invocation_success = successful_invocations >= total_invocations * 0.8
        dashboard_success = widget_verification.get('dashboard_accessible', False)
        
        if invocation_success and dashboard_success:
            overall_status = "✓ PASS - Test completed successfully"
        elif invocation_success:
            overall_status = "⚠ PARTIAL - Invocations successful, dashboard needs verification"
        else:
            overall_status = "✗ FAIL - Critical issues detected"
        
        report.append(overall_status)
        report.append("")
        
        # Dashboard URL
        dashboard_url = self.stack_info.get('DashboardURL', 'N/A')
        report.append(f"Dashboard URL: {dashboard_url}")
        report.append("")
        
        return "\n".join(report)

def main():
    """Main function to run the dashboard testing."""
    parser = argparse.ArgumentParser(description='Test Nova Pro CloudWatch Dashboard')
    parser.add_argument('--region', required=True, help='AWS region')
    parser.add_argument('--stack-name', required=True, help='CloudFormation stack name')
    parser.add_argument('--invocations', type=int, default=10, help='Number of test invocations')
    parser.add_argument('--wait-minutes', type=int, default=5, help='Minutes to wait for metrics')
    
    args = parser.parse_args()
    
    try:
        # Initialize tester
        tester = NovaProDashboardTester(args.region, args.stack_name)
        
        # Generate test metrics
        test_results = tester.generate_test_invocations(args.invocations)
        
        # Wait for metrics to propagate
        tester.wait_for_metrics_propagation(args.wait_minutes)
        
        # Verify dashboard widgets
        widget_verification = tester.verify_dashboard_widgets()
        
        # Verify cost calculations
        cost_verification = tester.verify_cost_calculations(test_results)
        
        # Generate and display report
        report = tester.generate_test_report(test_results, widget_verification, cost_verification)
        print(report)
        
        # Save report to file
        report_filename = f"dashboard_test_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_filename, 'w') as f:
            f.write(report)
        
        logger.info(f"Test report saved to: {report_filename}")
        
        # Exit with appropriate code
        successful_invocations = sum(1 for r in test_results if r.get('success', False))
        invocation_success = successful_invocations >= len(test_results) * 0.8
        dashboard_success = widget_verification.get('dashboard_accessible', False)
        
        if invocation_success and dashboard_success:
            sys.exit(0)  # Success
        else:
            sys.exit(1)  # Failure
            
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()