# app/models/schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class ServiceType(str, Enum):
    HOSPITAL = "hospital"
    PHARMACY = "pharmacy"
    RESTAURANT = "restaurant"
    GAS_STATION = "gas_station"
    SCHOOL = "school"
    BANK = "bank"
    POLICE = "police"
    FIRE_STATION = "fire_station"

class Location(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    address: Optional[str] = Field(None, description="Human-readable address")

class GeocodeRequest(BaseModel):
    address: str = Field(..., min_length=1, description="Address to geocode")
    country: Optional[str] = Field("USA", description="Country for geocoding context")

class GeocodeResponse(BaseModel):
    location: Location
    confidence: float = Field(..., ge=0, le=100, description="Geocoding confidence score")
    match_type: str = Field(..., description="Type of match (exact, approximate, etc.)")

class ServiceSearchRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    service_type: ServiceType
    radius_miles: float = Field(5.0, gt=0, le=50, description="Search radius in miles")
    limit: int = Field(10, gt=0, le=50, description="Maximum number of results")

class ServiceLocation(BaseModel):
    name: str
    address: str
    location: Location
    distance_miles: float = Field(..., description="Distance from search point in miles")
    phone: Optional[str] = None
    rating: Optional[float] = Field(None, ge=0, le=5)
    categories: List[str] = []

class ServiceSearchResponse(BaseModel):
    search_location: Location
    service_type: ServiceType
    results: List[ServiceLocation]
    total_found: int
    search_radius_miles: float

class DemographicsRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    radius_miles: float = Field(1.0, gt=0, le=10, description="Analysis radius in miles")

class Demographics(BaseModel):
    total_population: Optional[int] = None
    median_age: Optional[float] = None
    median_income: Optional[int] = None
    households: Optional[int] = None
    education_bachelors_percent: Optional[float] = None
    race_white_percent: Optional[float] = None
    race_black_percent: Optional[float] = None
    race_hispanic_percent: Optional[float] = None
    race_asian_percent: Optional[float] = None

class DemographicsResponse(BaseModel):
    location: Location
    radius_miles: float
    demographics: Demographics
    data_vintage: Optional[str] = None

class RouteRequest(BaseModel):
    origin: Location
    destination: Location
    travel_mode: str = Field("driving", description="Travel mode: driving, walking, transit")

class RouteResponse(BaseModel):
    origin: Location
    destination: Location
    distance_miles: float
    duration_minutes: float
    travel_mode: str
    route_geometry: Optional[Dict[str, Any]] = None  # GeoJSON geometry

class ErrorResponse(BaseModel):
    error: str
    message: str
    status_code: int
