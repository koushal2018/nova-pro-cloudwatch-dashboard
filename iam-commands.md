# Bedrock IAM Configuration Commands

## Prerequisites Check
```bash
# Verify you have the necessary permissions
aws sts get-caller-identity

# Check if the role exists
aws iam get-role --role-name Bedrockcloudwatchlogs
```

## Step 5: Review Existing Policies
```bash
# List attached managed policies
aws iam list-attached-role-policies --role-name Bedrockcloudwatchlogs

# List inline policies
aws iam list-role-policies --role-name Bedrockcloudwatchlogs
```

## Steps 6-9: Create Inline Policy
```bash
# Create the inline policy
aws iam put-role-policy \
    --role-name Bedrockcloudwatchlogs \
    --policy-name BedrockCloudWatchLogsAccess \
    --policy-document '{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:us-west-2:401552979575:log-group:/aws/bedrock/modelinvocations:*"
    }
  ]
}'
```

## Step 11: Check Current Trust Relationship
```bash
# View current trust policy
aws iam get-role --role-name Bedrockcloudwatchlogs --query 'Role.AssumeRolePolicyDocument'
```

## Step 12: Update Trust Relationship
```bash
# Update the trust relationship
aws iam update-assume-role-policy \
    --role-name Bedrockcloudwatchlogs \
    --policy-document '{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "bedrock.amazonaws.com"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "aws:SourceAccount": "401552979575"
        },
        "ArnLike": {
          "aws:SourceArn": "arn:aws:bedrock:us-west-2:401552979575:*"
        }
      }
    }
  ]
}'
```

## Verification Commands
```bash
# Verify the inline policy was created
aws iam get-role-policy --role-name Bedrockcloudwatchlogs --policy-name BedrockCloudWatchLogsAccess

# Verify the trust relationship
aws iam get-role --role-name Bedrockcloudwatchlogs --query 'Role.AssumeRolePolicyDocument'

# List all policies (final check)
aws iam list-role-policies --role-name Bedrockcloudwatchlogs
aws iam list-attached-role-policies --role-name Bedrockcloudwatchlogs
```

## Test Bedrock Operation
After completing the IAM configuration, test your Bedrock operation:

```bash
# Example: Test model invocation (replace with your specific operation)
aws bedrock-runtime invoke-model \
    --model-id amazon.nova-pro-v1:0 \
    --body '{"inputText":"Hello, world!","textGenerationConfig":{"maxTokenCount":100}}' \
    --content-type application/json \
    --accept application/json \
    output.json
```