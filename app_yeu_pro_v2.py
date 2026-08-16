import streamlit as st
import datetime
import math
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium
import requests

# --- CONFIGURATION ---
LATITUDE, LONGITUDE = 46.7236, -2.3503
START_POINTS = {
    "Port-Joinville": {"lat": 46.7280, "lon": -2.3510},
    "Saint-Sauveur": {"lat": 46.7110, "lon": -2.3300},
    "Port-Meule": {"lat": 46.6970, "lon": -2.3190}
}

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

def get_tide_height(hour):
    # Algorithme harmonique : 2 pics par jour (~12.4h)
    # Calé pour correspondre à la marée haute de 7h28 ce 16 août 2026
    offset = 7.46 
    return 3.0 + 2.1 * math.cos((hour - offset) * 2 * math.pi / 12.4)

st.set_page_config(page_title="Plages Yeu PRO", layout="wide")
st.title("🏝️ Plages Idéales - Île d'Yeu")

col1, col2 = st.columns([1.5, 1])

with col1:
    st.subheader("🗺️ Carte de l'île")
    start_name = st.selectbox("📍 Départ", list(START_POINTS.keys()))
    transport = st.radio("🚲 Moyen de transport", ["Vélo", "Voiture"], horizontal=True)
    
    # Météo
    url = f"https://api.open-meteo.com/v1/forecast?latitude={LATITUDE}&longitude={LONGITUDE}&hourly=wind_speed_10m,wind_direction_10m&timezone=Europe/Paris&start_date={datetime.date.today()}&end_date={datetime.date.today()}"
    w = requests.get(url).json()["hourly"]
    hour = datetime.datetime.now().hour
    wind_speed, wind_deg = w["wind_speed_10m"][hour], w["wind_direction_10m"][hour]
    card = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"][round(wind_deg / 45) % 8]

    m = folium.Map(location=[46.72, -2.35], zoom_start=13, tiles="CartoDB positron")
    for b in BEACHES:
        icon, color = ("👍", "green") if card in b["good"] else (("👎", "red") if card in b["bad"] else ("✋", "orange"))
        folium.Marker([b["lat"], b["lon"]], icon=folium.DivIcon(html=f'<div style="font-size:20px; color:{color};"><b>{icon}</b></div>')).add_to(m)
    st_folium(m, width="100%", height=400)

with col2:
    st.subheader("📊 Conditions")
    st.write(f"💨 Vent : **{wind_speed} km/h** ({card})")
    
    # Marée précise
    x = [i for i in range(24)]
    y = [get_tide_height(h) for h in x]
    fig, ax = plt.subplots(figsize=(5, 2.5))
    ax.plot(x, y, color="#0288d1")
    ax.scatter(hour, get_tide_height(hour), color="red", s=100, zorder=5)
    ax.set_title("Marée (Point rouge = Maintenant)")
    st.pyplot(fig)
