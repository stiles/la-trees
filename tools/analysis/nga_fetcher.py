import os
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

# Base URL for the directory listing
BASE_URL = "https://rockyweb.usgs.gov/vdelivery/Datasets/Staged/Elevation/Non_Standard_Contributed/NGA_US_Cities/Los_Angeles_CA/Los_Angeles_20121005-17/VEC/TR/"

# Set target directory relative to this script’s location and create it if needed
TARGET_DIR = os.path.join(os.path.dirname(__file__), "../data/large")
os.makedirs(TARGET_DIR, exist_ok=True)

# Get the HTML of the directory page and parse it
resp = requests.get(BASE_URL)
soup = BeautifulSoup(resp.text, "html.parser")

# Find links ending with the desired extensions (.dbf, .prj, .shp, .shx)
exts = (".dbf", ".prj", ".shp", ".shx")
links = [a["href"] for a in soup.find_all("a", href=True) if a["href"].lower().endswith(exts)]

def download_file(link, chunk_size=65536):
    """Download a single file using a larger chunk size (64KB)."""
    file_url = BASE_URL + link
    local_path = os.path.join(TARGET_DIR, link)
    print(f"Downloading {link}...")
    with requests.get(file_url, stream=True) as r:
        r.raise_for_status()  # Make sure we catch any errors
        with open(local_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk:  # Skip keep-alive chunks
                    f.write(chunk)
    return link

# Use ThreadPoolExecutor to download files concurrently
with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(download_file, link) for link in links]
    for future in as_completed(futures):
        try:
            result = future.result()
            print(f" Finished: {result}!")
        except Exception as e:
            print(f" Error downloading a file: {e}")
