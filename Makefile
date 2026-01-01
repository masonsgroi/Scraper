.PHONY: setup test test-infra build push clean logs

# Install local development dependencies
setup:
	pip3 install -r requirements.txt

# Run unit tests only (excludes infrastructure tests)
test:
	python3 -m pytest -v --ignore=tests/test_infra.py

# Run infrastructure tests (AWS deployment verification)
test-infra:
	python3 -m pytest tests/test_infra.py -v -s

# Build Docker image for Lambda
build:
	docker build -t scraper .

# Push Docker image to ECR
push: build
	@ECR_URL=$$(cd terraform && terraform output -raw ecr_repository_url); \
	echo "Logging into ECR..."; \
	aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin $$ECR_URL; \
	echo "Tagging image..."; \
	docker tag scraper:latest $$ECR_URL:latest; \
	echo "Pushing to ECR (with extended timeout)..."; \
	DOCKER_CLIENT_TIMEOUT=600 docker push $$ECR_URL:latest; \
	echo "✅ Image pushed to $$ECR_URL:latest"

# Clean up Docker images and containers
clean:
	@echo "Cleaning up Docker resources..."
	docker stop scraper-test-container 2>/dev/null || true
	docker rm scraper-test-container 2>/dev/null || true
	docker rmi scraper-test 2>/dev/null || true
	@echo "Cleanup complete"

# Tail Lambda logs in real-time
logs:
	@LAMBDA_NAME=$$(cd terraform && terraform output -raw lambda_function_name); \
	aws logs tail /aws/lambda/$$LAMBDA_NAME --follow
