import requests
from bs4 import BeautifulSoup


url = 'https://www.palisadestahoe.com/mountain-information/lift-and-grooming-status'
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')
#print(soup)
#elements_by_class = soup.find_all(class_='lift')
all_items = soup.find('div', class_='main-content')
#id_element=soup.find(id='mtnDashboardApp')
if all_items:
    nested_divs = all_items.find_all("div", class_="dynamic-tabs-container swipeable")
    for nested_div in nested_divs:
        # Extract data from the nested div, e.g., text content
        text_content = nested_div.get_text(strip=True)
        print(text_content)
#print("output", all_items)
#if elements_by_class:
    #for element in elements_by_class:
        #print(element.get_text(strip=True))