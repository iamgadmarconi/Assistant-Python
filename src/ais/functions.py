import requests
import os
import spacy
import dateparser

from geopy.geocoders import Nominatim
from typing import Optional
from datetime import datetime, timedelta
from geotext import GeoText

from src.utils.tools import getLocation, O365Auth, getContext


def getWeather(msg: str):
    api_key = os.environ.get("OPENWEATHER_API_KEY")

    time = getContext(msg, ["TIME", "DATE"])
    location = getContext(msg, ["GPE"])

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

def sendEmail():
    pass

def readEmail():
    pass
    
def getCalendar(upto: Optional[str] = None):

    account = O365Auth()

    if upto is None:
        upto = datetime.now() + timedelta(days=7)
        
    else:
        time = getContext(upto, ["TIME", "DATE"])
        settings = {"PREFER_DATES_FROM": "future"}
        diff = dateparser.parse(time, settings=settings)

        if diff is not None:
            upto = diff

        else:
            upto = datetime.now() + timedelta(days=7)  # Default to 7 days from now if parsing fails

    schedule = account.schedule()
    calendar = schedule.get_default_calendar()

    q = calendar.new_query('start').greater_equal(datetime.now())
    q.chain('and').on_attribute('end').less_equal(upto)

    events = calendar.get_events(query=q, include_recurring=True)

    for event in events:

        cal_report = (f"Event: {event.subject}\n"
                      f"Start: {event.start}\n"
                      f"End: {event.end}\n"
                      f"Location: {event.location}\n"
                      f"Description: {event.body}")

    return cal_report

def addCalendarEvent():
    pass