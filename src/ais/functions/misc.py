import requests
import os
import dateparser
import geocoder

from geopy.geocoders import Nominatim
from typing import Optional
from datetime import datetime
from geotext import GeoText

from src.utils.tools import get_context


def getDate() -> str:
    """
    The getDate function returns the current date and time in a string format.
        The function is called by the main program to print out the current date and time.

    Parameters
    ----------

    Returns
    -------

        The current date and time in the format dd/mm/yyyy, hh:mm:ss
    """
    return datetime.now().strftime("%d/%m/%Y, %H:%M:%S")


def getLocation() -> str:
    """
    The getLocation function uses the geocoder library to get the user's location.
        It then uses that location to find a more specific address using Nominatim,
        which is a Python wrapper for OpenStreetMap's API.

    Parameters
    ----------

    Returns
    -------

        The city name and country code
    """
    g = geocoder.ip("me").city
    geolocator = Nominatim(user_agent="User")
    location = geolocator.geocode(g)
    if location is not None:
        return location.address  # type: ignore
    else:
        return "Location not found"


def getWeather(msg: Optional[str] = None) -> str:
    """
    The getWeather function takes in a message and returns the weather report for that location.
    If no location is provided, it will return the weather report for your current IP address.

    Parameters
    ----------
        msg: Optional[str]
            Pass in the message that is to be processed

    Returns
    -------

        A string containing the weather report for a given location
    """
    api_key = os.environ.get("OPENWEATHER_API_KEY")

    time = get_context(msg, ["TIME", "DATE"])  # type: ignore
    location = get_context(msg, ["GPE"])  # type: ignore

    if not location:
        g = geocoder.ip("me").city
        geolocator = Nominatim(user_agent="User")
        location = geolocator.geocode(g)
        if location:
            lat, lon = location.latitude, location.longitude  # type: ignore
        else:  # If location is not found
            return "Location not found"

    else:
        location = GeoText(location).cities

        geolocator = Nominatim(user_agent="User")
        location = geolocator.geocode(location[0])
        if location:
            lat = location.latitude # type: ignore
            lon = location.longitude # type: ignore
        else:
            return "Location not found"

    try:
        time = dateparser.parse(time).timestamp() # type: ignore

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
