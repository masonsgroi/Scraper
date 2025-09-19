#save csv file to aws s3 bucket
import boto3
import pandas as pd
import requests
import json

def read_csv_to_dfs():
    #change to AWS later !!!!!!!!!!!!!!!!!!!!!!!!!
    
    status = pd.read_csv('/home/masonsgroi/status.csv')
    wait_time = pd.read_csv('/home/masonsgroi/wait_time.csv')
    return status, wait_time

def add_data_to_dfs(dfs):
    data1 = fetch_json_from_url("https://vicomap-cdn.resorts-interactive.com/api/maps/152")
    lifts = data1.get("lifts", [])

    first=dfs[0]
    second=dfs[1]

    for lift in lifts:
        name = lift.get("name", "Unknown")
        status = lift.get("status", "Unknown")
        wait_time = lift.get("waitTime", "N/A")
        print(f"Lift: {name}, Status: {status}, Wait Time: {wait_time} minutes")
        first=pd.concat([dfs[0], pd.DataFrame([{"Lift": name, "Status": status}])], ignore_index=True)
        second=pd.concat([dfs[1], pd.DataFrame([{"Lift": name, "Wait Time": wait_time}])], ignore_index=True)
    data2 = fetch_json_from_url("https://vicomap-cdn.resorts-interactive.com/api/maps/1446")
    lifts = data2.get("lifts", [])
    for lift in lifts:
        name = lift.get("name", "Unknown")
        status = lift.get("status", "Unknown")
        wait_time = lift.get("waitTime", "N/A")
        print(f"Lift: {name}, Status: {status}, Wait Time: {wait_time} minutes")
        first=pd.concat([dfs[0], pd.DataFrame([{"Lift": name, "Status": status}])], ignore_index=True)
        second=pd.concat([dfs[1], pd.DataFrame([{"Lift": name, "Wait Time": wait_time}])], ignore_index=True)
    #read datafram into csv file
    first.to_csv('status.csv', index=False)
    second.to_csv('wait_time.csv', index=False)
    print("Data appended and saved to CSV files.")
    return

def fetch_json_from_url(url):
    headers = {'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36'}
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Raise an error for bad responses
    return response.json()

def upload_to_s3(file_name, bucket, object_name=None):  
    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name

    # Upload the file
    s3_client = boto3.client('s3')
    try:
        s3_client.upload_file(file_name, bucket, object_name)
    except Exception as e:
        print(f"Error uploading {file_name} to {bucket}/{object_name}: {e}")
        return False
    return True

add_data_to_dfs(read_csv_to_dfs())