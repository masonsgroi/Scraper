# Hosting Options for Scraper

> **Decision**: AWS Lambda selected. See [infra_design.md](infra_design.md) for architecture details.

---

## Requirements

### Primary Requirement
**Docker-based scheduling with cost optimization**

The solution must support one of the following approaches:
1. **Scheduled Docker Container Execution**: Run a Docker image on a schedule (e.g., using cron-like scheduling)
   - Container starts, executes scraper, outputs to S3, then terminates
   - Only pay for actual execution time
   - Preferred if cost-effective
   
2. **Long-running Container with Internal Scheduler**: Docker image runs indefinitely with internal scheduling logic
   - Container stays running with a scheduler (cron, Python schedule library, etc.) inside
   - Executes scraper tasks at specified intervals
   - Consider if cheaper/easier than option 1

### Key Constraint
- **Cost Optimization**: Solution should be **as inexpensive as is reasonable**
  - Minimize idle compute costs
  - Leverage pay-per-execution or low-cost always-on options
  - Free tier eligibility is a plus

### Functional Requirements
- **Docker Support**: Must be able to deploy and run Docker containers
- **Storage Integration**: Access to AWS S3 for output data
- **HTTP/HTTPS Support**: Ability to make outbound web requests to scrape target websites
- **Scheduling**: Either platform-provided scheduling or support for internal scheduler

### Non-Functional Requirements
- **Reliability**: Reasonable uptime and ability to recover from failures
- **Simplicity**: Easy setup and maintenance (prefer simpler over more complex)
- **Monitoring**: Basic ability to track execution status and failures
- **Logging**: Capture logs for debugging
- **Security**: Secure credential management for AWS S3 access

### Technical Constraints
- **Execution Time**: Support for scripts that may run for several minutes
- **Memory**: Sufficient memory for web scraping libraries and data processing
- **Network**: Stable outbound network connectivity
- **Region**: Ideally in US region for lower latency to target websites

---

## Options Considered

### Potential Low-Cost Options
- **AWS Lambda with Container Images** ✅ **SELECTED**
- **AWS ECS with Fargate Spot** (scheduled tasks)
- **Google Cloud Run Jobs** (scheduled)
- **fly.io** (always-on micro instances)
- **Railway** (simple Docker deployment)
- **Render** (cron jobs or background workers)
- **DigitalOcean App Platform** (scheduled jobs)
- **Self-hosted on low-cost VPS** (DigitalOcean Droplet, Linode, etc. with internal scheduler)

---

## AWS Lambda (Selected)

### Overview
Serverless compute service that runs code in response to events. For this use case:
- Docker container triggered by EventBridge on schedule
- Executes scraper, writes to S3, terminates
- Pay only for execution time

### Architecture
```
EventBridge (Schedule) → Lambda (Container) → S3 (Output)
                              ↓
                        CloudWatch Logs
```

### Pros
- ✅ **Pay-per-execution** - No idle costs, only charged during scraper execution
- ✅ **Very low cost** - Free tier covers typical usage ($0/month), ~$0.30/month after
- ✅ **Native AWS integration** - Built-in S3 access, IAM security, CloudWatch logging
- ✅ **No server management** - Fully managed, automatic scaling
- ✅ **Built-in scheduling** - EventBridge provides cron-like scheduling
- ✅ **Container support** - Native Docker image support (up to 10GB)
- ✅ **Simple deployment** - Terraform manages all infrastructure

### Cons
- ⚠️ **15-minute timeout** - Maximum execution time limit (current scraper runs in ~5 seconds)
- ⚠️ **Handler wrapper needed** - Requires Lambda handler function in Python code
- ⚠️ **Cold starts** - 1-2 second initialization delay (acceptable for scheduled tasks)
- ⚠️ **AWS lock-in** - Tied to AWS ecosystem
- ⚠️ **Learning curve** - Need to understand Lambda + Terraform (moderate complexity)

### Cost Estimate
**Assumptions**: Hourly execution (720 times/month), 5 seconds per run, 512MB memory

- Monthly executions: 720 requests
- Compute time: 3,600 seconds (1 hour total)
- Memory: 1,800 GB-seconds
- **Within free tier**: $0.00/month
- **After free tier**: ~$0.30/month

### Meets Requirements?
- ✅ Docker support (native container images)
- ✅ Scheduled execution (EventBridge)
- ✅ Cost-effective (cheapest option, within free tier)
- ✅ S3 integration (native)
- ✅ Simple maintenance (Terraform manages all)
- ⚠️ Execution time limit (15 min max, but sufficient for this use case)

---

## Comparison Matrix

| Option | Monthly Cost | Setup Complexity | Maintenance | Time Limit | Best For |
|--------|-------------|------------------|-------------|------------|----------|
| **AWS Lambda** | **$0-0.30** | **Medium** | **Low** | 15 min | ✅ **Short periodic tasks** |
| AWS ECS Fargate | $2-5 | High | Medium | None | Long-running tasks |
| Google Cloud Run | $0-1 | Medium | Low | 24 hrs | Multi-cloud setups |
| VPS (DO, Linode) | $5-10 | Low | High | None | Always-on services |
| PaaS (Render, etc.) | $5+ | Low | Low | Varies | Simple apps, prototypes |

---

## Decision Rationale

**AWS Lambda selected** for optimal cost-to-value ratio:

- **Cost-effective**: Free tier covers expected usage; ~$0.30/month after (10-30x cheaper than alternatives)
- **Right fit**: Pay-per-execution model ideal for short, periodic tasks
- **Low maintenance**: Fully managed with Terraform-based infrastructure
- **Native integration**: Built-in S3 and CloudWatch support

**Trade-off**: 15-minute execution timeout (acceptable for 5-second scraper runtime)

See [infra_design.md](infra_design.md) for architecture details and [infra_devplan.md](infra_devplan.md) for deployment steps.