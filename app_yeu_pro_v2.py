import os
import requests
import datetime
import math
import matplotlib.pyplot as plt
import streamlit as st
import folium
from streamlit_folium import st_folium
from google import genai

# --- DONNÉES GÉOGRAPHIQUES ---
LATITUDE, LONGITUDE = 46.7236, -2.3503
START_POINTS = {
    "Port-Joinville": {"lat": 46.7280, "lon": -2.3510},
    "Saint-Sauveur": {"lat": 46.7110, "lon": -2.3300},
    "Port de la Meule": {"lat": 46.6970, "lon": -2.3190}
}

# --- LISTE DES PLAGES (Vos coordonnées précises) ---
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

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371
    dLat, dLon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dLat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon/2)**2
    return R * (2 * math.asin(math.sqrt(a)))

@st.cache_data(ttl=3600)
def fetch_weather(date_str):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={LATITUDE}&longitude={LONGITUDE}&hourly=temperature_2m,wind_speed_10m,wind_direction_10m,sea_surface_temperature&timezone=Europe/Paris&start_date={date_str}&end_date={date_str}"
    return requests.get(url).json()["hourly"]

# --- INTERFACE ---
st.set_page_config(page_title="Plages Yeu", layout="wide")
st.title("🏝️ Plages Idéales - Île d'Yeu")

weather = fetch_weather(datetime.date.today().strftime("%Y-%m-%d"))
temp = weather["temperature_2m"][12]
water_temp = weather["sea_surface_temperature"][12]
wind_speed = weather["wind_speed_10m"][12]
wind_deg = weather["wind_direction_10m"][12]

# Direction du vent simplifiée
cardinals_short = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]
card_short = cardinals_short[round(wind_deg / 45) % 8]

st.write(f"🌡️ Air: {temp}°C | 💧 Eau: {water_temp}°C | 💨 Vent: {wind_speed} km/h")

m = folium.Map(location=[46.72, -2.35], zoom_start=13, tiles="CartoDB positron")
for b in BEACHES:
    if card_short in b["good"]: emoji, color = "😊", "green"
    elif card_short in b["bad"]: emoji, color = "☹️", "red"
    else: emoji, color = "😐", "orange"
    
    folium.Marker(
        location=[b["lat"], b["lon"]],
        icon=folium.Icon(color=color),
        popup=f"{b['name']} {emoji}"
    ).add_to(m)

st_folium(m, width=700, height=500)
