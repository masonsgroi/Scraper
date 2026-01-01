# Operations Guide

Operational procedures for managing the deployed scraper on AWS Lambda.

---

## Prerequisites

### Required Tools

**Terraform:**
```bash
# Install Terraform (one time)
brew install terraform  # macOS
# or: choco install terraform  # Windows
# or: download from terraform.io

# Verify installation
terraform --version
```

**AWS CLI:**
```bash
# Configure AWS credentials
aws configure
# Enter your AWS credentials when prompted (Access Key ID, Secret Access Key, region)
```

**Docker:**
- Docker Desktop installed and running
- Verify: `docker --version`

### Project Setup

- Working directory: `/Users/msgroi/Documents/d/github/Scraper` (project root)
- Terraform initialized: `cd terraform/ && terraform init` (run once after cloning)

---

## Deployment

### Initial Deployment

See [infra_devplan.md](infra_devplan.md) for the complete initial setup process (Phases 1-4).

### Code Deployment (Python Changes)

When you modify the scraper code:

```bash
# 1. Build Docker image
docker build -t scraper .

# 2. Tag for ECR
ECR_URL=$(cd terraform && terraform output -raw ecr_repository_url)
docker tag scraper:latest $ECR_URL:latest

# 3. Push to ECR
docker push $ECR_URL:latest

# 4. Update Lambda function
LAMBDA_NAME=$(cd terraform && terraform output -raw lambda_function_name)
aws lambda update-function-code \
  --function-name $LAMBDA_NAME \
  --image-uri $ECR_URL:latest
```

Wait 30-60 seconds for Lambda to update, then test.

### Infrastructure Changes (Terraform)

When you modify infrastructure (schedule, memory, permissions, etc.):

```bash
cd terraform/

# Review what will change
terraform plan

# Apply changes
terraform apply
```

---

## Monitoring

### View Lambda Logs

```bash
# Real-time logs (follow mode)
aws logs tail /aws/lambda/$(cd terraform && terraform output -raw lambda_function_name) --follow

# Recent logs (last hour)
aws logs tail /aws/lambda/$(cd terraform && terraform output -raw lambda_function_name) --since 1h

# Recent logs (last 30 minutes)
aws logs tail /aws/lambda/$(cd terraform && terraform output -raw lambda_function_name) --since 30m

# Filter for errors
aws logs tail /aws/lambda/$(cd terraform && terraform output -raw lambda_function_name) --filter-pattern "ERROR"

# Filter for specific text
aws logs tail /aws/lambda/$(cd terraform && terraform output -raw lambda_function_name) --filter-pattern "Scraper completed"
```

### Check S3 Output

```bash
# List all files in S3 bucket
aws s3 ls s3://$(cd terraform && terraform output -raw s3_bucket_name)/ --recursive

# List only data files
aws s3 ls s3://$(cd terraform && terraform output -raw s3_bucket_name)/data/

# Download a specific file
aws s3 cp s3://$(cd terraform && terraform output -raw s3_bucket_name)/data/status_20250101_120000.csv .

# View file contents without downloading
aws s3 cp s3://$(cd terraform && terraform output -raw s3_bucket_name)/data/status_*.csv - | head -20
```

### Check Lambda Status

```bash
# Get Lambda configuration
aws lambda get-function --function-name $(cd terraform && terraform output -raw lambda_function_name)

# Get last execution time
aws lambda get-function --function-name $(cd terraform && terraform output -raw lambda_function_name) | jq '.Configuration.LastModified'
```

### Check Schedule Status

```bash
# List EventBridge rules
aws events list-rules --name-prefix scraper

# Get rule details
aws events describe-rule --name scraper-hourly
```

---

## Testing

### Manual Lambda Invocation

Trigger Lambda manually (useful for testing changes):

```bash
# Invoke Lambda
aws lambda invoke \
  --function-name $(cd terraform && terraform output -raw lambda_function_name) \
  --payload '{}' \
  response.json

# Check response
cat response.json

# Should see: {"statusCode": 200, "body": "..."}
```

### Verify End-to-End

Complete test from invocation to S3 output:

```bash
# 1. Note current time
date

# 2. Invoke Lambda
aws lambda invoke \
  --function-name $(cd terraform && terraform output -raw lambda_function_name) \
  --payload '{}' \
  response.json

# 3. Check response
cat response.json

# 4. View logs
aws logs tail /aws/lambda/$(cd terraform && terraform output -raw lambda_function_name) --since 5m

# 5. Check S3 for new files
aws s3 ls s3://$(cd terraform && terraform output -raw s3_bucket_name)/data/ --human-readable

# 6. Verify CSV contents
aws s3 cp s3://$(cd terraform && terraform output -raw s3_bucket_name)/data/status_*.csv - | head
```

---

## Common Operations

### Change Schedule

Edit `terraform/main.tf`:

```hcl
resource "aws_cloudwatch_event_rule" "scraper_schedule" {
  name                = "scraper-schedule"
  description         = "Trigger scraper"
  schedule_expression = "rate(30 minutes)"  # Change this
}
```

Common schedule expressions:
- `rate(30 minutes)` - Every 30 minutes
- `rate(1 hour)` - Every hour
- `rate(1 day)` - Every day
- `cron(0 9 * * ? *)` - Every day at 9:00 AM UTC
- `cron(0 */2 * * ? *)` - Every 2 hours
- `cron(0 9-17 * * ? *)` - Every hour from 9 AM to 5 PM UTC

Apply changes:

```bash
cd terraform/
terraform apply
```

### Disable Scheduled Execution

Temporarily disable the schedule without destroying infrastructure:

```bash
# Disable rule
aws events disable-rule --name scraper-hourly

# Re-enable later
aws events enable-rule --name scraper-hourly
```

### View Terraform State

```bash
cd terraform/

# List all resources
terraform state list

# Show specific resource details
terraform state show aws_lambda_function.scraper

# Get outputs
terraform output

# Get specific output
terraform output ecr_repository_url
```

---

## Troubleshooting

### Lambda Fails to Pull Image

**Symptoms**: Lambda execution fails immediately, logs show image pull error

**Diagnosis**:
```bash
# Check ECR repository exists
aws ecr describe-repositories --repository-names scraper

# Verify image was pushed
aws ecr list-images --repository-name scraper

# Check Lambda configuration
aws lambda get-function --function-name $(cd terraform && terraform output -raw lambda_function_name) | jq '.Code.ImageUri'
```

**Solution**:
- Ensure Docker image was pushed successfully
- Verify Lambda function points to correct ECR image URI
- Check IAM role has ECR pull permissions

### S3 Access Denied

**Symptoms**: Lambda executes but fails when writing to S3

**Diagnosis**:
```bash
# Check Lambda environment variables
aws lambda get-function-configuration \
  --function-name $(cd terraform && terraform output -raw lambda_function_name) | jq '.Environment'

# Check IAM role policies
aws iam list-attached-role-policies --role-name scraper-lambda-role
aws iam list-role-policies --role-name scraper-lambda-role
```

**Solution**:
1. Verify IAM role has AdministratorAccess attached
2. Check `S3_BUCKET` environment variable is set correctly
3. Run `terraform apply` to ensure changes are applied
4. Verify S3 bucket exists and matches environment variable

### No Logs Appearing

**Symptoms**: Lambda executes but no logs in CloudWatch

**Diagnosis**:
```bash
# Check log group exists
aws logs describe-log-groups --log-group-name-prefix /aws/lambda/scraper

# Check IAM role policies
aws iam list-attached-role-policies --role-name scraper-lambda-role
```

**Solution**:
- Verify IAM role has `AdministratorAccess` attached
- Check log group exists: `/aws/lambda/<function-name>`
- Wait 1-2 minutes for logs to appear (there can be delay)

### Lambda Timeout

**Symptoms**: Lambda execution terminates at configured timeout

**Diagnosis**:
```bash
# Check current timeout setting
aws lambda get-function-configuration \
  --function-name $(cd terraform && terraform output -raw lambda_function_name) | jq '.Timeout'
```

**Solution**:
Increase timeout in `terraform/main.tf`:

```hcl
resource "aws_lambda_function" "scraper" {
  # ... other config ...
  timeout     = 300  # Increase from 60 to 300 (5 minutes)
}
```

Then apply:
```bash
cd terraform/
terraform apply
```

### Schedule Not Triggering

**Symptoms**: Manual invocation works, but scheduled execution doesn't happen

**Diagnosis**:
```bash
# Check rule is enabled
aws events describe-rule --name scraper-hourly

# Check targets are configured
aws events list-targets-by-rule --rule scraper-hourly

# Check Lambda permissions
aws lambda get-policy --function-name $(cd terraform && terraform output -raw lambda_function_name)
```

**Solution**:
- Ensure EventBridge rule is enabled (State: ENABLED)
- Verify Lambda permission allows EventBridge to invoke
- Check schedule expression is valid
- Wait for next scheduled time (may take time to activate)

---

## Maintenance

### Update Dependencies

Update Python packages in `requirements.txt`, then redeploy:

```bash
# Update requirements.txt
# Then rebuild and redeploy
docker build -t scraper .
docker tag scraper:latest $(cd terraform && terraform output -raw ecr_repository_url):latest
docker push $(cd terraform && terraform output -raw ecr_repository_url):latest
aws lambda update-function-code \
  --function-name $(cd terraform && terraform output -raw lambda_function_name) \
  --image-uri $(cd terraform && terraform output -raw ecr_repository_url):latest
```

### Clean Up Old S3 Files

If S3 bucket accumulates too many files:

```bash
# List files older than 30 days (adjust date as needed)
aws s3 ls s3://$(cd terraform && terraform output -raw s3_bucket_name)/data/ --recursive

# Delete files in a specific date range (example)
aws s3 rm s3://$(cd terraform && terraform output -raw s3_bucket_name)/data/ --recursive --exclude "*" --include "status_202501*"
```

Consider adding S3 lifecycle policy in Terraform for automatic cleanup.

### Rotate ECR Images

If ECR accumulates many images:

```bash
# List images
aws ecr list-images --repository-name scraper

# Delete specific image by digest
aws ecr batch-delete-image \
  --repository-name scraper \
  --image-ids imageDigest=<digest>
```

---

## Infrastructure Teardown

### Option 1: Temporary Shutdown (Pause)

If you want to temporarily stop the scraper without deleting resources:

```bash
# Disable the EventBridge schedule rule
aws events disable-rule --name scraper-hourly

# Verify it's disabled
aws events describe-rule --name scraper-hourly | jq '.State'
# Should show: "DISABLED"
```

**What this does:**
- ✅ Stops scheduled Lambda executions
- ✅ Keeps all infrastructure (Lambda, S3, etc.)
- ✅ Stops incurring Lambda execution costs
- ⚠️ S3 storage costs continue (minimal)

**To re-enable later:**
```bash
aws events enable-rule --name scraper-hourly
```

---

### Option 2: Complete Teardown (Delete Everything)

Remove all AWS infrastructure and clean up resources.

#### Step 1: Verify Current Infrastructure

Before destroying, see what exists:

```bash
cd terraform/

# List all managed resources
terraform state list

# Review what will be destroyed
terraform plan -destroy
```

#### Step 2: Empty S3 Bucket

S3 buckets must be empty before Terraform can delete them:

```bash
# View what's in the bucket
aws s3 ls s3://$(terraform output -raw s3_bucket_name)/ --recursive --human-readable --summarize

# Delete all contents
aws s3 rm s3://$(terraform output -raw s3_bucket_name) --recursive

# Verify bucket is empty
aws s3 ls s3://$(terraform output -raw s3_bucket_name)/
```

#### Step 3: Destroy Infrastructure

```bash
cd terraform/

# Destroy all resources
terraform destroy

# Review the plan (lists everything to be deleted)
# Type 'yes' when prompted to confirm
```

#### Step 4: Verify Clean Removal

Confirm everything was deleted:

```bash
# Check Lambda
aws lambda list-functions --query 'Functions[?FunctionName==`scraper`]'
# Should return: []

# Check ECR
aws ecr describe-repositories --repository-names scraper
# Should return: RepositoryNotFoundException

# Check S3
aws s3 ls | grep scraper-output
# Should return nothing

# Check EventBridge rules
aws events list-rules --name-prefix scraper
# Should return: {"Rules": []}
```

#### Optional: Clean Up Terraform State

If you want to completely reset Terraform:

```bash
cd terraform/

# Remove state files (do this ONLY after terraform destroy)
rm -f terraform.tfstate terraform.tfstate.backup

# Remove Terraform directory
rm -rf .terraform

# Remove lock file
rm -f .terraform.lock.hcl
```

**⚠️ Warning**: Only do this after successful `terraform destroy`. If you delete state files while resources exist, Terraform loses track of them and you'll need to delete resources manually.

---

## Cost Monitoring

### View Current Costs

1. Go to AWS Console → Cost Management → Cost Explorer
2. Filter by Service: Lambda
3. Group by: Tag or Resource

### Check Usage

```bash
# Lambda invocations (requires CloudWatch Insights or AWS CLI v2)
# Check AWS Cost Explorer or CloudWatch metrics in console
```

### Expected Monthly Cost

| Component | Usage | Cost (Free Tier) | Cost (After Free Tier) |
|-----------|-------|------------------|----------------------|
| Lambda executions | 720/month | $0.00 | $0.00 |
| Lambda compute | 1,800 GB-sec | $0.00 | $0.30/month |
| S3 storage | ~1 MB | $0.00 | $0.00 |
| S3 PUT requests | 720/month | $0.00 | $0.36/month |
| **Total** | | **$0.00** | **~$0.66/month** |

