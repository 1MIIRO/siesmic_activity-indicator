import os
import xml.etree.ElementTree as ET
import folium
import re
from folium.plugins import MarkerCluster
from datetime import datetime, timedelta

folder_path = "user.atomfiles"  

def parse_atom_files_by_place_and_date(folder_path, start_date, end_date, place):
    entries = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".atom"):
            file_path = os.path.join(folder_path, filename)
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
                title = entry.find("{http://www.w3.org/2005/Atom}title").text
                updated = entry.find("{http://www.w3.org/2005/Atom}updated").text
                point = entry.find("{http://www.georss.org/georss}point").text if entry.find("{http://www.georss.org/georss}point") is not None else None
                
                if title and updated and point:
                    title_parts = title.split()
                    location_in_title = title_parts[-1]  
                
                    if location_in_title.lower() == place.lower():
                        date = datetime.strptime(updated.split('T')[0], '%Y-%m-%d')
                        if start_date <= date <= end_date:
                            magnitude = None
                            match = re.search(r'M\s([-]?[\d\.]+)', title)  
                            if match:
                                try:
                                    magnitude = float(match.group(1))  
                                except ValueError as e:
                                    print(f"Error converting magnitude for {title}: {e}")
                                    continue
                            else:
                                print(f"No magnitude found in title for {title}")
                                continue
                            
                            entries.append((date, point, magnitude))  
    return entries

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

def plot_on_map(entries):
    m = folium.Map(location=[0, 0], zoom_start=2)
    
    marker_cluster = MarkerCluster().add_to(m)
    
    for date, point, magnitude in entries:
        lat, lon = map(float, point.split())
        marker_color = get_marker_color(magnitude)  
        
        folium.Marker(
            location=[lat, lon],
            popup=f"{date}<br>Magnitude: {magnitude}<br>Latitude: {lat}, Longitude: {lon}",
            icon=folium.Icon(color=marker_color, icon_size=(40, 40)) 
        ).add_to(marker_cluster)
    
    return m

def get_single_date(user_input):
    try:
        if user_input.lower() == "all":  # If the input is "all", select all available data
            # Use a very broad date range that encompasses all possible dates
            start_date = datetime(1900, 1, 1)  # Set a start date far in the past
            end_date = datetime.now()  # Set the end date as today
            return start_date, end_date
        elif len(user_input) == 7:  # If the input is in the format YYYY-MM (month precision)
            start_date = datetime.strptime(f"{user_input}-01", "%Y-%m-%d")
            end_date = (start_date.replace(day=28) + timedelta(days=4)) - timedelta(days=start_date.replace(day=28).day)
            return start_date, end_date
        elif len(user_input) == 4:  # If only year is entered (YYYY)
            start_date = datetime.strptime(f"{user_input}-01-01", "%Y-%m-%d")
            end_date = datetime.strptime(f"{user_input}-12-31", "%Y-%m-%d")
            return start_date, end_date
    except Exception as e:
        print(f"Error parsing date: {e}")
        return None, None

def get_date_range(start_date_input, end_date_input):
    try:
        start_date = datetime.strptime(start_date_input, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_input, "%Y-%m-%d")
        
        if start_date > end_date:
            print("Error: Start date cannot be later than the end date.")
            return None, None
        return start_date, end_date
    except Exception as e:
        print(f"Error parsing date range: {e}")
        return None, None

def main():
    choice = input("Would you like to view data for a single date or a date range? (Enter 'single' for a single date, 'range' for a date range): ").lower()

    if choice == 'single':
        user_input_date = input("Enter the date (YYYY, YYYY-MM, or 'all' for all data): ")
        start_date, end_date = get_single_date(user_input_date)
    elif choice == 'range':
        start_date_input = input("Enter the start date (YYYY-MM-DD): ")
        end_date_input = input("Enter the end date (YYYY-MM-DD): ")
        start_date, end_date = get_date_range(start_date_input, end_date_input)
    else:
        print("Invalid choice. Please enter 'single' or 'range'.")
        return

    if start_date and end_date:
        user_place = input("Enter the place (e.g., California): ")

        entries = parse_atom_files_by_place_and_date(folder_path, start_date, end_date, user_place)
        
        if entries:
            map_obj = plot_on_map(entries)
            map_obj.save("earthquake_map.html")
            print(f"Map has been saved to 'earthquake_map.html'. Showing entries for {user_place} between {start_date} and {end_date}.")
        else:
            print(f"No entries found for the place '{user_place}' within the date range {start_date} to {end_date}.")
    else:
        print("Invalid date range input.")

if __name__ == "__main__":
    main()
