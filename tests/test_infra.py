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
    
    # Check that response indicates S3 write success
    bucket_name = get_terraform_output('s3_bucket_name')
    assert f'Timestamp written to s3://{bucket_name}/timestamps/' in payload['body'], \
        f"Expected S3 write success message, got '{payload['body']}'"
    
    print("✅ Lambda function invoked successfully")
    print(f"   Response: {payload['body']}")


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
        
        # Check for our expected log message (S3 write success)
        log_messages = [event['message'] for event in events_response['events']]
        bucket_name = get_terraform_output('s3_bucket_name')
        assert any(f'Timestamp written to s3://{bucket_name}/timestamps/' in msg for msg in log_messages), \
            "Expected log message about S3 write not found in CloudWatch logs"
        
        print("✅ Lambda function logs to CloudWatch correctly")
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            raise AssertionError(f"CloudWatch log group '{log_group}' not found")
        raise


def test_eventbridge_rule_exists():
    """Test that EventBridge rule exists with correct configuration"""
    events_client = boto3.client('events', region_name='us-west-2')
    
    try:
        response = events_client.describe_rule(Name='scraper-hourly')
        
        assert response['Name'] == 'scraper-hourly'
        assert response['State'] == 'ENABLED', f"Expected rule to be ENABLED, got {response['State']}"
        assert response['ScheduleExpression'] == 'rate(1 minute)', \
            f"Expected 'rate(1 minute)', got '{response['ScheduleExpression']}'"
        
        print("✅ EventBridge rule exists with correct configuration")
        print(f"   Schedule: {response['ScheduleExpression']}")
        print(f"   State: {response['State']}")
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            raise AssertionError("EventBridge rule 'scraper-hourly' not found")
        raise


def test_eventbridge_target_configured():
    """Test that EventBridge rule has Lambda as target"""
    events_client = boto3.client('events', region_name='us-west-2')
    
    try:
        response = events_client.list_targets_by_rule(Rule='scraper-hourly')
        
        assert len(response['Targets']) == 1, \
            f"Expected 1 target, found {len(response['Targets'])}"
        
        target = response['Targets'][0]
        assert 'scraper' in target['Arn'], \
            f"Expected Lambda ARN to contain 'scraper', got {target['Arn']}"
        
        print("✅ EventBridge target configured correctly")
        print(f"   Target ARN: {target['Arn']}")
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            raise AssertionError("EventBridge rule 'scraper-hourly' not found")
        raise


def test_lambda_eventbridge_permission():
    """Test that Lambda has permission for EventBridge to invoke it"""
    lambda_client = boto3.client('lambda', region_name='us-west-2')
    
    try:
        response = lambda_client.get_policy(FunctionName='scraper')
        policy = json.loads(response['Policy'])
        
        # Check that there's a statement allowing EventBridge to invoke
        eventbridge_permissions = [
            stmt for stmt in policy['Statement']
            if stmt.get('Principal', {}).get('Service') == 'events.amazonaws.com'
            and stmt.get('Action') == 'lambda:InvokeFunction'
        ]
        
        assert len(eventbridge_permissions) > 0, \
            "No EventBridge invoke permission found in Lambda policy"
        
        print("✅ Lambda has EventBridge invoke permission")
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            raise AssertionError("Lambda function 'scraper' not found")
        raise


def test_s3_bucket_exists():
    """Test that S3 bucket exists"""
    s3_client = boto3.client('s3', region_name='us-west-2')
    
    # Get bucket name from Terraform output
    bucket_name = get_terraform_output('s3_bucket_name')
    
    try:
        response = s3_client.head_bucket(Bucket=bucket_name)
        print(f"✅ S3 bucket exists: {bucket_name}")
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            raise AssertionError(f"S3 bucket '{bucket_name}' not found")
        raise


def test_lambda_has_s3_environment_variable():
    """Test that Lambda has S3_BUCKET environment variable set"""
    lambda_client = boto3.client('lambda', region_name='us-west-2')
    
    try:
        response = lambda_client.get_function_configuration(FunctionName='scraper')
        
        env_vars = response.get('Environment', {}).get('Variables', {})
        assert 'S3_BUCKET' in env_vars, "S3_BUCKET environment variable not set"
        
        bucket_name = env_vars['S3_BUCKET']
        expected_bucket = get_terraform_output('s3_bucket_name')
        
        assert bucket_name == expected_bucket, \
            f"S3_BUCKET mismatch: expected '{expected_bucket}', got '{bucket_name}'"
        
        print(f"✅ Lambda has S3_BUCKET environment variable: {bucket_name}")
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            raise AssertionError("Lambda function 'scraper' not found")
        raise


def test_s3_file_content():
    """Test that Lambda writes correct content to S3 and verify by downloading"""
    lambda_client = boto3.client('lambda', region_name='us-west-2')
    s3_client = boto3.client('s3', region_name='us-west-2')
    
    bucket_name = get_terraform_output('s3_bucket_name')
    
    # Invoke Lambda to create a new timestamp file
    response = lambda_client.invoke(
        FunctionName='scraper',
        InvocationType='RequestResponse',
        Payload=json.dumps({})
    )
    
    # Parse response to get the S3 key
    payload = json.loads(response['Payload'].read())
    assert payload['statusCode'] == 200, f"Lambda invocation failed: {payload}"
    
    # Extract S3 key from response body
    # Example: "Timestamp written to s3://bucket-name/timestamps/2026-01-01T19:57:55.012744+00:00.txt"
    body = payload['body']
    assert 'timestamps/' in body, f"Expected S3 path in response, got: {body}"
    
    # Extract key from the message
    s3_key = body.split('timestamps/')[1].split('"')[0].strip()
    s3_key = f"timestamps/{s3_key}"
    
    # Download the file from S3
    try:
        obj_response = s3_client.get_object(Bucket=bucket_name, Key=s3_key)
        file_content = obj_response['Body'].read().decode('utf-8')
        
        # Verify content is a valid ISO format timestamp
        assert len(file_content) > 0, "File content is empty"
        assert 'T' in file_content, "Content doesn't look like an ISO timestamp"
        assert file_content.strip() in s3_key, \
            f"Timestamp in file '{file_content.strip()}' doesn't match key '{s3_key}'"
        
        print(f"✅ S3 file verified: {s3_key}")
        print(f"   Content: {file_content.strip()}")
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            raise AssertionError(f"S3 file not found: {s3_key}")
        raise


if __name__ == "__main__":
    print("Running infrastructure tests...\n")
    
    try:
        test_ecr_repository_exists()
        test_ecr_image_exists()
        test_lambda_function_exists()
        test_lambda_invocation()
        test_lambda_logs()
        test_eventbridge_rule_exists()
        test_eventbridge_target_configured()
        test_lambda_eventbridge_permission()
        test_s3_bucket_exists()
        test_lambda_has_s3_environment_variable()
        test_s3_file_content()
        
        print("\n🎉 All infrastructure tests passed!")
    except Exception as e:
        print(f"\n❌ Infrastructure test failed: {e}")
        exit(1)

