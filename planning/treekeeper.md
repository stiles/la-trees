## Overview

We have a two-stage workflow:

1. **Bulk-download a "light" street-tree inventory** via WFS.
2. **Fetch detailed records** for each tree by calling TreeKeeper's `getSitePieces` API, then process into multiple geospatial formats using `geopandas`.

These steps let us capture everything from basic locations to full species, planting dates, and addresses. The final enriched data (GeoJSON, zipped Shapefile, and zipped File Geodatabase) is then optionally uploaded to Amazon S3.

---

### 1. Pull `CityPlantsLA_UFDInventory(Public)` (the "slim" layer)

- **Why**:
  This WFS layer exposes only two fields per feature—`site_id` (an integer) and `tree_type`—plus geometry. We don't get species or common name here. Instead, we grab it first to build a list of all `site_id` values without hammering the API one‐by‐one.

- **How**:
  - The script first checks if `data/raw/cities/los-angeles-city/la_street_trees.geojson` exists and contains data. If so, this step is skipped, and the existing data is loaded.
  - If not, configure cookies and headers exactly as your browser's DevTools shows.
  - Hit the GeoServer endpoint (`geoserver/Treekeeper/ows`) with a WFS 2.0.0 `GetFeature` request.
  - Request 2 000 features at a time (via `count=2000` and `startIndex=<offset>`), sorted by `site_id`. That prevents "no primary key" errors.
  - As soon as the first batch returns, write it to `data/raw/cities/los-angeles-city/sample_trees.geojson` so you can inspect fields and confirm everything looks correct.
  - Continue fetching in 2 000-feature chunks until you receive an empty array.
  - Once complete, compile all batches into one large GeoJSON—`data/raw/cities/los-angeles-city/la_street_trees.geojson`.

- **Result**:
  - `data/raw/cities/los-angeles-city/sample_trees.geojson`: first 2 000 records (if downloaded fresh), each feature containing `site_id`, `tree_type`, and location.
  - `data/raw/cities/los-angeles-city/la_street_trees.geojson`: full "slim" inventory (e.g., ~800 000 features), ready for step 2. This file is reused on subsequent runs if it exists.

---

### 2. Call `getSitePieces` for each `site_id` and process data

- **Why**:
  The WFS layer doesn't include rich attributes like `common` (common name), `scientific` (Latin name), `address`, or `plantdate`. To harvest everything, we use `site_id` as a key, looping through each one and retrieving full "site pieces" JSON. This data is then converted into standard geospatial formats for wider usability.

- **How**:
  - Read `data/raw/cities/los-angeles-city/la_street_trees.geojson` (or use the in-memory list of `site_id` values if Step 1 was just run).
  - For each `site_id`, send a GET request to
    ```
    https://losangelesca.treekeepersoftware.com/cffiles/site.cfc
      ?method=getSitePieces
      &searchID=<site_id>
      &idType=site
      &requestSite=true
      &requestWork=false
      &requestCall=false
      &requestArchives=false
    ```
    (Ensure cookies and headers match your logged‐in session.)
  - Each successful call returns a JSON object—typically under `info["SITES"][0]`—containing `common`, `scientific`, `address`, `species_id`, `plantdate`, and more.
  - The script merges the WFS geometry and original properties (like `tree_type`) with these detailed attributes.
  - Accumulate these full, combined records into a list. Be mindful of API rate limits; the script includes a small delay between requests.
  - After fetching all details, the list of features is converted to a `geopandas` GeoDataFrame.
  - The GeoDataFrame is then saved locally in multiple formats.

- **Result**:
  - `data/processed/cities/los-angeles-city/la_street_trees_detailed.geojson`: A GeoJSON file with all enriched tree features.
  - `data/processed/cities/los-angeles-city/la_street_trees_detailed_shp.zip`: A zipped Shapefile containing the enriched tree features.
  - `data/processed/cities/los-angeles-city/la_street_trees_detailed_gdb.zip`: A zipped File Geodatabase containing the enriched tree features.
  These files allow for analysis of species distributions, map generation with labels, or calculation of planting timelines using various GIS software.

---

### 3. Upload to Amazon S3 (Optional)

- **Why**:
  For persistent storage, sharing, or integration with other cloud services, the final processed geospatial files can be uploaded to an S3 bucket.

- **How**:
  - After the GeoJSON, zipped Shapefile, and zipped File Geodatabase are successfully created locally, the script attempts to upload them.
  - It uses `boto3` and requires AWS credentials configured (e.g., via an AWS CLI profile like 'haekeo').
  - The files are uploaded to `s3://stilesdata.com/trees/los-angeles/` with their respective filenames (e.g., `la_street_trees_detailed.geojson`, `la_street_trees_detailed_shp.zip`, `la_street_trees_detailed_gdb.zip`).

- **Result**:
  - The `la_street_trees_detailed.geojson`, `la_street_trees_detailed_shp.zip`, and `la_street_trees_detailed_gdb.zip` files are available in the specified S3 location.

---

## Next Steps & Tips

1. **Dependencies**:
   - Ensure `geopandas` and its dependencies (`fiona`, `pyproj`, `shapely`, GDAL, etc.) are installed in the Python environment. This can typically be done via `pip install geopandas` or, for a smoother experience with complex dependencies, `conda install geopandas`.
   - `boto3` is required for S3 uploads (`pip install boto3`).

2. **Verification**:
   - After step 1 (if data was downloaded fresh), load `data/raw/cities/los-angeles-city/sample_trees.geojson` in QGIS or GeoPandas. Confirm that each feature has only `site_id` and `tree_type`.
   - After step 2, load the output files (e.g., `data/processed/cities/los-angeles-city/la_street_trees_detailed.geojson` or the unzipped Shapefile/GDB) into GIS software. Spot-check a few `site_id` values to ensure you're getting `common`, `scientific`, geometry, and other expected fields back.

3. **Error Handling**:
   - The script includes basic error handling for API requests, file saving (including `geopandas` operations), and S3 uploads.
   - If any `getSitePieces` call returns an HTTP error or missing data, it logs the `site_id` and continues. Consider adding failed IDs to a retry list for more robust processing.
   - If GeoServer times out on large WFS requests, reduce `CHUNK_SIZE` in the script (e.g., to 1 000 or 500).
   - File Geodatabase export might require specific GDAL drivers (OpenFileGDB is used; ESRI FileGDB API is an alternative if available and configured).

4. **Data Merging**:
   - The script already merges WFS geometry and basic properties with the detailed attributes from `getSitePieces`, using `site_id` as the join key. The final output is a single, enriched dataset available in multiple formats.

5. **Performance**:
   - Step 1 now intelligently skips re-downloading if raw data exists.
   - For thousands of `site_id` calls in Step 2, the script processes them sequentially with a small delay. For very large datasets or faster processing, consider modifying the script to use `concurrent.futures.ThreadPoolExecutor` (Python) or similar—just don't flood the API.
   - The script writes the full detailed output at the end of Step 2. For very long runs, consider writing partial outputs to disk (e.g., every N trees) to avoid data loss if the script crashes mid-process, especially before the `geopandas` conversion stage.

6. **Credentials**:
   - Ensure `COOKIES` and `HEADERS` in the script are valid for TreeKeeper access.
   - For S3 upload, ensure your AWS credentials profile (e.g., 'haekeo') is correctly configured and has permissions to write to the target S3 bucket and path.

7. **Known Issues: Server Blocking / 403 Forbidden Errors**:
   - The TreeKeeper server may actively block sustained scripted access, even for slow, sequential requests. This typically manifests as a wall of `HTTP 403 Forbidden` errors.
   - The most common cause is that the session `COOKIES` and `HEADERS` have been invalidated by the server. To resolve this, you must get a fresh set of credentials by logging into the site in a browser and copying them again. This may need to be done frequently.
   - If the issue persists even with fresh credentials, it indicates a more aggressive blocking policy. In this case, the most reliable alternatives are to use an official data source (e.g., from a public records request) or to re-implement the fetching logic using a browser automation tool like Selenium, which is more difficult for servers to detect.

With these stages, you'll efficiently harvest the entire LA street-tree inventory—first grabbing every ID/point (or loading existing data), then enriching each with full details, converting to multiple geospatial formats, and finally uploading to S3. Good luck!
