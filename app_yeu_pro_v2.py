import os
import requests
import datetime
import math
import matplotlib.pyplot as plt
import streamlit as st
import folium
from streamlit_folium import st_folium
from google import genai

# --- CONFIGURATION ---
LATITUDE, LONGITUDE = 46.7236, -2.3503
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
    {"name": "Plage des Corbeaux", "lat": 46.6960, "lon": -2.2930, "good": ["O", "NO", "SO"], "bad": ["E", "NE", "SE"]},
    {"name": "Marais Salés", "lat": 46.7127, "lon": -2.3103, "good": ["S", "SO", "O"], "bad": ["N", "NE", "E"]},
    {"name": "Ker Châlon", "lat": 46.7196, "lon": -2.3351, "good": ["S", "SO", "SE"], "bad": ["N", "NE", "E", "NO"]},
    {"name": "Plage des Sapins", "lat": 46.7174, "lon": -2.3159, "good": ["S", "SO", "SE"], "bad": ["N", "NE", "E", "NO"]},
    {"name": "Anse des Fontaines", "lat": 46.6895, "lon": -2.3334, "good": ["N", "NE", "E"], "bad": ["S", "SO", "O"]},
    {"name": "Plage de la Gournaise", "lat": 46.7337, "lon": -2.3809, "good": ["S", "SE", "SO"], "bad": ["N", "NE", "NO"]},
    {"name": "Plage du But", "lat": 46.7257, "lon": -2.3969, "good": ["S", "SE", "E"], "bad": ["N", "NO", "O"]},
    {"name": "Plage des Sabias", "lat": 46.7034, "lon": -2.3739, "good": ["E", "SE", "NE"], "bad": ["O", "NO", "SO"]}
]

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dLat, dLon = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(dLat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dLon/2)**2
    return R * (2 * math.asin(math.sqrt(a)))

st.set_page_config(page_title="Plages Yeu PRO", layout="wide")
st.title("🏝️ Plages Idéales - Île d'Yeu")

start_point = st.sidebar.selectbox("📍 Départ", list(START_POINTS.keys()))
date = st.date_input("📅 Date", datetime.date.today())

# Fetch Data
url = f"https://api.open-meteo.com/v1/forecast?latitude={LATITUDE}&longitude={LONGITUDE}&hourly=temperature_2m,wind_speed_10m,wind_direction_10m,sea_surface_temperature&timezone=Europe/Paris&start_date={date}&end_date={date}"
w = requests.get(url).json()["hourly"]
idx = 12 # Mid-day
temp, water, wind, deg = w["temperature_2m"][idx], w["sea_surface_temperature"][idx], w["wind_speed_10m"][idx], w["wind_direction_10m"][idx]
card = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"][round(deg / 45) % 8]

st.subheader(f"🌡️ Air: {temp}°C | 💧 Eau: {water}°C | 💨 Vent: {wind} km/h ({card})")

# Marée (Simulation)
heights = [3.0 + 2.0 * math.sin((i - 4) * math.pi / 6.2) for i in range(24)]
fig, ax = plt.subplots(figsize=(8, 2))
ax.plot(range(24), heights, color="#0288d1")
ax.set_title("Cycle Marée")
st.pyplot(fig)

# Carte
m = folium.Map(location=[46.72, -2.35], zoom_start=13, tiles="CartoDB positron")
for b in BEACHES:
    status, emoji, color = ("Recommandée", "😊", "green") if card in b["good"] else (("Déconseillée", "☹️", "red") if card in b["bad"] else ("Moyenne", "😐", "orange"))
    dist = haversine(START_POINTS[start_point]["lat"], START_POINTS[start_point]["lon"], b["lat"], b["lon"])
    
    popup_text = f"<b>{b['name']}</b><br>{emoji} {status}<br>🚲 {int(dist*1.3/14*60)} min<br>📍 {b['lat']:.4f}, {b['lon']:.4f}"
    folium.Marker(
        location=[b["lat"], b["lon"]],
        icon=folium.DivIcon(html=f'<div style="font-size: 20px;">{emoji}</div>'),
        popup=folium.Popup(popup_text, max_width=200)
    ).add_to(m)

st_folium(m, width=800, height=500)
