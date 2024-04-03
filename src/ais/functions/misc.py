import requests
import os
import dateparser
import geocoder

from geopy.geocoders import Nominatim
from typing import Optional
from datetime import datetime
from geotext import GeoText

from src.utils.tools import get_context


def getDate():
    return datetime.now().strftime("%d/%m/%Y, %H:%M:%S")


def getLocation():
    g = geocoder.ip("me").city
    geolocator = Nominatim(user_agent="User")
    location = geolocator.geocode(g)
    return location.address


def getWeather(msg: Optional[str] = None):
    # print(f"Debug--- Called getWeather with parameters: {msg}")
    api_key = os.environ.get("OPENWEATHER_API_KEY")

    time = get_context(msg, ["TIME", "DATE"])
    location = get_context(msg, ["GPE"])

    if not location:
        g = geocoder.ip("me").city
        geolocator = Nominatim(user_agent="User")
        location = geolocator.geocode(g)
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
        time = datetime.now().timestamp()

    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}"

    response = requests.get(url)

    if response.status_code == 200:
        # Successful API call
        data = response.json()

        match = min(data["list"], key=lambda x: abs(x["dt"] - int(time)))
        main = match["main"]

        temperature = main["temp"]
        humidity = main["humidity"]
        weather_description = match["weather"][0]["description"]

        weather_report = (
            f"Location: {location}\n"
            f"Time: {datetime.fromtimestamp(time)}\n"
            f"Temperature: {temperature - 273.15}°C\n"
            f"Humidity: {humidity}%\n"
            f"Description: {weather_description.capitalize()}"
        )
        return weather_report
    else:
        # API call failed this usually happens if the API key is invalid or not provided
        return f"Failed to retrieve weather data: {response.status_code}"
