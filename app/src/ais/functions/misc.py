import geocoder

from geopy.geocoders import Nominatim
from typing import Optional
from datetime import datetime


from src.utils.tools import (
    fetch_weather_report,
    get_current_time,
    get_lat_lon_from_location,
    get_context_from_message,
)

USER_AGENT = "User"


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
    print("\n--debug: called getDate()\n")
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


def getWeather(location_message: Optional[str] = None) -> str:
    """
    Fetches the weather report for a given location. If no location is provided,
    it uses the current IP address to determine the location.

    Parameters:
        location_message (Optional[str]): The location as a string message, if any.

    Returns:
        str: A weather report for the specified or derived location.
    """
    print("\n--debug: called getWeather()\n")
    geolocator = Nominatim(user_agent=USER_AGENT)
    time, location = get_context_from_message(location_message)

    lat, lon = get_lat_lon_from_location(location, geolocator)
    if lat is None or lon is None:
        return "Location not found"

    current_time = get_current_time(time)
    weather_report = fetch_weather_report(lat, lon, current_time)
    return weather_report
