import requests
import os
import spacy
import dateparser
import geocoder

from datetime import datetime
from typing import Optional
from geotext import GeoText
from bs4 import BeautifulSoup


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
    except (TypeError, AttributeError):
        return datetime.now().timestamp()


def fetch_weather_report(lat: float, lon: float, time: float) -> str:
    """
    Fetches the weather report from the OpenWeatherMap API for the given coordinates and time.
    """

    api_key = os.environ.get("OPENWEATHER_API_KEY")
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units=metric&appid={api_key}"
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


def web_text(url: str):
    """
    The webText function takes a url as an argument and returns the text of that webpage.
        This function is used to extract the text from webpages for use in other functions.

    Parameters
    ----------
        url: str
            Pass the url of the website to be parsed

    Returns
    -------

        The text of the url
    """
    text = web_parser(url).get_text()

    return text


def web_menus(url: str) -> str:
    """
    The webMenus function takes a url as an argument and returns the text of all menu items on that page.
        It uses BeautifulSoup to parse the HTML, then finds all elements with class names containing 'menu', 'nav',
        or 'nav-menu' and appends their text to a list. The function then joins each item in the list into one string
        separated by newlines.

    Parameters
    ----------
        url: str
            Specify the url of the website to be parsed

    Returns
    -------

        A string containing all the menu items in a webpage
    """
    soup = web_parser(url)
    menus = soup.find_all(
        ["a", "nav", "ul", "li"], class_=["menu", "nav", "nav-menu", "nav-menu-item"]
    )
    menu_list = []
    for menu in menus:
        menu_list.append(menu.text)
    return "\n".join(menu_list)


def web_links(url: str) -> str:
    """
    The webLinks function takes a url as an argument and returns all the links on that page.
        It uses the web_parser function to parse through the html of a given url, then finds all
        anchor tags in that html. The href attribute is extracted from each anchor tag and added to
        a list which is returned by this function.

    Parameters
    ----------
        url: str
            Specify the type of parameter that is being passed into the function

    Returns
    -------

        A list of all the links on a webpage
    """
    soup = web_parser(url)
    links = soup.find_all("a")
    link_list = []
    for link in links:
        link_list.append(link.get("href"))
    return "\n".join(link_list)


def web_images(url: str) -> str:
    """
    The webImages function takes a url as an argument and returns all the images on that page.
        It uses the web_parser function to parse through the html of a given url, then finds all
        image tags in that html. The src attribute is extracted from each image tag and added to
        a list which is returned by this function.

    Parameters
    ----------
        url: str
            Pass the url of a website into the function

    Returns
    -------

        A list of all the images on a page
    """
    soup = web_parser(url)
    images = soup.find_all("img")
    image_list = []
    for image in images:
        image_list.append(image.get("src"))
    return "\n".join(image_list)


def web_tables(url: str) -> str:
    """
    The webTables function takes a url as an argument and returns all the tables on that page.
        It uses the web_parser function to parse the html of a given url, then finds all table tags in that html.
        The text from each table is appended to a list, which is returned as one string.

    Parameters
    ----------
        url: str
            Specify the url of the website you want to scrape

    Returns
    -------

        The text of all the tables on a webpage
    """
    soup = web_parser(url)
    tables = soup.find_all("table")
    table_list = []
    for table in tables:
        table_list.append(table.text)
    return "\n".join(table_list)


def web_forms(url: str) -> str:
    """
    The webForms function takes a URL as an argument and returns the text of all forms on that page.

    Parameters
    ----------
        url: str
            Specify the url that will be used to parse the web page

    Returns
    -------

        A string of all the forms on a webpage
    """
    soup = web_parser(url)
    forms = soup.find_all("form")
    form_list = []
    for form in forms:
        form_list.append(form.text)
    return "\n".join(form_list)
