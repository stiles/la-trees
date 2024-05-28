import requests
import geopandas as gpd
import pandas as pd

offset = 0
feature_limit = 2000
has_next_page = True

# Initialize an empty list to store features
all_features_list = []

# Base URL for the Esri service
base_url = "https://services2.arcgis.com/zNjnZafDYCAJAbN0/ArcGIS/rest/services/Street_ROW_Trees/FeatureServer/0/query?outFields=*&where=1%3D1&f=pgeojson&resultOffset={}&resultRecordCount={}"

while has_next_page:
    # Construct the URL with the current offset
    url = base_url.format(offset, feature_limit)

    # Send a request
    response = requests.get(url)
    data = response.json()

    # Check if the response contains features
    if "features" in data:
        # Convert the response to a GeoDataFrame
        features_gdf = gpd.GeoDataFrame.from_features(data["features"], crs="EPSG:4326")

        # Append the current page of features to the list
        all_features_list.append(features_gdf)

        # Increment the offset for the next page
        offset += feature_limit

        # Check if there are more features to retrieve
        has_next_page = len(features_gdf) == feature_limit
    else:
        # No more features to retrieve
        has_next_page = False

# Concatenate all collected GeoDataFrames
if all_features_list:
    all_features_df = pd.concat(all_features_list, axis=0, ignore_index=True)
else:
    all_features_df = gpd.GeoDataFrame()

# Reset index and ensure the GeoDataFrame has a proper CRS
all_features_df.reset_index(drop=True, inplace=True)
all_features_df.crs = "EPSG:4326"

# Display the dataframe
all_features_df.head()