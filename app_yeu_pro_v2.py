import os
import requests
import datetime
import math
import matplotlib.pyplot as plt
import streamlit as st
import folium
from streamlit_folium import st_folium
import streamlit.components.v1 as components

# --- CONFIGURATION ---
LATITUDE, LONGITUDE = 46.7236, -2.3503
MARINE_LAT, MARINE_LON = 46.7000, -2.4500 

START_POINTS = {
    "Port-Joinville": {"lat": 46.7280, "lon": -2.3510},
    "Saint-Sauveur": {"lat": 46.7110, "lon": -2.3300},
    "Port de la Meule": {"lat": 46.6970, "lon": -2.3190}
}

# J'ai remis votre logique de vent d'origine qui fonctionnait très bien !
BEACHES = [
    {"name": "Anse des Soux", "lat": 46.6910, "lon": -2.3209, "good": ["N", "NE", "E"], "bad": ["S", "SO", "O"]},
    {"name": "Plage des Vieilles", "lat": 46.6957, "lon": -2.3137, "good": ["N", "NE", "E", "NO"], "bad": ["S", "SO", "SE"]},
    {"name": "Grande Conche", "lat": 46.6946, "lon": -2.2850, "good": ["N", "NO", "O"], "bad": ["S", "SE", "E"]},
    {"name": "Petite Conche", "lat": 46.7065, "lon": -2.2991, "good": ["N", "NO", "O"], "bad": ["S", "SE", "E"]},
    {"name": "Plage des Corbeaux", "lat": 46.6908, "lon": -2.2820, "good": ["O", "NO", "SO"], "bad": ["E", "NE", "SE"]},
    {"name": "Marais Salés", "lat": 46.7127, "lon": -2.3103, "good": ["S", "SO", "O"], "bad": ["N", "NE", "E"]},
    {"name": "Ker Châlon", "lat": 46.7196, "lon": -2.3351, "good": ["S", "SO", "SE"], "bad": ["N", "NE", "E", "NO"]},
    {"name": "Plage des Sapins", "lat": 46.7174, "lon": -2.3159, "good": ["S", "SO", "SE"], "bad": ["N", "NE", "E", "NO"]},
    {"name": "Anse des Fontaines", "lat": 46.6895, "lon": -2.3334, "good": ["N", "NE", "E"], "bad": ["S", "SO", "O"]},
    {"name": "Plage de la Gournaise", "lat": 46.7337, "lon": -2.3809, "good": ["S", "SE", "SO"], "bad": ["N", "NE", "NO"]},
    {"name": "Plage du But", "lat": 46.7257, "lon": -2.3969, "good": ["S", "SE", "E"], "bad": ["N", "NO", "O"]},
    {"name": "Plage des Sabias", "lat": 46.7034, "lon": -2.3739, "good": ["S", "SE", "E"], "bad": ["N", "NO", "O"]}
]

WIND_POINTS = [
    {"lat": 46.728, "lon": -2.351}, {"lat": 46.721, "lon": -2.388},
    {"lat": 46.695, "lon": -2.292}, {"lat": 46.710, "lon": -2.330},
    {"lat": 46.700, "lon": -2.319}, {"lat": 46.718, "lon": -2.360},
    {"lat": 46.705, "lon": -2.350}, {"lat": 46.710, "lon": -2.300},
    {"lat": 46.735, "lon": -2.330}, {"lat": 46.685, "lon": -2.330}
]

# --- DESIGN DES POUCES ---
svg_up = '''<div style="filter: drop-shadow(2px 2px 2px rgba(0,0,0,0.5)); width:28px; height:28px;"><svg viewBox="0 0 24 24" fill="#28a745" stroke="white" stroke-width="1"><path d="M2 20h2c.55 0 1-.45 1-1v-9c0-.55-.45-1-1-1H2v11zm19.83-7.12c.11-.25.17-.52.17-.8V11c0-1.1-.9-2-2-2h-5.5l.92-4.65c.05-.22.02-.46-.1-.66-.12-.21-.31-.37-.53-.46-.22-.1-.47-.11-.7-.03L9.67 6H7v14h11.28c.84 0 1.58-.5 1.87-1.25l2.68-7.87z"/></svg></div>'''
svg_down = '''<div style="filter: drop-shadow(2px 2px 2px rgba(0,0,0,0.5)); width:28px; height:28px;"><svg viewBox="0 0 24 24" fill="#dc3545" stroke="white" stroke-width="1"><path d="M22 4h-2c-.55 0-1 .45-1 1v9c0 .55.45 1 1 1h2V4zM2.17 11.12c-.11.25-.17.52-.17.8V13c0 1.1.9 2 2 2h5.5l-.92 4.65c-.05.22-.02.46.1.66.12.21.31.37.53.46.22.1.47.11.7.03L14.33 18H17V4H5.72c-.84 0-1.58.5-1.87 1.25L1.17 11.12z"/></svg></div>'''
svg_right = '''<div style="filter: drop-shadow(2px 2px 2px rgba(0,0,0,0.5)); transform: rotate(90deg); width:28px; height:28px;"><svg viewBox="0 0 24 24" fill="#fd7e14" stroke="white" stroke-width="1"><path d="M2 20h2c.55 0 1-.45 1-1v-9c0-.55-.45-1-1-1H2v11zm19.83-7.12c.11-.25.17-.52.17-.8V11c0-1.1-.9-2-2-2h-5.5l.92-4.65c.05-.22.02-.46-.1-.66-.12-.21-.31-.37-.53-.46-.22-.1-.47-.11-.7-.03L9.67 6H7v14h11.28c.84 0 1.58-.5 1.87-1.25l2.68-7.87z"/></svg></div>'''

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dLat, dLon = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(dLat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dLon/2)**2
    return R * (2 * math.asin(math.sqrt(a)))

# Gestion des paramètres GPS
query_params = st.query_params
if "lat" in query_params and "lon" in query_params:
    user_lat = float(query_params["lat"])
    user_lon = float(query_params["lon"])
    START_POINTS["📍 Ma Position GPS"] = {"lat": user_lat, "lon": user_lon}

st.set_page_config(page_title="Plages Yeu PRO", layout="wide")
st.title("🏝️ Plages Idéales - Île d'Yeu")

# Par défaut, on sélectionne "Ma Position GPS" si elle est disponible
default_index = list(START_POINTS.keys()).index("📍 Ma Position GPS") if "📍 Ma Position GPS" in START_POINTS else 0
start_name = st.sidebar.selectbox("Lieu de départ", list(START_POINTS.keys()), index=default_index)
transport = st.sidebar.radio("🚲 Moyen de transport", ["Vélo musculaire", "Voiture"], index=0)

time_now = datetime.datetime.now().hour

# Récupération Météo
url_weather = f"https://api.open-meteo.com/v1/forecast?latitude={LATITUDE}&longitude={LONGITUDE}&hourly=temperature_2m,wind_speed_10m,wind_direction_10m,sea_surface_temperature&timezone=Europe/Paris&start_date={datetime.date.today()}&end_date={datetime.date.today()}"
w = requests.get(url_weather).json()["hourly"]
t, w_t, w_s, d = w["temperature_2m"][time_now], w["sea_surface_temperature"][time_now], w["wind_speed_10m"][time_now], w["wind_direction_10m"][time_now]
card = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"][round(d / 45) % 8]
anim_speed = max(0.4, 40.0 / max(w_s, 1))

# Récupération Marée (Algorithme Harmonique)
def get_tide_height(hour):
    offset = 7.46 
    return 3.0 + 2.1 * math.cos((hour - offset) * 2 * math.pi / 12.4)

col1, col2 = st.columns([1.5, 1])

with col1:
    st.subheader("🗺️ Carte de l'île")
    m_map = folium.Map(location=[46.72, -2.35], zoom_start=13, tiles="CartoDB positron")
    
    start_coords = START_POINTS[start_name]
    folium.Marker([start_coords["lat"], start_coords["lon"]], icon=folium.Icon(color="black", icon="home"), popup=start_name).add_to(m_map)
    
    # Plages avec nos Pouces
    for b in BEACHES:
        if card in b["good"]: icon_html, status = svg_up, "Recommandée"
        elif card in b["bad"]: icon_html, status = svg_down, "Déconseillée"
        else: icon_html, status = svg_right, "Moyenne"
        
        dist = haversine(start_coords["lat"], start_coords["lon"], b["lat"], b["lon"])
        speed = 15 if transport == "Vélo musculaire" else 30
        bike_time = int(dist * 1.3 / speed * 60)
        popup_text = f"<b>{b['name']}</b><br>{status}<br>{transport} : {bike_time} min"
        
        folium.Marker(
            location=[b["lat"], b["lon"]],
            icon=folium.DivIcon(html=icon_html),
            popup=folium.Popup(popup_text, max_width=150)
        ).add_to(m_map)
    
    # Vent Animé
    wind_towards = (d + 180) % 360
    for pt in WIND_POINTS:
        svg_wind = f"""
        <style>
            @keyframes windBlow {{
                0% {{ transform: translateY(10px); opacity: 0; }}
                20% {{ opacity: 1; }}
                80% {{ opacity: 1; }}
                100% {{ transform: translateY(-10px); opacity: 0; }}
            }}
        </style>
        <div style="transform: rotate({wind_towards}deg);">
            <svg viewBox="0 0 24 24" width="24" height="24" style="animation: windBlow {anim_speed}s infinite linear;">
                <path d="M12 21 V3 M5 10 L12 3 L19 10" stroke="#005580" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        </div>"""
        folium.Marker(location=[pt["lat"], pt["lon"]], icon=folium.DivIcon(html=svg_wind)).add_to(m_map)

    st_folium(m_map, width="100%", height=500)

with col2:
    st.subheader("📊 Conditions et Marées")
    st.write(f"🌡️ Air : **{t}°C** | 💧 Eau : **{w_t}°C**")
    st.write(f"💨 Vent : **{w_s} km/h** (Orientation : **{card}**)")
    st.caption("ℹ️ Source eau : Programme spatial Copernicus")
    
    x = [i for i in range(24)]
    y = [get_tide_height(h) for h in x]
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.plot(x, y, color="#0288d1", linewidth=2)
    ax.scatter(time_now, get_tide_height(time_now), color="red", zorder=5, s=80)
    ax.axvline(x=time_now, color='red', linestyle='--', alpha=0.5)
    ax.set_title("Cycle de la Marée (Heure actuelle en rouge)")
    ax.set_xlabel("Heure de la journée")
    ax.set_ylabel("Hauteur (m)")
    ax.grid(True, linestyle="--", alpha=0.4)
    st.pyplot(fig)

st.markdown("---")
st.subheader("📍 Calcul d'itinéraire GPS")
st.write("Utilisez le GPS de votre smartphone pour calculer les temps de trajet exacts.")

if st.button("Obtenir ma position actuelle"):
    loc_js = """
    <script>
    navigator.geolocation.getCurrentPosition(
        function(position) {
            window.parent.location.href = window.parent.location.pathname + "?lat=" + position.coords.latitude + "&lon=" + position.coords.longitude;
        },
        function(error) {
            alert("Veuillez autoriser la localisation dans votre navigateur pour utiliser cette fonction.");
        }
    );
    </script>
    """
    components.html(loc_js, height=0)
