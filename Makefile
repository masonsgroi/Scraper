.PHONY: setup test clean

# Install local development dependencies
setup:
	pip3 install -r requirements.txt

# Run all tests
test:
	python3 -m pytest -v

# Clean up Docker images and containers
clean:
	@echo "Cleaning up Docker resources..."
	docker stop scraper-test-container 2>/dev/null || true
	docker rm scraper-test-container 2>/dev/null || true
	docker rmi scraper-test 2>/dev/null || true
	@echo "Cleanup complete"
