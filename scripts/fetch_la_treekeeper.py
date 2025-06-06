import time
import requests
import json
import os
import boto3
import geopandas as gpd
import zipfile
import shutil
import glob
from tqdm import tqdm
import getpass
import concurrent.futures
import urllib3
import urllib.parse

# --- Suppress InsecureRequestWarning from `verify=False` ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
print("---")
print("⚠️ NOTE: SSL certificate verification is disabled for this script. This is a standard practice for this type of web scraping but is not recommended for handling sensitive data.")
print("---")

# --- SESSION & HEADERS ---
COOKIES = {
    'cfid': 'dabad99c-9f9e-4c14-ae67-0c25dc4721f8',
    'cftoken': '0',
    'TK8LOGIN': '2133',
    'TK8LVL': '0',
    'SITEURL': 'losangelesca.treekeepersoftware.com',
    'ARRAffinity': '8937d6d9195b95556011246d3e1dc6d7ea257d7e79b10769150a240ffa8f0494',
    'ARRAffinitySameSite': '8937d6d9195b95556011246d3e1dc6d7ea257d7e79b10769150a240ffa8f0494',
    '_gid': 'GA1.2.74143669.1749144862',
    '_ga': 'GA1.1.965583879.1748978010',
    '_gat_gtag_UA_37419256_20': '1',
    '_ga_39T5PYWTLE': 'GS2.1.s1749144861$o4$g1$t1749144932$j59$l0$h0',
    '_ga_HRZ0TSV74S': 'GS2.1.s1749144863$o4$g1$t1749144934$j58$l0$h0',
}
HEADERS = {
    'Accept': '*/*', 'Accept-Language': 'en-US,en;q=0.9,es;q=0.8', 'Cache-Control': 'no-cache', 'Connection': 'keep-alive', 'Content-Type': 'application/json',
    'Origin': 'https://losangelesca.treekeepersoftware.com', 'Pragma': 'no-cache', 'Referer': 'https://losangelesca.treekeepersoftware.com/index.cfm?deviceWidth=1920',
    'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest', 'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"macOS"',
}

# --- FILE & PATHS ---
WFS_URL   = "https://geola.daveytreekeeper.com/geoserver/Treekeeper/ows"
TYPE_NAME = "Treekeeper:CityPlantsLA_UFDInventory(Public)"
CHUNK_SIZE = 2000
SORT_FIELD = "site_id"
OUTPUT_DIR = "data/processed/cities/los-angeles-city"
RAW_OUTPUT_DIR = "data/raw/cities/los-angeles-city"
FULL_GEOJSON_PATH = os.path.join(RAW_OUTPUT_DIR, "la_street_trees.geojson")
CHECKPOINT_GEOJSON_PATH = os.path.join(OUTPUT_DIR, "la_street_trees_detailed.checkpoint.geojson")
DETAILED_JSON_PATH = os.path.join(OUTPUT_DIR, "la_street_trees_detailed.geojson")
SHP_ZIP_PATH = os.path.join(OUTPUT_DIR, "la_street_trees_detailed_shp.zip")
GDB_ZIP_PATH = os.path.join(OUTPUT_DIR, "la_street_trees_detailed_gdb.zip")

# --- BEHAVIOR & PERFORMANCE ---
NUM_WORKERS = 50
SAVE_INTERVAL = 1000
MAX_RETRIES_SITE_DETAIL = 3
RETRY_DELAY_SECONDS = 5
TEST_SITE_IDS_SUBSET = None # Set to a list of site_id's to test, e.g., [123, 456]

# --- S3 CONFIG ---
S3_BUCKET = "stilesdata.com"
S3_PREFIX = "trees/los-angeles/"
S3_PROFILE_NAME = "haekeo"

# --- SCRAPEOPS PROXY CONFIG ---
SCRAPEOPS_API_KEY = os.environ.get("SCRAPE_PROXY_KEY")
if not SCRAPEOPS_API_KEY:
    user_api_key = getpass.getpass("ScrapeOps API key not found. Please paste key or press Enter to run directly: ")
    if user_api_key: SCRAPEOPS_API_KEY = user_api_key

PROXIES = {}
if SCRAPEOPS_API_KEY:
    print("✅ ScrapeOps proxy configured with residential IPs.")
    # URL encode the password portion to handle special characters
    password = urllib.parse.quote("residential=true&country=us", safe='')
    proxy_url = f'http://{SCRAPEOPS_API_KEY}:{password}@proxy.scrapeops.io:5353'
    PROXIES = {
        'http': proxy_url,
        'https': proxy_url,
    }
else:
    print("⚠️ WARNING: ScrapeOps API key not provided. Requests will be made directly.")


os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(RAW_OUTPUT_DIR, exist_ok=True)

# --- STEP 1: FETCH WFS DATA ---
print("--- Starting Step 1: Fetching WFS Data ---")
all_features = []
if os.path.exists(FULL_GEOJSON_PATH) and os.path.getsize(FULL_GEOJSON_PATH) > 0:
    print(f"Found existing raw data at {FULL_GEOJSON_PATH}. Loading it.")
    try:
        with open(FULL_GEOJSON_PATH, "r") as f:
            all_features = json.load(f).get("features", [])
        print(f"Successfully loaded {len(all_features)} features from file.")
    except Exception as e:
        print(f"Error loading {FULL_GEOJSON_PATH}: {e}. Proceeding to re-download.")
        all_features = []
else:
    print(f"No existing raw data found at {FULL_GEOJSON_PATH}. Proceeding to download.")

if not all_features:
    def fetch_chunk(start_index):
        params = {"service": "WFS", "version": "2.0.0", "request": "GetFeature", "typeName": TYPE_NAME, "outputFormat": "application/json", "count": str(CHUNK_SIZE), "startIndex": str(start_index), "sortBy": f"{SORT_FIELD} A"}
        resp = requests.get(WFS_URL, params=params, headers=HEADERS, cookies=COOKIES, timeout=60)
        resp.raise_for_status()
        return resp.json()
    offset = 0
    with tqdm(desc="Fetching WFS data", unit=" features") as pbar:
        while True:
            try:
                data = fetch_chunk(offset)
                feats = data.get("features", [])
                if not feats: break
                all_features.extend(feats)
                pbar.update(len(feats))
                pbar.set_postfix_str(f"Total: {len(all_features)}")
                offset += CHUNK_SIZE
            except requests.HTTPError as e:
                pbar.write(f"✖ HTTP {e.response.status_code} fetching WFS data. Stopping.")
                break
    if all_features:
        with open(FULL_GEOJSON_PATH, "w") as f:
            json.dump({"type": "FeatureCollection", "features": all_features}, f)
        print(f"Saved freshly downloaded WFS data → {FULL_GEOJSON_PATH}")

# --- STEP 2: FETCH DETAILED TREE DATA ---
print("\n--- Starting Step 2: Fetching Detailed Tree Data ---")
SITE_PIECES_URL = "https://losangelesca.treekeepersoftware.com/cffiles/site.cfc"

def fetch_site_details(site_id):
    """Fetches and parses detailed info for a site_id via POST, using proxies if configured."""
    params = {
        'method': 'getSitePieces', 'searchID': str(site_id), 'idType': 'site',
        'requestSite': 'true', 'requestWork': 'true', 'requestCall': 'true', 'requestArchives': 'true'
    }

    current_retry_delay = RETRY_DELAY_SECONDS
    for attempt in range(MAX_RETRIES_SITE_DETAIL):
        try:
            # Use POST as discovered from browser. Pass PROXIES dict to let requests handle it.
            # Increased timeout to 120s for residential proxies.
            resp = requests.post(SITE_PIECES_URL, params=params, headers=HEADERS, cookies=COOKIES, timeout=120, verify=False, proxies=PROXIES)
            
            if resp.status_code == 200:
                details_json = resp.json()
                parsed_data = {}
                if not details_json.get("siteID"): return None, f"⚠️ No 'siteID' in response for {site_id}"
                parsed_data["api_response_siteID"] = details_json.get("siteID")
                rawdata = details_json.get("rawdata", {})
                if isinstance(rawdata, dict):
                    parsed_data["inventory_date"] = rawdata.get("site_date")
                    parsed_data["site_comment"] = rawdata.get("site_comment")
                main_site = details_json.get("mainSite", {})
                if isinstance(main_site, dict):
                    for i, section in enumerate(['1', '2'], 1):
                        for item in main_site.get(section, []):
                            if isinstance(item, dict) and item.get("name"):
                                name, value = item.get("name"), item.get("value")
                                key_name = f"ms{i}_" + "".join(filter(lambda c: c.isalnum() or c == '_', name.lower().replace(" ", "_")))
                                if name == "Species":
                                    parsed_data[key_name + "_value"], parsed_data[key_name + "_common"], parsed_data[key_name + "_scientific"] = value, item.get("commonName"), item.get("botanicalName")
                                else:
                                    parsed_data[key_name] = value
                return parsed_data, None
            elif (resp.status_code >= 500 or resp.status_code == 429) and attempt < MAX_RETRIES_SITE_DETAIL - 1:
                log_msg = f"↪️ HTTP {resp.status_code}{' (Rate Limit)' if resp.status_code == 429 else ''} for {site_id}. Retrying in {current_retry_delay}s..."
                tqdm.write(log_msg)
                time.sleep(current_retry_delay)
                current_retry_delay *= 2
            else:
                return None, f"❌ HTTP {resp.status_code}"
        except requests.exceptions.Timeout:
            if attempt < MAX_RETRIES_SITE_DETAIL - 1:
                tqdm.write(f"⌛ Timeout for {site_id}. Retrying...")
                time.sleep(current_retry_delay)
            else:
                return None, "❌ Timeout"
        except Exception as e:
            if attempt < MAX_RETRIES_SITE_DETAIL - 1:
                tqdm.write(f"Unexpected error for {site_id}: {e}. Retrying...")
                time.sleep(current_retry_delay)
            else:
                return None, f"❌ Error: {e}"
    return None, f"❌ Failed Retries"

if not all_features:
    print("No features found from Step 1. Cannot proceed.")
else:
    detailed_trees_data, processed_site_ids = [], set()
    if os.path.exists(CHECKPOINT_GEOJSON_PATH):
        print(f"Found checkpoint file, loading... (Total records will reflect this)")
        try:
            gdf_checkpoint = gpd.read_file(CHECKPOINT_GEOJSON_PATH)
            for _, row in gdf_checkpoint.iterrows():
                props = row.to_dict()
                geom_dict = row.geometry.__geo_interface__ if row.geometry else None
                if 'geometry' in props: del props['geometry']
                detailed_trees_data.append({"type": "Feature", "geometry": geom_dict, "properties": props})
                if props.get(SORT_FIELD): processed_site_ids.add(props.get(SORT_FIELD))
        except Exception as e:
            print(f"Error loading checkpoint file: {e}. Starting fresh.")
            detailed_trees_data, processed_site_ids = [], set()

    features_to_process = TEST_SITE_IDS_SUBSET or [f for f in all_features if f.get("properties", {}).get(SORT_FIELD) not in processed_site_ids]
    if TEST_SITE_IDS_SUBSET:
        print(f"---!!! RUNNING IN TEST MODE for {len(features_to_process)} site_ids !!!---")
        features_to_process = [{"type": "Feature", "properties": {SORT_FIELD: site_id}, "geometry": None} for site_id in features_to_process]

    if not features_to_process:
        print("No new sites to process.")
    else:
        print(f"Found {len(all_features)} total sites. {len(processed_site_ids)} already processed. Attempting to fetch {len(features_to_process)} new sites.")
        newly_processed_count = 0
        def save_checkpoint(pbar=None):
            if not detailed_trees_data: return
            msg = f"\n--- Saving checkpoint: {len(detailed_trees_data)} total records... ---"
            if pbar: pbar.write(msg)
            else: print(msg)
            try:
                temp_path = CHECKPOINT_GEOJSON_PATH + ".tmp"
                gpd.GeoDataFrame.from_features(detailed_trees_data, crs="EPSG:4326").to_file(temp_path, driver="GeoJSON")
                os.replace(temp_path, CHECKPOINT_GEOJSON_PATH)
                if pbar: pbar.write(f"Checkpoint saved to {CHECKPOINT_GEOJSON_PATH}")
                return True
            except Exception as e:
                if pbar: pbar.write(f"Error saving checkpoint: {e}")
                return False

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
                future_to_feature = {executor.submit(fetch_site_details, f.get("properties", {}).get(SORT_FIELD)): f for f in features_to_process}
                with tqdm(concurrent.futures.as_completed(future_to_feature), total=len(features_to_process), desc="Processing site details") as pbar:
                    for future in pbar:
                        original_feature = future_to_feature[future]
                        site_id = original_feature.get("properties", {}).get(SORT_FIELD)
                        try:
                            parsed_data, error_status = future.result()
                            if error_status:
                                pbar.set_postfix_str(f"{error_status} for {site_id}", refresh=True)
                            elif parsed_data:
                                pbar.set_postfix_str(f"✅ Success: {site_id}", refresh=True)
                                combined_props = {**original_feature.get("properties", {}), **parsed_data}
                                detailed_trees_data.append({"type": "Feature", "geometry": original_feature.get("geometry"), "properties": combined_props})
                                newly_processed_count += 1
                                if newly_processed_count >= SAVE_INTERVAL:
                                    if save_checkpoint(pbar): newly_processed_count = 0
                        except Exception as exc:
                            pbar.set_postfix_str(f"💥 Exception for {site_id}: {exc}", refresh=True)
        except KeyboardInterrupt:
            print("\n\nScript interrupted. Saving final checkpoint...")
            save_checkpoint()
            os._exit(130)

    print(f"\n🎉 Step 2 finished. Total detailed records in memory: {len(detailed_trees_data)}.")

    if detailed_trees_data:
        print("\n--- Saving data to local files and uploading to S3 ---")
        try:
            gdf = gpd.GeoDataFrame.from_features(detailed_trees_data, crs="EPSG:4326")
            files_to_upload = []
            # GeoJSON
            try:
                gdf.to_file(DETAILED_JSON_PATH, driver="GeoJSON"); files_to_upload.append(DETAILED_JSON_PATH)
                print(f"Saved GeoJSON → {DETAILED_JSON_PATH}")
            except Exception as e: print(f"Error saving GeoJSON: {e}")
            # Zipped Shapefile & GDB
            for ftype, driver, path in [("Shapefile", "ESRI Shapefile", SHP_ZIP_PATH), ("FileGDB", "OpenFileGDB", GDB_ZIP_PATH)]:
                temp_dir = os.path.join(OUTPUT_DIR, f"temp_{ftype.lower()}")
                os.makedirs(temp_dir, exist_ok=True)
                try:
                    export_path = os.path.join(temp_dir, f"la_trees.{'shp' if ftype=='Shapefile' else 'gdb'}")
                    gdf.to_file(export_path, driver=driver)
                    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as zf:
                        for root, _, files in os.walk(temp_dir):
                            for file in files:
                                if not file.endswith('.lock'):
                                    zf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), temp_dir))
                    files_to_upload.append(path)
                    print(f"Zipped {ftype} → {path}")
                except Exception as e: print(f"Error saving {ftype}: {e}")
                finally: shutil.rmtree(temp_dir)
            # S3 Upload
            if files_to_upload and S3_PROFILE_NAME:
                print(f"\n--- Uploading {len(files_to_upload)} file(s) to S3 ---")
                try:
                    session = boto3.Session(profile_name=S3_PROFILE_NAME)
                    s3 = session.client("s3")
                    for path in files_to_upload:
                        key = f"{S3_PREFIX}{os.path.basename(path)}"
                        print(f"Uploading {path} to s3://{S3_BUCKET}/{key}...")
                        s3.upload_file(path, S3_BUCKET, key)
                except Exception as e: print(f"S3 Upload Error: {e}")
        except Exception as e:
            print(f"An error occurred during final file processing: {e}")
    else:
        print("\nNo detailed data available. Skipping final file creation and upload.")

print("\n--- Script Finished ---")