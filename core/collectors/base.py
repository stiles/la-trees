"""
Base classes and utilities for data collection
"""
import os
import json
import yaml
import logging
import requests
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseCollector(ABC):
    """Base class for all data collectors"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.endpoints = self._load_endpoints()
        self.session = requests.Session()
        
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "settings.yaml"
        
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _load_endpoints(self) -> Dict[str, Any]:
        """Load endpoint configuration"""
        endpoints_path = Path(__file__).parent.parent / "config" / "endpoints.yaml"
        with open(endpoints_path, 'r') as f:
            return yaml.safe_load(f)
    
    @abstractmethod
    def collect_data(self, source: str) -> List[Dict[str, Any]]:
        """Collect data from the specified source"""
        pass
    
    def save_raw_data(self, data: List[Dict[str, Any]], filename: str) -> str:
        """Save raw data to file"""
        os.makedirs(self.config['storage']['raw_data_dir'], exist_ok=True)
        filepath = os.path.join(self.config['storage']['raw_data_dir'], filename)
        
        geojson = {
            "type": "FeatureCollection",
            "features": data,
            "metadata": {
                "collected_at": datetime.now().isoformat(),
                "feature_count": len(data)
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(geojson, f)
        
        logger.info(f"Saved {len(data)} features to {filepath}")
        return filepath
    
    def check_data_freshness(self, source: str) -> Dict[str, Any]:
        """Check if data needs updating based on freshness settings"""
        endpoint_config = self._get_endpoint_config(source)
        if not endpoint_config:
            return {"needs_update": True, "reason": "Unknown source"}
        
        last_updated = endpoint_config.get('last_updated')
        if not last_updated:
            return {"needs_update": True, "reason": "Never collected"}
        
        # Calculate time since last update
        last_update_time = datetime.fromisoformat(last_updated)
        hours_since_update = (datetime.now() - last_update_time).total_seconds() / 3600
        
        # Get freshness threshold
        frequency = endpoint_config.get('update_frequency', 'weekly')
        max_age = self.config['monitoring']['max_age_hours'].get(frequency, 168)
        
        needs_update = hours_since_update > max_age
        
        return {
            "needs_update": needs_update,
            "hours_since_update": hours_since_update,
            "max_age_hours": max_age,
            "last_updated": last_updated
        }
    
    def _get_endpoint_config(self, source: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific endpoint"""
        # Check in primary sources
        if source in self.endpoints.get('primary', {}):
            return self.endpoints['primary'][source]
        
        # Check in live services
        if source in self.endpoints.get('live_services', {}):
            return self.endpoints['live_services'][source]
        
        return None
    
    def update_last_collected(self, source: str, timestamp: Optional[str] = None):
        """Update the last collected timestamp for a source"""
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        # This would ideally update the endpoints.yaml file
        # For now, just log it
        logger.info(f"Updated {source} last_collected: {timestamp}")

class TreeKeeperCollector(BaseCollector):
    """Collector for TreeKeeper WFS services"""
    
    def collect_data(self, source: str = "la_city") -> List[Dict[str, Any]]:
        """Collect data from TreeKeeper WFS service"""
        endpoint_config = self._get_endpoint_config(source)
        if not endpoint_config:
            raise ValueError(f"Unknown source: {source}")
        
        url = endpoint_config['url']
        layer = endpoint_config['layer']
        
        return self._fetch_wfs_data(url, layer)
    
    def _fetch_wfs_data(self, url: str, layer: str) -> List[Dict[str, Any]]:
        """Fetch data from WFS endpoint in chunks"""
        all_features = []
        offset = 0
        chunk_size = self.config['collection']['chunk_size']
        
        logger.info(f"Starting WFS collection from {url}")
        
        while True:
            params = {
                "service": "WFS",
                "version": "2.0.0",
                "request": "GetFeature", 
                "typeName": layer,
                "outputFormat": "application/json",
                "count": str(chunk_size),
                "startIndex": str(offset),
                "sortBy": "site_id A"
            }
            
            try:
                response = self.session.get(
                    url, 
                    params=params, 
                    timeout=self.config['collection']['timeout']
                )
                response.raise_for_status()
                data = response.json()
                
                features = data.get('features', [])
                if not features:
                    break
                
                all_features.extend(features)
                logger.info(f"Collected {len(features)} features (total: {len(all_features)})")
                offset += chunk_size
                
            except requests.RequestException as e:
                logger.error(f"Error fetching data: {e}")
                break
        
        logger.info(f"Collection complete: {len(all_features)} total features")
        return all_features

class EsriCollector(BaseCollector):
    """Collector for Esri Feature Services"""
    
    def collect_data(self, source: str) -> List[Dict[str, Any]]:
        """Collect data from Esri Feature Service"""
        endpoint_config = self._get_endpoint_config(source)
        if not endpoint_config:
            raise ValueError(f"Unknown source: {source}")
        
        url = endpoint_config['url']
        return self._fetch_esri_data(url)
    
    def _fetch_esri_data(self, base_url: str) -> List[Dict[str, Any]]:
        """Fetch data from Esri service in chunks"""
        all_features = []
        offset = 0
        chunk_size = self.config['collection']['chunk_size']
        
        logger.info(f"Starting Esri collection from {base_url}")
        
        while True:
            # Construct query URL
            query_url = f"{base_url}/query"
            params = {
                "outFields": "*",
                "where": "1=1", 
                "f": "geojson",
                "resultOffset": offset,
                "resultRecordCount": chunk_size
            }
            
            try:
                response = self.session.get(
                    query_url,
                    params=params,
                    timeout=self.config['collection']['timeout']
                )
                response.raise_for_status()
                data = response.json()
                
                features = data.get('features', [])
                if not features:
                    break
                
                all_features.extend(features)
                logger.info(f"Collected {len(features)} features (total: {len(all_features)})")
                offset += chunk_size
                
            except requests.RequestException as e:
                logger.error(f"Error fetching data: {e}")
                break
        
        logger.info(f"Collection complete: {len(all_features)} total features")
        return all_features
