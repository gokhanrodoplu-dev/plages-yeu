import streamlit as st
import datetime
import math
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium
import requests
import streamlit.components.v1 as components

# --- CONFIGURATION ---
LATITUDE, LONGITUDE = 46.7236, -2.3503
START_POINTS = {
    "Port-Joinville": {"lat": 46.7280, "lon": -2.3510},
    "Saint-Sauveur": {"lat": 46.7110, "lon": -2.3300},
    "Port de la Meule": {"lat": 46.6970, "lon": -2.3190}
}

# VOTRE LISTE D'ORIGINE EXACTE
BEACHES = [
    {"name": "Anse des Soux", "lat": 46.6910, "lon": -2.3209, "good": ["N", "NE", "E", "NO"], "bad": ["S", "SO", "O"]},
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
    {"name": "Plage des Sabias", "lat": 46.7034, "lon": -2.3739, "good": ["E", "SE", "NE"], "bad": ["O", "NO", "SO"]}
]

WIND_POINTS = [
    {"lat": 46.728, "lon": -2.351}, {"lat": 46.721, "lon": -2.388},
    {"lat": 46.695, "lon": -2.292}, {"lat": 46.710, "lon": -2.330},
    {"lat": 46.700, "lon": -2.319}, {"lat": 46.718, "lon": -2.360},
    {"lat": 46.705, "lon": -2.350}, {"lat": 46.710, "lon": -2.300}
]

def get_tide_height(hour):
    return 2.94 + 2.06 * math.cos((hour - 7.46) * 2 * math.pi / 12.4)

query_params = st.query_params
if "lat" in query_params and "lon" in query_params:
    START_POINTS["📍 Ma Position GPS"] = {"lat": float(query_params["lat"]), "lon": float(query_params["lon"])}

st.set_page_config(page_title="Plages Yeu PRO", layout="wide")
st.title("🏝️ Plages Idéales - Île d'Yeu")

url = f"https://api.open-meteo.com/v1/forecast?latitude={LATITUDE}&longitude={LONGITUDE}&hourly=wind_speed_10m,wind_direction_10m,temperature_2m,sea_surface_temperature&timezone=Europe/Paris&start_date={datetime.date.today()}&end_date={datetime.date.today()}"
w = requests.get(url).json()["hourly"]
hour = datetime.datetime.now().hour
ws, wd, temp, water = w["wind_speed_10m"][hour], w["wind_direction_10m"][hour], w["temperature_2m"][hour], w["sea_surface_temperature"][hour]
card = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"][round(wd / 45) % 8]
anim_speed = max(0.4, 40.0 / max(ws, 1))

default_index = list(START_POINTS.keys()).index("📍 Ma Position GPS") if "📍 Ma Position GPS" in START_POINTS else 0
start_name = st.sidebar.selectbox("📍 Départ", list(START_POINTS.keys()), index=default_index)
transport = st.sidebar.radio("🚲 Transport", ["Vélo", "Voiture"], horizontal=True)

col1, col2 = st.columns([1.5, 1])

with col1:
    st.subheader("🗺️ Carte de l'île")
    m = folium.Map(location=[46.72, -2.35], zoom_start=13, tiles="CartoDB positron")
    
    start_coords = START_POINTS[start_name]
    folium.Marker([start_coords["lat"], start_coords["lon"]], icon=folium.Icon(color="black", icon="home"), popup=start_name).add_to(m)
    
    for b in BEACHES:
        if card in b["good"]: icon, color = "👍", "green"
        elif card in b["bad"]: icon, color = "👎", "red"
        else: icon, color = "✋", "orange"
        
        folium.Marker(
            [b["lat"], b["lon"]], 
            icon=folium.DivIcon(html=f'<div style="font-size:20px; color:{color};"><b>{icon}</b></div>'),
            popup=b["name"]
        ).add_to(m)
    
    # Flèches de vent animées
    wind_towards = (wd + 180) % 360
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
            <svg viewBox="0 0 24 24" width="22" height="22" style="animation: windBlow {anim_speed}s infinite linear;">
                <path d="M12 21 V3 M5 10 L12 3 L19 10" stroke="#005580" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        </div>"""
        folium.Marker(location=[pt["lat"], pt["lon"]], icon=folium.DivIcon(html=svg_wind)).add_to(m)

    st_folium(m, width="100%", height=450)

with col2:
    st.subheader("📊 Conditions et Marées")
    st.write(f"🌡️ Air : **{temp}°C** | 💧 Eau : **{water}°C**")
    st.write(f"💨 Vent : **{ws} km/h** ({card})")
    
    fig, ax = plt.subplots(figsize=(6, 2.8))
    ax.plot(range(24), [get_tide_height(h) for h in range(24)], color="#0288d1")
    ax.scatter(hour, get_tide_height(hour), color="red", zorder=5)
    ax.axvline(x=hour, color='red', linestyle='--', alpha=0.5)
    ax.set_title("Cycle de la Marée (Heure actuelle en rouge)")
    st.pyplot(fig)

st.markdown("---")
if st.button("📍 Obtenir ma position GPS (Smartphone)"):
    components.html("""<script>navigator.geolocation.getCurrentPosition(p => {window.location.search="?lat="+p.coords.latitude+"&lon="+p.coords.longitude})</script>""", height=0)
