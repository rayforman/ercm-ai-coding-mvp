#### #! DO NOT MODIFY THIS CODE #! ####

import requests

API_BASE_URL = "http://localhost:8000"

def test_api() -> dict:
    """
    Test the API by making a GET request to the test-view endpoint.

    :return: The JSON response from the test-view endpoint.
    :rtype: dict
    """
    response = requests.get(f"{API_BASE_URL}/app/test-view/")
    return response.json()


#### #! END OF DO NOT MODIFY THIS CODE #! ####

# Build your script here.

import os
import re
import json

def get_chart_schema() -> dict:
    """
    Get the chart schema from the API.

    :return: The API response.
    :rtype: dict
    """
    # We assume the Django server is running on the default local address
    url = "http://127.0.0.1:8000/app/chart-schema"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises an error for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to connect to API: {e}"}

def transform_chart_to_json() -> dict:
    """
    Transform a chart to a JSON object.

    :return: The JSON object of the chart.
    :rtype: dict
    """
    # Hardcoded file path
    file_path = "data/medical_chart.txt"
    
    if not os.path.exists(file_path):
        return {"error": "File not found"}

    with open(file_path, "r") as f:
        content = f.read()

    # Regex to identify Section Title, Note ID, and Content
    # Logic: Look for ALL CAPS title, then 'Note ID: <id>', then everything until next title
    pattern = r"([A-Z ]+)\nNote ID: ([\w-]+)\n(.*?)(?=\n[A-Z ]+\nNote ID:|$)"
    matches = re.findall(pattern, content, re.DOTALL)

    notes = []
    for title, note_id, text in matches:
        notes.append({
            "title": title.strip(),
            "note_id": note_id.strip(),
            "content": text.strip()
        })

    # The blueprint requires an idempotent identifier for the chart itself.
    # We can derive a chart ID from the first note ID (e.g., 'case12').
    external_chart_id = "unknown"
    if notes:
        # Splits 'note-hpi-case12' to get 'case12'
        external_chart_id = notes[0]['note_id'].split('-')[-1]

    return {
        "external_chart_id": external_chart_id,
        "notes": notes
    }

def upload_chart() -> dict:
    """
    Upload a chart to the API.

    :return: The API response.
    :rtype: dict
    """
    # 1. Transform the local data/medical_chart.txt into a JSON-compatible dict
    # This calls the parser we implemented previously.
    chart_json = transform_chart_to_json()
    
    if "error" in chart_json:
        return chart_json

    # 2. Define the hardcoded endpoint URL
    url = "http://127.0.0.1:8000/app/upload-chart"
    
    try:
        # 3. Send the POST request with the JSON payload
        response = requests.post(url, json=chart_json)
        response.raise_for_status()
        
        # This will return the {"message": "...", "count": ...} object defined in your view
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"API Upload failed: {e}"}

def list_charts() -> dict:
    """
    List all the charts in the API.

    :return: The API response.
    :rtype: dict
    """
    # We assume the Django server is running on the default local address
    url = "http://127.0.0.1:8000/app/charts"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises an error for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to retrieve charts: {e}"}

def code_chart() -> dict:
    """
    Code a chart using the API.

    :return: The API response.
    :rtype: dict
    """
    pass


#### #! DO NOT MODIFY THIS CODE #! ####

def build_output() -> str:
    """
    Print the output of the script.
    """

    print("##### OUTPUT GENERATION #####")
    print()
    
    print("Test Output:")
    print()
    print(test_api())

    print()
    print("--------------------------------")
    print()

    print("1. Chart Schema:")
    print()
    print(get_chart_schema())

    print()
    print("--------------------------------")
    print()

    print("2. Chart to JSON:")
    print()
    print(transform_chart_to_json())

    print()
    print("--------------------------------")
    print()

    print("3. Upload Chart:")
    print()
    print(upload_chart())

    print()
    print("--------------------------------")
    print()

    print("4. List Charts:")
    print()
    print(list_charts())

    print()
    print("--------------------------------")
    print()

    print("5. Code Chart:")
    print()
    print(code_chart())

    print()
    print("--------------------------------")
    print()

    print("##### END OF OUTPUT GENERATION #####")

build_output()

#### #! END OF DO NOT MODIFY THIS CODE #! ####
