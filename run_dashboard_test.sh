#!/bin/bash

# Nova Pro CloudWatch Dashboard Test Runner
# This script runs the dashboard metrics generation and verification test

set -e

# Default values
REGION=""
STACK_NAME=""
INVOCATIONS=20
WAIT_MINUTES=10

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
usage() {
    echo "Usage: $0 --region REGION --stack-name STACK_NAME [OPTIONS]"
    echo ""
    echo "Required arguments:"
    echo "  --region REGION          AWS region where the stack is deployed"
    echo "  --stack-name STACK_NAME  CloudFormation stack name"
    echo ""
    echo "Optional arguments:"
    echo "  --invocations NUM        Number of test invocations (default: 20)"
    echo "  --wait-minutes NUM       Minutes to wait for metrics (default: 10)"
    echo "  --help                   Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --region us-east-1 --stack-name nova-pro-dashboard"
    echo "  $0 --region us-west-2 --stack-name my-dashboard --invocations 30 --wait-minutes 15"
    exit 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --region)
            REGION="$2"
            shift 2
            ;;
        --stack-name)
            STACK_NAME="$2"
            shift 2
            ;;
        --invocations)
            INVOCATIONS="$2"
            shift 2
            ;;
        --wait-minutes)
            WAIT_MINUTES="$2"
            shift 2
            ;;
        --help)
            usage
            ;;
        *)
            print_error "Unknown option: $1"
            usage
            ;;
    esac
done

# Validate required arguments
if [[ -z "$REGION" ]]; then
    print_error "Region is required"
    usage
fi

if [[ -z "$STACK_NAME" ]]; then
    print_error "Stack name is required"
    usage
fi

# Check if required tools are installed
print_status "Checking prerequisites..."

if ! command -v aws &> /dev/null; then
    print_error "AWS CLI is not installed or not in PATH"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if boto3 is available
if ! python3 -c "import boto3" &> /dev/null; then
    print_error "boto3 library is not installed. Install with: pip install boto3"
    exit 1
fi

print_success "Prerequisites check passed"

# Verify AWS credentials
print_status "Verifying AWS credentials..."
if ! aws sts get-caller-identity --region "$REGION" &> /dev/null; then
    print_error "AWS credentials not configured or invalid"
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text --region "$REGION")
print_success "AWS credentials verified (Account: $ACCOUNT_ID)"

# Verify stack exists
print_status "Verifying CloudFormation stack exists..."
if ! aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" &> /dev/null; then
    print_error "CloudFormation stack '$STACK_NAME' not found in region '$REGION'"
    exit 1
fi

STACK_STATUS=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" --query 'Stacks[0].StackStatus' --output text)
if [[ "$STACK_STATUS" != "CREATE_COMPLETE" && "$STACK_STATUS" != "UPDATE_COMPLETE" ]]; then
    print_error "Stack is in status '$STACK_STATUS'. Expected CREATE_COMPLETE or UPDATE_COMPLETE"
    exit 1
fi

print_success "Stack '$STACK_NAME' found and ready"

# Check Bedrock access
print_status "Verifying Bedrock access..."
if ! aws bedrock list-foundation-models --region "$REGION" &> /dev/null; then
    print_error "Cannot access Bedrock in region '$REGION'. Check permissions and region availability"
    exit 1
fi

# Check if Nova Pro model is available
if ! aws bedrock list-foundation-models --region "$REGION" --query 'modelSummaries[?contains(modelId, `nova-pro`)]' --output text | grep -q nova-pro; then
    print_warning "Nova Pro model may not be available in region '$REGION'"
    print_warning "Continuing anyway - the test will show if the model is accessible"
fi

print_success "Bedrock access verified"

# Display test configuration
echo ""
print_status "Test Configuration:"
echo "  Region: $REGION"
echo "  Stack Name: $STACK_NAME"
echo "  Test Invocations: $INVOCATIONS"
echo "  Wait Time: $WAIT_MINUTES minutes"
echo ""

# Get dashboard URL for reference
DASHBOARD_URL=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" --query 'Stacks[0].Outputs[?OutputKey==`DashboardURL`].OutputValue' --output text 2>/dev/null || echo "N/A")
if [[ "$DASHBOARD_URL" != "N/A" ]]; then
    print_status "Dashboard URL: $DASHBOARD_URL"
    echo ""
fi

# Confirm before proceeding
read -p "Proceed with the test? This will invoke the Nova Pro model $INVOCATIONS times. (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_status "Test cancelled by user"
    exit 0
fi

# Run the test
print_status "Starting dashboard metrics test..."
echo ""

# Make sure the test script is executable
chmod +x test_dashboard_metrics.py

# Run the Python test script
if python3 test_dashboard_metrics.py \
    --region "$REGION" \
    --stack-name "$STACK_NAME" \
    --invocations "$INVOCATIONS" \
    --wait-minutes "$WAIT_MINUTES"; then
    
    echo ""
    print_success "Dashboard test completed successfully!"
    
    # Show the latest report file
    LATEST_REPORT=$(ls -t dashboard_test_report_*.txt 2>/dev/null | head -n1)
    if [[ -n "$LATEST_REPORT" ]]; then
        print_status "Test report saved to: $LATEST_REPORT"
        echo ""
        print_status "You can view the full report with: cat $LATEST_REPORT"
    fi
    
    if [[ "$DASHBOARD_URL" != "N/A" ]]; then
        echo ""
        print_status "View your dashboard at: $DASHBOARD_URL"
    fi
    
else
    echo ""
    print_error "Dashboard test failed!"
    
    # Show the latest report file even on failure
    LATEST_REPORT=$(ls -t dashboard_test_report_*.txt 2>/dev/null | head -n1)
    if [[ -n "$LATEST_REPORT" ]]; then
        print_status "Test report saved to: $LATEST_REPORT"
        echo ""
        print_status "Check the report for details: cat $LATEST_REPORT"
    fi
    
    exit 1
fi