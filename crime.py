# backend to produce top 5 closest crimes that happened in the week

import requests
from bs4 import BeautifulSoup
import pandas as pd
import folium
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import geocoder

# 1. Get all weekly log links from archive
def get_archive_links():
    archive_url = "https://www.purdue.edu/ehps/police/statistics-policies/daily-crime-log-archives/"
    resp = requests.get(archive_url)
    if resp.status_code != 200:
        print("Error fetching archive:", resp.status_code)
        return []
    
    soup = BeautifulSoup(resp.text, 'lxml')
    links = []
    # Inspect the archive page HTML: likely a list of <a href="...">Week of ...</a>
    for a in soup.find_all('a', href=True):
        href = a['href']
        text = a.get_text().strip()
        
        # Filter for weekly log pages; e.g., "Week of September 8" or similar
        if "Week of" in text:
            # Make full URL if relative
            full_url = href
            if not href.lower().startswith("http"):
                full_url = requests.compat.urljoin(archive_url, href)
            links.append({"text": text, "url": full_url})

# 2. Fetch a specific crime log (weekly page)
def fetch_crime_log(week_url):
    resp = requests.get(week_url)
    if resp.status_code != 200:
        print(f"Error fetching crime log {week_url}:", resp.status_code)
        return None
    return resp.text

# 3. Parse crime log HTML into structured incidents
def parse_crime_log(html):
    soup = BeautifulSoup(html, 'lxml')
    table = soup.find('table')
    if table is None:
        print("No table found on page.")
        return []
    
    rows = table.find_all('tr')
    if not rows:
        return []
    
    # Get headers
    header_row = rows[0]
    headers = [th.text.strip() for th in header_row.find_all('th')]
    
    incidents = []
    for row in rows[1:]:
        cols = [td.text.strip() for td in row.find_all('td')]
        if len(cols) != len(headers):
            # Skip malformed rows
            continue
        data = dict(zip(headers, cols))
        incidents.append(data)
    return incidents


# 4. (Optional) Geocode the incident general location
def geocode_location(location_name, cache={}):
    # Use a cache dict to avoid repeated lookups
    if location_name in cache:
        return cache[location_name]
    geolocator = Nominatim(user_agent="wl_incident_mapper")
    try:
        loc = geolocator.geocode(f"{location_name}, West Lafayette, Indiana")
        if loc:
            coords = (loc.latitude, loc.longitude)
            cache[location_name] = coords
            return coords
    except Exception as e:
        print("Geocode error:", e)
    cache[location_name] = None
    return None

def incidents_with_coords(incidents):
    out = []
    for inc in incidents:
        loc_name = inc.get("General Location", "")
        coords = geocode_location(loc_name)
        if coords:
            inc["lat_lon"] = coords
            out.append(inc)
    return out

# 5. Filter by proximity to a point of interest
def filter_by_distance(incidents, center_coord, max_miles=1.0):
    filtered = []
    for inc in incidents:
        if "lat_lon" not in inc:
            continue
        dist = geodesic(center_coord, inc["lat_lon"]).miles
        if dist <= max_miles:
            inc["distance_miles"] = dist
            filtered.append(inc)
    return filtered

# 6. Plot on map
def plot_incidents_map(incidents, center_coord=(40.4230, -86.9210)):
    m = folium.Map(location=center_coord, zoom_start=15)
    for inc in incidents:
        lat, lon = inc["lat_lon"]
        desc = inc.get("Nature", "Unknown")
        popup_text = f"{desc} at {inc.get('General Location', '')}, {inc.get('Date/Time Occurred','')}"
        folium.Marker(
            location=[lat, lon],
            popup=popup_text,
            icon=folium.Icon(color='red')
        ).add_to(m)
    return m

# 7. Get user coordinates
def get_coords_from_google(location_name, api_key):
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": f"{location_name}, West Lafayette, IN",
        "key": api_key
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    if data["status"] != "OK" or not data["results"]:
        print(f"Could not geocode '{location_name}'. Error: {data['status']}")
        return None
    
    result = data["results"][0]
    lat = result["geometry"]["location"]["lat"]
    lon = result["geometry"]["location"]["lng"]
    return (lat, lon)

# A. Get archive links
archive_links = get_archive_links()
print("Found weekly logs:", [l["text"] for l in archive_links])

# B. Prompt for user location
user_place = input("Enter your current location (e.g., 'Shreve Hall'): ")
api_key = "AIzaSyD-Z4Mg13JZ7ivLjwYzemRsjPKwzpx6yf8"

user_location = get_coords_from_google(user_place, api_key)
if user_location:
    print(f"Coordinates for '{user_place}': {user_location}")
else:
    print("Could not find location. Falling back to campus center.")
    user_location = (40.4230, -86.9210)

# C. Print closest crimes
if archive_links:
    # Pick the most recent archive link
    most_recent = archive_links[0]  # Make sure archive_links is sorted by date descending

    # Fetch and parse the crime log HTML from that URL
    html = fetch_crime_log(most_recent["url"])
    if not html:
        print("Failed to fetch HTML from the crime log URL.")
    else:
        # Extract incidents from the HTML
        incidents = parse_crime_log(html)
        if not incidents:
            print("No incidents found in the crime log.")
        else:
            # Geocode incident locations to lat/lon
            incidents_geo = incidents_with_coords(incidents)
            if not incidents_geo:
                print("No incidents with geocodable locations.")
            else:
                # Filter incidents by distance from user location
                nearby = filter_by_distance(incidents_geo, user_location, max_miles=1.0)
                if not nearby:
                    print("No incidents found within 1.0 mile of your location.")
                else:
                    # Create DataFrame
                    df_near = pd.DataFrame(nearby)

                    # Drop unwanted columns if they exist
                    columns_to_drop = ["Case Number", "lat_lon"]
                    df_near = df_near.drop(columns=[col for col in columns_to_drop if col in df_near.columns])

                    # Sort by proximity
                    if "distance_miles" in df_near.columns:
                        df_near = df_near.sort_values("distance_miles")

                    # Display table and map
                    display(df_near)
                    map_viz = plot_incidents_map(nearby, center_coord=user_location)
                    map_viz
else:
    print("No archive links found. Check that the archive_links list was populated.")

    return links
