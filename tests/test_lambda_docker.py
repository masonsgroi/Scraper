"""
Integration test for Lambda Docker image
"""
import subprocess
import time
import requests
import json


def test_lambda_docker_image():
    """Test that the Lambda Docker image works correctly"""
    container_name = "scraper-test-container"
    image_name = "scraper-test"
    port = 9001
    
    # Clean up any existing container
    subprocess.run(
        ["docker", "stop", container_name],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    try:
        # Build the Docker image
        print("Building Lambda Docker image...")
        result = subprocess.run(
            ["docker", "build", "-t", image_name, "."],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Docker build failed: {result.stderr}"
        
        # Start the container with S3_BUCKET and dummy AWS credentials
        print("Starting Lambda container...")
        result = subprocess.run(
            ["docker", "run", "--rm", "-d", "-p", f"{port}:8080",
             "-e", "S3_BUCKET=test-bucket",
             "-e", "AWS_ACCESS_KEY_ID=test",
             "-e", "AWS_SECRET_ACCESS_KEY=test",
             "-e", "AWS_DEFAULT_REGION=us-west-2",
             "--name", container_name, image_name],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Failed to start container: {result.stderr}"
        
        # Wait for container to be ready
        time.sleep(3)
        
        # Invoke the Lambda function
        print("Invoking Lambda function...")
        url = f"http://localhost:{port}/2015-03-31/functions/function/invocations"
        response = requests.post(url, json={})
        
        # Validate response
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        response_data = response.json()
        # With dummy credentials, scraper will fail (network or auth error)
        # The important thing is the Lambda container runs and handles errors gracefully
        assert response_data["statusCode"] == 500, f"Lambda returned statusCode {response_data['statusCode']}"
        assert "Scraper failed:" in response_data["body"], \
            f"Expected scraper error in body, got: {response_data['body']}"
        
        # Check container logs - should show the error was logged
        result = subprocess.run(
            ["docker", "logs", container_name],
            capture_output=True,
            text=True
        )
        assert "ERROR: Scraper failed:" in result.stdout, \
            "Expected error log message not found"
        
        print("✅ Lambda Docker test passed")
        
    finally:
        # Clean up: stop the container
        subprocess.run(
            ["docker", "stop", container_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

