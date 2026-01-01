# Infrastructure Design

## Overview

The scraper infrastructure is designed as a serverless, event-driven system using AWS Lambda for compute, EventBridge for scheduling, and S3 for persistent storage.

**Design Philosophy**: Minimize operational overhead and cost while maintaining reliability for periodic data collection.do

---

## Architecture

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│  EventBridge    │────▶ │  Lambda Function │────▶ │   Amazon S3     │
│  (Scheduler)    │      │  (Container)     │      │  (Output Data)  │
│  cron: 0 * * *  │      │                  │      │  bucket/path    │
└─────────────────┘      └──────────────────┘      └─────────────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │  CloudWatch Logs │
                         │  (Monitoring)    │
                         └──────────────────┘
```

### Execution Flow

1. **EventBridge** triggers Lambda on schedule (e.g., every hour)
2. **Lambda** pulls Docker image from ECR and executes scraper code
3. **Scraper** fetches data from ski resort APIs
4. **Lambda** writes CSV files to S3
5. **CloudWatch** captures all logs automatically

---

## Components

### 1. AWS Lambda Function

**Purpose**: Execute scraper logic in response to scheduled events

**Configuration**:
- **Runtime**: Container (Docker image)
- **Memory**: 512 MB
- **Timeout**: 300 seconds (5 minutes)
- **Concurrency**: 1 (default, only one execution at a time)
- **Handler**: `scraper.lambda_handler`

**Limitations**:
- 15-minute maximum execution time
- Cold start latency (1-2 seconds, acceptable for scheduled tasks)

### 2. Amazon ECR (Elastic Container Registry)

**Purpose**: Store and version Docker images for Lambda

**Configuration**:
- **Repository name**: `scraper`
- **Image scanning**: Enabled (security best practice)
- **Tag strategy**: `latest` for active deployment

### 3. Amazon EventBridge (CloudWatch Events)

**Purpose**: Schedule Lambda invocations

**Configuration**:
- **Rule name**: `scraper-hourly`
- **Schedule**: `rate(1 hour)` or custom cron expression
- **Target**: Lambda function
- **Enabled**: Yes

**Schedule Patterns**:
- Rate: `rate(1 hour)`, `rate(30 minutes)`, `rate(1 day)`
- Cron: `cron(0 9 * * ? *)` (9 AM UTC daily)
- Cron: `cron(0 */2 * * ? *)` (every 2 hours)

### 4. Amazon S3 Bucket

**Purpose**: Persistent storage for scraped data

**Configuration**:
- **Bucket name**: `scraper-output-{account-id}` (globally unique)
- **Structure**: 
  - `data/status_{timestamp}.csv`
  - `data/wait_time_{timestamp}.csv`
- **Versioning**: Disabled (not needed, data is append-only)
- **Lifecycle**: None (consider adding retention policy)

### 5. IAM Role & Policies

**Purpose**: Grant Lambda permission to access AWS services

**Role**: `scraper-lambda-role`

**Attached Policy**:
- **AdministratorAccess** (AWS managed)
  - Full access to all AWS services
  - Simplifies development and deployment
  - No need to manage specific permissions

### 6. CloudWatch Logs

**Purpose**: Capture execution logs for debugging and monitoring

**Configuration**:
- **Log group**: `/aws/lambda/scraper` (auto-created)
- **Retention**: Default (never expire) or configurable (7 days, 30 days, etc.)
- **Log streams**: One per Lambda execution

**What's Logged**:
- Function start/stop
- All `print()` statements from Python
- Errors and stack traces
- Execution duration and memory usage

---

## Security

### IAM Permissions
- Lambda role has AdministratorAccess for simplicity
- No public access to S3 bucket
- No hardcoded credentials

### Network Security
- Lambda runs in AWS-managed VPC (default)
- Outbound internet access for API calls
- No inbound access required
- S3 accessed via AWS internal network

### Data Security
- Data in transit: HTTPS to resort APIs, AWS internal TLS to S3
- Data at rest: S3 server-side encryption (enabled by default)
- Logs: CloudWatch encrypted at rest

### Secrets Management
- No secrets needed currently (public API)
- If needed: AWS Secrets Manager or Parameter Store
- Environment variables for non-sensitive config (S3 bucket name)

---

## Scalability

### Current Capacity
- **Lambda**: Can execute 1000 concurrent functions (default limit)
- **S3**: Unlimited storage, 3,500 PUT/second per prefix
- **EventBridge**: 10,000 rules per account (default limit)

### Scaling Scenarios

**Multiple Scrapers**:
- Add more EventBridge rules pointing to same Lambda
- Or: Add multiple targets to same rule with different input
- Or: Create separate Lambda functions per scraper

**Higher Frequency**:
- Change schedule to `rate(5 minutes)` = 8,640 executions/month
- Still within Lambda free tier
- Cost after free tier: ~$1.50/month

**More Data Sources**:
- Lambda can scrape multiple sites in one execution
- Or: Fan-out pattern with Step Functions (more complex)

### Current Bottlenecks
- None identified
- Scraper completes in ~5 seconds
- Lambda timeout is 5 minutes (60x headroom)

---

## Monitoring & Observability

### Available Metrics (CloudWatch)

**Lambda Metrics** (automatic):
- Invocations
- Duration
- Errors
- Throttles
- Concurrent executions

**Custom Metrics** (can add):
- Number of lifts scraped
- API response time
- Data validation failures

### Logging Strategy
- All function output logged to CloudWatch
- Structured logging: timestamp, event, status
- Error logging with stack traces
- Searchable via CloudWatch Logs Insights

### Alerting (Future)
- CloudWatch Alarms on Lambda errors
- SNS notification on failures
- Lambda Dead Letter Queue for failed events

