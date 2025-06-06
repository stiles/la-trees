# Los Angeles street trees

A spatial data collection of trees planted within municipal right of way in Los Angeles and parts of Los Angeles County, in `geojson` and `Esri Shapefile` formats. (Some larger cities are stored here as `csv` to avoid Github's 100MB file size restriction.)

This repository contains **1.6 million** records of individual trees in **40+** cities collected in recents years as a hobby project and during my time as a reporter at the *Los Angeles Times*. Tree records in a county the size of Los Angeles become immediately dated and incomplete after their inital collection, so I can't guarantee the accuracy or completeness of the data.

The data are used to create this interactive map showing LA's Jacaranda locations: [https://jacarandamap.com](https://jacarandamap.com). 

![](images/og-image.png?raw=true)

The data used in the Jacaranda project is too large to store here, but it's on S3 in GeoJSON format: 

- [LA neighborhoods](https://stilesdata.com/la/la_county_hoods.geojson)
- [Jacaranda tree locations](https://stilesdata.com/jacarandas/lacounty_jacaranda_locations.geojson)
- [All LA street tree locations (caution: ~500MB)](https://s3.us-west-1.amazonaws.com/stilesdata.com/jacarandas/la_county_tree_locations.geojson)

Questions? [Email me](mailto:mattstiles@gmail.com).

## Municpalities collected, by name

**Municipality &darr;** | Tree count | Population
---------------- | ----------: | ----------:
[Agoura Hills](https://github.com/stiles/la-trees/tree/main/data/municipalities/agoura-hills) | 5,100 | 20,330
[Alhambra](https://github.com/stiles/la-trees/tree/main/data/municipalities/alhambra) | 20,100 | 83,653
[Arcadia](https://github.com/stiles/la-trees/tree/main/data/municipalities/arcadia) | 15,600 | 56,364
[Artesia](https://github.com/stiles/la-trees/tree/main/data/municipalities/artesia) | 2,500 | 16,522
[Bell Gardens](https://github.com/stiles/la-trees/tree/main/data/municipalities/bell-gardens) | 7,000 | 42,072
[Bellflower](https://github.com/stiles/la-trees/tree/main/data/municipalities/bellflower) | 8,400 | 76,616
[Beverly Hills](https://github.com/stiles/la-trees/tree/main/data/municipalities/beverly-hills) | 29,000 | 34,109
[Burbank](https://github.com/stiles/la-trees/tree/main/data/municipalities/burbank) | 37,000 | 103,340
[Carson](https://github.com/stiles/la-trees/tree/main/data/municipalities/carson) | 22,500 | 91,714
[Cerritos](https://github.com/stiles/la-trees/tree/main/data/municipalities/cerritos) | 31,300 | 49,041
[Covina](https://github.com/stiles/la-trees/tree/main/data/municipalities/covina) | 14,600 | 47,796
[Culver City](https://github.com/stiles/la-trees/tree/main/data/municipalities/culver-city) | 16,900 | 38,883
[Diamond Bar](https://github.com/stiles/la-trees/tree/main/data/municipalities/diamond-bar) | 20,100 | 55,544
[Downey](https://github.com/stiles/la-trees/tree/main/data/municipalities/downey) | 18,500 | 111,772
[Duarte](https://github.com/stiles/la-trees/tree/main/data/municipalities/duarte) | 7,900 | 21,321
[El Monte](https://github.com/stiles/la-trees/tree/main/data/municipalities/el-monte) | 11,000 | 113,475
[El Segundo](https://github.com/stiles/la-trees/tree/main/data/municipalities/el-segundo) | 6,400 | 16,654
[Glendale](https://github.com/stiles/la-trees/tree/main/data/municipalities/glendale) | 56,000 | 203,054
[Glendora](https://github.com/stiles/la-trees/tree/main/data/municipalities/glendora) | 12,600 | 50,073
[Inglewood](https://github.com/stiles/la-trees/tree/main/data/municipalities/inglewood) | 21,800 | 109,673
[La Mirada](https://github.com/stiles/la-trees/tree/main/data/municipalities/la-mirada) | 17,000 | 48,527
[Lancaster](https://github.com/stiles/la-trees/tree/main/data/municipalities/lancaster) | 46,000 | 160,316
[Lawndale](https://github.com/stiles/la-trees/tree/main/data/municipalities/lawndale) | 7,400 | 32,769
[Lomita](https://github.com/stiles/la-trees/tree/main/data/municipalities/lomita) | 3,000 | 20,256
[Long Beach](https://github.com/stiles/la-trees/tree/main/data/municipalities/long-beach) | 140,000 | 462,257
[Los Angeles City](https://github.com/stiles/la-trees/tree/main/data/municipalities/los-angeles-city) | 545,000 | 3,792,621
[Los Angeles County](https://github.com/stiles/la-trees/tree/main/data/municipalities/los-angeles-county) | 99,000 | 10,100,000
[Malibu](https://github.com/stiles/la-trees/tree/main/data/municipalities/malibu) | 7,400 | 12,645
[Norwalk](https://github.com/stiles/la-trees/tree/main/data/municipalities/norwalk) | 21,400 | 105,549
[Palmdale](https://github.com/stiles/la-trees/tree/main/data/municipalities/palmdale) | 19,000 | 152,750
[Paramount](https://github.com/stiles/la-trees/tree/main/data/municipalities/paramount) | 7,800 | 54,098
[Pasadena](https://github.com/stiles/la-trees/tree/main/data/municipalities/pasadena) | 71,000 | 137,122
[Pomona](https://github.com/stiles/la-trees/tree/main/data/municipalities/pomona) | 50,000 | 149,058
[Rancho Palos Verdes](https://github.com/stiles/la-trees/tree/main/data/municipalities/rancho-palos-verdes) | 13,500 | 41,643
[Redondo Beach](https://github.com/stiles/la-trees/tree/main/data/municipalities/redondo-beach) | 13,000 | 66,748
[San Dimas](https://github.com/stiles/la-trees/tree/main/data/municipalities/san-dimas) | 10,400 | 33,371
[San Fernando](https://github.com/stiles/la-trees/tree/main/data/municipalities/san-fernando) | 9,500 | 23,645
[San Gabriel](https://github.com/stiles/la-trees/tree/main/data/municipalities/san-gabriel) | 9,900 | 39,718
[San Marino](https://github.com/stiles/la-trees/tree/main/data/municipalities/san-marino) | 9500 | 13147
[Santa Clarita](https://github.com/stiles/la-trees/tree/main/data/municipalities/santa-clarita) | 112,000 | 210,888
[Santa Fe Springs](https://github.com/stiles/la-trees/tree/main/data/municipalities/santa-fe-springs) | 8,700 | 16,223
[Santa Monica](https://github.com/stiles/la-trees/tree/main/data/municipalities/santa-monica) | 32,000 | 89,736
[South Gate](https://github.com/stiles/la-trees/tree/main/data/municipalities/south-gate) | 20,900 | 94,396
[South Pasadena](https://github.com/stiles/la-trees/tree/main/data/municipalities/south-pasadena) | 11,400 | 25,619
[Temple City](https://github.com/stiles/la-trees/tree/main/data/municipalities/temple-city) | 9,000 | 35,558
[Ventura County/Simi Valley](https://github.com/stiles/la-trees/tree/main/data/municipalities/ventura-county/simi-valley) | 16,400 | 126,000
[Walnut](https://github.com/stiles/la-trees/tree/main/data/municipalities/walnut) | 3,200 | 29,172
[West Covina](https://github.com/stiles/la-trees/tree/main/data/municipalities/west-covina) | 33,000 | 106,098
[West Hollywood](https://github.com/stiles/la-trees/tree/main/data/municipalities/west-hollywood) | 9,000 | 34,399
[Whittier](https://github.com/stiles/la-trees/tree/main/data/municipalities/whittier) | 27,800 | 85,331

## Municpalities collected, by tree count

Municipality | **Tree count &darr;** | Population
------------ | --------------: | ----------:
[Los Angeles City](https://github.com/stiles/la-trees/tree/main/data/municipalities/los-angeles-city) | 545,000 | 3,792,621
[Long Beach](https://github.com/stiles/la-trees/tree/main/data/municipalities/long-beach) | 140,000 | 462,257
[Santa Clarita](https://github.com/stiles/la-trees/tree/main/data/municipalities/santa-clarita) | 112,000 | 210,888
[Los Angeles County](https://github.com/stiles/la-trees/tree/main/data/municipalities/los-angeles-county) | 99,000 | 10,100,000
[Pasadena](https://github.com/stiles/la-trees/tree/main/data/municipalities/pasadena) | 71,000 | 137,122
[Glendale](https://github.com/stiles/la-trees/tree/main/data/municipalities/glendale) | 56,000 | 203,054
[Pomona](https://github.com/stiles/la-trees/tree/main/data/municipalities/pomona) | 50,000 | 149,058
[Lancaster](https://github.com/stiles/la-trees/tree/main/data/municipalities/lancaster) | 46,000 | 160,316
[Burbank](https://github.com/stiles/la-trees/tree/main/data/municipalities/burbank) | 37,000 | 103,340
[West Covina](https://github.com/stiles/la-trees/tree/main/data/municipalities/west-covina) | 33,000 | 106,098
[Santa Monica](https://github.com/stiles/la-trees/tree/main/data/municipalities/santa-monica) | 32,000 | 89,736
[Cerritos](https://github.com/stiles/la-trees/tree/main/data/municipalities/cerritos) | 31,300 | 49,041
[Beverly Hills](https://github.com/stiles/la-trees/tree/main/data/municipalities/beverly-hills) | 29,000 | 34,109
[Whittier](https://github.com/stiles/la-trees/tree/main/data/municipalities/whittier) | 27,800 | 85,331
[Carson](https://github.com/stiles/la-trees/tree/main/data/municipalities/carson) | 22,500 | 91,714
[Inglewood](https://github.com/stiles/la-trees/tree/main/data/municipalities/inglewood) | 21,800 | 109,673
[Norwalk](https://github.com/stiles/la-trees/tree/main/data/municipalities/norwalk) | 21,400 | 105,549
[South Gate](https://github.com/stiles/la-trees/tree/main/data/municipalities/south-gate) | 20,900 | 94,396
[Alhambra](https://github.com/stiles/la-trees/tree/main/data/municipalities/alhambra) | 20,100 | 83,653
[Diamond Bar](https://github.com/stiles/la-trees/tree/main/data/municipalities/diamond-bar) | 20,100 | 55,544
[Palmdale](https://github.com/stiles/la-trees/tree/main/data/municipalities/palmdale) | 19,000 | 152,750
[Downey](https://github.com/stiles/la-trees/tree/main/data/municipalities/downey) | 18,500 | 111,772
[La Mirada](https://github.com/stiles/la-trees/tree/main/data/municipalities/la-mirada) | 17,000 | 48,527
[Culver City](https://github.com/stiles/la-trees/tree/main/data/municipalities/culver-city) | 16,900 | 38,883
[Ventura County/Simi Valley](https://github.com/stiles/la-trees/tree/main/data/municipalities/ventura-county/simi-valley) | 16,400 | 126,000
[Arcadia](https://github.com/stiles/la-trees/tree/main/data/municipalities/arcadia) | 15,600 | 56,364
[Covina](https://github.com/stiles/la-trees/tree/main/data/municipalities/covina) | 14,600 | 47,796
[Rancho Palos Verdes](https://github.com/stiles/la-trees/tree/main/data/municipalities/rancho-palos-verdes) | 13,500 | 41,643
[Redondo Beach](https://github.com/stiles/la-trees/tree/main/data/municipalities/redondo-beach) | 13,000 | 66,748
[Glendora](https://github.com/stiles/la-trees/tree/main/data/municipalities/glendora) | 12,600 | 50,073
[South Pasadena](https://github.com/stiles/la-trees/tree/main/data/municipalities/south-pasadena) | 11,400 | 25,619
[El Monte](https://github.com/stiles/la-trees/tree/main/data/municipalities/el-monte) | 11,000 | 113,475
[San Dimas](https://github.com/stiles/la-trees/tree/main/data/municipalities/san-dimas) | 10,400 | 33,371
[San Gabriel](https://github.com/stiles/la-trees/tree/main/data/municipalities/san-gabriel) | 9,900 | 39,718
[San Fernando](https://github.com/stiles/la-trees/tree/main/data/municipalities/san-fernando) | 9,500 | 23,645
[San Marino](https://github.com/stiles/la-trees/tree/main/data/municipalities/san-marino) | 9500 | 13147
[Temple City](https://github.com/stiles/la-trees/tree/main/data/municipalities/temple-city) | 9,000 | 35,558
[West Hollywood](https://github.com/stiles/la-trees/tree/main/data/municipalities/west-hollywood) | 9,000 | 34,399
[Santa Fe Springs](https://github.com/stiles/la-trees/tree/main/data/municipalities/santa-fe-springs) | 8,700 | 16,223
[Bellflower](https://github.com/stiles/la-trees/tree/main/data/municipalities/bellflower) | 8,400 | 76,616
[Duarte](https://github.com/stiles/la-trees/tree/main/data/municipalities/duarte) | 7,900 | 21,321
[Paramount](https://github.com/stiles/la-trees/tree/main/data/municipalities/paramount) | 7,800 | 54,098
[Lawndale](https://github.com/stiles/la-trees/tree/main/data/municipalities/lawndale) | 7,400 | 32,769
[Malibu](https://github.com/stiles/la-trees/tree/main/data/municipalities/malibu) | 7,400 | 12,645
[Bell Gardens](https://github.com/stiles/la-trees/tree/main/data/municipalities/bell-gardens) | 7,000 | 42,072
[El Segundo](https://github.com/stiles/la-trees/tree/main/data/municipalities/el-segundo) | 6,400 | 16,654
[Agoura Hills](https://github.com/stiles/la-trees/tree/main/data/municipalities/agoura-hills) | 5,100 | 20,330
[Walnut](https://github.com/stiles/la-trees/tree/main/data/municipalities/walnut) | 3,200 | 29,172
[Lomita](https://github.com/stiles/la-trees/tree/main/data/municipalities/lomita) | 3,000 | 20,256
[Artesia](https://github.com/stiles/la-trees/tree/main/data/municipalities/artesia) | 2,500 | 16,522

## Sources

Records collected from municipalities via the [California Public Records Act](https://en.wikipedia.org/wiki/California_Public_Records_Act) or official open-data portals. Population via the US Census Bureau.

## NGA data

This repository also includes a script to access historical geospatial data from the National Geospatial-Intelligence Agency for Los Angeles, as of 2012. The dataset has 8.9 million trees in and around the city — part of a 130-plus city series that captured 3D trees (and buidings). Each record includes spatial coordinates and associated attributes, such as height in meters. The data is derived from imagery, not a census, so it doesn't include species.

The records were intially hosted on a legacy USGS server that experience timeouts and slower response times. After I inquired about this issue, the agency unfortunately took the data down. I had already downloaded and processed the Los Angeles data, adding features such as neighborhood or city name. It's now stored on S3 as [GeoJSON](https://stilesdata.com/trees/los-angeles/combined_trees_converted.geojson) (1.6GB) and [GeoPackage](https://stilesdata.com/trees/los-angeles/combined_trees.gpkg) (1 GB).

Much of the overall city series (including the buildings features for each) is also now [stored](https://www.arcgis.com/apps/mapviewer/index.html?url=https://services.arcgis.com/QCty4ZXRXx9qyVVL/ArcGIS/rest/services/NGA_Historic_3D_Buildings_And_Trees_DatasetCatalog/FeatureServer&source=sd) by an Esri employee working on [fascinating 3D scenes](https://www.arcgis.com/home/webscene/viewer.html?webscene=5a4cf99d91d542fdbbef773135d1da3b).

## Treekeeper



## Etc.

Numerous cities in LA County have store their tree inventories in Esri services. 

- [Beverly Hills](https://gis.beverlyhills.org/arcgis/rest/services/OD/OpenData_BeverlyHillsGeoHub/FeatureServer/1)
- [Los Angeles](https://maps.lacity.org/arcgis/rest/services/Mapping/UFDTreeInventory/MapServer/1)
- [Pasadena](https://services2.arcgis.com/zNjnZafDYCAJAbN0/ArcGIS/rest/services/Street_ROW_Trees/FeatureServer/0/)
- [Santa Monica](https://gis.santamonica.gov/server/rest/services/Trees/FeatureServer/0/)