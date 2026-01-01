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
        assert response['Configuration']['Timeout'] == 300
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
    
    # Check that response indicates scraper completed successfully
    bucket_name = get_terraform_output('s3_bucket_name')
    assert 'Scraper completed' in payload['body'], \
        f"Expected 'Scraper completed' in response, got '{payload['body']}'"
    assert 'lifts' in payload['body'], \
        f"Expected lift count in response, got '{payload['body']}'"
    
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
            limit=100
        )
        
        # Check for our expected log messages (scraper execution)
        log_messages = [event['message'] for event in events_response['events']]
        assert any('Scraper version' in msg for msg in log_messages), \
            "Expected 'Scraper version' log message not found in CloudWatch logs"
        assert any('Scraper completed' in msg for msg in log_messages), \
            "Expected 'Scraper completed' log message not found in CloudWatch logs"
        
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
    """Test that Lambda writes correct CSV content to S3 and verify by downloading"""
    lambda_client = boto3.client('lambda', region_name='us-west-2')
    s3_client = boto3.client('s3', region_name='us-west-2')
    
    bucket_name = get_terraform_output('s3_bucket_name')
    
    # Invoke Lambda to create new CSV files
    response = lambda_client.invoke(
        FunctionName='scraper',
        InvocationType='RequestResponse',
        Payload=json.dumps({})
    )
    
    # Parse response
    payload = json.loads(response['Payload'].read())
    assert payload['statusCode'] == 200, f"Lambda invocation failed: {payload}"
    
    # Wait a moment for S3 to be consistent
    time.sleep(2)
    
    # List files in bucket to find the most recent ones
    try:
        list_response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            MaxKeys=10
        )
        
        assert 'Contents' in list_response, "No files found in bucket"
        
        # Get the most recent status file
        status_files = [obj for obj in list_response['Contents'] if 'status_' in obj['Key']]
        assert len(status_files) > 0, "No status files found"
        
        latest_status = sorted(status_files, key=lambda x: x['LastModified'], reverse=True)[0]
        
        # Download and verify the status CSV
        obj_response = s3_client.get_object(Bucket=bucket_name, Key=latest_status['Key'])
        csv_content = obj_response['Body'].read().decode('utf-8')
        
        # Verify CSV structure
        assert 'Lift' in csv_content, "CSV doesn't contain 'Lift' column"
        assert 'Status' in csv_content, "CSV doesn't contain 'Status' column"
        lines = csv_content.strip().split('\n')
        assert len(lines) > 1, "CSV file has no data rows"
        
        print(f"✅ S3 file verified: {latest_status['Key']}")
        print(f"   Rows: {len(lines) - 1} (excluding header)")
        print(f"   Preview: {lines[0]}")
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchBucket':
            raise AssertionError(f"S3 bucket not found: {bucket_name}")
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

