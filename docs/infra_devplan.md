# Infrastructure Deployment Plan

This document provides step-by-step instructions for deploying the scraper infrastructure incrementally through 4 phases.

**Before starting**: Review [infra_design.md](infra_design.md) to understand the architecture and design decisions.

---

## Incremental Development Approach

This plan uses an incremental, test-as-you-go approach. Each phase builds on the previous one, allowing you to validate functionality before adding complexity.

### Development Phases

| Phase | Goal | What You'll Learn | Validation |
|-------|------|-------------------|------------|
| **1** | Hello World Lambda | Deploy container to Lambda, view logs | Lambda executes, prints to CloudWatch |
| **2** | Add Scheduling | Configure EventBridge to trigger Lambda | Lambda runs automatically every 5 min |
| **3** | Add S3 Output | Write data to S3 from Lambda | Timestamp files appear in S3 bucket |
| **4** | Integrate Scraper | Full scraper logic with S3 storage | CSV files with lift data in S3 |

### Phase Progression

```
Phase 1: Lambda (Hello World)
   ↓
Phase 2: Lambda + EventBridge (Scheduled Hello World)
   ↓
Phase 3: Lambda + EventBridge + S3 (Write Timestamp)
   ↓
Phase 4: Lambda + EventBridge + S3 (Full Scraper)
```

---

## Phase 1: Hello World Lambda

**Goal**: Deploy a simple Lambda function that prints "Hello World" to CloudWatch Logs.

### Step 1.1: Create Hello World Python Script

Create `hello.py`:
- `lambda_handler(event, context)` function
- Print "Hello World from Lambda!"
- Return statusCode 200 with body

### Step 1.2: Create Lambda-compatible Dockerfile

Create `Dockerfile`:
- Use base image: `public.ecr.aws/lambda/python:3.11`
- Copy `hello.py` to `${LAMBDA_TASK_ROOT}`
- Set CMD to `["hello.lambda_handler"]`

### Step 1.3: Create Minimal Terraform Configuration

Create `terraform/main.tf` with:

**Provider setup**:
- AWS provider, region: `us-west-2`

**Resources**:
- `aws_ecr_repository.scraper` - name: "scraper", enable image scanning
- `aws_iam_role.lambda_role` - name: "scraper-lambda-role", trust policy for Lambda service
- `aws_iam_role_policy_attachment.lambda_admin` - attach AdministratorAccess policy
- `aws_lambda_function.scraper` - package_type: "Image", timeout: 60, memory: 512

**Outputs**:
- `ecr_repository_url`
- `lambda_function_name`

### Step 1.4: Deploy Infrastructure

```bash
cd terraform/
terraform init
terraform plan
terraform apply
```

### Step 1.5: Build and Push Docker Image

```bash
# Get ECR URL and login
ECR_URL=$(terraform output -raw ecr_repository_url)
aws ecr get-login-password --region us-west-2 | \
  docker login --username AWS --password-stdin $ECR_URL

# Build, tag, and push
cd ..
docker build -t scraper .
docker tag scraper:latest $ECR_URL:latest
docker push $ECR_URL:latest
```

### Step 1.6: Update Lambda with Image

```bash
cd terraform/
aws lambda update-function-code \
  --function-name $(terraform output -raw lambda_function_name) \
  --image-uri $(terraform output -raw ecr_repository_url):latest
```

### Step 1.7: Test Lambda Function

```bash
# Invoke manually
aws lambda invoke \
  --function-name $(terraform output -raw lambda_function_name) \
  --payload '{}' \
  response.json

# Check response and logs
cat response.json
aws logs tail /aws/lambda/$(terraform output -raw lambda_function_name) --follow
```

**Expected Output**:
- `response.json`: `{"statusCode": 200, "body": "Hello World!"}`
- Logs: "Hello World from Lambda!"

✅ **Phase 1 Complete**: Lambda function deployed and executing successfully!

---

## Phase 2: Add Scheduling

**Goal**: Trigger Lambda function automatically every 5 minutes using EventBridge.

### Step 2.1: Update Terraform Configuration

Add to `terraform/main.tf`:

**EventBridge resources**:
- `aws_cloudwatch_event_rule.scraper_schedule`
  - name: "scraper-every-5-min"
  - schedule_expression: `"rate(5 minutes)"`
- `aws_cloudwatch_event_target.scraper_target`
  - rule: event rule name
  - arn: Lambda function ARN
- `aws_lambda_permission.allow_eventbridge`
  - Allow EventBridge to invoke Lambda
  - principal: "events.amazonaws.com"

### Step 2.2: Apply Terraform Changes

```bash
cd terraform/
terraform plan
terraform apply
```

### Step 2.3: Verify Scheduled Execution

```bash
# Wait 5-10 minutes, then check logs
aws logs tail /aws/lambda/$(terraform output -raw lambda_function_name) --since 10m
```

**Expected**: Multiple "Hello World" messages as Lambda runs every 5 minutes

✅ **Phase 2 Complete**: Lambda now runs automatically on schedule!

---

## Phase 3: Write Timestamp to S3

**Goal**: Lambda writes current timestamp to an S3 file.

### Step 3.1: Update Python Script

Update `hello.py`:
- Import: `boto3`, `os`, `datetime`
- Get bucket name from `os.environ.get('S3_BUCKET')`
- Generate timestamp: `datetime.utcnow().isoformat()`
- Use `boto3.client('s3').put_object()` to write to S3
- Key: `f"timestamps/{timestamp}.txt"`

### Step 3.2: Update Dockerfile

Update `Dockerfile`:
- Add `boto3` installation (or use requirements.txt)

### Step 3.3: Update Terraform Configuration

Add to `terraform/main.tf`:

**S3 resources**:
- `aws_s3_bucket.scraper_output`
  - bucket: `"scraper-output-${data.aws_caller_identity.current.account_id}"`

**Lambda updates**:
- Add environment variable: `S3_BUCKET = aws_s3_bucket.scraper_output.id`

**Data source**:
- `data.aws_caller_identity.current` for account ID

**Outputs**:
- Add `s3_bucket_name`

### Step 3.4: Apply Changes

```bash
# Apply Terraform
cd terraform/
terraform apply

# Rebuild and push Docker image
cd ..
docker build -t scraper .
docker tag scraper:latest $ECR_URL:latest
docker push $ECR_URL:latest

# Update Lambda
cd terraform/
aws lambda update-function-code \
  --function-name $(terraform output -raw lambda_function_name) \
  --image-uri $(terraform output -raw ecr_repository_url):latest
```

### Step 3.5: Verify S3 Output

```bash
# Wait 5-10 minutes, then check S3
aws s3 ls s3://$(terraform output -raw s3_bucket_name)/timestamps/
```

**Expected**: Multiple timestamp files in S3

✅ **Phase 3 Complete**: Lambda writing to S3 successfully!

---

## Phase 4: Integrate Full Scraper

**Goal**: Deploy complete scraper that fetches lift data and writes CSV files to S3.

### Step 4.1: Update Python Script

Replace `hello.py` with `scraper.py`:
- Import: `boto3`, `pandas`, `requests`, `os`, `datetime`
- `fetch_json_from_url(url)` - fetch from Palisades APIs
- `scrape_lift_data()` - parse JSON, extract lift info
- `upload_to_s3(df, bucket, key)` - upload DataFrame as CSV to S3
- `lambda_handler(event, context)` - orchestrate scraping and upload

**Key elements**:
- Two API endpoints (maps 152 and 1446)
- Two CSV files: `status_{timestamp}.csv` and `wait_time_{timestamp}.csv`
- S3 prefix: `data/`

### Step 4.2: Update Dockerfile

Update `Dockerfile`:
- Copy `scraper.py` instead of `hello.py`
- Update CMD to `["scraper.lambda_handler"]`

### Step 4.3: Create requirements.txt

```
requests
pandas
boto3
```

Update `Dockerfile` to install requirements:
- `COPY requirements.txt ${LAMBDA_TASK_ROOT}`
- `RUN pip install -r requirements.txt`

### Step 4.4: Update Terraform Configuration

Update `terraform/main.tf`:

**Lambda updates**:
- Change timeout to 300 seconds (5 minutes)
- Keep memory at 512 MB

**EventBridge updates**:
- Change schedule to `"rate(1 hour)"` for production
- Update rule name to "scraper-hourly"

### Step 4.5: Deploy Final Version

```bash
# Apply Terraform
cd terraform/
terraform apply

# Rebuild and push Docker image
cd ..
docker build -t scraper .
docker tag scraper:latest $ECR_URL:latest
docker push $ECR_URL:latest

# Update Lambda
cd terraform/
aws lambda update-function-code \
  --function-name $(terraform output -raw lambda_function_name) \
  --image-uri $(terraform output -raw ecr_repository_url):latest
```

### Step 4.6: Test Scraper

```bash
# Invoke manually to test
aws lambda invoke \
  --function-name $(terraform output -raw lambda_function_name) \
  --payload '{}' \
  response.json

# Check response
cat response.json

# View logs
aws logs tail /aws/lambda/$(terraform output -raw lambda_function_name) --follow

# Check S3 for CSV files
aws s3 ls s3://$(terraform output -raw s3_bucket_name)/data/
```

**Expected Output**:
- Response indicates successful execution
- Logs show scraping progress
- Two CSV files in S3: `status_*.csv` and `wait_time_*.csv`

✅ **Phase 4 Complete**: Full scraper deployed and running on schedule!

---

## Cleanup

To remove all AWS resources:

```bash
cd terraform/

# Delete all S3 objects first
aws s3 rm s3://$(terraform output -raw s3_bucket_name) --recursive

# Destroy infrastructure
terraform destroy
```

For more operational details, see [ops.md](ops.md).
