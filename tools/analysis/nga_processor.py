import os
import glob
import subprocess
import geopandas as gpd
import pandas as pd

# Path to your directory with the downloaded shapefile components
shp_dir = os.path.join(os.path.dirname(__file__), "../data/large")

# Get all .shp files from the directory
shp_files = glob.glob(os.path.join(shp_dir, "*.shp"))

# Read each shapefile into a GeoDataFrame
gdfs = [gpd.read_file(shp) for shp in shp_files]

# Concatenate all GeoDataFrames into one
combined_gdf = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True))

# Output the combined GeoDataFrame to a GeoPackage
output_gpkg = os.path.join(shp_dir, "combined_trees.gpkg")
combined_gdf.to_file(output_gpkg, layer="trees", driver="GPKG")
print(f"Data saved to {output_gpkg}")

def main():
    # Paths and file names
    large_dir = os.path.join(os.path.dirname(__file__), "../data/large")
    processed_dir = os.path.join(os.path.dirname(__file__), "../data/large")
    os.makedirs(processed_dir, exist_ok=True)

    # Input GeoPackage with trees (from previous download)
    trees_gpkg = os.path.join(large_dir, "combined_trees.gpkg")
    
    # Read trees layer and standardize column names to lowercase
    print("Reading trees from GeoPackage...")
    trees_gdf = gpd.read_file(trees_gpkg, layer="trees")
    trees_gdf.columns = trees_gdf.columns.str.lower()
    
    # Read LA neighborhoods from a public GeoJSON URL
    hood_url = "https://stilesdata.com/gis/la_city_hoods_county_munis.geojson"
    print("Reading LA neighborhoods from URL...")
    hoods_gdf = gpd.read_file(hood_url)
    
    # Perform spatial join to assign each tree a neighborhood (using 'within')
    print("Performing spatial join to assign neighborhood names...")
    trees_with_hoods = gpd.sjoin(trees_gdf, hoods_gdf, how='left', predicate='within')
    
    # (Optional) Count trees per neighborhood and merge counts back into hoods_gdf
    point_counts = trees_with_hoods.groupby('index_right').size().rename('trees')
    hoods_with_counts = hoods_gdf.merge(point_counts, left_index=True, right_index=True, how='left')
    print("Tree counts per neighborhood computed.")
    
    # Create a slim GeoDataFrame of trees with selected columns (adjust as needed)
    slim_trees = trees_with_hoods[['name', 'height_m', 'city', 'geometry']].copy()
    
    # Export slim trees as GeoJSON for backup/inspection
    slim_geojson = os.path.join(processed_dir, "combined_trees.geojson")
    print(f"Saving slim trees to GeoJSON at {slim_geojson} ...")
    slim_trees.to_file(slim_geojson, driver="GeoJSON")
    
    # Also export the joined result as a new processed GeoPackage
    processed_gpkg = os.path.join(processed_dir, "combined_trees.gpkg")
    print(f"Saving processed trees with neighborhoods to GeoPackage at {processed_gpkg} ...")
    slim_trees.to_file(processed_gpkg, layer="trees", driver="GPKG")
    
    # Convert the processed GeoPackage to GeoJSON using ogr2ogr via subprocess
    converted_geojson = os.path.join(processed_dir, "combined_trees_converted.geojson")
    print("Converting GeoPackage to GeoJSON with ogr2ogr...")
    subprocess.run(
        ["ogr2ogr", "-f", "GeoJSON", converted_geojson, processed_gpkg, "trees"],
        check=True
    )
    print(f"GeoJSON created at: {converted_geojson}")
    
    # Use tippecanoe to create vector tiles (MBTiles) from the GeoJSON
    output_mbtiles = os.path.join(processed_dir, "trees.mbtiles")
    tippecanoe_command = [
        "tippecanoe",
        "-o", output_mbtiles,
        "-Z", "10",  # minimum zoom level
        "-z", "16",  # maximum zoom level
        "--drop-densest-as-needed",
        converted_geojson,
    ]
    print("Running tippecanoe to create vector tiles (MBTiles)...")
    subprocess.run(tippecanoe_command, check=True)
    print(f"MBTiles file created at: {output_mbtiles}")

if __name__ == "__main__":
    main()