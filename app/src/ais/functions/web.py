import os
import requests

from src.utils.tools import (
    web_text,
    web_menus,
    web_links,
    web_images,
    web_tables,
    web_forms,
)


def webViewer(url: str) -> str:
    """
    The webViewer function takes a url as an argument and returns all the content on that page.

    Parameters
    ----------
    url: str
        Pass in the url of the website you want to view.

    Returns
    -------
    str
        The website content.
    """
    print("\n--debug: called webViewer()\n")
    text = web_text(url)
    menus = web_menus(url)
    links = web_links(url)
    images = web_images(url)
    tables = web_tables(url)
    forms = web_forms(url)

    content = f"URL: {url}\n\nText: {text}\n\nMenus: {menus}\n\nLinks: {links}\n\nImages: {images}\n\nTables: {tables}\n\nForms: {forms}"

    return content


def dataQuery(query: str) -> str:
    """
    The webQuery function takes a string as an argument and returns the output of that query from Wolfram Alpha.

    Parameters
    ----------
    query: str
        Pass in the query string that will be used to make a request to Wolfram Alpha's API.

    Returns
    -------
    str
        The response text from the Wolfram Alpha query.
    """
    print(f"\n--debug: called dataQuery() with parameter: {query}\n")
    app_id = os.environ.get("WOLFRAM_APP_ID")

    try:
        query = query.replace(" ", "+")
    except AttributeError:
        return f"You entered the query: {query} which is not a valid query. Please try again with the inferred query."

    url = f"https://www.wolframalpha.com/api/v1/llm-api?input={query}&appid={app_id}"
    response = requests.get(url)

    print(f"\n--debug: response: {response}\n")

    if response.status_code == 200:
        response_text = response.text

        return response_text
    else:
        return f"Failed to get a valid response, status code: {response.status_code}"


def webQuery(query: str) -> str:
    print(f"\n--debug: called webQuery() with parameter: {query}\n")
    api_key = os.environ.get("You_API_key")
    headers = {"X-API-Key": api_key}
    params = {"query": query}
    hits = requests.get(
        f"https://api.ydc-index.io/search",
        params=params,
        headers=headers,
    ).json()["hits"]

    print(f"\n--debug: hits: {hits}\n")

    results = "\n\n\n".join(
        [f"{hit['title']}\n{hit['description']}\n{hit['url']}" for hit in hits]
    )
    return results
