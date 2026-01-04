import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import re
from typing import Dict, List, Tuple, Optional

# Configuración de la página
st.set_page_config(page_title="Mapa de Isócronos", layout="wide")

# Inicializar session_state
if 'attractions' not in st.session_state:
    st.session_state.attractions = []
if 'isochrones_cache' not in st.session_state:
    st.session_state.isochrones_cache = {}
if 'hotel_coords' not in st.session_state:
    st.session_state.hotel_coords = None

# Iconos disponibles
ICON_OPTIONS = {
    "🏨 Hotel": "home",
    "📍 Pin": "info-sign",
    "⭐ Estrella": "star",
    "🎯 Objetivo": "record",
    "🏢 Edificio": "tower"
}

ATTRACTION_ICONS = {
    "📍 Pin azul": "info-sign",
    "🎭 Cultura": "music",
    "🍴 Restaurante": "cutlery",
    "🎡 Atracción": "camera",
    "🏛️ Museo": "education",
    "🌳 Parque": "tree-conifer"
}

# Función para extraer el nombre del lugar de la URL de Google Maps
def extract_place_name(url: str) -> str:
    """Extrae el nombre del lugar de una URL de Google Maps"""
    try:
        # Intentar extraer el nombre después de /place/
        match = re.search(r'/place/([^/@]+)', url)
        if match:
            name = match.group(1).replace('+', ' ').replace('%20', ' ')
            return name
        return "Lugar sin nombre"
    except:
        return "Lugar sin nombre"

# Función para obtener coordenadas
def get_coordinates_from_link(link: str) -> Tuple[Optional[float], Optional[float]]:
    """Extrae coordenadas de un enlace de Google Maps"""
    try:
        pattern = r"@(-?\d+\.\d+),(-?\d+\.\d+)"
        match = re.search(pattern, link)
        if match:
            lat, lon = float(match.group(1)), float(match.group(2))
            return lat, lon
        return None, None
    except Exception as e:
        st.error(f"Error al extraer coordenadas: {e}")
        return None, None

# Función para obtener isócronos con caché
def get_isochrones(coords: Tuple[float, float], intervals: List[int]) -> Dict:
    """Obtiene isócronos usando caché para evitar llamadas repetidas"""
    cache_key = f"{coords[0]},{coords[1]}_{','.join(map(str, intervals))}"
    
    if cache_key in st.session_state.isochrones_cache:
        return st.session_state.isochrones_cache[cache_key]
    
    isochrones_data = {}
    
    for minutes in intervals:
        payload = {
            "locations": [{"lat": coords[0], "lon": coords[1]}],
            "costing": "pedestrian",
            "contours": [{"time": minutes}],
            "polygons": True
        }
        headers = {"Content-Type": "application/json"}
        
        try:
            response = requests.post(
                "https://valhalla1.openstreetmap.de/isochrone",
                json=payload,
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                isochrones_data[minutes] = response.json()
        except Exception as e:
            st.warning(f"Error al cargar isócrono de {minutes} min: {e}")
    
    st.session_state.isochrones_cache[cache_key] = isochrones_data
    return isochrones_data

# Función para agregar atracción
def add_attraction(url: str, icon: str):
    """Agrega una nueva atracción a la lista"""
    if url.strip():
        coords = get_coordinates_from_link(url)
        if coords != (None, None):
            name = extract_place_name(url)
            st.session_state.attractions.append({
                "name": name,
                "url": url,
                "coords": coords,
                "icon": icon
            })
            return True
    return False

# Función para eliminar atracción
def remove_attraction(index: int):
    """Elimina una atracción de la lista"""
    if 0 <= index < len(st.session_state.attractions):
        st.session_state.attractions.pop(index)

# ==================== UI ====================
st.title("🗺️ Mapa de Isócronos y Atracciones")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuración")
    
    # Punto central (Hotel)
    st.subheader("📍 Punto Central")
    hotel_link = st.text_input(
        "Enlace de Google Maps",
        placeholder="Pega aquí el enlace del hotel",
        help="Este es el punto desde donde se calcularán los isócronos"
    )
    
    if hotel_link:
        coords = get_coordinates_from_link(hotel_link)
        if coords != (None, None):
            st.session_state.hotel_coords = coords
            st.success(f"✅ Coordenadas: {coords[0]:.5f}, {coords[1]:.5f}")
        else:
            st.error("❌ No se pudieron extraer las coordenadas")
            st.session_state.hotel_coords = None
    
    # Icono del punto central
    hotel_icon_label = st.selectbox(
        "Icono del punto central",
        options=list(ICON_OPTIONS.keys()),
        index=0
    )
    hotel_icon = ICON_OPTIONS[hotel_icon_label]
    
    st.divider()
    
    # Configuración de Isócronos
    st.subheader("⏱️ Isócronos")
    show_isochrones = st.checkbox("Mostrar isócronos", value=True)
    
    if show_isochrones:
        # Input para intervalos
        intervals_input = st.text_input(
            "Intervalos de tiempo (minutos)",
            value="10, 20, 30, 40",
            placeholder="Ej: 5, 10, 15, 20, 30",
            help="Separa los valores con comas. Solo se usarán números."
        )
        
        # Procesar input y extraer solo números
        available_intervals = []
        if intervals_input:
            parts = intervals_input.split(',')
            for part in parts:
                # Extraer solo números
                number = re.sub(r'[^\d]', '', part.strip())
                if number and int(number) > 0:
                    available_intervals.append(int(number))
        
        # Eliminar duplicados y ordenar
        available_intervals = sorted(list(set(available_intervals)))
        
        # Pills para seleccionar intervalos
        if available_intervals:
            st.write("**Seleccionar intervalos:**")
            selected_intervals = []
            
            # Crear checkboxes dinámicamente
            cols = st.columns(3)
            for idx, interval in enumerate(available_intervals):
                with cols[idx % 3]:
                    if st.checkbox(f"{interval} min", value=True, key=f"interval_{interval}"):
                        selected_intervals.append(interval)
        else:
            selected_intervals = []
            st.warning("Ingresa intervalos válidos (números separados por comas)")
        
        # Control de opacidad
        opacity = st.slider("Opacidad de isócronos", 0.0, 1.0, 0.2, 0.05)
    
    st.divider()
    
    # Atracciones
    st.subheader("🎯 Atracciones")
    show_attractions = st.checkbox("Mostrar atracciones", value=True)
    
    if show_attractions:
        # Selector de icono para atracciones
        attraction_icon_label = st.selectbox(
            "Icono para nuevas atracciones",
            options=list(ATTRACTION_ICONS.keys()),
            index=0
        )
        attraction_icon = ATTRACTION_ICONS[attraction_icon_label]
        
        # Input para agregar atracción
        new_attraction_url = st.text_input(
            "Agregar nueva atracción",
            placeholder="Pega el enlace de Google Maps",
            key="new_attraction_input"
        )
        
        if new_attraction_url:
            if add_attraction(new_attraction_url, attraction_icon):
                st.success("✅ Atracción agregada")
                st.rerun()
            else:
                st.error("❌ URL inválida o sin coordenadas")
        
        # Lista de atracciones agregadas
        if st.session_state.attractions:
            st.write("**Atracciones agregadas:**")
            for i, attraction in enumerate(st.session_state.attractions):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"• {attraction['name']}")
                with col2:
                    if st.button("🗑️", key=f"delete_{i}"):
                        remove_attraction(i)
                        st.rerun()
    
    st.divider()
    
    # Botón para limpiar caché
    if st.button("🔄 Limpiar caché de isócronos"):
        st.session_state.isochrones_cache = {}
        st.success("Caché limpiado")

# ==================== MAPA ====================
if st.session_state.hotel_coords:
    # Crear mapa
    m = folium.Map(
        location=st.session_state.hotel_coords,
        zoom_start=13,
        tiles="OpenStreetMap"
    )
    
    # Agregar isócronos
    if show_isochrones and selected_intervals:
        with st.spinner("Cargando isócronos desde caché..."):
            isochrones_data = get_isochrones(
                st.session_state.hotel_coords,
                selected_intervals
            )
            
            # Colores dinámicos para intervalos
            color_palette = ["green", "blue", "yellow", "orange", "red", "purple", "pink", "darkgreen", "lightblue", "darkred"]
            colors = {interval: color_palette[idx % len(color_palette)] for idx, interval in enumerate(sorted(selected_intervals))}
            
            # Agregar en orden inverso para que los más grandes queden abajo
            for minutes in sorted(selected_intervals, reverse=True):
                if minutes in isochrones_data:
                    data = isochrones_data[minutes]
                    for feature in data.get("features", []):
                        coords = feature["geometry"]["coordinates"][0]
                        coords = [(c[1], c[0]) for c in coords]
                        folium.Polygon(
                            locations=coords,
                            color=colors.get(minutes, "gray"),
                            fill=True,
                            fill_opacity=opacity,
                            weight=2,
                            popup=f"{minutes} minutos caminando"
                        ).add_to(m)
    
    # Agregar marcador del hotel
    folium.Marker(
        st.session_state.hotel_coords,
        popup="<b>Punto Central</b>",
        tooltip="Punto Central",
        icon=folium.Icon(color="red", icon=hotel_icon)
    ).add_to(m)
    
    # Agregar marcadores de atracciones
    if show_attractions:
        for attraction in st.session_state.attractions:
            folium.Marker(
                attraction["coords"],
                popup=f"<b>{attraction['name']}</b>",
                tooltip=attraction['name'],
                icon=folium.Icon(color="blue", icon=attraction['icon'])
            ).add_to(m)
    
    # Renderizar mapa (ancho completo del container)
    st_folium(m, width="100%", height=600, use_container_width=True)
    
else:
    st.info("👆 Por favor, ingresa el enlace de Google Maps del punto central en el panel lateral para comenzar.")
    st.image("https://maps.google.com/mapfiles/kml/shapes/placemark_circle.png", width=100)