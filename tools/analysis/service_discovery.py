import requests
import pandas as pd
from bs4 import BeautifulSoup
import time

# Step 1: Scrape LA County cities from Wikipedia
wiki_url = "https://en.wikipedia.org/wiki/List_of_cities_in_Los_Angeles_County,_California"
soup = BeautifulSoup(requests.get(wiki_url).text, "html.parser")
cities = [td.get_text(strip=True) for td in soup.select("table.wikitable td:nth-child(1)")[1:]]
cities = [city for city in cities if city.lower() != "los angeles"]  # Exclude LA

# Step 2: Define helper for slugs and common GIS domain formats
def city_to_slug(city):
    return (
        city.lower()
        .replace(" ", "")
        .replace("-", "")
        .replace("ñ", "n")
        .replace("é", "e")
    )

suffixes = [".gov", ".org", ".com"]
service_paths = [
    "/arcgis/rest/services",
    "/server/rest/services",
    "/arcgis/rest/services/Public",
    "/arcgis/rest/services/OpenData",
]

# Step 3: Test REST endpoints for each city
results = []

for city in cities:
    slug = city_to_slug(city)
    found = False  # flag to stop after first hit
    for suffix in suffixes:
        if found:
            break
        base = f"https://gis.{slug}{suffix}"
        for path in service_paths:
            url = base + path
            try:
                r = requests.get(url + "?f=json", timeout=4)
                if r.status_code == 200 and "services" in r.text:
                    results.append({"City": city, "REST URL": url})
                    print(f"✅ {city}: {url}")
                    found = True
                    break
            except requests.RequestException:
                continue

# Save or display results
df = pd.DataFrame(results)
df.to_csv("la_county_gis_rest_endpoints.csv", index=False)
print("\n🎉 Finished! Results saved to la_county_gis_rest_endpoints.csv")
