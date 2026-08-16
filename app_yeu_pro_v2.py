import os
import requests
import datetime
import math
import matplotlib.pyplot as plt
import streamlit as st
import folium
from streamlit_folium import st_folium

# --- CONFIGURATION ---
LATITUDE, LONGITUDE = 46.7236, -2.3503
# Points marins décalés vers l'océan pour éviter l'erreur de l'API sur la "terre ferme"
MARINE_LAT, MARINE_LON = 46.7000, -2.4500 

START_POINTS = {
    "Port-Joinville": {"lat": 46.7280, "lon": -2.3510},
    "Saint-Sauveur": {"lat": 46.7110, "lon": -2.3300},
    "Port de la Meule": {"lat": 46.6970, "lon": -2.3190}
}

BEACHES = [
    {"name": "Anse des Soux", "lat": 46.6910, "lon": -2.3209, "good": ["N", "NE", "E", "NO"], "bad": ["S", "SO", "O"]},
    {"name": "Plage des Vieilles", "lat": 46.6957, "lon": -2.3137, "good": ["N", "NE", "E", "NO"], "bad": ["S", "SO", "SE"]},
    {"name": "Grande Conche", "lat": 46.6946, "lon": -2.2850, "good": ["N", "NO", "O"], "bad": ["S", "SE", "E"]},
    {"name": "Petite Conche", "lat": 46.7065, "lon": -2.2991, "good": ["N", "NO", "O"], "bad": ["S", "SE", "E"]},
    {"name": "Plage des Corbeaux", "lat": 46.6945, "lon": -2.2915, "good": ["O", "NO", "SO"], "bad": ["E", "NE", "SE"]},
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
    {"lat": 46.705, "lon": -2.350}, {"lat": 46.710, "lon": -2.300},
    {"lat": 46.735, "lon": -2.330}, {"lat": 46.685, "lon": -2.330}
]

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dLat, dLon = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(dLat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dLon/2)**2
    return R * (2 * math.asin(math.sqrt(a)))

st.set_page_config(page_title="Plages Yeu PRO", layout="wide")
st.title("🏝️ Plages Idéales - Île d'Yeu")

start_name = st.sidebar.selectbox("📍 Départ", list(START_POINTS.keys()))
transport = st.sidebar.radio("🚲 Moyen de transport", ["Vélo", "Voiture"])
time_now = datetime.datetime.now().hour

# Récupération Météo
url_weather = f"https://api.open-meteo.com/v1/forecast?latitude={LATITUDE}&longitude={LONGITUDE}&hourly=temperature_2m,wind_speed_10m,wind_direction_10m,sea_surface_temperature&timezone=Europe/Paris&start_date={datetime.date.today()}&end_date={datetime.date.today()}"
w = requests.get(url_weather).json()["hourly"]
t, w_t, w_s, d = w["temperature_2m"][time_now], w["sea_surface_temperature"][time_now], w["wind_speed_10m"][time_now], w["wind_direction_10m"][time_now]
card = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"][round(d / 45) % 8]

# Récupération Marée (avec de vraies données décalées vers la mer)
try:
    url_marine = f"https://marine-api.open-meteo.com/v1/marine?latitude={MARINE_LAT}&longitude={MARINE_LON}&hourly=sea_surface_height_above_sea_level&timezone=Europe/Paris&start_date={datetime.date.today()}&end_date={datetime.date.today()}"
    m_data = requests.get(url_marine).json()["hourly"]
    heights = m_data["sea_surface_height_above_sea_level"]
except:
    # Fallback mathématique si l'API est injoignable
    heights = [3.0 + 2.0 * math.sin((i - 4) * math.pi / 6.2) for i in range(24)]

col1, col2 = st.columns([1.5, 1])

with col1:
    st.subheader("🗺️ Carte de l'île")
    m_map = folium.Map(location=[46.72, -2.35], zoom_start=13, tiles="CartoDB positron")
    
    # Plages avec pouces
    for b in BEACHES:
        if card in b["good"]: icon, color = "👍", "green"
        elif card in b["bad"]: icon, color = "👎", "red"
        else: icon, color = "✋", "orange"
        
        dist = haversine(START_POINTS[start_name]["lat"], START_POINTS[start_name]["lon"], b["lat"], b["lon"])
        popup_text = f"<b>{b['name']}</b><br>{icon}<br>{int(dist*1.3/(14 if transport=='Vélo' else 30)*60)} min en {transport}"
        folium.Marker(
            location=[b["lat"], b["lon"]],
            icon=folium.DivIcon(html=f'<div style="font-size:20px; color:{color}; font-weight:bold;">{icon}</div>'),
            popup=folium.Popup(popup_text, max_width=150)
        ).add_to(m_map)
    
    # Vent Animé
    wind_towards = (d + 180) % 360
    for pt in WIND_POINTS:
        svg = f"""<div style="transform: rotate({wind_towards}deg); animation: windBlow 1.5s infinite linear; opacity: 0.6;">
        <svg viewBox="0 0 24 24" width="20" height="20" stroke="gray" stroke-width="3" fill="none"><line x1="12" y1="19" x2="12" y2="5"/><polyline points="7 10 12 5 17 10"/></svg></div>"""
        folium.Marker(location=[pt["lat"], pt["lon"]], icon=folium.DivIcon(html=svg)).add_to(m_map)

    st_folium(m_map, width="100%", height=500)

with col2:
    st.subheader("📊 Conditions et Marées")
    st.write(f"🌡️ Air: **{t}°C** | 💧 Eau: **{w_t}°C**")
    st.write(f"💨 Vent: **{w_s} km/h** (Orientation : **{card}**)")
    
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.plot(range(24), heights, color="#0288d1", linewidth=2)
    ax.scatter(time_now, heights[time_now], color="red", zorder=5, s=80)
    ax.axvline(x=time_now, color='red', linestyle='--', alpha=0.5)
    ax.set_title("Cycle de la Marée (Heure actuelle en rouge)")
    ax.set_xlabel("Heure de la journée")
    ax.set_ylabel("Hauteur (m)")
    ax.grid(True, linestyle="--", alpha=0.4)
    st.pyplot(fig)
