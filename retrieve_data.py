import requests
import json
import os
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from xml.dom import minidom 

os.makedirs('user.atomfiles', exist_ok=True)

def json_to_atom(json_data, feed_title="USGS Earthquake Feed", feed_link="https://earthquake.usgs.gov/"):
    namespaces = {
        '': 'http://www.w3.org/2005/Atom',
        'georss': 'http://www.georss.org/georss' 
    }
    
    feed = ET.Element('feed', xmlns='http://www.w3.org/2005/Atom', xmlns_georss='http://www.georss.org/georss')
    
    title = ET.SubElement(feed, 'title')
    title.text = feed_title
    
    updated = ET.SubElement(feed, 'updated')
    updated.text = datetime.now(timezone.utc).isoformat() 
    
    id = ET.SubElement(feed, 'id')
    id.text = feed_link
    
    link = ET.SubElement(feed, 'link', rel="self", href=feed_link)
    
    author = ET.SubElement(feed, 'author')
    name = ET.SubElement(author, 'name')
    name.text = "U.S. Geological Survey"
    uri = ET.SubElement(author, 'uri')
    uri.text = "http://earthquake.usgs.gov/"
    
    icon = ET.SubElement(feed, 'icon')
    icon.text = "http://earthquake.usgs.gov/favicon.ico"
    
    for feature in json_data['features']:
        entry = ET.SubElement(feed, 'entry')
        
        entry_id = ET.SubElement(entry, 'id')
        entry_id.text = f"urn:earthquake-usgs-gov:{feature['properties']['net']}:{feature['properties']['code']}"
        
        entry_title = ET.SubElement(entry, 'title')
        entry_title.text = feature['properties']['title']
        
        entry_updated = ET.SubElement(entry, 'updated')
        entry_updated.text = datetime.fromtimestamp(feature['properties']['time'] / 1000, tz=timezone.utc).isoformat()
        
        entry_link = ET.SubElement(entry, 'link', rel="alternate", type="text/html", href=feature['properties']['url'])
        
        georss_point = ET.SubElement(entry, '{http://www.georss.org/georss}point')
        georss_point.text = f"{feature['geometry']['coordinates'][1]} {feature['geometry']['coordinates'][0]}"
        
        georss_elev = ET.SubElement(entry, '{http://www.georss.org/georss}elev')
        georss_elev.text = str(feature['geometry']['coordinates'][2])
        
        category = ET.SubElement(entry, 'category', label="Magnitude", term=f"Magnitude {feature['properties']['mag']}")

    return feed

def download_earthquake_data(start_date, end_date, file_format='geojson'):
    url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format={file_format}&starttime={start_date}&endtime={end_date}"
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.json() 
    else:
        print(f"Failed to retrieve data for {start_date} to {end_date}. HTTP Status Code: {response.status_code}")
        return None

def save_atom_file(atom_data, file_name):
    tree = ET.ElementTree(atom_data)
    
    atom_file_path = os.path.join('user.atomfiles', file_name)
    tree.write(atom_file_path, encoding='utf-8', xml_declaration=True)

    with open(atom_file_path, 'r+', encoding='utf-8') as file:
        xml_str = file.read()
        xml_str = minidom.parseString(xml_str).toprettyxml()
        file.seek(0)
        file.write(xml_str)
        
    print(f"Atom file saved as {atom_file_path}")

def process_monthly_data():
    start_month = datetime(2024, 12,30)
    end_month = datetime(2024, 12, 31)

    while start_month < end_month:
        month_start = start_month.strftime('%Y-%m-%d')
        month_end = (start_month + timedelta(days=31)).replace(day=1).strftime('%Y-%m-%d')

        if month_end > end_month.strftime('%Y-%m-%d'):
            month_end = end_month.strftime('%Y-%m-%d')

        data = download_earthquake_data(month_start, month_end, 'geojson')

        if data:
            atom_data = json_to_atom(data)
            save_atom_file(atom_data, f"earthquake_data_{month_start}_{month_end}.atom")
        else:
            print(f"No data found for {month_start} to {month_end}.")
        
        start_month = (start_month.replace(day=1) + timedelta(days=31)).replace(day=1)

    print("Data download and conversion complete!")

process_monthly_data()
