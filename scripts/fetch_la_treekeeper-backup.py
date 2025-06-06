import time
import requests
import json
import os # Added for path manipulation
import boto3 # Added for S3 upload
import geopandas as gpd # Added for geospatial data handling
import zipfile # Added for zipping shapefiles and GDB
import shutil # Added for removing temporary directories
import glob # Added for finding files to zip
from tqdm import tqdm # Added for progress bar
import getpass
import concurrent.futures
import urllib3 # To disable SSL warnings

# --- Suppress InsecureRequestWarning from `verify=False` ---
# We are intentionally bypassing SSL verification for this scraping task.
# This is a common practice for scraping public data where the risk is low,
# but it's important to acknowledge.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
print("---")
print("⚠️ NOTE: SSL certificate verification is disabled for this script. This is a standard practice for this type of web scraping but is not recommended for handling sensitive data.")
print("---")

# CONFIGURATION: copy cookies/headers exactly from DevToolsååå
COOKIES = {
    'cfid': 'dabad99c-9f9e-4c14-ae67-0c25dc4721f8',
    'cftoken': '0',
    'TK8LOGIN': '2133',
    'TK8LVL': '0',
    'SITEURL': 'losangelesca.treekeepersoftware.com',
    'ARRAffinity': '8937d6d9195b95556011246d3e1dc6d7ea257d7e79b10769150a240ffa8f0494',
    'ARRAffinitySameSite': '8937d6d9195b95556011246d3e1dc6d7ea257d7e79b10769150a240ffa8f0494',
    '_gid': 'GA1.2.74143669.1749144862',
    '_gat_gtag_UA_37419256_20': '1',
    '_ga_39T5PYWTLE': 'GS2.1.s1749144861$o4$g1$t1749144932$j59$l0$h0',
    '_ga': 'GA1.1.965583879.1748978010',
    '_ga_HRZ0TSV74S': 'GS2.1.s1749144863$o4$g1$t1749144934$j58$l0$h0',
}

# Let ScrapeOps handle most headers. We only need to send the most essential ones
# that the target server might specifically check for application logic.
HEADERS = {
    "Accept":           "application/json, text/plain, */*",
    "Referer":          "https://losangelesca.treekeepersoftware.com/index.cfm",
    "User-Agent":       "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/136.0.0.0 Safari/537.36",
    'X-Requested-With': 'XMLHttpRequest', # Often important for AJAX/fetch requests
}

WFS_URL   = "https://geola.daveytreekeeper.com/geoserver/Treekeeper/ows"
TYPE_NAME = "Treekeeper:CityPlantsLA_UFDInventory(Public)"

CHUNK_SIZE = 2000
SORT_FIELD = "site_id"

# Output directory
OUTPUT_DIR = "data/processed/cities/los-angeles-city"
RAW_OUTPUT_DIR = "data/raw/cities/los-angeles-city" # For intermediate files from step 1
SAMPLE_GEOJSON_PATH = os.path.join(RAW_OUTPUT_DIR, "sample_trees.geojson")
FULL_GEOJSON_PATH = os.path.join(RAW_OUTPUT_DIR, "la_street_trees.geojson")
DETAILED_JSON_PATH = os.path.join(OUTPUT_DIR, "la_street_trees_detailed.geojson")
SHP_ZIP_PATH = os.path.join(OUTPUT_DIR, "la_street_trees_detailed_shp.zip")
GDB_ZIP_PATH = os.path.join(OUTPUT_DIR, "la_street_trees_detailed_gdb.zip")

# Concurrency Configuration for Step 2
NUM_WORKERS = 50  # Set to ScrapeOps concurrency limit
SAVE_INTERVAL = 1000  # How many new records to process before saving a checkpoint
MAX_RETRIES_SITE_DETAIL = 3  # Max retries for a single site detail fetch on 5xx error
RETRY_DELAY_SECONDS = 5  # Initial delay in seconds for retries

# --- !!! FOR TESTING ONLY: Process a small subset of site_ids !!! ---
# Set to None or empty list to process all sites from WFS features.
# If a list of site_id strings is provided, the script will ONLY attempt to fetch
# details for those specific sites, bypassing the main checkpoint and WFS data list.
TEST_SITE_IDS_SUBSET = None

# S3 Configuration
S3_BUCKET = "stilesdata.com"
S3_PREFIX = "trees/los-angeles/"
S3_PROFILE_NAME = "haekeo"

# ScrapeOps Configuration
SCRAPEOPS_API_KEY = os.environ.get("SCRAPE_PROXY_KEY")
PROXIES = {}
if SCRAPEOPS_API_KEY:
    PROXIES = {
        "http": f"http://scrapeops.api_key:{SCRAPEOPS_API_KEY}@proxy.scrapeops.io:5353",
        "https": f"http://scrapeops.api_key:{SCRAPEOPS_API_KEY}@proxy.scrapeops.io:5353"
    }
    print("✅ ScrapeOps proxy configured.")
else:
    # Use built-in getpass to obscure the input
    user_api_key = getpass.getpass(
        "ScrapeOps API key not found in environment variable 'SCRAPE_PROXY_KEY'. Please paste your key here to continue (it will not be shown) or press Enter to proceed without a proxy: ")
    if user_api_key:
        SCRAPEOPS_API_KEY = user_api_key
        PROXIES = {
            "http": f"http://scrapeops.api_key:{SCRAPEOPS_API_KEY}@proxy.scrapeops.io:5353",
            "https": f"http://scrapeops.api_key:{SCRAPEOPS_API_KEY}@proxy.scrapeops.io:5353"
        }
        print("✅ ScrapeOps proxy configured for this session.")
    else:
        print("⚠️ WARNING: ScrapeOps API key not provided. Requests will be made directly and are likely to be blocked.")

# Ensure output directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(RAW_OUTPUT_DIR, exist_ok=True)


# --- Step 1: Fetch WFS Data ---
print("--- Starting Step 1: Fetching WFS Data ---")

# Fetch a single batch of features
def fetch_chunk(start_index):
    params = {
        "service":      "WFS",
        "version":      "2.0.0",
        "request":      "GetFeature",
        "typeName":     TYPE_NAME,
        "outputFormat": "application/json",
        "count":        str(CHUNK_SIZE),
        "startIndex":   str(start_index),
        "sortBy":       f"{SORT_FIELD} A",
    }
    resp = requests.get(WFS_URL, params=params, headers=HEADERS, cookies=COOKIES, timeout=60)
    resp.raise_for_status()
    return resp.json()


all_features = []
offset = 0
sample_written = False

# Check if the full GeoJSON already exists
if os.path.exists(FULL_GEOJSON_PATH) and os.path.getsize(FULL_GEOJSON_PATH) > 0:
    print(f"Found existing raw data at {FULL_GEOJSON_PATH}. Loading it.")
    try:
        with open(FULL_GEOJSON_PATH, "r") as f:
            fc = json.load(f)
            all_features = fc.get("features", [])
            if all_features:
                print(f"Successfully loaded {len(all_features)} features from file.")
                # If we load the full file, we can consider the sample as "written"
                # or ensure the sample file also exists from a previous run.
                # For simplicity, we'll skip re-writing the sample if the full file is loaded.
                sample_written = True # Prevents trying to write a new sample
            else:
                print(f"Warning: {FULL_GEOJSON_PATH} was found but contained no features. Proceeding to download.")
                all_features = [] # Ensure it's empty if loading failed
    except json.JSONDecodeError:
        print(f"Error decoding JSON from {FULL_GEOJSON_PATH}. File might be corrupted. Proceeding to re-download.")
        all_features = [] # Ensure it's empty if loading failed
    except Exception as e:
        print(f"An error occurred loading {FULL_GEOJSON_PATH}: {e}. Proceeding to re-download.")
        all_features = [] # Ensure it's empty if loading failed
else:
    print(f"No existing raw data found at {FULL_GEOJSON_PATH} or file is empty. Proceeding to download.")

# Only run the download loop if all_features is still empty (i.e., not loaded from file)
if not all_features:
    while True:
        print(f"→ fetching {offset}–{offset+CHUNK_SIZE-1}…", end=" ")
        try:
            data = fetch_chunk(offset)
        except requests.HTTPError as e:
            print(f"✖ HTTP {e.response.status_code}: {e.response.text[:200]}…")
            break

        feats = data.get("features", [])
        if not feats:
            print("✅ no more features; done.")
            break

        print(f"pulled {len(feats)}")
        all_features.extend(feats)

        # write the first batch to a sample file so you can inspect early
        if not sample_written:
            sample_fc = {"type": "FeatureCollection", "features": feats}
            with open(SAMPLE_GEOJSON_PATH, "w") as sf:
                json.dump(sample_fc, sf)
            print(f"   ✎ wrote first batch to {SAMPLE_GEOJSON_PATH}")
            sample_written = True

        offset += CHUNK_SIZE
        # time.sleep(0.1)

    print(f"\n🎉 Total features fetched: {len(all_features)}")

    # Check if the file needs to be written (i.e., if it was downloaded in this session)
    # This condition is tricky. If `all_features` is populated, it could be from file or download.
    # The `while True` loop for downloading only runs if `all_features` is initially empty.
    # So, if `all_features` is populated *after* this point, it means it was downloaded.
    # Let's simplify: If the download loop was entered (because all_features was initially empty),
    # then save the result.
    # The original placement of this save block is after the `while True` loop.
    # We need to ensure it only saves if the download loop actually ran and populated `all_features`.

    # Let's track if download happened
    download_occurred = not (os.path.exists(FULL_GEOJSON_PATH) and os.path.getsize(FULL_GEOJSON_PATH) > 0 and len(all_features) > 0)

    if download_occurred and all_features:
        fc = {"type": "FeatureCollection", "features": all_features}
        with open(FULL_GEOJSON_PATH, "w") as f:
            json.dump(fc, f)
        print(f"Saved freshly downloaded WFS data → {FULL_GEOJSON_PATH}")
    elif not download_occurred and all_features:
        print(f"Using already existing WFS data from {FULL_GEOJSON_PATH}.")
    # If all_features is empty here, Step 2 will handle it by printing a message.
    # The previous problematic "No features fetched or loaded from WFS. Exiting." line has been removed.
    # Ensure no 'else' block here unintentionally reintroduces it or calls exit().

# --- Step 2: Call getSitePieces for each site_id ---
print("\n--- Starting Step 2: Fetching Detailed Tree Data ---")

SITE_PIECES_URL = "https://losangelesca.treekeepersoftware.com/cffiles/site.cfc"

# The `fetch_site_details` function from the sequential version was more robust. Let's use that as the base.
def fetch_site_details(site_id):
    """Fetches and parses detailed information for a single site_id, with retries for 5xx errors."""
    params = {
        "method": "getSitePieces",
        "searchID": site_id,
        "idType": "site",
        "requestSite": "true",
        "requestWork": "false",
        "requestCall": "false",
        "requestArchives": "false",
    }
    current_retry_delay = RETRY_DELAY_SECONDS
    for attempt in range(MAX_RETRIES_SITE_DETAIL):
        try:
            resp = requests.get(SITE_PIECES_URL, params=params, headers=HEADERS, cookies=COOKIES, timeout=90,
                                proxies=PROXIES, verify=False)
            resp.raise_for_status()
            details_json = resp.json()

            # --- PARSING LOGIC NOW INSIDE THIS FUNCTION ---
            parsed_data = {}
            api_site_id_val = details_json.get("siteID")
            if not api_site_id_val:
                # Return an error tuple
                return None, f"⚠️ No 'siteID' in response for {site_id}"

            parsed_data["api_response_siteID"] = api_site_id_val
            
            rawdata = details_json.get("rawdata", {})
            if isinstance(rawdata, dict):
                parsed_data["inventory_date"] = rawdata.get("site_date")
                parsed_data["site_comment"] = rawdata.get("site_comment")

            main_site = details_json.get("mainSite", {})
            if isinstance(main_site, dict):
                # Process section '1'
                for item in main_site.get("1", []):
                    if not isinstance(item, dict): continue
                    name = item.get("name")
                    value = item.get("value")
                    if not name: continue
                    key_name_base = name.lower().replace(" ", "_")
                    key_name = "ms1_" + "".join(filter(lambda char: char.isalnum() or char == '_', key_name_base))
                    if name == "Species":
                        parsed_data[key_name + "_value"] = value
                        parsed_data[key_name + "_common"] = item.get("commonName")
                        parsed_data[key_name + "_scientific"] = item.get("botanicalName")
                    else:
                        parsed_data[key_name] = value
                # Process section '2'
                for item in main_site.get("2", []):
                    if not isinstance(item, dict): continue
                    name = item.get("name")
                    value = item.get("value")
                    if not name: continue
                    key_name_base = name.lower().replace(" ", "_")
                    key_name = "ms2_" + "".join(filter(lambda char: char.isalnum() or char == '_', key_name_base))
                    parsed_data[key_name] = value

            return parsed_data, None  # Success: Return parsed data and no error

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            if status_code >= 500 and attempt < MAX_RETRIES_SITE_DETAIL - 1:
                tqdm.write(f"↪️ HTTP {status_code} for site_id {site_id} (attempt {attempt + 1}/{MAX_RETRIES_SITE_DETAIL}). Retrying in {current_retry_delay}s...")
                time.sleep(current_retry_delay)
                current_retry_delay *= 2
                continue
            else:
                return None, f"❌ HTTP {status_code}"
        except requests.exceptions.Timeout:
            if attempt < MAX_RETRIES_SITE_DETAIL - 1:
                tqdm.write(f"⌛ Timeout for site_id {site_id} (attempt {attempt + 1}/{MAX_RETRIES_SITE_DETAIL}). Retrying in {current_retry_delay}s...")
                time.sleep(current_retry_delay)
                current_retry_delay *= 2
                continue
            else:
                return None, "❌ Timeout"
        except json.JSONDecodeError:
            return None, "❌ Decode Error"
        except Exception as e:
            if attempt < MAX_RETRIES_SITE_DETAIL - 1:
                tqdm.write(f"Unexpected error for site_id {site_id} (attempt {attempt + 1}): {e}. Retrying in {current_retry_delay}s...")
                time.sleep(current_retry_delay)
                current_retry_delay *= 2
                continue
            else:
                return None, f"❌ Error: {e}"

    return None, f"❌ Failed Retries"


if not all_features:
    print("No features found from Step 1. Cannot proceed to Step 2.")
else:
    total_wfs_sites = len(all_features)
    
    # --- Checkpoint Loading ---    
    CHECKPOINT_GEOJSON_PATH = os.path.join(OUTPUT_DIR, "la_street_trees_detailed.checkpoint.geojson")
    detailed_trees_data = []
    processed_site_ids = set()
    newly_processed_since_last_save = 0

    if os.path.exists(CHECKPOINT_GEOJSON_PATH):
        print(f"Found checkpoint file: {CHECKPOINT_GEOJSON_PATH}. Loading existing detailed data...")
        try:
            gdf_checkpoint = gpd.read_file(CHECKPOINT_GEOJSON_PATH)
            features_from_checkpoint = []
            for _, row in gdf_checkpoint.iterrows():
                props = row.to_dict()
                geom_obj = row.geometry
                geom_dict = geom_obj.__geo_interface__ if geom_obj and hasattr(geom_obj, '__geo_interface__') else None
                if 'geometry' in props: # Remove if geopandas included it in properties
                    del props['geometry']
                
                features_from_checkpoint.append({"type": "Feature", "geometry": geom_dict, "properties": props})
                site_id_from_row = props.get(SORT_FIELD) # SORT_FIELD is 'site_id'
                if site_id_from_row is not None:
                    processed_site_ids.add(site_id_from_row)
            detailed_trees_data.extend(features_from_checkpoint)
            print(f"Loaded {len(detailed_trees_data)} records and {len(processed_site_ids)} unique processed site IDs from checkpoint.")
        except Exception as e:
            print(f"Error loading checkpoint file '{CHECKPOINT_GEOJSON_PATH}': {e}. Starting Step 2 fresh for details.")
            detailed_trees_data = []
            processed_site_ids = set()

    features_to_process_this_run = []
    if TEST_SITE_IDS_SUBSET and len(TEST_SITE_IDS_SUBSET) > 0:
        print(f"---!!! RUNNING IN TEST MODE: Processing ONLY {len(TEST_SITE_IDS_SUBSET)} site_ids: {TEST_SITE_IDS_SUBSET} !!!---")
        print("---!!! TEST MODE: Checkpoint loading for processed IDs is bypassed for these test IDs. Fetches will be attempted regardless of checkpoint. !!!---")
        # For test mode, we create dummy features just to carry the site_ids
        for test_site_id_str in TEST_SITE_IDS_SUBSET:
            current_test_id = None
            try: 
                current_test_id = int(test_site_id_str)
            except ValueError:
                try:
                    current_test_id = float(test_site_id_str)
                    if current_test_id.is_integer():
                        current_test_id = int(current_test_id)
                except ValueError:
                    current_test_id = test_site_id_str # Fallback if not clearly numeric
            
            features_to_process_this_run.append({
                "type": "Feature", 
                "properties": {SORT_FIELD: current_test_id, "tree_type": "TEST_SUBSET_ID"},
                "geometry": None 
            })
        # Note: In TEST_SITE_IDS_SUBSET mode, we are not pre-populating detailed_trees_data from the main checkpoint for these test IDs.
        # We want to see the API response for them. Any successfully fetched test IDs will be added to detailed_trees_data.
        # The main checkpoint saving logic will still apply if SAVE_INTERVAL is met.

    else: # Normal mode: Process all features from WFS data not in checkpoint
        # Load from checkpoint (if it exists)
        if os.path.exists(CHECKPOINT_GEOJSON_PATH):
            print(f"Found checkpoint file: {CHECKPOINT_GEOJSON_PATH}. Loading existing detailed data...")
            try:
                gdf_checkpoint = gpd.read_file(CHECKPOINT_GEOJSON_PATH)
                features_from_checkpoint = []
                for _, row in gdf_checkpoint.iterrows():
                    props = row.to_dict()
                    geom_obj = row.geometry
                    geom_dict = geom_obj.__geo_interface__ if geom_obj and hasattr(geom_obj, '__geo_interface__') else None
                    if 'geometry' in props: 
                        del props['geometry']
                    features_from_checkpoint.append({"type": "Feature", "geometry": geom_dict, "properties": props})
                    site_id_from_row = props.get(SORT_FIELD)
                    if site_id_from_row is not None:
                        processed_site_ids.add(site_id_from_row)
                detailed_trees_data.extend(features_from_checkpoint)
                print(f"Loaded {len(detailed_trees_data)} records and {len(processed_site_ids)} unique processed site IDs from checkpoint.")
            except Exception as e:
                print(f"Error loading checkpoint file '{CHECKPOINT_GEOJSON_PATH}': {e}. Starting Step 2 fresh for details (if not in test mode).")
                detailed_trees_data = [] # Reset if checkpoint loading failed
                processed_site_ids = set()
        
        # Filter WFS features against processed_site_ids from checkpoint
        for feature_wfs in all_features:
            site_id_wfs = feature_wfs.get("properties", {}).get(SORT_FIELD)
            if site_id_wfs is not None and site_id_wfs not in processed_site_ids:
                features_to_process_this_run.append(feature_wfs)
            elif site_id_wfs is None:
                 tqdm.write(f"⚠️ Missing '{SORT_FIELD}' in WFS feature properties: {feature_wfs.get('properties')}. Skipping this original feature.", refresh=True)

    if not features_to_process_this_run:
        # This condition means no new sites to process, either in test mode or normal mode.
        # If detailed_trees_data has items (from a successfully loaded checkpoint in normal mode), 
        # the script will proceed to the final conversion/upload steps with that data.
        # If detailed_trees_data is empty, those final steps will do nothing.
        print("No new sites to process for details (either all test IDs processed, or all WFS sites already in checkpoint, or WFS data was empty/problematic).")
        if not detailed_trees_data:
            print("And no data loaded from checkpoint (or test mode was active with no new sites to test). Final output files will likely be empty or not generated if script proceeds.")
    else:
        num_to_process_this_run = len(features_to_process_this_run)
        print(f"Found {total_wfs_sites} total sites from WFS. {len(processed_site_ids)} already processed (from checkpoint). Attempting to fetch details for {num_to_process_this_run} new sites concurrently...")

        tasks_completed_this_run = 0
        
        # --- Function for saving checkpoint ---
        def save_checkpoint_data(pbar=None):
            msg = f"\n--- Saving checkpoint: {len(detailed_trees_data)} total detailed records now in memory... ---"
            # Use pbar.write if available, otherwise print
            if pbar:
                pbar.write(msg)
            else:
                print(msg)
            
            if not detailed_trees_data:
                if pbar: pbar.write("No detailed data to save. Skipping checkpoint.")
                else: print("No detailed data to save. Skipping checkpoint.")
                return
            try:
                temp_checkpoint_path = CHECKPOINT_GEOJSON_PATH + ".tmp"
                gdf_current_checkpoint = gpd.GeoDataFrame.from_features(detailed_trees_data, crs="EPSG:4326")
                gdf_current_checkpoint.to_file(temp_checkpoint_path, driver="GeoJSON")
                os.replace(temp_checkpoint_path, CHECKPOINT_GEOJSON_PATH)
                if pbar: pbar.write(f"Checkpoint successfully saved to {CHECKPOINT_GEOJSON_PATH}")
                else: print(f"Checkpoint successfully saved to {CHECKPOINT_GEOJSON_PATH}")
                return True
            except Exception as e:
                if pbar: pbar.write(f"Error saving checkpoint to '{CHECKPOINT_GEOJSON_PATH}': {e}")
                else: print(f"Error saving checkpoint to '{CHECKPOINT_GEOJSON_PATH}': {e}")
                return False

        # --- Main processing loop with graceful exit on interruption ---
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
                future_to_original_feature = {
                    executor.submit(fetch_site_details, feature.get("properties", {}).get(SORT_FIELD)): feature
                    for feature in features_to_process_this_run
                }

                with tqdm(concurrent.futures.as_completed(future_to_original_feature), total=len(future_to_original_feature), desc="Processing site details") as pbar:
                    for future in pbar:
                        original_feature = future_to_original_feature[future]
                        site_id = original_feature.get("properties", {}).get(SORT_FIELD)

                        try:
                            parsed_data, error_status = future.result()

                            if error_status:
                                pbar.set_postfix_str(f"{error_status} for {site_id}", refresh=True)
                            elif parsed_data:
                                pbar.set_postfix_str(f"✅ Success: {site_id}", refresh=True)
                                
                                combined_data = {
                                    "type": "Feature",
                                    "geometry": original_feature.get("geometry"),
                                    "properties": {
                                        **original_feature.get("properties", {}),
                                        **parsed_data
                                    }
                                }
                                detailed_trees_data.append(combined_data)
                                newly_processed_since_last_save += 1
                                processed_site_ids.add(site_id)

                                if newly_processed_since_last_save >= SAVE_INTERVAL:
                                    if save_checkpoint_data(pbar):
                                        newly_processed_since_last_save = 0
                        
                        except Exception as exc:
                            pbar.set_postfix_str(f"💥 Exception for {site_id}: {exc}", refresh=True)

        except KeyboardInterrupt:
            print("\n\nScript interrupted by user (Ctrl+C).")
            # Final save attempt on interruption
            save_checkpoint_data()
            print("Exiting.")
            # Exit gracefully
            try:
                import sys
                sys.exit(130) # Standard exit code for Ctrl+C
            except:
                os._exit(130)

    # Final summary counts based on actual attempts and successes in this run
    # The len(detailed_trees_data) will include those loaded from checkpoint + newly added.
    # tasks_completed_this_run refers to only new tasks.
    print(f"\n🎉 Step 2 processing for new sites finished. Total detailed records now in memory: {len(detailed_trees_data)}.") 
    # (This count includes checkpointed data + new data from this run)


    if detailed_trees_data:
        # --- Convert to GeoDataFrame ---
        print("\n--- Converting to GeoDataFrame ---")
        try:
            gdf = gpd.GeoDataFrame.from_features(detailed_trees_data, crs="EPSG:4326")
            print(f"Successfully created GeoDataFrame with {len(gdf)} features.")

            # --- Save to Local Files ---
            print("\n--- Saving data to local files ---")
            files_to_upload = []

            # 1. GeoJSON
            try:
                gdf.to_file(DETAILED_JSON_PATH, driver="GeoJSON")
                print(f"Saved GeoJSON → {DETAILED_JSON_PATH}")
                files_to_upload.append(DETAILED_JSON_PATH)
            except Exception as e:
                print(f"Error saving GeoJSON: {e}")

            # 2. Shapefile (zipped)
            temp_shp_dir = os.path.join(OUTPUT_DIR, "temp_shp_export")
            shp_name = "la_street_trees_detailed.shp"
            os.makedirs(temp_shp_dir, exist_ok=True)
            try:
                # Truncate field names for shapefile compatibility if necessary
                # Shapefile driver will attempt this, but explicit control might be needed for complex names
                # For now, rely on geopandas to handle it.
                gdf.to_file(os.path.join(temp_shp_dir, shp_name), driver="ESRI Shapefile")
                print(f"Exported Shapefile components to {temp_shp_dir}")
                with zipfile.ZipFile(SHP_ZIP_PATH, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for file_to_zip in glob.glob(os.path.join(temp_shp_dir, "*")) :
                        zipf.write(file_to_zip, os.path.basename(file_to_zip))
                print(f"Zipped Shapefile → {SHP_ZIP_PATH}")
                files_to_upload.append(SHP_ZIP_PATH)
            except Exception as e:
                print(f"Error saving Shapefile: {e}")
            finally:
                if os.path.exists(temp_shp_dir):
                    shutil.rmtree(temp_shp_dir)
                    print(f"Cleaned up temporary shapefile directory: {temp_shp_dir}")
            
            # 3. File Geodatabase (zipped)
            temp_gdb_export_dir = os.path.join(OUTPUT_DIR, "temp_gdb_export") # Parent for the .gdb folder
            gdb_name = "la_street_trees_detailed.gdb"
            full_gdb_path = os.path.join(temp_gdb_export_dir, gdb_name)
            os.makedirs(temp_gdb_export_dir, exist_ok=True)
            try:
                gdf.to_file(full_gdb_path, driver="OpenFileGDB") # Or "FileGDB" if available/preferred
                print(f"Exported File GDB to {full_gdb_path}")
                with zipfile.ZipFile(GDB_ZIP_PATH, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    # Zip the entire .gdb directory
                    for root, dirs, files in os.walk(full_gdb_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            # Arcname relative to the temp_gdb_export_dir to maintain .gdb structure in zip
                            arcname = os.path.relpath(file_path, temp_gdb_export_dir)
                            zipf.write(file_path, arcname)
                print(f"Zipped File GDB → {GDB_ZIP_PATH}")
                files_to_upload.append(GDB_ZIP_PATH)
            except Exception as e:
                print(f"Error saving File Geodatabase: {e}")
                print("Note: Saving to FileGDB often requires specific drivers (OpenFileGDB or ESRI's FileGDB API).")
                print("Ensure your geopandas installation supports the chosen driver.")
            finally:
                if os.path.exists(temp_gdb_export_dir):
                    shutil.rmtree(temp_gdb_export_dir)
                    print(f"Cleaned up temporary GDB directory: {temp_gdb_export_dir}")

            # --- Upload to S3 ---
            if files_to_upload:
                print(f"\n--- Uploading {len(files_to_upload)} file(s) to S3 ---")
                try:
                    session = boto3.Session(profile_name=S3_PROFILE_NAME)
                    s3_client = session.client("s3")
                    for local_file_path in files_to_upload:
                        s3_key = os.path.join(S3_PREFIX, os.path.basename(local_file_path))
                        print(f"Uploading {local_file_path} to s3://{S3_BUCKET}/{s3_key}...")
                        s3_client.upload_file(local_file_path, S3_BUCKET, s3_key)
                        print(f"Successfully uploaded {os.path.basename(local_file_path)}")
                except boto3.exceptions.NoCredentialsError:
                    print(f"S3 Upload Error: AWS credentials not found. Ensure profile '{S3_PROFILE_NAME}' is configured.")
                except boto3.exceptions.Boto3Error as e:
                    print(f"S3 Upload Error (Boto3): {e}")
                except Exception as e:
                    print(f"S3 Upload Error: {e}")
            else:
                print("\nNo files were successfully created to upload to S3.")

        except ImportError:
            print("GeoPandas library not found. Please install it (e.g., pip install geopandas) to enable GeoJSON, Shapefile and GDB export.")
            # Fallback to original JSON dump if GeoPandas fails for broader compatibility
            # This part is removed as the user specifically requested GeoJSON, SHP, GDB.
            # If GeoPandas is critical, we should not have a simple JSON fallback for this part.
            print("Skipping geospatial file format export and S3 upload due to missing GeoPandas or error during conversion.")
        except Exception as e:
            print(f"An error occurred during GeoDataFrame conversion or file saving: {e}")
            print("Skipping geospatial file format export and S3 upload.")
            
    else:
        print("\nNo detailed tree data fetched, skipping file export and S3 upload.")


print("\n--- Script Finished ---")
