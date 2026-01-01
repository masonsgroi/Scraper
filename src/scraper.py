import boto3
import pandas as pd
import requests
import json
import os
from datetime import datetime, timezone
from io import StringIO


def get_version():
    """Read version from VERSION file"""
    try:
        with open('VERSION', 'r') as f:
            return f.read().strip()
    except Exception:
        return 'unknown'


def fetch_json_from_url(url):
    """Fetch JSON data from URL with proper headers"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36'
    }
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()


def scrape_lift_data():
    """Scrape lift data from ski resort APIs"""
    # URLs for the two ski resorts
    urls = [
        "https://vicomap-cdn.resorts-interactive.com/api/maps/152",
        "https://vicomap-cdn.resorts-interactive.com/api/maps/1446"
    ]
    
    status_data = []
    wait_time_data = []
    
    for url in urls:
        try:
            data = fetch_json_from_url(url)
            lifts = data.get("lifts", [])
            
            for lift in lifts:
                name = lift.get("name", "Unknown")
                status = lift.get("status", "Unknown")
                wait_time = lift.get("waitTime", "N/A")
                
                print(f"Lift: {name}, Status: {status}, Wait Time: {wait_time} minutes")
                
                status_data.append({"Lift": name, "Status": status})
                wait_time_data.append({"Lift": name, "Wait Time": wait_time})
                
        except Exception as e:
            print(f"Error fetching data from {url}: {e}")
            continue
    
    # Create DataFrames
    status_df = pd.DataFrame(status_data)
    wait_time_df = pd.DataFrame(wait_time_data)
    
    return status_df, wait_time_df


def upload_df_to_s3(df, bucket_name, s3_key):
    """Upload DataFrame as CSV to S3"""
    s3_client = boto3.client('s3')
    
    # Convert DataFrame to CSV string
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_content = csv_buffer.getvalue()
    
    # Upload to S3
    s3_client.put_object(
        Bucket=bucket_name,
        Key=s3_key,
        Body=csv_content,
        ContentType='text/csv'
    )
    
    print(f"Uploaded {s3_key} to s3://{bucket_name}/{s3_key}")


def lambda_handler(event, context):
    """
    AWS Lambda handler function that scrapes ski resort data and writes to S3.
    
    Args:
        event: Event data passed to the function
        context: Runtime information provided by AWS Lambda
        
    Returns:
        dict: Response with statusCode and body
    """
    # Get version
    version = get_version()
    print(f"Scraper version {version}")
    
    # Get S3 bucket name from environment variable
    bucket_name = os.environ.get('S3_BUCKET')
    
    if not bucket_name:
        error_msg = "S3_BUCKET environment variable not set"
        print(f"ERROR: {error_msg}")
        return {
            'statusCode': 500,
            'body': error_msg
        }
    
    # Generate timestamp for filenames
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    
    try:
        # Scrape data
        print("Starting scrape...")
        status_df, wait_time_df = scrape_lift_data()
        
        # Generate S3 keys
        status_key = f"data/status_{timestamp}.csv"
        wait_time_key = f"data/wait_time_{timestamp}.csv"
        
        # Upload to S3
        upload_df_to_s3(status_df, bucket_name, status_key)
        upload_df_to_s3(wait_time_df, bucket_name, wait_time_key)
        
        success_msg = f"Scraper completed. Uploaded {len(status_df)} lifts to s3://{bucket_name}/data/"
        print(success_msg)
        
        return {
            'statusCode': 200,
            'body': success_msg
        }
        
    except Exception as e:
        error_msg = f"Scraper failed: {str(e)}"
        print(f"ERROR: {error_msg}")
        return {
            'statusCode': 500,
            'body': error_msg
        }

