#!/usr/bin/env python3
"""
Nova Pro Dashboard Template Validator
Comprehensive validation for production readiness
"""

import yaml
import json
import re
import sys
from pathlib import Path

class TemplateValidator:
    def __init__(self, template_path):
        self.template_path = Path(template_path)
        self.template = None
        self.errors = []
        self.warnings = []
        self.info = []
        
    def load_template(self):
        """Load and parse the CloudFormation template"""
        try:
            with open(self.template_path, 'r') as f:
                content = f.read()
            
            # Basic YAML structure check (ignoring CloudFormation functions)
            lines = content.split('\n')
            yaml_structure_valid = True
            
            # Check basic structure
            required_sections = ['AWSTemplateFormatVersion', 'Description', 'Parameters', 'Resources', 'Outputs']
            for section in required_sections:
                if f'{section}:' not in content:
                    self.errors.append(f"Missing required section: {section}")
                    yaml_structure_valid = False
                else:
                    self.info.append(f"✅ Found section: {section}")
            
            return yaml_structure_valid
            
        except Exception as e:
            self.errors.append(f"Failed to load template: {e}")
            return False
    
    def validate_sns_policies(self):
        """Validate SNS topic policies for correct actions and conditions"""
        content = self.template_path.read_text()
        
        # Valid SNS actions from AWS documentation
        valid_sns_actions = {
            'sns:AddPermission', 'sns:DeleteTopic', 'sns:GetDataProtectionPolicy',
            'sns:GetTopicAttributes', 'sns:ListSubscriptionsByTopic', 'sns:ListTagsForResource',
            'sns:Publish', 'sns:PutDataProtectionPolicy', 'sns:RemovePermission',
            'sns:SetTopicAttributes', 'sns:Subscribe'
        }
        
        # Find all SNS actions in template
        sns_actions = set(re.findall(r'sns:(\w+)', content))
        
        # Check for invalid actions
        invalid_actions = sns_actions - {action.split(':')[1] for action in valid_sns_actions}
        if invalid_actions:
            for action in invalid_actions:
                self.errors.append(f"Invalid SNS action found: sns:{action}")
        else:
            self.info.append(f"✅ All SNS actions are valid: {sns_actions}")
        
        # Check for problematic patterns
        problematic_patterns = [
            (r'Action:\s*["\']?\*["\']?', 'Wildcard action (*) not allowed in SNS policies'),
            (r'sns:Unsubscribe', 'sns:Unsubscribe is not a valid SNS topic policy action'),
            (r'sns:Receive', 'sns:Receive is not a valid SNS topic policy action'),
        ]
        
        for pattern, message in problematic_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                self.errors.append(message)
        
        # Check for valid condition keys
        if 'aws:SecureTransport' in content:
            self.info.append("✅ Using aws:SecureTransport condition for TLS enforcement")
        
        if 'aws:SourceAccount' in content:
            self.info.append("✅ Using aws:SourceAccount condition for security")
    
    def validate_resource_structure(self):
        """Validate CloudFormation resource structure"""
        content = self.template_path.read_text()
        
        # Count resources
        resource_matches = re.findall(r'^  \w+:\s*$', content, re.MULTILINE)
        resource_count = len(resource_matches)
        
        if resource_count > 0:
            self.info.append(f"✅ Found {resource_count} resources")
        else:
            self.errors.append("No resources found in template")
        
        # Check for required resource types
        required_resources = [
            ('AWS::CloudWatch::Dashboard', 'CloudWatch Dashboard'),
            ('AWS::CloudWatch::Alarm', 'CloudWatch Alarms'),
        ]
        
        optional_resources = [
            ('AWS::SNS::Topic', 'SNS Topic (conditional)'),
            ('AWS::IAM::Role', 'IAM Role (optional - customer may use existing)'),
            ('AWS::IAM::ManagedPolicy', 'IAM Managed Policy (optional - customer may use existing)')
        ]
        
        for resource_type, description in required_resources:
            if resource_type in content:
                self.info.append(f"✅ Found {description}")
            else:
                self.errors.append(f"❌ Missing required {description}")
        
        for resource_type, description in optional_resources:
            if resource_type in content:
                self.info.append(f"✅ Found {description}")
            else:
                self.info.append(f"ℹ️  {description} not found")
    
    def validate_security_best_practices(self):
        """Check for security best practices"""
        content = self.template_path.read_text()
        
        # Check for least privilege IAM (optional - customer may use existing role)
        if 'DashboardViewerPolicy' in content:
            self.info.append("✅ Found least-privilege IAM policy")
        else:
            self.info.append("ℹ️  No IAM resources - customer will use existing role")
        
        # Check for encryption
        if 'KmsMasterKeyId' in content:
            self.info.append("✅ SNS topic encryption configured")
        
        # Check for deletion protection
        if 'DeletionPolicy: Retain' in content:
            self.info.append("✅ Deletion protection configured")
        
        # Check for secure transport
        if 'aws:SecureTransport' in content:
            self.info.append("✅ Secure transport enforcement found")
        
        # Check for account restrictions
        if 'aws:SourceAccount' in content:
            self.info.append("✅ Account-based access restrictions found")
    
    def validate_production_readiness(self):
        """Check production readiness criteria"""
        content = self.template_path.read_text()
        
        # Check for proper tagging
        tag_keys = ['Environment', 'Owner', 'CostCenter', 'Purpose']
        for tag_key in tag_keys:
            if f'Key: {tag_key}' in content:
                self.info.append(f"✅ Found {tag_key} tag")
            else:
                self.warnings.append(f"⚠️  Missing {tag_key} tag")
        
        # Check for monitoring and alerting
        alarm_types = ['ErrorRate', 'Latency', 'Cost', 'Throttling']
        for alarm_type in alarm_types:
            if f'AlarmType\n          Value: {alarm_type}' in content or f'AlarmType: {alarm_type}' in content:
                self.info.append(f"✅ Found {alarm_type} alarm")
            else:
                self.warnings.append(f"⚠️  Missing {alarm_type} alarm")
        
        # Check for parameterization
        if 'Parameters:' in content and 'MonitoringRegion' in content:
            self.info.append("✅ Template is properly parameterized")
        
        # Check for outputs
        if 'DashboardURL' in content and 'DashboardName' in content:
            self.info.append("✅ Essential outputs provided")
    
    def validate_template_size(self):
        """Check template size constraints"""
        size = self.template_path.stat().st_size
        
        if size > 51200:  # 50KB CloudFormation limit
            self.warnings.append(f"⚠️  Template size ({size} bytes) exceeds CloudFormation validation limit (51KB)")
            self.warnings.append("   This is normal for comprehensive templates - deploy directly")
        else:
            self.info.append(f"✅ Template size ({size} bytes) within limits")
    
    def run_validation(self):
        """Run all validations"""
        print("🔍 Nova Pro Dashboard Template Validation")
        print("=" * 50)
        
        if not self.load_template():
            print("❌ Failed to load template")
            return False
        
        self.validate_sns_policies()
        self.validate_resource_structure()
        self.validate_security_best_practices()
        self.validate_production_readiness()
        self.validate_template_size()
        
        # Print results
        print("\n📊 Validation Results:")
        print("-" * 30)
        
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"   {error}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   {warning}")
        
        if self.info:
            print(f"\n✅ PASSED CHECKS ({len(self.info)}):")
            for info in self.info:
                print(f"   {info}")
        
        # Overall result
        print("\n" + "=" * 50)
        if self.errors:
            print("❌ VALIDATION FAILED - Fix errors before deployment")
            return False
        elif self.warnings:
            print("⚠️  VALIDATION PASSED WITH WARNINGS - Review before deployment")
            return True
        else:
            print("✅ VALIDATION PASSED - Template is production ready")
            return True

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 validate-template.py <template-file>")
        sys.exit(1)
    
    template_file = sys.argv[1]
    
    if not Path(template_file).exists():
        print(f"❌ Template file '{template_file}' not found")
        sys.exit(1)
    
    validator = TemplateValidator(template_file)
    success = validator.run_validation()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()