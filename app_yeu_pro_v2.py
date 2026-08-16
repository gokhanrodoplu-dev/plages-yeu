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

# --- MATRICE D'EXPOSITION STRICTE ---
BEACHES = [
    # Côte Sauvage (Abritée par N, NE, E)
    {"name": "Anse des Soux", "lat": 46.6910, "lon": -2.3209, "good": ["N", "NE", "E"], "bad": ["S", "SO", "O", "NO"]},
    {"name": "Plage des Vieilles", "lat": 46.6957, "lon": -2.3137, "good": ["N", "NE", "E"], "bad": ["S", "SO", "O", "NO"]},
    {"name": "Grande Conche", "lat": 46.6946, "lon": -2.2850, "good": ["N", "NE", "E"], "bad": ["S", "SO", "O", "NO"]},
    {"name": "Petite Conche", "lat": 46.7065, "lon": -2.2991, "good": ["N", "NE", "E"], "bad": ["S", "SO", "O", "NO"]},
    {"name": "Plage de la Belle Maison", "lat": 46.7081, "lon": -2.3844, "good": ["N", "NE", "E"], "bad": ["S", "SO", "O", "NO"]},
    
    # Côte Nord / Nord-Est (Abritée par S, SO, O)
    {"name": "Plage des Sabias", "lat": 46.7034, "lon": -2.3739, "good": ["S", "SO", "O", "NO"], "bad": ["N", "NE", "E"]},
    {"name": "Ker Châlon", "lat": 46.7196, "lon": -2.3351, "good": ["S", "SO", "O", "NO"], "bad": ["N", "NE", "E"]},
    {"name": "Plage des Corbeaux", "lat": 46.6908, "lon": -2.2820, "good": ["S", "SO", "O", "NO"], "bad": ["N", "NE", "E"]},
    {"name": "Marais Salés", "lat": 46.7127, "lon": -2.3103, "good": ["S", "SO", "O", "NO"], "bad": ["N", "NE", "E"]},
    {"name": "Plage des Sapins", "lat": 46.7174, "lon": -2.3159, "good": ["S", "SO", "O", "NO"], "bad": ["N", "NE", "E"]},
    
    # Autres
    {"name": "Plage de la Gournaise", "lat": 46.7337, "lon": -2.3809, "good": ["S", "SE", "E"], "bad": ["N", "NO", "O"]},
    {"name": "Plage du But", "lat": 46.7257, "lon": -2.3969, "good": ["S", "SE", "E"], "bad": ["N", "NO", "O"]}
]

WIND_POINTS = [{"lat": 46.728, "lon": -2.351}, {"lat": 46.721, "lon": -2.388}, {"lat": 46.695, "lon": -2.292}, {"lat": 46.710, "lon": -2.330}]

# --- SVG ---
svg_up = '''<div style="width:28px; height:28px;"><svg viewBox="0 0 24 24" fill="#28a745"><path d="M2 20h2c.55 0 1-.45 1-1v-9c0-.55-.45-1-1-1H2v11zm19.83-7.12c.11-.25.17-.52.17-.8V11c0-1.1-.9-2-2-2h-5.5l.92-4.65c.05-.22.02-.46-.1-.66-.12-.21-.31-.37-.53-.46-.22-.1-.47-.11-.7-.03L9.67 6H7v14h11.28c.84 0 1.58-.5 1.87-1.25l2.68-7.87z"/></svg></div>'''
svg_down = '''<div style="width:28px; height:28px;"><svg viewBox="0 0 24 24" fill="#dc3545"><path d="M22 4h-2c-.55 0-1 .45-1 1v9c0 .55.45 1 1 1h2V4zM2.17 11.12c-.11.25-.17.52-.17.8V13c0 1.1.9 2 2 2h5.5l-.92 4.65c-.05.22-.02.46.1.66.12.21.31.37.53.46.22.1.47.11.7.03L14.33 18H17V4H5.72c-.84 0-1.58.5-1.87 1.25L1.17 11.12z"/></svg></div>'''
svg_right = '''<div style="width:28px; height:28px;"><svg viewBox="0 0 24 24" fill="#fd7e14"><path d="M2 20h2c.55 0 1-.45 1-1v-9c0-.55-.45-1-1-1H2v11zm19.83-7.12c.11-.25.17-.52.17-.8V11c0-1.1-.9-2-2-2h-5.5l.92-4.65c.05-.22.02-.46-.1-.66-.12-.21-.31-.37-.53-.46-.22-.1-.47-.11-.7-.03L9.67 6H7v14h11.28c.84 0 1.58-.5 1.87-1.25l2.68-7.87z" transform="rotate(90 12 12)"/></svg></div>'''

# --- LOGIQUE ---
st.set_page_config(page_title="Plages Yeu PRO", layout="wide")
st.title("🏝️ Plages Idéales - Île d'Yeu")

# GPS
query_params = st.query_params
if "lat" in query_params:
    START_POINTS["📍 Position GPS"] = {"lat": float(query_params["lat"]), "lon": float(query_params["lon"])}

start_name = st.sidebar.selectbox("Départ", list(START_POINTS.keys()))
transport = st.sidebar.radio("Transport", ["Vélo", "Voiture"])
time_now = datetime.datetime.now().hour

# Météo
url = f"https://api.open-meteo.com/v1/forecast?latitude={LATITUDE}&longitude={LONGITUDE}&hourly=wind_speed_10m,wind_direction_10m,sea_surface_temperature,temperature_2m&timezone=Europe/Paris&start_date={datetime.date.today()}&end_date={datetime.date.today()}"
w = requests.get(url).json()["hourly"]
t, w_t, w_s, d = w["temperature_2m"][time_now], w["sea_surface_temperature"][time_now], w["wind_speed_10m"][time_now], w["wind_direction_10m"][time_now]
card = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"][round(d / 45) % 8]

col1, col2 = st.columns([1.5, 1])

with col1:
    m = folium.Map(location=[46.72, -2.35], zoom_start=13, tiles="CartoDB positron")
    for b in BEACHES:
        icon = svg_up if card in b["good"] else (svg_down if card in b["bad"] else svg_right)
        folium.Marker([b["lat"], b["lon"]], icon=folium.DivIcon(html=icon), popup=b["name"]).add_to(m)
    
    wind_rot = (d + 180) % 360
    for pt in WIND_POINTS:
        folium.Marker([pt["lat"], pt["lon"]], icon=folium.DivIcon(html=f'<div style="transform: rotate({wind_rot}deg);"><svg width="20" height="20" viewBox="0 0 24 24" stroke="blue" fill="none"><path d="M12 21V3M5 10l7-7 7 7"/></svg></div>')).add_to(m)
    st_folium(m, width="100%", height=500)

with col2:
    st.write(f"🌡️ Air: {t}°C | 💧 Eau: {w_t}°C | 💨 {w_s} km/h ({card})")
    y = [2.94 + 2.06 * math.cos((h - 7.46) * 2 * math.pi / 12.4) for h in range(24)]
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.plot(range(24), y)
    ax.scatter(time_now, y[time_now], color="red")
    st.pyplot(fig)

if st.button("Obtenir ma position GPS"):
    components.html("""<script>navigator.geolocation.getCurrentPosition(p => {window.location.search="?lat="+p.coords.latitude+"&lon="+p.coords.longitude})</script>""", height=0)
