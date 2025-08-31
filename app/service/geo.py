import googlemaps
import requests
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

def get_temperature(lat, lon, timestamp):
    date = timestamp.split("T")[0]
    today = datetime.utcnow().strftime("%Y-%m-%d")
    
    if date < today:  # Historical (Archive API)
        weather_url = (
            f"https://archive-api.open-meteo.com/v1/archive?"
            f"latitude={lat}&longitude={lon}"
            f"&start_date={date}&end_date={date}"
            f"&daily=temperature_2m_max,temperature_2m_min"
            f"&timezone=UTC"
        )
    else:  # Forecast (Forecast API)
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}"
            f"&start_date={date}&end_date={date}"
            f"&daily=temperature_2m_max,temperature_2m_min"
            f"&timezone=UTC"
        )
        
    weather_data = requests.get(weather_url).json()
    temperature = 25
    if "daily" in weather_data and "temperature_2m_max" in weather_data["daily"]:
        t_max = weather_data["daily"]["temperature_2m_max"][0]
        t_min = weather_data["daily"]["temperature_2m_min"][0]
        temperature = (t_max + t_min) / 2
    return temperature



def get_place_info(place_name, api_key, date=None, use_google_elevation=False):
    """
    Get latitude, longitude, altitude, and temperature for a place and date.
    - place_name: Name of the place
    - api_key: Google Maps API key (for geocoding, optional for elevation)
    - date: 'YYYY-MM-DD' string (past = history, today/future = forecast)
    - use_google_elevation: If True, use Google Elevation API, else Open-Elevation
    """
    gmaps = googlemaps.Client(key=api_key)

    # Step 1: Geocoding
    geocode_result = gmaps.geocode(place_name)
    if not geocode_result:
        return None
    
    loc = geocode_result[0]['geometry']['location']
    lat, lon = loc['lat'], loc['lng']
    address = geocode_result[0]['formatted_address']

    # Step 2: Altitude
    altitude = None
    if use_google_elevation:
        try:
            elev_result = gmaps.elevation((lat, lon))
            altitude = elev_result[0]['elevation'] if elev_result else None
        except Exception as e:
            print("Google Elevation API failed:", e)

    if altitude is None:  # fallback to Open-Elevation
        url = f"https://api.open-elevation.com/api/v1/lookup?locations={lat},{lon}"
        response = requests.get(url).json()
        altitude = response["results"][0]["elevation"] if "results" in response else None

    # Step 3: Temperature (past vs future)
    print("Fetching temperature for date:", date, "at location:", lat, lon)
    temperature = get_temperature(lat, lon, f"{date}T12:00:00") if date else 25
    
    return {
        "lat": lat,
        "lon": lon,
        "address": address,
        "altitude_m": altitude,
        "temperature_C": temperature,
    }