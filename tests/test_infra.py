"""
Infrastructure tests for AWS infrastructure and Lambda deployment
"""
import subprocess
import json
import time
import boto3
from botocore.exceptions import ClientError


def get_terraform_output(output_name):
    """Get Terraform output value"""
    result = subprocess.run(
        ["terraform", "output", "-raw", output_name],
        cwd="terraform",
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to get Terraform output '{output_name}': {result.stderr}")
    return result.stdout.strip()


def test_ecr_repository_exists():
    """Test that ECR repository is created"""
    ecr_client = boto3.client('ecr', region_name='us-west-2')
    
    try:
        response = ecr_client.describe_repositories(repositoryNames=['scraper'])
        assert len(response['repositories']) == 1
        assert response['repositories'][0]['repositoryName'] == 'scraper'
        print("✅ ECR repository exists")
    except ClientError as e:
        if e.response['Error']['Code'] == 'RepositoryNotFoundException':
            raise AssertionError("ECR repository 'scraper' not found")
        raise


def test_ecr_image_exists():
    """Test that Docker image exists in ECR"""
    ecr_client = boto3.client('ecr', region_name='us-west-2')
    
    try:
        response = ecr_client.describe_images(
            repositoryName='scraper',
            imageIds=[{'imageTag': 'latest'}]
        )
        assert len(response['imageDetails']) > 0
        print("✅ Docker image exists in ECR")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ImageNotFoundException':
            raise AssertionError("Docker image with tag 'latest' not found in ECR")
        raise


def test_lambda_function_exists():
    """Test that Lambda function is created"""
    lambda_client = boto3.client('lambda', region_name='us-west-2')
    
    try:
        response = lambda_client.get_function(FunctionName='scraper')
        assert response['Configuration']['FunctionName'] == 'scraper'
        assert response['Configuration']['PackageType'] == 'Image'
        assert response['Configuration']['Timeout'] == 60
        assert response['Configuration']['MemorySize'] == 512
        print("✅ Lambda function exists with correct configuration")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            raise AssertionError("Lambda function 'scraper' not found")
        raise


def test_lambda_invocation():
    """Test that Lambda function can be invoked and returns correct response"""
    lambda_client = boto3.client('lambda', region_name='us-west-2')
    
    # Invoke Lambda
    response = lambda_client.invoke(
        FunctionName='scraper',
        InvocationType='RequestResponse',
        Payload=json.dumps({})
    )
    
    # Check response status
    assert response['StatusCode'] == 200, f"Expected status 200, got {response['StatusCode']}"
    
    # Parse and validate response payload
    payload = json.loads(response['Payload'].read())
    assert payload['statusCode'] == 200, f"Expected statusCode 200, got {payload['statusCode']}"
    assert payload['body'] == 'Hello World!', f"Expected 'Hello World!', got '{payload['body']}'"
    
    print("✅ Lambda function invoked successfully")
    print(f"   Response: {payload}")


def test_lambda_logs():
    """Test that Lambda function logs to CloudWatch"""
    logs_client = boto3.client('logs', region_name='us-west-2')
    log_group = '/aws/lambda/scraper'
    
    # Wait a moment for logs to be available
    time.sleep(2)
    
    try:
        # Get the most recent log stream
        streams_response = logs_client.describe_log_streams(
            logGroupName=log_group,
            orderBy='LastEventTime',
            descending=True,
            limit=1
        )
        
        if not streams_response['logStreams']:
            raise AssertionError("No log streams found")
        
        log_stream_name = streams_response['logStreams'][0]['logStreamName']
        
        # Get recent log events
        events_response = logs_client.get_log_events(
            logGroupName=log_group,
            logStreamName=log_stream_name,
            limit=50
        )
        
        # Check for our expected log message
        log_messages = [event['message'] for event in events_response['events']]
        assert any('Hello World from Lambda!' in msg for msg in log_messages), \
            "Expected log message 'Hello World from Lambda!' not found in CloudWatch logs"
        
        print("✅ Lambda function logs to CloudWatch correctly")
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            raise AssertionError(f"CloudWatch log group '{log_group}' not found")
        raise


if __name__ == "__main__":
    print("Running infrastructure tests...\n")
    
    try:
        test_ecr_repository_exists()
        test_ecr_image_exists()
        test_lambda_function_exists()
        test_lambda_invocation()
        test_lambda_logs()
        
        print("\n🎉 All infrastructure tests passed!")
    except Exception as e:
        print(f"\n❌ Infrastructure test failed: {e}")
        exit(1)

