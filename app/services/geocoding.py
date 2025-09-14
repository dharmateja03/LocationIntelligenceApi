# app/services/geocoding.py
import httpx
import json
import logging
from typing import Dict, Any, Optional
from app.models.schemas import GeocodeResponse, Location
from app.config import settings, ESRI_FREE_SERVICES

# Configure logging
logger = logging.getLogger(__name__)

class GeocodingService:
    """Service for address geocoding using Esri World Geocoding Service"""
    
    def __init__(self):
        self.base_url = ESRI_FREE_SERVICES["world_geocoding"]
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def geocode_address(self, address: str, country: str = "USA") -> GeocodeResponse:
        """
        Geocode an address using Esri's World Geocoding Service
        
        Args:
            address: Address string to geocode
            country: Country context for geocoding
            
        Returns:
            GeocodeResponse with location and metadata
        """
        try:
            # Prepare request parameters
            params = {
                "singleLine": address,
                "f": "json",
                "outFields": "Addr_type,Score,Match_addr",
                "maxLocations": 1,
                "countryCode": country
            }
            
            # Add API key if available
            if settings.arcgis_api_key:
                params["token"] = settings.arcgis_api_key
            
            url = f"{self.base_url}/findAddressCandidates"
            logger.info(f"🔍 Geocoding request: {address} (country: {country})")
            logger.debug(f"📡 URL: {url}")
            logger.debug(f"📊 Params: {params}")
            
            # Make request to Esri Geocoding Service
            response = await self.client.get(url, params=params)
            logger.info(f"📡 Response status: {response.status_code}")
            
            response.raise_for_status()
            data = response.json()
            logger.debug(f"📊 Response data: {json.dumps(data, indent=2)}")
            
            if not data.get("candidates"):
                logger.warning(f"⚠️ No geocoding results found for address: {address}")
                logger.debug(f"📊 Full response: {json.dumps(data, indent=2)}")
                raise ValueError(f"No geocoding results found for address: {address}")
            
            # Get best candidate
            candidate = data["candidates"][0]
            location_data = candidate["location"]
            attributes = candidate.get("attributes", {})
            
            logger.info(f"✅ Geocoded '{address}' -> lat: {location_data['y']:.4f}, lon: {location_data['x']:.4f}")
            logger.info(f"📊 Confidence: {candidate.get('score', 0.0)}, Match type: {attributes.get('Addr_type', 'Unknown')}")
            
            return GeocodeResponse(
                location=Location(
                    latitude=location_data["y"],
                    longitude=location_data["x"],
                    address=attributes.get("Match_addr", address)
                ),
                confidence=candidate.get("score", 0.0),
                match_type=attributes.get("Addr_type", "Unknown")
            )
            
        except httpx.HTTPError as e:
            logger.error(f"❌ HTTP Error: {str(e)}")
            logger.error(f"📡 Response status: {getattr(e.response, 'status_code', 'N/A')}")
            logger.error(f"📡 Response text: {getattr(e.response, 'text', 'N/A')}")
            raise Exception(f"Geocoding service HTTP error: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON Decode Error: {str(e)}")
            raise Exception(f"Invalid JSON response from geocoding service: {str(e)}")
        except ValueError as e:
            logger.error(f"❌ Value Error: {str(e)}")
            raise e  # Re-raise ValueError as-is
        except Exception as e:
            logger.error(f"❌ Unexpected Error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise Exception(f"Geocoding failed with unexpected error: {str(e)}")
    
    async def reverse_geocode(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Reverse geocode coordinates to get address information
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            Dictionary with address information
        """
        try:
            params = {
                "location": f"{longitude},{latitude}",
                "f": "json",
                "outFields": "Addr_type,Match_addr,StAddr,City,RegionAbbr,Postal"
            }
            
            if settings.arcgis_api_key:
                params["token"] = settings.arcgis_api_key
            
            response = await self.client.get(
                f"{self.base_url}/reverseGeocode",
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            
            if "address" not in data:
                raise ValueError(f"No address found for coordinates: {latitude}, {longitude}")
            
            return data["address"]
            
        except httpx.HTTPError as e:
            raise Exception(f"Reverse geocoding service error: {str(e)}")
        except Exception as e:
            raise Exception(f"Reverse geocoding failed: {str(e)}")
    
    async def batch_geocode(self, addresses: list[str]) -> list[GeocodeResponse]:
        """
        Geocode multiple addresses in batch
        
        Args:
            addresses: List of address strings
            
        Returns:
            List of GeocodeResponse objects
        """
        # For now, process sequentially - could be optimized with Esri batch service
        results = []
        for address in addresses:
            try:
                result = await self.geocode_address(address)
                results.append(result)
            except Exception as e:
                # Create failed result
                results.append(GeocodeResponse(
                    location=Location(latitude=0, longitude=0, address=address),
                    confidence=0.0,
                    match_type="Failed"
                ))
        
        return results
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

# Global instance
geocoding_service = GeocodingService()
