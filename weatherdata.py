import os
import xml.etree.ElementTree as ET
import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after=-1)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)  # Corrected retry usage
openmeteo = openmeteo_requests.Client(session=retry_session)

# Function to read earthquake Atom files from the folder
def read_earthquake_atom_files(folder_path):
    atom_files = []
    
    # List all files in the directory
    for filename in os.listdir(folder_path):
        if filename.endswith(".atom"):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, "r", encoding="utf-8") as file:
                atom_files.append(file.read())
    
    return atom_files

# Function to fetch weather data from Open-Meteo API
def fetch_weather_data(lat, lon, date):
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": date,
        "end_date": date,
        "daily": [
            "weather_code", "temperature_2m_max", "temperature_2m_min", "temperature_2m_mean",
            "apparent_temperature_max", "apparent_temperature_min", "apparent_temperature_mean",
            "sunrise", "daylight_duration", "sunshine_duration", "precipitation_sum", "rain_sum",
            "snowfall_sum", "precipitation_hours", "wind_speed_10m_max", "wind_gusts_10m_max",
            "wind_direction_10m_dominant"
        ],
        "timezone": "auto"
    }
    
    response = openmeteo.weather_api(url, params=params)
    if response:
        return response[0]  # Returning the first result
    return None

# Parse Atom File and extract earthquake info
def parse_atom_file(atom_content):
    tree = ET.ElementTree(ET.fromstring(atom_content))
    root = tree.getroot()
    
    earthquake_entries = []
    
    for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
        title = entry.find('{http://www.w3.org/2005/Atom}title').text
        updated = entry.find('{http://www.w3.org/2005/Atom}updated').text.split("T")[0]
        georss_point = entry.find('{http://www.georss.org/georss}point').text
        
        # Extract latitude and longitude from georss:point
        lat, lon = map(float, georss_point.split())
        
        earthquake_entries.append({
            'title': title,
            'updated': updated,
            'latitude': lat,
            'longitude': lon
        })
    
    return earthquake_entries

# Store weather data in XML format
def save_weather_data(weather_data, filename="weather_data.xml"):
    root = ET.Element("weather_data")
    for data in weather_data:
        entry = ET.SubElement(root, "entry")
        location = ET.SubElement(entry, "location")
        location.text = f"{data['latitude']},{data['longitude']}"
        
        weather = ET.SubElement(entry, "weather")
        for key, value in data['weather'].items():
            ET.SubElement(weather, key).text = str(value)
    
    tree = ET.ElementTree(root)
    tree.write(filename, encoding="utf-8", xml_declaration=True)
    print(f"Weather data saved to {filename}")

# Main processing function
def process_earthquake_weather_data(folder_path):
    # Read Atom files from the folder
    atom_data_list = read_earthquake_atom_files(folder_path)
    
    weather_data = []
    
    for atom_data in atom_data_list:
        # Parse Atom file
        earthquake_entries = parse_atom_file(atom_data)
        
        for entry in earthquake_entries:
            print(f"Fetching weather data for coordinates: {entry['latitude']}, {entry['longitude']} on {entry['updated']}")
            weather_info = fetch_weather_data(entry['latitude'], entry['longitude'], entry['updated'])
            
            if weather_info:
                weather_data.append({
                    'latitude': entry['latitude'],
                    'longitude': entry['longitude'],
                    'weather': {
                        'weather_code': weather_info.Daily().Variables(0).ValuesAsNumpy()[0],
                        'temperature_2m_max': weather_info.Daily().Variables(1).ValuesAsNumpy()[0],
                        'temperature_2m_min': weather_info.Daily().Variables(2).ValuesAsNumpy()[0],
                        'temperature_2m_mean': weather_info.Daily().Variables(3).ValuesAsNumpy()[0],
                        'apparent_temperature_max': weather_info.Daily().Variables(4).ValuesAsNumpy()[0],
                        'apparent_temperature_min': weather_info.Daily().Variables(5).ValuesAsNumpy()[0],
                        'apparent_temperature_mean': weather_info.Daily().Variables(6).ValuesAsNumpy()[0],
                        'daylight_duration': weather_info.Daily().Variables(8).ValuesAsNumpy()[0],
                        'sunshine_duration': weather_info.Daily().Variables(9).ValuesAsNumpy()[0],
                        'precipitation_sum': weather_info.Daily().Variables(10).ValuesAsNumpy()[0],
                        'rain_sum': weather_info.Daily().Variables(11).ValuesAsNumpy()[0],
                        'snowfall_sum': weather_info.Daily().Variables(12).ValuesAsNumpy()[0],
                        'precipitation_hours': weather_info.Daily().Variables(13).ValuesAsNumpy()[0],
                        'wind_speed_10m_max': weather_info.Daily().Variables(14).ValuesAsNumpy()[0],
                        'wind_gusts_10m_max': weather_info.Daily().Variables(15).ValuesAsNumpy()[0],
                        'wind_direction_10m_dominant': weather_info.Daily().Variables(16).ValuesAsNumpy()[0]
                    }
                })
    
    # Save the weather data to an XML file
    save_weather_data(weather_data)

# Running the code for the year range 2022-2024
folder_path = "user.atomfiles"  # Path to your folder with Atom files
process_earthquake_weather_data(folder_path)
