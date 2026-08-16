import streamlit as st
import datetime
import math
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium
import requests

# Configuration initiale
LATITUDE, LONGITUDE = 46.7236, -2.3503
START_POINTS = {
    "Port-Joinville": {"lat": 46.7280, "lon": -2.3510},
    "Saint-Sauveur": {"lat": 46.7110, "lon": -2.3300},
    "Port de la Meule": {"lat": 46.6970, "lon": -2.3190}
}

# --- MATRICE D'EXPOSITION (Règle : "good" = plages abritées du vent actuel) ---
BEACHES = [
    {"name": "Anse des Soux", "lat": 46.6910, "lon": -2.3209, "good": ["N", "NE", "E"], "bad": ["S", "SO", "O"]},
    {"name": "Plage des Vieilles", "lat": 46.6957, "lon": -2.3137, "good": ["N", "NE", "E"], "bad": ["S", "SO", "O"]},
    {"name": "Grande Conche", "lat": 46.6946, "lon": -2.2850, "good": ["N", "NE", "E"], "bad": ["S", "SO", "O"]},
    {"name": "Petite Conche", "lat": 46.7065, "lon": -2.2991, "good": ["N", "NE", "E"], "bad": ["S", "SO", "O"]},
    {"name": "Plage des Corbeaux", "lat": 46.6908, "lon": -2.2820, "good": ["S", "SO", "O"], "bad": ["N", "NE", "E"]},
    {"name": "Marais Salés", "lat": 46.7127, "lon": -2.3103, "good": ["S", "SO", "O"], "bad": ["N", "NE", "E"]},
    {"name": "Ker Châlon", "lat": 46.7196, "lon": -2.3351, "good": ["S", "SO", "O"], "bad": ["N", "NE", "E"]},
    {"name": "Plage des Sapins", "lat": 46.7174, "lon": -2.3159, "good": ["S", "SO", "O"], "bad": ["N", "NE", "E"]},
    {"name": "Anse des Fontaines", "lat": 46.6895, "lon": -2.3334, "good": ["N", "NE", "E"], "bad": ["S", "SO", "O"]},
    {"name": "Plage de la Gournaise", "lat": 46.7337, "lon": -2.3809, "good": ["S", "SE", "E"], "bad": ["N", "NO", "O"]},
    {"name": "Plage du But", "lat": 46.7257, "lon": -2.3969, "good": ["S", "SE", "E"], "bad": ["N", "NO", "O"]},
    {"name": "Plage des Sabias", "lat": 46.7034, "lon": -2.3739, "good": ["S", "SO", "O"], "bad": ["N", "NE", "E"]}
]

# Fonction de marée fixe et fiable
def get_tide_height(hour):
    return 2.94 + 2.06 * math.cos((hour - 7.46) * 2 * math.pi / 12.4)

st.set_page_config(page_title="Plages Yeu", layout="wide")
st.title("🏝️ Plages Idéales - Île d'Yeu")

# Météo
url = f"https://api.open-meteo.com/v1/forecast?latitude={LATITUDE}&longitude={LONGITUDE}&hourly=wind_speed_10m,wind_direction_10m&timezone=Europe/Paris&start_date={datetime.date.today()}&end_date={datetime.date.today()}"
w = requests.get(url).json()["hourly"]
hour = datetime.datetime.now().hour
ws, wd = w["wind_speed_10m"][hour], w["wind_direction_10m"][hour]
card = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"][round(wd / 45) % 8]

# Affichage
col1, col2 = st.columns([1.5, 1])

with col1:
    m = folium.Map(location=[46.72, -2.35], zoom_start=13, tiles="CartoDB positron")
    for b in BEACHES:
        icon, color = ("👍", "green") if card in b["good"] else (("👎", "red") if card in b["bad"] else ("✋", "orange"))
        folium.Marker([b["lat"], b["lon"]], icon=folium.DivIcon(html=f'<div style="font-size:20px; color:{color};"><b>{icon}</b></div>'), popup=b["name"]).add_to(m)
    st_folium(m, width="100%", height=500)

with col2:
    st.write(f"💨 Vent : **{ws} km/h** ({card})")
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.plot(range(24), [get_tide_height(h) for h in range(24)])
    ax.scatter(hour, get_tide_height(hour), color="red")
    st.pyplot(fig)
