# Palisades Scraper

Automated web scraper for Palisades Tahoe ski resort lift and trail data, deployed on AWS Lambda.

## Overview

This project scrapes lift status and wait time data from Palisades Tahoe website, stores the data in S3, and runs automatically on a schedule using AWS Lambda.

**Architecture**: AWS Lambda (Docker container) + EventBridge (scheduler) + S3 (storage)

## Project Structure

```
Scraper/
├── web_scraper2.py         # Main scraper logic
├── Dockerfile              # Lambda-compatible Docker image
├── requirements.txt        # Python dependencies
├── terraform/              # Infrastructure as code
│   └── main.tf            # AWS resources definition
├── docs/                   # Documentation
│   ├── scraper_design.md  # What the scraper does
│   ├── scraper_devplan.md # Building the scraper (phases 1-5)
│   ├── hosting.md         # Hosting evaluation & decision
│   ├── infra_design.md    # Architecture & design decisions
│   ├── infra_devplan.md   # Infrastructure deployment (phases 1-4)
│   └── ops.md             # Operations guide
└── README.md              # This file
```

## Documentation

### 📊 Scraper Design
- **[scraper_design.md](docs/scraper_design.md)** - What the scraper does and how it works
- **[scraper_devplan.md](docs/scraper_devplan.md)** - Step-by-step guide to building the scraper incrementally

### 📋 Hosting
- **[hosting.md](docs/hosting.md)** - Requirements, options evaluated, and why AWS Lambda was selected

### 🏗️ Infrastructure
- **[infra_design.md](docs/infra_design.md)** - Architecture overview and components
- **[infra_devplan.md](docs/infra_devplan.md)** - Step-by-step deployment guide with 4 incremental phases

### 🔧 Operations
- **[ops.md](docs/ops.md)** - Day-to-day operations including deployment, monitoring, testing, and troubleshooting

## Getting Started

1. Read [scraper_design.md](docs/scraper_design.md) to understand what the scraper does
2. Follow [scraper_devplan.md](docs/scraper_devplan.md) to build the scraper locally (optional)
3. Review [infra_design.md](docs/infra_design.md) to understand the architecture
4. Follow [infra_devplan.md](docs/infra_devplan.md) for step-by-step deployment to AWS
5. Use [ops.md](docs/ops.md) for day-to-day operations

