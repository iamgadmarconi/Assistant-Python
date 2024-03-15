import requests
import os
import geocoder
from geopy.geocoders import Nominatim
from typing import Optional
from datetime import datetime
import datefinder
from geotext import GeoText
import spacy
import dateparser


def getLocation():
    g = geocoder.ip('me').city
    geolocator = Nominatim(user_agent="User")
    location = geolocator.geocode(g)
    return location


def getWeather(msg: str):
    api_key = os.environ.get("OPENWEATHER_API_KEY")

    nlp = spacy.load("en_core_web_sm")

    doc = nlp(msg)

    times = [ent.text for ent in doc.ents if ent.label_ in ["TIME", "DATE"]]
    locations = [ent.text for ent in doc.ents if ent.label_ == "GPE"]

    time = " ".join(times)
    location = " ".join(locations)

    if location == "":
        location = getLocation()
        lat, lon = location.latitude, location.longitude

    else:
        location = GeoText(location).cities

        geolocator = Nominatim(user_agent="User")
        location = geolocator.geocode(location[0])
        lat = location.latitude
        lon = location.longitude

    try:
        time = dateparser.parse(time).timestamp()

    except:
        print("\nThe date range is outside the range of the API\n Using the current time instead\n")
        time = datetime.now().timestamp()
        
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}"

    response = requests.get(url)

    if response.status_code == 200:
        # Successful API call
        data = response.json()

        match = min(data['list'], key=lambda x: abs(x['dt'] - int(time)))
        main = match['main']

        temperature = main['temp']
        humidity = main['humidity']
        weather_description = match['weather'][0]['description']
        
        weather_report = (f"Location: {location}\n"
                          f"Time: {datetime.fromtimestamp(time)}\n"
                          f"Temperature: {temperature - 273.15}°C\n"
                          f"Humidity: {humidity}%\n"
                          f"Description: {weather_description.capitalize()}")
        return weather_report
    else:
        # API call failed this usually happens if the API key is invalid or not provided
        return f"Failed to retrieve weather data: {response.status_code}"