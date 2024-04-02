import os
import requests

from src.utils.tools import web_parser


def webText(url: str):
    text = web_parser(url).get_text()

    return text

def webMenus(url: str):
    soup = web_parser(url)
    menus = soup.find_all(['a', 'nav', 'ul', 'li'], class_=['menu', 'nav', 'nav-menu', 'nav-menu-item'])
    menu_list = []
    for menu in menus:
        menu_list.append(menu.text)
    return "\n".join(menu_list)

def webLinks(url: str):
    soup = web_parser(url)
    links = soup.find_all('a')
    link_list = []
    for link in links:
        link_list.append(link.get('href'))
    return "\n".join(link_list)

def webImages(url: str):
    soup = web_parser(url)
    images = soup.find_all('img')
    image_list = []
    for image in images:
        image_list.append(image.get('src'))
    return "\n".join(image_list)

def webTables(url: str):
    soup = web_parser(url)
    tables = soup.find_all('table')
    table_list = []
    for table in tables:
        table_list.append(table.text)
    return "\n".join(table_list)

def webForms(url: str):
    soup = web_parser(url)
    forms = soup.find_all('form')
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

def webQuery(query: str):
    # print(f"Debug--- Called webQuery with prompt: {query}")
    app_id = os.getenv('WOLFRAM_APP_ID')
    try:
        query = query.replace(" ", "+")
    except AttributeError:
        return f"You entered the query: {query} which is not a valid query. Please try again with the inferred query."
    url = f'https://www.wolframalpha.com/api/v1/llm-api?input={query}&appid={app_id}'
    response = requests.get(url)
    # print(f"Debug--- Wolfram response: {response.json()}")
    return response.json()['output']
