import time
import requests
import json
import os
import boto3
import geopandas as gpd
import zipfile
import shutil
from tqdm import tqdm
import getpass
from pyproj import Transformer

# --- FILE & PATHS ---
WFS_URL = "https://geola.daveytreekeeper.com/geoserver/Treekeeper/ows"
# Using UFDSpeciesLabel which contains location + species data directly
TYPE_NAME = "Treekeeper:streetsla_UFDSpeciesLabel"
CHUNK_SIZE = 5000  # Larger chunks since we're not doing individual API calls
SORT_FIELD = "site_id"
OUTPUT_DIR = "data/processed/cities/los-angeles-city"
RAW_OUTPUT_DIR = "data/raw/cities/los-angeles-city"
FULL_GEOJSON_PATH = os.path.join(RAW_OUTPUT_DIR, "la_street_trees_species.geojson")
CONVERTED_GEOJSON_PATH = os.path.join(OUTPUT_DIR, "la_street_trees_latlon.geojson")
SHP_ZIP_PATH = os.path.join(OUTPUT_DIR, "la_street_trees_shp.zip")
GDB_ZIP_PATH = os.path.join(OUTPUT_DIR, "la_street_trees_gdb.zip")

# --- S3 CONFIG ---
S3_BUCKET = "stilesdata.com"
S3_PREFIX = "trees/los-angeles/"
S3_PROFILE_NAME = "haekeo"

# --- COORDINATE TRANSFORMATION ---
# Transform from California State Plane Zone V (EPSG:2229) to WGS84 (EPSG:4326)
transformer = Transformer.from_crs("EPSG:2229", "EPSG:4326", always_xy=True)

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(RAW_OUTPUT_DIR, exist_ok=True)

print("=== LA Street Trees Data Collection ===")
print(f"Downloading from: {TYPE_NAME}")
print(f"This layer contains street tree locations and species data directly from StreetsLA")
print("No API scraping required - all data available via WFS")
print("=" * 50)

# --- FETCH WFS DATA ---
print("\n--- Fetching Street Trees with Species Data ---")
all_features = []

# Check if we already have the raw data
if os.path.exists(FULL_GEOJSON_PATH) and os.path.getsize(FULL_GEOJSON_PATH) > 0:
    print(f"Found existing raw data at {FULL_GEOJSON_PATH}. Loading it.")
    try:
        with open(FULL_GEOJSON_PATH, "r") as f:
            data = json.load(f)
            all_features = data.get("features", [])
        print(f"Successfully loaded {len(all_features)} features from file.")
    except Exception as e:
        print(f"Error loading {FULL_GEOJSON_PATH}: {e}. Proceeding to re-download.")
        all_features = []
else:
    print(f"No existing raw data found. Downloading from WFS...")

if not all_features:
    def fetch_chunk(start_index):
        """Fetch a chunk of WFS data"""
        params = {
            "service": "WFS",
            "version": "2.0.0", 
            "request": "GetFeature",
            "typeName": TYPE_NAME,
            "outputFormat": "application/json",
            "count": str(CHUNK_SIZE),
            "startIndex": str(start_index),
            "sortBy": f"{SORT_FIELD} A"
        }
        
        resp = requests.get(WFS_URL, params=params, timeout=120)
        resp.raise_for_status()
        return resp.json()

    offset = 0
    with tqdm(desc="Downloading street trees", unit=" trees") as pbar:
        while True:
            try:
                data = fetch_chunk(offset)
                feats = data.get("features", [])
                if not feats:
                    break
                    
                all_features.extend(feats)
                pbar.update(len(feats))
                pbar.set_postfix_str(f"Total: {len(all_features)}")
                offset += CHUNK_SIZE
                
            except requests.HTTPError as e:
                pbar.write(f"✖ HTTP {e.response.status_code} fetching WFS data. Stopping.")
                break
            except Exception as e:
                pbar.write(f"✖ Error fetching data: {e}. Stopping.")
                break

    # Save the raw data
    if all_features:
        raw_geojson = {
            "type": "FeatureCollection",
            "features": all_features,
            "crs": {
                "type": "name",
                "properties": {"name": "urn:ogc:def:crs:EPSG::2229"}
            }
        }
        
        with open(FULL_GEOJSON_PATH, "w") as f:
            json.dump(raw_geojson, f)
        print(f"✅ Saved raw WFS data → {FULL_GEOJSON_PATH}")

# --- COORDINATE TRANSFORMATION ---
print(f"\n--- Converting Coordinates to Lat/Lon ---")
print(f"Source: California State Plane Zone V (EPSG:2229)")
print(f"Target: WGS84 Geographic (EPSG:4326)")

if all_features:
    # Transform coordinates for each feature
    converted_features = []
    
    with tqdm(all_features, desc="Converting coordinates") as pbar:
        for feature in pbar:
            # Copy the feature
            new_feature = {
                "type": "Feature",
                "properties": feature["properties"].copy(),
                "geometry": None
            }
            
            # Transform coordinates
            if feature.get("geometry") and feature["geometry"].get("coordinates"):
                x, y = feature["geometry"]["coordinates"]
                lon, lat = transformer.transform(x, y)
                
                new_feature["geometry"] = {
                    "type": "Point",
                    "coordinates": [lon, lat]
                }
            
            converted_features.append(new_feature)

    # Create final GeoJSON with WGS84 coordinates
    final_geojson = {
        "type": "FeatureCollection",
        "features": converted_features,
        "crs": {
            "type": "name", 
            "properties": {"name": "urn:ogc:def:crs:EPSG::4326"}
        }
    }
    
    # Save converted data
    with open(CONVERTED_GEOJSON_PATH, "w") as f:
        json.dump(final_geojson, f)
    print(f"✅ Saved converted data → {CONVERTED_GEOJSON_PATH}")

    # --- ANALYZE DATASET ---
    print(f"\n--- Dataset Analysis ---")
    print(f"Total street trees: {len(converted_features):,}")
    
    # Analyze tree species
    species_count = {}
    for feature in converted_features:
        species = feature["properties"].get("tree_common", "Unknown")
        species_count[species] = species_count.get(species, 0) + 1
    
    print(f"Unique species: {len(species_count)}")
    print("\nTop 10 most common species:")
    for species, count in sorted(species_count.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {species}: {count:,} trees")
    
    # Check for vacant sites and stumps
    vacant_count = species_count.get("Vacant Site (UFD)", 0)
    stump_count = species_count.get("Stump", 0)
    actual_trees = len(converted_features) - vacant_count - stump_count
    
    print(f"\nTree status:")
    print(f"  Living trees: {actual_trees:,}")
    print(f"  Vacant sites: {vacant_count:,}")
    print(f"  Stumps: {stump_count:,}")

    # --- EXPORT TO MULTIPLE FORMATS ---
    print(f"\n--- Exporting to Multiple Formats ---")
    
    try:
        # Load as GeoDataFrame for easy export
        gdf = gpd.GeoDataFrame.from_features(converted_features, crs="EPSG:4326")
        files_to_upload = []
        
        # GeoJSON (already saved)
        files_to_upload.append(CONVERTED_GEOJSON_PATH)
        
        # Zipped Shapefile
        print("Creating Shapefile...")
        temp_shp_dir = os.path.join(OUTPUT_DIR, "temp_shp")
        os.makedirs(temp_shp_dir, exist_ok=True)
        try:
            shp_path = os.path.join(temp_shp_dir, "la_street_trees.shp")
            gdf.to_file(shp_path, driver="ESRI Shapefile")
            
            with zipfile.ZipFile(SHP_ZIP_PATH, 'w', zipfile.ZIP_DEFLATED) as zf:
                for root, _, files in os.walk(temp_shp_dir):
                    for file in files:
                        if not file.endswith('.lock'):
                            file_path = os.path.join(root, file)
                            zf.write(file_path, os.path.relpath(file_path, temp_shp_dir))
            
            files_to_upload.append(SHP_ZIP_PATH)
            print(f"✅ Shapefile → {SHP_ZIP_PATH}")
        except Exception as e:
            print(f"❌ Error creating Shapefile: {e}")
        finally:
            shutil.rmtree(temp_shp_dir, ignore_errors=True)
        
        # Zipped FileGDB
        print("Creating File Geodatabase...")
        temp_gdb_dir = os.path.join(OUTPUT_DIR, "temp_gdb")
        os.makedirs(temp_gdb_dir, exist_ok=True)
        try:
            gdb_path = os.path.join(temp_gdb_dir, "la_street_trees.gdb")
            gdf.to_file(gdb_path, driver="OpenFileGDB")
            
            with zipfile.ZipFile(GDB_ZIP_PATH, 'w', zipfile.ZIP_DEFLATED) as zf:
                for root, _, files in os.walk(temp_gdb_dir):
                    for file in files:
                        if not file.endswith('.lock'):
                            file_path = os.path.join(root, file)
                            zf.write(file_path, os.path.relpath(file_path, temp_gdb_dir))
            
            files_to_upload.append(GDB_ZIP_PATH)
            print(f"✅ File Geodatabase → {GDB_ZIP_PATH}")
        except Exception as e:
            print(f"❌ Error creating FileGDB: {e}")
        finally:
            shutil.rmtree(temp_gdb_dir, ignore_errors=True)

        # --- S3 UPLOAD ---
        if files_to_upload and S3_PROFILE_NAME:
            print(f"\n--- Uploading {len(files_to_upload)} file(s) to S3 ---")
            try:
                session = boto3.Session(profile_name=S3_PROFILE_NAME)
                s3 = session.client("s3")
                
                for file_path in files_to_upload:
                    filename = os.path.basename(file_path)
                    s3_key = f"{S3_PREFIX}{filename}"
                    
                    print(f"Uploading {filename}...")
                    s3.upload_file(file_path, S3_BUCKET, s3_key)
                    print(f"✅ Uploaded to s3://{S3_BUCKET}/{s3_key}")
                    
            except Exception as e:
                print(f"❌ S3 Upload Error: {e}")
        
        print(f"\n🎉 Data collection complete!")
        print(f"📁 Local files saved to: {OUTPUT_DIR}")
        if S3_PROFILE_NAME:
            print(f"☁️ Files uploaded to: s3://{S3_BUCKET}/{S3_PREFIX}")
            
    except Exception as e:
        print(f"❌ Error during export: {e}")

else:
    print("❌ No features downloaded. Please check the WFS connection and try again.")

print("\n--- Script Finished ---")