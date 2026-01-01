.PHONY: setup test test-infra test-live build push build-push clean logs s3

# Install local development dependencies
setup:
	pip3 install -r requirements.txt

# Run unit tests only (excludes infrastructure tests)
test:
	python3 -m pytest -v --ignore=tests/test_infra.py

# Run infrastructure tests (AWS deployment verification)
test-infra:
	python3 -m pytest tests/test_infra.py -v -s

# Test scraper against live API (no mocks)
test-live:
	python3 test_scraper_live.py

# Build Docker image for Lambda
build:
	@echo "Incrementing version..."
	@VERSION=$$(cat VERSION); \
	MAJOR=$$(echo $$VERSION | cut -d. -f1); \
	MINOR=$$(echo $$VERSION | cut -d. -f2); \
	NEW_MINOR=$$(($$MINOR + 1)); \
	NEW_VERSION="$$MAJOR.$$NEW_MINOR"; \
	echo $$NEW_VERSION > VERSION; \
	echo "Building version $$NEW_VERSION..."
	docker build -t scraper .

# Push Docker image to ECR and update Lambda
push: build
	@ECR_URL=$$(cd terraform && terraform output -raw ecr_repository_url); \
	LAMBDA_NAME=$$(cd terraform && terraform output -raw lambda_function_name); \
	echo "Logging into ECR..."; \
	aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin $$ECR_URL; \
	echo "Tagging image..."; \
	docker tag scraper:latest $$ECR_URL:latest; \
	echo "Pushing to ECR (with extended timeout)..."; \
	DOCKER_CLIENT_TIMEOUT=600 docker push $$ECR_URL:latest; \
	echo "✅ Image pushed to $$ECR_URL:latest"; \
	echo "Updating Lambda function..."; \
	aws lambda update-function-code \
		--function-name $$LAMBDA_NAME \
		--image-uri $$ECR_URL:latest \
		--region us-west-2 > /dev/null; \
	echo "✅ Lambda function updated"; \
	echo "⏳ Waiting for Lambda to be ready..."; \
	aws lambda wait function-updated --function-name $$LAMBDA_NAME --region us-west-2; \
	echo "✅ Lambda function is ready"

# Alias for push (builds and pushes in one command)
build-push: push

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

# Open S3 bucket in browser
s3:
	@BUCKET=$$(cd terraform && terraform output -raw s3_bucket_name); \
	URL="https://s3.console.aws.amazon.com/s3/buckets/$$BUCKET?region=us-west-2"; \
	echo "Opening S3 browser at: $$URL"; \
	open "$$URL"
