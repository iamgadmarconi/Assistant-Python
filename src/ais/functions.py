import requests
import os
import geocoder
from geopy.geocoders import Nominatim
from typing import Optional
from datetime import datetime, timedelta
import datefinder
from geotext import GeoText
import spacy
import dateparser

from O365 import Account, MSGraphProtocol


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

    if upto is None:
        upto = datetime.now() + timedelta(days=7)
    else:
        nlp = spacy.load("en_core_web_sm")
        doc = nlp(upto)
        times = [ent.text for ent in doc.ents if ent.label_ in ["TIME", "DATE"]]
        time = " ".join(times)

        settings = {"PREFER_DATES_FROM": "future"}
        diff = dateparser.parse(time, settings=settings)
        if diff is not None:
            upto = diff
        else:
            upto = datetime.now() + timedelta(days=7)  # Default to 7 days from now if parsing fails


    protocol = MSGraphProtocol()
    credentials = (os.environ.get("CLIENT_ID"), os.environ.get("CLIENT_SECRET"))
    scopes_graph = protocol.get_scopes_for(['calendar_all', 'basic'])

    account = Account(credentials, protocol=protocol)

    if not account.is_authenticated:
        account.authenticate(scopes=scopes_graph)

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