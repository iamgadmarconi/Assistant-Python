import os
import requests

from src.utils.tools import web_parser


def webText(url: str):
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


def webMenus(url: str) -> str:
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


def webLinks(url: str) -> str:
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


def webImages(url: str) -> str:
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


def webTables(url: str) -> str:
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


def webForms(url: str) -> str:
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


# def menuInteract(url: str, menu: str):
#     driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

#     driver.get(url)
#     # Use XPath to find an element by text, this is one example, adjust based on the webpage structure
#     menu_item = driver.find_element(By.XPATH, f"//*[contains(text(), '{menu}')]")
#     menu_item_id = menu_item.get_attribute('id')
#     print(f"The ID of the menu item '{menu}' is: {menu_item_id}")
#     menu_item.click()
#     driver.quit()
#     time.sleep(5)  # Adjust sleep time as necessary

#     new_page_url = driver.current_url
#     return new_page_url


def webQuery(query: str) -> str:
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
    app_id = os.environ.get("WOLFRAM_APP_ID")

    try:
        query = query.replace(" ", "+")
    except AttributeError:
        return f"You entered the query: {query} which is not a valid query. Please try again with the inferred query."

    url = f"https://www.wolframalpha.com/api/v1/llm-api?input={query}&appid={app_id}"
    response = requests.get(url)

    if response.status_code == 200:
        response_text = response.text

        return response_text
    else:
        return f"Failed to get a valid response, status code: {response.status_code}"
