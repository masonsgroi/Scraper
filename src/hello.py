import boto3
import os
from datetime import datetime, timezone


def lambda_handler(event, context):
    """
    AWS Lambda handler function that writes a timestamp to S3.
    
    Args:
        event: Event data passed to the function
        context: Runtime information provided by AWS Lambda
        
    Returns:
        dict: Response with statusCode and body
    """
    # Get S3 bucket name from environment variable
    bucket_name = os.environ.get('S3_BUCKET')
    
    if not bucket_name:
        error_msg = "S3_BUCKET environment variable not set"
        print(f"ERROR: {error_msg}")
        return {
            'statusCode': 500,
            'body': error_msg
        }
    
    # Generate timestamp
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # Write timestamp to S3
    s3_client = boto3.client('s3')
    key = f"timestamps/{timestamp}.txt"
    
    try:
        s3_client.put_object(
            Bucket=bucket_name,
            Key=key,
            Body=timestamp,
            ContentType='text/plain'
        )
        
        success_msg = f"Timestamp written to s3://{bucket_name}/{key}"
        print(success_msg)
        
        return {
            'statusCode': 200,
            'body': success_msg
        }
        
    except Exception as e:
        error_msg = f"Failed to write to S3: {str(e)}"
        print(f"ERROR: {error_msg}")
        return {
            'statusCode': 500,
            'body': error_msg
        }

