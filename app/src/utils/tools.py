import requests
import os
import spacy
import dateparser
import geocoder

from datetime import datetime
from typing import Optional
from geotext import GeoText


from bs4 import BeautifulSoup


OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY")


def get_context(string: str, tokens: list[str]) -> str:
    if not set(tokens).issubset({"TIME", "DATE", "GPE"}):
        raise ValueError("Invalid token; must be one of 'TIME', 'DATE', or 'GPE'")

    nlp = spacy.load("en_core_web_sm")

    try:
        doc = nlp(string)

        res = [ent.text for ent in doc.ents if ent.label_ in tokens]

        result = " ".join(res)

        return result

    except:
        return ""


def html_to_text(html: str, ignore_script_and_style: bool = True) -> str:
    soup = BeautifulSoup(html, "html.parser")

    # Optional: Remove script and style elements
    if ignore_script_and_style:
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()

    # Get text
    text = soup.get_text()

    # Break into lines and remove leading and trailing space on each
    lines = (line.strip() for line in text.splitlines())
    # Break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    # Drop blank lines
    text = "\n".join(chunk for chunk in chunks if chunk)

    return text


def web_parser(url: str) -> BeautifulSoup:
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "lxml")
        return soup

    else:
        raise ValueError(f"Error: {response.status_code}")


def get_context_from_message(message: Optional[str]) -> tuple:
    """
    Extracts time and location context from the given message.
    """
    # Assuming get_context is a function that extracts certain types of information from text
    time = get_context(message, ["TIME", "DATE"])
    location = get_context(message, ["GPE"])
    return time, location


def get_lat_lon_from_location(location: str, geolocator) -> tuple:
    """
    Determines the latitude and longitude of the given location.
    """
    if not location:
        location_info = geocoder.ip("me")
        location = geolocator.geocode(location_info.city)
    else:
        location = GeoText(location).cities[0]
        location = geolocator.geocode(location)

    if location:
        return location.latitude, location.longitude
    else:
        return None, None


def get_current_time(time: str) -> float:
    """
    Parses the time string to a timestamp. Defaults to current time if parsing fails.
    """
    try:
        return dateparser.parse(time).timestamp()
    except TypeError:
        return datetime.now().timestamp()


def fetch_weather_report(lat: float, lon: float, time: float) -> str:
    """
    Fetches the weather report from the OpenWeatherMap API for the given coordinates and time.
    """
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units=metric&appid={OPENWEATHER_API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        match = min(data["list"], key=lambda x: abs(x["dt"] - int(time)))
        main = match["main"]

        return (
            f"Time: {datetime.fromtimestamp(time)}\n"
            f"Temperature: {main['temp']}°C\n"
            f"Humidity: {main['humidity']}%\n"
            f"Description: {match['weather'][0]['description'].capitalize()}"
        )
    else:
        return f"Failed to retrieve weather data: {response.status_code}"
