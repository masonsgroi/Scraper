import requests
import json
import pandas as pd

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
data1 = fetch_json_from_url("https://vicomap-cdn.resorts-interactive.com/api/maps/152")
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
    print(f"Lift: {name}, Status: {status}, Wait Time: {wait_time} minutes")
def filter_data(first_data, second_data):
    #merge data from two jsons
    lifts1 = first_data.get("lifts", [])
    lifts2 = second_data.get("lifts", [])
    combined_lifts = lifts1 + lifts2
    rows=[]
     # format into row for each lift
    for lift in combined_lifts:
        name = lift.get("name", "Unknown")
        status = lift.get("status", "Unknown")
        wait_time = lift.get("waitTime", "N/A")
        rows.append({"Lift": name, "Status": status, "Wait Time (minutes)": wait_time})
    return rows

def json_to_csv(json_data):
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
    filename = pd.Timestamp.now().strftime("data_%Y%m%d_%H%M%S.csv")
    filename = path_string + filename
    df.to_csv(filename, index=False)
    print(f"Data saved to {filename}")
    return df
rows=filter_data(data1, data2)
json_to_csv(rows)