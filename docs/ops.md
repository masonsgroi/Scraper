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
# Install AWS CLI
brew install awscli  # macOS
# or: pip3 install awscli

# Configure AWS credentials (REQUIRED before Terraform operations)
aws configure
```

**How to get AWS credentials:**
1. Log into [AWS Console](https://console.aws.amazon.com/)
2. Click your username (top right) → **Security credentials**
3. Scroll to **Access keys** section → **Create access key**
4. Choose use case: **Command Line Interface (CLI)**
5. Save both the **Access Key ID** and **Secret Access Key** (secret key only shown once!)

**Verify credentials work:**
```bash
aws sts get-caller-identity
```

Expected output: Your AWS account ID and user ARN

**Note:** If using temporary credentials (AWS SSO), they expire periodically and you'll need to re-authenticate.

**Docker:**
- Docker Desktop installed and running
- Verify: `docker --version`

### Project Setup

- Working directory: `/Users/msgroi/Documents/d/github/Scraper` (project root)
- Terraform initialized: `cd terraform/ && terraform init` (run once after cloning)

---

## Terraform Operations

**Prerequisites:** AWS credentials must be configured (see Prerequisites section above).

### Initialize Terraform (First Time Only)

```bash
cd terraform/
terraform init
```

Run this once after cloning the repo or when Terraform configuration changes.

### Preview Infrastructure Changes

Before making any changes to AWS infrastructure, always preview what will happen:

```bash
cd terraform/
terraform plan
```

This shows what resources would be created/modified/destroyed **without actually making changes**.

**What to check:**
- Review the resources that will be created/modified/destroyed
- Verify region is `us-west-2`
- Check resource names match expectations
- Look for `Plan: X to add, Y to change, Z to destroy`

**Troubleshooting:**
- **Error: ExpiredToken** → Run `aws configure` to refresh credentials
- **Error: No credentials** → Run `aws configure` to set up credentials
- **Wrong region** → Ensure you set `us-west-2` in `aws configure`

### Apply Infrastructure Changes

After reviewing the plan, apply the changes to create/update AWS resources:

```bash
cd terraform/
terraform apply
```

Type `yes` when prompted to confirm.

**Save the outputs** - You'll need the ECR URL for pushing Docker images.

**Verify deployment:**
```bash
make test-infra
```

---

## Deployment

### Initial Deployment

See [infra_devplan.md](infra_devplan.md) for the complete initial setup process (Phases 1-4).

### Code Deployment (Python Changes)

When you modify the scraper code:

```bash
# Build, push Docker image to ECR, and update Lambda function
make push
```

This command will:
1. Build the Docker image
2. Push it to ECR
3. Update the Lambda function with the new image
4. Wait for the Lambda function to be ready

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
# Quick shortcut: Real-time logs (follow mode)
make logs

# Or use AWS CLI directly:
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

### Verify Lambda Deployment

Run automated infrastructure tests to verify the Lambda deployment:

```bash
make test-infra
```

This will verify:
- ECR repository exists
- Docker image is in ECR
- Lambda function is configured correctly
- Lambda invocation works
- CloudWatch logging is functioning

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
# Update requirements.txt, then rebuild and redeploy
make push
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

