import folium
import xml.etree.ElementTree as ET
import re
from folium import IFrame

# Function to get the weather icon URL from OpenWeatherMap
def get_weather_icon_url(icon_code):
    return f"http://openweathermap.org/img/wn/{icon_code}@2x.png"

# Function to get the wind direction based on the angle
def get_wind_direction(degree):
    if 0 <= degree <= 22.5 or degree > 337.5:
        return "North (N)"
    elif 22.5 < degree <= 67.5:
        return "North-East (NE)"
    elif 67.5 < degree <= 112.5:
        return "East (E)"
    elif 112.5 < degree <= 157.5:
        return "South-East (SE)"
    elif 157.5 < degree <= 202.5:
        return "South (S)"
    elif 202.5 < degree <= 247.5:
        return "South-West (SW)"
    elif 247.5 < degree <= 292.5:
        return "West (W)"
    elif 292.5 < degree <= 337.5:
        return "North-West (NW)"

# Function to calculate sunshine duration in hours
def get_sunshine_duration(sunshine_seconds):
    return sunshine_seconds / 3600  # Convert from seconds to hours

# Function to get magnitude color based on magnitude
def get_marker_color(magnitude):
    if magnitude >= 5:
        return 'red'
    elif 3 <= magnitude < 5:
        return 'orange'
    elif 1.5 <= magnitude < 3:
        return 'purple'
    elif magnitude < 1.5:
        return 'green'
    else:
        return 'blue'

# Function to safely extract data from XML (e.g., location, magnitude, etc.)
def safe_find(entry, tag, namespaces=None, default_value=0.0):
    try:
        element = entry.find(tag, namespaces) if namespaces else entry.find(tag)
        return element.text if element is not None else default_value
    except Exception as e:
        print(f"Error extracting {tag}: {e}")
        return default_value

# Parse the Atom file containing earthquake data
def parse_atom_file(file_path):
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        print(f"Atom file '{file_path}' parsed successfully.")
        return root
    except Exception as e:
        print(f"Error parsing Atom file: {e}")
        return None

# Parse the XML file containing weather data
def parse_xml_file(file_path):
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        print(f"XML file '{file_path}' parsed successfully.")
        return root
    except Exception as e:
        print(f"Error parsing XML file: {e}")
        return None

# Create a map centered at an average location
weather_map = folium.Map(location=[30.3753, 69.3451], zoom_start=6)

# Parse the XML file containing weather data
weather_data = parse_xml_file('formatted_output.xml')
if not weather_data:
    exit()

# Parse the Atom file containing earthquake data
earthquake_data = parse_atom_file('user.atomfiles/earthquake_data_2024-12-30_2024-12-31.atom')
if not earthquake_data:
    exit()

# Define namespaces for both Atom and Georss
namespaces = {
    '': 'http://www.w3.org/2005/Atom',   # Default namespace for Atom
    'ns0': 'http://www.georss.org/georss' # Georss namespace for point
}

# Iterate over each entry in the XML file and add markers on the map
for entry in weather_data.findall('entry'):
    # Extract location (latitude, longitude) from the XML
    location_str = safe_find(entry, 'location', default_value=None)
    if location_str is None:
        continue  # Skip if no location data exists
    
    try:
        latitude, longitude = map(float, location_str.split(','))
    except ValueError:
        print(f"Skipping entry with invalid location: {location_str}")
        continue

    # Extract weather-related data from the XML entry
    rain_sum = float(safe_find(entry, './/rain_sum', default_value=0.0))
    wind_speed = float(safe_find(entry, './/wind_speed_10m_max', default_value=0.0))
    wind_direction = float(safe_find(entry, './/wind_direction_10m_dominant', default_value=0.0))
    sunshine_duration = float(safe_find(entry, './/sunshine_duration', default_value=0.0))
    snowfall_sum = float(safe_find(entry, './/snowfall_sum', default_value=0.0))
    temp_max = float(safe_find(entry, './/temperature_2m_max', default_value=0.0))
    temp_min = float(safe_find(entry, './/temperature_2m_min', default_value=0.0))
    temp_mean = float(safe_find(entry, './/temperature_2m_mean', default_value=0.0))
    precipitation_hours = float(safe_find(entry, './/precipitation_hours', default_value=0.0))
    icon_code = safe_find(entry, './/weather/weather_code', default_value='01d')  # Default to 'clear' if no code found

    # Calculate values for wind direction and sunshine duration
    wind_direction_str = get_wind_direction(wind_direction)
    sunshine_hours = get_sunshine_duration(sunshine_duration)

    # Print the current entry data for debugging
    print(f"Processing weather entry at ({latitude}, {longitude}) - Rain: {rain_sum} mm, Wind Speed: {wind_speed} km/h")

    # Create the HTML content for the table in the popup
    popup_content = f"""
    <table border="1" cellpadding="5" cellspacing="0">
        <tr><td colspan="2"><strong>Weather Data</strong></td></tr>
        <tr><td>Weather</td><td>Rainfall Sum: {rain_sum} mm</td></tr>
        <tr><td>Rain Icon</td><td><img src="{get_weather_icon_url('10d')}" alt="Rain" width="40" height="40"></td></tr>
        <tr><td>Duration of Downpour</td><td>{precipitation_hours} hours</td></tr>
        <tr><td>Wind Speed</td><td>{wind_speed} km/h</td></tr>
        <tr><td>Wind Direction</td><td>{wind_direction_str}</td></tr>
        <tr><td>Wind Icon</td><td><img src="{get_weather_icon_url('50d')}" alt="Wind" width="40" height="40"></td></tr>
        <tr><td>Snowfall</td><td>{snowfall_sum} mm</td></tr>
        <tr><td>Snow Icon</td><td><img src="{get_weather_icon_url('13d')}" alt="Snow" width="40" height="40"></td></tr>
        <tr><td>Sunshine Duration</td><td>{sunshine_hours} hours</td></tr>
        <tr><td>Sunshine Icon</td><td><img src="https://img.icons8.com/ios-filled/50/000000/sun.png" alt="Sunshine" width="40" height="40"></td></tr>
        <tr><td>Max Temperature</td><td>{temp_max}°C</td></tr>
        <tr><td>Min Temperature</td><td>{temp_min}°C</td></tr>
        <tr><td>Avg Temperature</td><td>{temp_mean}°C</td></tr>
        <tr><td>Temperature Icon</td><td><img src="https://img.icons8.com/ios-filled/50/000000/temperature.png" alt="Temperature" width="40" height="40"></td></tr>
    </table>
    """

    # Add magnitude value in the table (parse from Atom file)
    for atom_entry in earthquake_data.findall('{http://www.w3.org/2005/Atom}entry'):
        # Extract the coordinates from the Atom feed entry
        point = safe_find(atom_entry, '{http://www.georss.org/georss}point', namespaces=namespaces)
        if point != "N/A":
            lat_lon = point.split()
            lat, lon = map(float, lat_lon)
            
            # Debugging: Print matching coordinates
            print(f"Checking coordinates: Weather ({latitude}, {longitude}) - Atom ({lat}, {lon})")

            # Check if coordinates match the weather entry
            if latitude == lat and longitude == lon:
                # Extract magnitude from the Atom entry
                title = safe_find(atom_entry, '{http://www.w3.org/2005/Atom}title', namespaces=namespaces)
                magnitude_match = re.search(r'M\s([\d\.]+)', title)
                if magnitude_match:
                    magnitude = float(magnitude_match.group(1))
                    print(f"Matching coordinates found! Magnitude: {magnitude}")
                else:
                    magnitude = 0.0  # Default value if no magnitude found

                # Determine marker color based on magnitude
                marker_color = get_marker_color(magnitude)

                # Add marker to map with popup
                folium.Marker(
                    [latitude, longitude],
                    popup=popup_content,
                    icon=folium.Icon(color=marker_color)
                ).add_to(weather_map)

# Save the map to an HTML file
weather_map.save("weather_map_with_earthquake_magnitudes.html")
print("Map has been saved as 'weather_map_with_earthquake_magnitudes.html'. Open this file in a browser to view the map.")
