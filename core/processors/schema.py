"""
Unified data schema for tree datasets
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

class DataSource(Enum):
    """Enumeration of data sources"""
    LA_CITY_TREEKEEPER = "la_city_treekeeper"
    BEVERLY_HILLS = "beverly_hills"
    PASADENA = "pasadena"
    SANTA_MONICA = "santa_monica"
    LONG_BEACH = "long_beach"
    LA_COUNTY = "la_county"
    NGA_HISTORICAL = "nga_historical"
    MANUAL_CPRA = "manual_cpra"

@dataclass
class TreeRecord:
    """Standardized tree record structure"""
    # Core identification
    source_id: str                    # Original ID from source system
    source: DataSource               # Data source
    
    # Geographic information
    latitude: float
    longitude: float
    coordinate_system: str = "EPSG:4326"
    
    # Tree information
    common_name: Optional[str] = None
    scientific_name: Optional[str] = None
    species: Optional[str] = None    # Fallback species field
    
    # Physical characteristics
    diameter_breast_height: Optional[float] = None  # DBH in inches
    height: Optional[float] = None                   # Height in feet
    canopy_diameter: Optional[float] = None          # Canopy width in feet
    
    # Location details
    address: Optional[str] = None
    street_name: Optional[str] = None
    side_of_street: Optional[str] = None
    
    # Administrative information
    municipality: Optional[str] = None
    neighborhood: Optional[str] = None
    council_district: Optional[str] = None
    
    # Tree status and maintenance
    condition: Optional[str] = None
    health_status: Optional[str] = None
    planted_date: Optional[str] = None
    maintenance_status: Optional[str] = None
    
    # Data provenance
    collected_date: Optional[str] = None
    last_updated: Optional[str] = None
    data_quality_score: Optional[float] = None
    
    # Original attributes (for reference)
    original_attributes: Optional[Dict[str, Any]] = None

class SchemaMapper:
    """Maps source-specific schemas to unified schema"""
    
    # Field mapping definitions for each source
    FIELD_MAPPINGS = {
        DataSource.LA_CITY_TREEKEEPER: {
            "source_id": "site_id",
            "common_name": "tree_common",
            "scientific_name": "scientific",
            "diameter_breast_height": "dbh",
            "address": "address",
            "street_name": "street",
            "side_of_street": "side",
            "condition": "condition",
            "planted_date": "date_planted",
            "maintenance_status": "maintenance"
        },
        DataSource.BEVERLY_HILLS: {
            "source_id": "OBJECTID",
            "common_name": "COMMON_NAM",
            "scientific_name": "SCIENTIFIC",
            "diameter_breast_height": "DBH",
            "address": "ADDRESS"
        },
        DataSource.PASADENA: {
            "source_id": "OBJECTID", 
            "common_name": "Species",
            "street_name": "Street",
            "condition": "Condition"
        },
        # Add more mappings as needed
    }
    
    # Species name standardization
    SPECIES_ALIASES = {
        # Common variations and misspellings
        "jacaranda mimosifolia": "Jacaranda mimosifolia",
        "jacaranda": "Jacaranda mimosifolia",
        "blue jacaranda": "Jacaranda mimosifolia",
        "ficus microcarpa": "Ficus microcarpa",
        "indian laurel fig": "Ficus microcarpa",
        # Add more standardizations
    }
    
    @classmethod
    def map_record(cls, source_data: Dict[str, Any], source: DataSource) -> TreeRecord:
        """Map source data to standardized TreeRecord"""
        
        # Get field mapping for this source
        field_map = cls.FIELD_MAPPINGS.get(source, {})
        
        # Extract coordinates
        geometry = source_data.get('geometry', {})
        coords = geometry.get('coordinates', [0, 0])
        
        # Map fields using the field mapping
        mapped_data = {}
        for standard_field, source_field in field_map.items():
            if source_field in source_data.get('properties', {}):
                mapped_data[standard_field] = source_data['properties'][source_field]
        
        # Create TreeRecord with mapped data
        record = TreeRecord(
            source_id=mapped_data.get('source_id', ''),
            source=source,
            latitude=coords[1] if len(coords) > 1 else 0,
            longitude=coords[0] if len(coords) > 0 else 0,
            **{k: v for k, v in mapped_data.items() if k != 'source_id'}
        )
        
        # Standardize species names
        if record.common_name:
            record.common_name = cls._standardize_species_name(record.common_name)
        
        # Store original attributes for reference
        record.original_attributes = source_data.get('properties', {})
        
        return record
    
    @classmethod
    def _standardize_species_name(cls, name: str) -> str:
        """Standardize species names using aliases"""
        if not name:
            return name
        
        # Clean and normalize
        clean_name = name.strip().lower()
        
        # Check aliases
        return cls.SPECIES_ALIASES.get(clean_name, name.strip())
    
    @classmethod
    def to_geojson_feature(cls, record: TreeRecord) -> Dict[str, Any]:
        """Convert TreeRecord to GeoJSON feature"""
        
        # Build properties dict with non-null values
        properties = {}
        for field, value in record.__dict__.items():
            if field not in ['latitude', 'longitude', 'coordinate_system', 'original_attributes']:
                if value is not None:
                    # Convert enum to string
                    if isinstance(value, Enum):
                        properties[field] = value.value
                    else:
                        properties[field] = value
        
        return {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [record.longitude, record.latitude]
            },
            "properties": properties
        }
    
    @classmethod
    def validate_record(cls, record: TreeRecord) -> List[str]:
        """Validate a tree record and return list of issues"""
        issues = []
        
        # Check required fields
        if not record.source_id:
            issues.append("Missing source_id")
        
        if not record.latitude or not record.longitude:
            issues.append("Missing coordinates")
        
        # Check coordinate bounds (LA County approximate)
        if record.latitude < 33.7 or record.latitude > 34.8:
            issues.append(f"Latitude {record.latitude} outside LA County bounds")
        
        if record.longitude < -118.9 or record.longitude > -117.6:
            issues.append(f"Longitude {record.longitude} outside LA County bounds")
        
        # Check for unknown species
        if not record.common_name or record.common_name.lower() in ['unknown', 'vacant site', 'stump']:
            issues.append("Unknown or missing species")
        
        return issues

# Standard export schema for APIs and downloads
EXPORT_SCHEMA = {
    "type": "object",
    "properties": {
        "source_id": {"type": "string"},
        "source": {"type": "string"},
        "latitude": {"type": "number"},
        "longitude": {"type": "number"}, 
        "common_name": {"type": ["string", "null"]},
        "scientific_name": {"type": ["string", "null"]},
        "diameter_breast_height": {"type": ["number", "null"]},
        "height": {"type": ["number", "null"]},
        "address": {"type": ["string", "null"]},
        "municipality": {"type": ["string", "null"]},
        "condition": {"type": ["string", "null"]},
        "collected_date": {"type": ["string", "null"]},
        "last_updated": {"type": ["string", "null"]}
    },
    "required": ["source_id", "source", "latitude", "longitude"]
}
