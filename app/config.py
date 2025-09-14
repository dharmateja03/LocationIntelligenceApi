# app/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # ArcGIS Configuration
    arcgis_api_key: Optional[str] = None
    esri_client_id: Optional[str] = None
    esri_client_secret: Optional[str] = None
    
    # API Configuration
    api_title: str = "Location Intelligence API"
    api_version: str = "1.0.0"
    
    # Service URLs (Esri public services)
    geocoding_service_url: str = "https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer"
    routing_service_url: str = "https://route.arcgis.com/arcgis/rest/services/World/Route/NAServer/Route_World"
    demographics_service_url: str = "https://geoenrich.arcgis.com/arcgis/rest/services/World/GeoenrichmentServer"
    
    # Rate limiting
    max_requests_per_minute: int = 60
    
    # Cache settings
    enable_cache: bool = True
    cache_ttl_seconds: int = 3600  # 1 hour
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Create global settings instance
settings = Settings()

# Esri service endpoints that are free to use
ESRI_FREE_SERVICES = {
    "world_geocoding": "https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer",
    "world_routing": "https://route-api.arcgis.com/arcgis/rest/services/World/Route/NAServer",
    "places": "https://places-api.arcgis.com/arcgis/rest/services/places-service/v1",
    "demographics": "https://geoenrich.arcgis.com/arcgis/rest/services/World/GeoenrichmentServer"
}
