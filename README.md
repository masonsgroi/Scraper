# Ski Resort Scraper

Automated web scraper for ski resort lift and trail data, deployed on AWS Lambda.

## Overview

This project scrapes lift status and wait time data from a ski resort website, stores the data in S3, and runs automatically on a schedule using AWS Lambda.

**Architecture**: AWS Lambda (Docker container) + EventBridge (scheduler) + S3 (storage)

## Project Structure

```
Scraper/
├── src/                        # Production code
│   └── hello.py               # Lambda handler (Phase 1 - Hello World)
├── tests/                      # Test files
│   ├── test_hello.py          # Unit tests for Lambda handler
│   └── test_lambda_docker.py  # Integration tests for Docker image
├── Dockerfile                  # Lambda-compatible Docker image
├── requirements.txt            # Python dependencies
├── Makefile                    # Build and test automation
├── terraform/                  # Infrastructure as code (coming in Phase 1.3)
│   └── main.tf                # AWS resources definition
├── docs/                       # Documentation
│   ├── scraper_design.md      # What the scraper does
│   ├── scraper_devplan.md     # Building the scraper (phases 1-5)
│   ├── hosting.md             # Hosting evaluation & decision
│   ├── infra_design.md        # Architecture & design decisions
│   ├── infra_devplan.md       # Infrastructure deployment (phases 1-4)
│   ├── infra_work.md          # Work tracker for infrastructure phases
│   └── ops.md                 # Operations guide
└── README.md                  # This file
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

## Local Development Setup

### Prerequisites
- **Python 3.12+** (recommended) or Python 3.10+ minimum
- Docker
- AWS CLI (for deployment)
- Terraform (for infrastructure)

**Note:** Python 3.9 is still functional but will lose boto3 support in April 2026. Use Python 3.12+ to avoid deprecation warnings.

#### Installing Python 3.12 with pyenv (recommended)

If you don't have Python 3.12+, use pyenv to install it:

```bash
# Install pyenv (macOS)
brew install pyenv

# Add pyenv to your shell (one time setup)
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init --path)"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc

# Restart your terminal or run:
source ~/.zshrc

# Install Python 3.12
pyenv install 3.12.12

# Set it globally
pyenv global 3.12.12

# Verify
python3 --version  # Should show Python 3.12.12
```

### Setup

1. Clone the repository
2. Install development dependencies:
```bash
make setup
```

This installs:
- `pytest` - for running tests
- `requests` - for integration testing

### Running Tests

Run unit tests:
```bash
make test
```

This will:
- Run unit tests for the Lambda handler
- Build the Docker image and test it locally with the Lambda runtime emulator

Run infrastructure tests (requires AWS deployment):
```bash
make test-infra
```

### Building Docker Image

Build the Docker image locally:

```bash
make build
```

### Cleaning Up

Remove Docker containers and images:
```bash
make clean
```

## Deployment Guide

1. Read [scraper_design.md](docs/scraper_design.md) to understand what the scraper does
2. Review [infra_design.md](docs/infra_design.md) to understand the architecture
3. Follow [infra_devplan.md](docs/infra_devplan.md) for step-by-step deployment to AWS
4. Use [ops.md](docs/ops.md) for day-to-day operations

