import requests
import pandas as pd
from bs4 import BeautifulSoup

# 1. Scrape LA County cities from Wikipedia
wiki_url = "https://en.wikipedia.org/wiki/List_of_cities_in_Los_Angeles_County,_California"
soup = BeautifulSoup(requests.get(wiki_url).text, "html.parser")
cities = [td.get_text(strip=True) for td in soup.select("table.wikitable td:nth-child(1)")[1:]]

# Remove "Los Angeles" since we already know it
cities = [city for city in cities if city.lower() != "los angeles"]

print(cities)

# 2. Generate possible TreeKeeper URLs
def city_to_slug(city):
    return city.lower().replace(" ", "").replace("-", "")

urls = {
    city: f"http://{city_to_slug(city)}.treekeepersoftware.com/"
    for city in cities
}

# 3. Test each URL
def is_valid_treekeeper(url):
    try:
        r = requests.get(url, timeout=3)
        return r.status_code == 200 and "treekeeper" in r.text.lower()
    except:
        return False

results = {
    city: url for city, url in urls.items()
    if is_valid_treekeeper(url)
}

# Display hits
df = pd.DataFrame(results.items(), columns=["City", "Working TreeKeeper URL"])
print(df)
