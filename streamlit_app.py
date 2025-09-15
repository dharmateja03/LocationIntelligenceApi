import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
import pandas as pd
from typing import Optional, List, Dict, Any

# Page config
st.set_page_config(
    page_title="Location Intelligence Dashboard",
    page_icon="map",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants
API_BASE_URL = "http://localhost:8000/api/v1"

def main():
    st.title("Location Intelligence Dashboard")
    st.markdown("*Powered by Esri Geocoding Services*")
    
   
    if 'geocode_result' not in st.session_state:
        st.session_state.geocode_result = None
    if 'place_search_results' not in st.session_state:
        st.session_state.place_search_results = None
    if 'batch_results' not in st.session_state:
        st.session_state.batch_results = None
    
    # Test API connection
    with st.sidebar:
        st.title("Tools")
        api_status = test_api_connection()
        if api_status:
            st.success("API Connected")
        else:
            st.error("API Disconnected")
            st.info("Start FastAPI: `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`")
        
        tool = st.selectbox(
            "Select a tool:",
            ["Address Geocoding", "Place Search", "Batch Geocoding"]
        )
    
    if tool == "Address Geocoding":
        geocoding_tool()
    elif tool == "Place Search":
        place_search_tool()
    elif tool == "Batch Geocoding":
        batch_geocoding_tool()

def test_api_connection():
    """Test if the API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def geocoding_tool():
    st.header("Address Geocoding")
    st.markdown("Convert addresses to coordinates and visualize on map")
    
    # Input
    col1, col2 = st.columns([3, 1])
    
    with col1:
        address = st.text_input(
            "Enter an address:",
            placeholder="e.g., 1600 Pennsylvania Avenue, Washington DC",
            help="Enter any address to get its coordinates"
        )
    
    with col2:
        country = st.selectbox("Country", ["USA", "Canada", "UK", "Global"], index=0)
        st.write("")  # spacing
        geocode_btn = st.button("Geocode", type="primary")
    
    if geocode_btn and address:
        with st.spinner("Geocoding address..."):
            result = geocode_address(address, country)
            if result:
                st.session_state.geocode_result = result
                st.rerun()
    
    # Display stored results (persists across interactions)
    if st.session_state.geocode_result:
        display_geocode_results(st.session_state.geocode_result)

def place_search_tool():
    st.header("Place Search")
    st.markdown("Find nearby services and visualize them on a map")
    
    # Input section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Search Location")
        location_method = st.radio(
            "How would you like to specify the location?",
            ["Enter Coordinates", "Enter Address"],
            horizontal=True
        )
        
        if location_method == "Enter Address":
            search_address = st.text_input(
                "Search near address:",
                placeholder="e.g., Times Square, New York",
                help="Enter an address to search around"
            )
            lat, lon = None, None
            
            if search_address and st.button("Get Coordinates"):
                with st.spinner("Geocoding..."):
                    result = geocode_address(search_address)
                    if result:
                        lat = result["location"]["latitude"]
                        lon = result["location"]["longitude"]
                        st.success(f"Coordinates: {lat:.4f}, {lon:.4f}")
                        st.session_state.search_lat = lat #storing
                        st.session_state.search_lon = lon
            
            # Use stored coordinates if available
            if 'search_lat' in st.session_state and 'search_lon' in st.session_state:
                lat = st.session_state.search_lat
                lon = st.session_state.search_lon
                st.info(f"Using coordinates: {lat:.4f}, {lon:.4f}")
        else:
            col_lat, col_lon = st.columns(2)
            with col_lat:
                lat = st.number_input("Latitude", value=43.1557, format="%.6f", min_value=-90.0, max_value=90.0)
            with col_lon:
                lon = st.number_input("Longitude", value=-77.6125, format="%.6f", min_value=-180.0, max_value=180.0)
    
    with col2:
        st.subheader("Search Parameters")
        service_type = st.selectbox(
            "Service Type:",
            ["hospital", "pharmacy", "restaurant", "gas_station", "school", "bank", "police", "fire_station"],
            help="Type of service to search for"
        )
        
        radius = st.slider("Search Radius (miles)", 0.5, 10.0, 2.0, 0.5)
        limit = st.slider("Max Results", 1, 20, 10)
        
        search_btn = st.button("Search Places", type="primary")
    
    # Search execution
    if search_btn and lat is not None and lon is not None:
        with st.spinner(f"Searching for {service_type} near ({lat:.4f}, {lon:.4f})..."):
            result = search_places(lat, lon, service_type, radius, limit)
            if result is not None:
                st.session_state.place_search_results = result
                st.rerun()
    
    if st.session_state.place_search_results:
        display_place_search_results(st.session_state.place_search_results)

def batch_geocoding_tool():
    st.header("Batch Geocoding")
    st.markdown("Geocode multiple addresses at once")
    
    # Input methods
    input_method = st.radio(
        "Input method:",
        ["Text Area", "Upload CSV"],
        horizontal=True
    )
    
    addresses = []
    
    if input_method == "Text Area":
        addresses_text = st.text_area(
            "Enter addresses (one per line):",
            placeholder="1600 Pennsylvania Ave, Washington DC\nTimes Square, New York\nGolden Gate Bridge, San Francisco",
            height=150
        )
        addresses = [addr.strip() for addr in addresses_text.split('\n') if addr.strip()]
        
    else:
        uploaded_file = st.file_uploader(
            "Upload CSV file with addresses",
            type=['csv'],
            help="CSV should have an 'address' column"
        )
        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file)
                if 'address' in df.columns:
                    addresses = df['address'].dropna().tolist()
                    st.success(f"Loaded {len(addresses)} addresses from CSV")
                else:
                    st.error("CSV must have an 'address' column")
            except Exception as e:
                st.error(f"Error reading CSV: {str(e)}")
    
    # Process batch
    if addresses and st.button("Batch Geocode", type="primary"):
        with st.spinner(f"Processing {len(addresses)} addresses..."):
            result = batch_geocode(addresses)
            if result:
                st.session_state.batch_results = result
                st.rerun()
    
    if st.session_state.batch_results:
        display_batch_results(st.session_state.batch_results)

def geocode_address(address: str, country: str = "USA") -> Optional[Dict]:
    """Geocode a single address"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/geocode",
            params={"address": address, "country": country},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                'address': address,
                'location': data["location"],
                'confidence': data['confidence'],
                'match_type': data['match_type']
            }
        else:
            st.error(f"Geocoding failed: {response.json().get('detail', 'Unknown error')}")
            return None
            
    except requests.exceptions.RequestException as e:
        st.error(f"Network error: {str(e)}")
        return None

def search_places(lat: float, lon: float, service_type: str, radius: float, limit: int) -> Optional[Dict]:
    """Search for places near a location"""
    try:
        st.info(f"Searching for {service_type} near ({lat:.4f}, {lon:.4f}) within {radius} miles...")
        
        response = requests.get(
            f"{API_BASE_URL}/services/nearest",
            params={
                "lat": lat,
                "lon": lon,
                "service_type": service_type,
                "radius_miles": radius,
                "limit": limit
            },
            timeout=15
        )
        
        st.info(f"API Response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            places = data.get("nearest_services", [])
            
            return {
                'lat': lat,
                'lon': lon,
                'service_type': service_type,
                'radius': radius,
                'places': places,
                'total_found': len(places)
            }
        else:
            st.error(f"Place search failed: {response.json().get('detail', 'Unknown error')}")
            st.error(f"Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        st.error(f"Network error during place search: {str(e)}")
        return None

def batch_geocode(addresses: List[str]) -> Optional[Dict]:
    """Batch geocode multiple addresses"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/batch/geocode",
            json=addresses,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                'addresses': addresses,
                'results': data["results"],
                'total_processed': len(data["results"])
            }
        else:
            st.error(f"Batch geocoding failed: {response.json().get('detail', 'Unknown error')}")
            return None
            
    except requests.exceptions.RequestException as e:
        st.error(f"Network error during batch geocoding: {str(e)}")
        return None

def display_geocode_results(result: Dict):
    """Display geocoding results with persistent state"""
    location = result['location']
    
    st.subheader("Geocoding Results")
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Latitude", f"{location['latitude']:.6f}")
    with col2:
        st.metric("Longitude", f"{location['longitude']:.6f}")
    with col3:
        st.metric("Confidence", f"{result['confidence']:.1f}%")
    
    # Additional info
    st.info(f"**Original Address:** {result['address']}")
    st.info(f"**Matched Address:** {location.get('address', 'N/A')}")
    st.info(f"**Match Type:** {result['match_type']}")
    
    # Create map
    create_single_point_map(
        location['latitude'], 
        location['longitude'], 
        result['address'],
        f"Location: {location.get('address', result['address'])}"
    )
    
    # Clear button
    if st.button("Clear Results"):
        st.session_state.geocode_result = None
        st.rerun()

def display_place_search_results(results: Dict):
    """Display place search results with persistent state"""
    places = results['places']
    
    st.subheader("Place Search Results")
    
    if places:
        st.success(f"Found {len(places)} {results['service_type']}(s)")
        
        # Create results table
        df = pd.DataFrame(places)
        st.dataframe(
            df[['name', 'address', 'distance_miles', 'confidence', 'category']],
            use_container_width=True
        )
        
        # Create map with all places
        create_places_map(results['lat'], results['lon'], places, results['service_type'])
        
    else:
        st.warning(f"No {results['service_type']} found within {results['radius']} miles")
        # Still show map with center point
        create_single_point_map(results['lat'], results['lon'], "Search Center", "Search Location")
    
    # Clear button
    if st.button("Clear Place Results"):
        st.session_state.place_search_results = None
        st.rerun()

def display_batch_results(results: Dict):
    """Display batch geocoding results with persistent state"""
    st.subheader("Batch Results")
    
    st.success(f"Processed {results['total_processed']} addresses")
    
    # Create results DataFrame
    processed_data = []
    for i, result in enumerate(results['results']):
        processed_data.append({
            'Original Address': results['addresses'][i] if i < len(results['addresses']) else 'N/A',
            'Matched Address': result['location']['address'],
            'Latitude': result['location']['latitude'],
            'Longitude': result['location']['longitude'],
            'Confidence': result['confidence'],
            'Match Type': result['match_type']
        })
    
    df = pd.DataFrame(processed_data)
    
    # Display results table
    st.dataframe(df, use_container_width=True)
    
    # Download button
    csv = df.to_csv(index=False)
    st.download_button(
        "Download Results as CSV",
        data=csv,
        file_name="geocoding_results.csv",
        mime="text/csv"
    )
    
    # Create map with all points
    valid_results = [r for r in results['results'] if r['confidence'] > 0]
    if valid_results:
        create_batch_map(valid_results)
    
    # Clear button
    if st.button("Clear Batch Results"):
        st.session_state.batch_results = None
        st.rerun()

def create_single_point_map(lat: float, lon: float, title: str, popup_text: str):
    """Create a map with a single point"""
    st.subheader("Map View")
    
    # Create map centered on the point
    m = folium.Map(location=[lat, lon], zoom_start=12)
    
    # Add marker
    folium.Marker(
        [lat, lon],
        popup=popup_text,
        tooltip=title,
        icon=folium.Icon(color='red', icon='info-sign')
    ).add_to(m)
    
    # Display map
    st_folium(m, width=700, height=400)

def create_places_map(center_lat: float, center_lon: float, places: List[Dict], service_type: str):
    """Create a map showing search center and found places"""
    st.subheader("Map View")
    
    # Create map centered on search location
    m = folium.Map(location=[center_lat, center_lon], zoom_start=12)
    
    # Add center point
    folium.Marker(
        [center_lat, center_lon],
        popup="Search Center",
        tooltip="Search Location",
        icon=folium.Icon(color='blue', icon='crosshairs')
    ).add_to(m)
    
    # Add found places
    for i, place in enumerate(places):
        folium.Marker(
            [place['latitude'], place['longitude']],
            popup=f"<b>{place['name']}</b><br>{place['address']}<br>Distance: {place['distance_miles']} mi<br>Confidence: {place['confidence']}",
            tooltip=f"{service_type.title()} #{i+1}",
            icon=folium.Icon(color='green', icon='plus' if service_type == 'hospital' else 'info-sign')
        ).add_to(m)
    
    # Display map
    st_folium(m, width=700, height=400)

def create_batch_map(results: List[Dict]):
    """Create a map with multiple geocoded points"""
    st.subheader("Batch Results Map")
    
    if not results:
        return
    
    # Calculate center point
    center_lat = sum(r['location']['latitude'] for r in results) / len(results)
    center_lon = sum(r['location']['longitude'] for r in results) / len(results)
    
    # Create map
    m = folium.Map(location=[center_lat, center_lon], zoom_start=6)
    
    # Add markers for each result
    for i, result in enumerate(results):
        lat = result['location']['latitude']
        lon = result['location']['longitude']
        
        # Color based on confidence
        if result['confidence'] >= 90:
            color = 'green'
        elif result['confidence'] >= 70:
            color = 'orange'
        else:
            color = 'red'
        
        folium.Marker(
            [lat, lon],
            popup=f"<b>{result['location']['address']}</b><br>Confidence: {result['confidence']}%<br>Type: {result['match_type']}",
            tooltip=f"Point {i+1}",
            icon=folium.Icon(color=color, icon='info-sign')
        ).add_to(m)
    
    # Display map
    st_folium(m, width=700, height=400)

if __name__ == "__main__":
    main()