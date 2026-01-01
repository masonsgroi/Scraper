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
        
        # Start the container
        print("Starting Lambda container...")
        result = subprocess.run(
            ["docker", "run", "--rm", "-d", "-p", f"{port}:8080", 
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
        assert response_data["statusCode"] == 200, f"Lambda returned statusCode {response_data['statusCode']}"
        assert response_data["body"] == "Hello World!", f"Unexpected body: {response_data['body']}"
        
        # Check container logs
        result = subprocess.run(
            ["docker", "logs", container_name],
            capture_output=True,
            text=True
        )
        assert "Hello World from Lambda!" in result.stdout, "Expected log message not found"
        
        print("✅ Lambda Docker test passed")
        
    finally:
        # Clean up: stop the container
        subprocess.run(
            ["docker", "stop", container_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

