import requests
import json
import pandas as pd

#create dataframe from existing csv file, append new data to it, save as new csv file
#read csv file into dataframe
def read_csv_to_dfs():
    status = pd.read_csv('/Users/masonsgroi/Desktop/Scraper_Output/status.csv')
    wait_time = pd.read_csv('/Users/masonsgroi/Desktop/Scraper_Output/wait_time.csv')
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


def fetch_json_from_url(url):
    """
    Fetch JSON data from a given URL.

    Args:
        url (str): The URL to fetch JSON data from.

    Returns:
        dict: Parsed JSON data.
    """
    response = requests.get(url)
    response.raise_for_status()  # Raise an error for bad responses
    return response.json()
# Usage: Lift ride times and status
""" data1 = fetch_json_from_url("https://vicomap-cdn.resorts-interactive.com/api/maps/152")
lifts = data1.get("lifts", [])
for lift in lifts:
    name = lift.get("name", "Unknown")
    status = lift.get("status", "Unknown")
    wait_time = lift.get("waitTime", "N/A")
    print(f"Lift: {name}, Status: {status}, Wait Time: {wait_time} minutes")
data2 = fetch_json_from_url("https://vicomap-cdn.resorts-interactive.com/api/maps/1446")
lifts = data2.get("lifts", [])
for lift in lifts:
    name = lift.get("name", "Unknown")
    status = lift.get("status", "Unknown")
    wait_time = lift.get("waitTime", "N/A")
    print(f"Lift: {name}, Status: {status}, Wait Time: {wait_time} minutes") """


def filter_status_data(first_data, second_data):
    #merge data from two jsons
    lifts1 = first_data.get("lifts", [])
    lifts2 = second_data.get("lifts", [])
    combined_lifts = lifts1 + lifts2
    rows=[]
     # format into row for each lift
     # specify date above column
     # each row is one lift
    for lift in combined_lifts:
        name = lift.get("name", "Unknown")
        status = lift.get("status", "Unknown")
        rows.append({"Lift": name, "Status": status})
    return rows

def filter_wait_time_data(first_data, second_data):
    #merge data from two jsons
    lifts1 = first_data.get("lifts", [])
    lifts2 = second_data.get("lifts", [])
    combined_lifts = lifts1 + lifts2
    rows=[]
     # format into row for each lift
     # specify date above column
     # each row is one lift
    for lift in combined_lifts:
        name = lift.get("name", "Unknown")
        wait_time = lift.get("waitTime", "N/A")
        rows.append({"Lift": name, "Wait Time": wait_time})
    return rows

def json_to_csv(json_data,extension):
    """
    Convert JSON data to a pandas DataFrame and save it as a CSV file.
    file named current date and time.
    Args:
        json_data (dict): The JSON data to convert.

    Returns:
        pd.DataFrame: The resulting DataFrame.
    """
    path_string = "/Users/masonsgroi/Desktop/Scraper_Output/"
    df = pd.json_normalize(json_data)
    full_filename = path_string + extension + ".csv"
    df.to_csv(full_filename, index=False)
    print(f"Data saved to {full_filename}")
    return df

add_data_to_dfs(read_csv_to_dfs())