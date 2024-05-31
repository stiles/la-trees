// LA County neighborhood locations

fetch('https://stilesdata.com/la/la_county_hoods.geojson')
    .then(response => response.json())
    .then(data => {
        const selector = document.getElementById('location-selector');
        // Sort features alphabetically by the 'name' property within 'properties'
        const sortedFeatures = data.features.sort((a, b) => {
            const nameA = a.properties.name.toUpperCase(); // ignore upper and lowercase
            const storeCoordinatesA = JSON.stringify(a.geometry.coordinates);
            const nameB = b.properties.name.toUpperCase(); // ignore upper and lowercase
            const storeCoordinatesB = JSON.stringify(b.geometry.coordinates);
            if (nameA < nameB) {
                return -1;
            }
            if (nameA > nameB) {
                return 1;
            }
            return 0;
        });

        // Populate the selector with options
        sortedFeatures.forEach(feature => {
            const option = document.createElement('option');
            option.value = JSON.stringify(feature.geometry.coordinates); // Store coordinates as a string in the value attribute
            option.textContent = feature.properties.name; // Adjust based on your actual property names
            selector.appendChild(option);
        });
    })
    .catch(error => console.error('Error loading the place data:', error));

// MAPBOX MAP

mapboxgl.accessToken = 'pk.eyJ1Ijoic3RpbGVzIiwiYSI6ImNsd3Rpc3V2aTAzeXUydm9sMHdoN210b2oifQ.66AJmPYxe2ixku1o7Rwdlg';

// Restrict geocoder to addresses in the area
const LA_BOUNDS = [-118.9448, 33.3328, -117.6462, 34.8233];

// Function to determine if the device is mobile based on viewport width
function isMobileDevice() {
    return window.innerWidth <= 767; // You can adjust this value based on your needs
}

// Default settings for desktop
let initialCenter = [-118.3156679, 34.0744439];
let initialZoom = 11;

// Settings for mobile
if (isMobileDevice()) {
    initialCenter = [-118.3156679, 34.0744439]; // Modify as needed for mobile
    initialZoom = 10; // Adjust zoom level for mobile
}

// Initialize the map with conditional settings
const map = new mapboxgl.Map({
    container: 'map',
    style: 'mapbox://styles/stiles/clwtdw8mn012c01pp3gg5fbd2',
    center: initialCenter,
    zoom: initialZoom
});

// Adjust zoom when selecting a location
document.getElementById('location-selector').addEventListener('change', function() {
    const coordinates = JSON.parse(this.value); 
    let zoomLevel = 13.8; // Default zoom for desktop

    if (isMobileDevice()) {
        zoomLevel = 12.5; // Adjust zoom level for mobile when selecting a location
    }

    if (coordinates) {
        map.flyTo({
            center: coordinates,
            zoom: zoomLevel
        });
    }
});

// Optionally, listen to window resize events to adjust map settings dynamically
window.addEventListener('resize', function() {
    const mobile = isMobileDevice();
    map.setZoom(mobile ? 10 : 11); // Adjust zoom dynamically on resize
});


// 

map.on('load', function () {
    // Source for jacaranda tileset
    map.addSource('jacarandas', {
        type: 'vector',
        url: 'mapbox://stiles.baakgm8n'  // Using the Tileset ID
    });

    // Locations layer with zoom conditions
    map.addLayer({
        'id': 'jacarandas',
        'type': 'circle',
        'source': 'jacarandas',  // Reference to the source
        'source-layer': 'lacounty_jacaranda_locations',  // Layer name within the tileset
        'paint': {
            'circle-radius': [
                'interpolate', 
                ['linear'], 
                ['zoom'],
                0, 1,
                10, 1,
                10.5, 1.5,
                12, 2,
                13, 3,
                14, 4,
                15, 5,
                18, 6,
                19, 7
            ],
            'circle-color': '#888fc7',
            'circle-opacity': 0.6
        }
    });   
    
    const geocoder = new MapboxGeocoder({
        accessToken: mapboxgl.accessToken,
        mapboxgl: mapboxgl,
        bbox: LA_BOUNDS,
        placeholder: 'Find an LA address',
        proximity: {
            longitude: -118.2437,
            latitude: 34.0522
        },
        marker: false
    });

    document.getElementById('geocoder').appendChild(geocoder.onAdd(map));
    
    map.moveLayer('place-city-lg-n', 'jacarandas');
    map.moveLayer('place-city-md-n', 'jacarandas');

    map.addControl(new mapboxgl.NavigationControl());

    map.getContainer().appendChild(document.getElementById('legend'));
    
    geocoder.on('result', function(ev) {
        if (window.marker) {
            window.marker.remove();
        }
        window.marker = new mapboxgl.Marker({
            color: "#4b549e",
            draggable: false
        })
        .setLngLat(ev.result.geometry.coordinates)
        .setPopup(new mapboxgl.Popup().setHTML(`<h4>${ev.result.place_name}</h4>`))
        .addTo(map);
    });

    // Define a variable to hold the current popup reference
    let currentPopup = null;

    map.on('mouseenter', 'jacarandas', function (e) {
        const coordinates = e.features[0].geometry.coordinates.slice();
        const properties = e.features[0].properties;
        const place = properties.region_desc || 'Unknown place';  // Using 'place' from properties
        const description = properties.city || `${place}`;  // Default description if none is provided

        // Close existing popup if it exists
        if (currentPopup) {
            currentPopup.remove();
        }

        // Create a new popup and set it as the current popup
        currentPopup = new mapboxgl.Popup()
            .setLngLat(coordinates)
            .setHTML(description)
            .addTo(map);
    });

    map.on('mouseleave', 'jacarandas', function () {
        // Remove the current popup when the mouse leaves the feature
        if (currentPopup) {
            currentPopup.remove();
            currentPopup = null;  // Reset the current popup reference
        }
    });
});
