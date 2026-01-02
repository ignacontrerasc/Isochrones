# main.py

import streamlit as st
import folium
from streamlit_folium import folium_static
import requests
from time import sleep

# Coordinates for hotel and attractions
hotel_coords = (13.747, 100.508)
attractions = [
    {"name": "Chatuchak Weekend Market", "coords": (13.8005, 100.5508)},
    {"name": "Wat Arun", "coords": (13.7437, 100.4874)},
    {"name": "Grand Palace", "coords": (13.7503, 100.4912)},
    {"name": "Wat Pho", "coords": (13.7412, 100.4895)},
    {"name": "Khao San Road", "coords": (13.7589, 100.4972)},
    {"name": "Silom Thai Cooking School", "coords": (13.724, 100.531)},
    {"name": "Chinatown Bangkok", "coords": (13.740, 100.506)},
]

# Streamlit app title
st.title("Isócronos y Atracciones Turísticas en Bangkok")

# Sidebar options
st.sidebar.title("Opciones")
show_isochrones = st.sidebar.checkbox("Mostrar isócronos", True)
show_attractions = st.sidebar.checkbox("Mostrar atracciones", True)

# Create map
m = folium.Map(location=hotel_coords, zoom_start=13)

# Add hotel marker
folium.Marker(hotel_coords, popup="SOHO Heritage House", icon=folium.Icon(color="red")).add_to(m)

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
folium_static(m)
