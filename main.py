import streamlit as st
import folium
from streamlit_folium import st_folium  # Updated import
import requests
from time import sleep
import re

# Function to get coordinates from a Google Maps link
def get_coordinates_from_link(link):
    try:
        pattern = r"@(-?\d+\.\d+),(-?\d+\.\d+)"
        match = re.search(pattern, link)
        if match:
            lat, lon = float(match.group(1)), float(match.group(2))
            return lat, lon
        else:
            return None, None
    except Exception as e:
        st.error("Error al extraer coordenadas del enlace de Google Maps.")
        return None, None

# Streamlit app
st.title("Isócronos y Atracciones Dinámicas")

# Sidebar
st.sidebar.title("Opciones")

# Input for the hotel Google Maps link
hotel_link = st.sidebar.text_input("Enlace de Google Maps del hotel")

if hotel_link:
    hotel_coords = get_coordinates_from_link(hotel_link)
    if hotel_coords == (None, None):
        st.sidebar.error("No se pudieron obtener las coordenadas del hotel.")
    st.sidebar.info(f"{hotel_coords}")

# Input for dynamic attraction Google Maps links
attractions_links = st.sidebar.text_area("Enlaces de Google Maps de atracciones (uno por línea)")
attractions = []
if attractions_links:
    links = attractions_links.strip().split("\n")
    for link in links:
        coords = get_coordinates_from_link(link)
        if coords != (None, None):
            attractions.append({"name": link, "coords": coords})

# Checkbox options
show_isochrones = st.sidebar.checkbox("Mostrar isócronos", True)
show_attractions = st.sidebar.checkbox("Mostrar atracciones", True)

# Create map
if hotel_coords != (None, None):
    
    m = folium.Map(location=hotel_coords, zoom_start=13)
    
    # Add hotel marker
    folium.Marker(hotel_coords, popup="Hotel", icon=folium.Icon(color="red")).add_to(m)
    
    # Add attraction markers if checkbox selected
    if show_attractions:
        for attraction in attractions:
            folium.Marker(
                attraction["coords"],
                popup=attraction["name"],
                icon=folium.Icon(color="blue")
            ).add_to(m)
    
    # Fetch and add isochrones if checkbox selected
    if show_isochrones:
        with st.spinner("Cargando isócronos..."):
            isochrone_colors = ["green", "blue", "yellow", "red"]
            intervals = [10, 20, 30, 40]
            intervals.reverse()
    
            for i, minutes in enumerate(intervals):
                # Prepare API request to Valhalla
                payload = {
                    "locations": [{"lat": hotel_coords[0], "lon": hotel_coords[1]}],
                    "costing": "pedestrian",
                    "contours": [{"time": minutes}],
                    "polygons": True
                }
                headers = {"Content-Type": "application/json"}
    
                try:
                    response = requests.post(
                        "https://valhalla1.openstreetmap.de/isochrone", json=payload, headers=headers
                    )
                    data = response.json()
    
                    # Add isochrone polygon to map
                    for feature in data.get("features", []):
                        coords = feature["geometry"]["coordinates"][0]
                        coords = [(c[1], c[0]) for c in coords]  # Swap lat/lon for folium
                        folium.Polygon(
                            locations=coords,
                            color=isochrone_colors[i],
                            fill=True,
                            fill_opacity=0.4,
                            weight=2,
                            popup=f"{minutes} minutos"
                        ).add_to(m)
    
                except Exception as e:
                    st.error(f"Error al cargar isócronos: {e}")
    
                # Simulate loading behavior
                sleep(0.5)
    
    # Render map in Streamlit
    st_folium(m)  # Updated function for rendering