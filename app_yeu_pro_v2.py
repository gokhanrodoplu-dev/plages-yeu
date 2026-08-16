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

BEACHES = [
    {"name": "Anse des Soux", "lat": 46.6910, "lon": -2.3209, "facing": 210},
    {"name": "Plage des Vieilles", "lat": 46.6957, "lon": -2.3137, "facing": 200},
    {"name": "Grande Conche", "lat": 46.6946, "lon": -2.2850, "facing": 160},
    {"name": "Petite Conche", "lat": 46.7065, "lon": -2.2991, "facing": 180},
    {"name": "Plage des Corbeaux", "lat": 46.6908, "lon": -2.2820, "facing": 90},
    {"name": "Marais Salés", "lat": 46.7127, "lon": -2.3103, "facing": 10},
    {"name": "Ker Châlon", "lat": 46.7196, "lon": -2.3351, "facing": 0},
    {"name": "Plage des Sapins", "lat": 46.7174, "lon": -2.3159, "facing": 20},
    {"name": "Anse des Fontaines", "lat": 46.6895, "lon": -2.3334, "facing": 220},
    {"name": "Plage de la Gournaise", "lat": 46.7337, "lon": -2.3809, "facing": 310},
    {"name": "Plage du But", "lat": 46.7257, "lon": -2.3969, "facing": 340},
    {"name": "Plage des Sabias", "lat": 46.7034, "lon": -2.3739, "facing": 30}
]

WIND_POINTS = [
    {"lat": 46.728, "lon": -2.351}, {"lat": 46.721, "lon": -2.388},
    {"lat": 46.695, "lon": -2.292}, {"lat": 46.710, "lon": -2.330},
    {"lat": 46.700, "lon": -2.319}, {"lat": 46.718, "lon": -2.360},
    {"lat": 46.705, "lon": -2.350}, {"lat": 46.710, "lon": -2.300}
]

# --- DESIGN DES POUCES (TAILLE UNIFORMISÉE 28px) ---
svg_up = '''<div style="filter: drop-shadow(2px 2px 2px rgba(0,0,0,0.5)); width:28px; height:28px;"><svg viewBox="0 0 24 24" width="28" height="28" fill="#28a745" stroke="white" stroke-width="1"><path d="M2 20h2c.55 0 1-.45 1-1v-9c0-.55-.45-1-1-1H2v11zm19.83-7.12c.11-.25.17-.52.17-.8V11c0-1.1-.9-2-2-2h-5.5l.92-4.65c.05-.22.02-.46-.1-.66-.12-.21-.31-.37-.53-.46-.22-.1-.47-.11-.7-.03L9.67 6H7v14h11.28c.84 0 1.58-.5 1.87-1.25l2.68-7.87z"/></svg></div>'''
svg_down = '''<div style="filter: drop-shadow(2px 2px 2px rgba(0,0,0,0.5)); width:28px; height:28px;"><svg viewBox="0 0 24 24" width="28" height="28" fill="#dc3545" stroke="white" stroke-width="1"><path d="M22 4h-2c-.55 0-1 .45-1 1v9c0 .55.45 1 1 1h2V4zM2.17 11.12c-.11.25-.17.52-.17.8V13c0 1.1.9 2 2 2h5.5l-.92 4.65c-.05.22-.02.46.1.66.12.21.31.37.53.46.22.1.47.11.7.03L14.33 18H17V4H5.72c-.84 0-1.58.5-1.87 1.25L1.17 11.12z"/></svg></div>'''
svg_right = '''<div style="filter: drop-shadow(2px 2px 2px rgba(0,0,0,0.5)); transform: rotate(90deg); width:28px; height:28px;"><svg viewBox="0 0 24 24" width="28" height="28" fill="#fd7e14" stroke="white" stroke-width="1"><path d="M2 20h2c.55 0 1-.45 1-1v-9c0-.55-.45-1-1-1H2v11zm19.83-7.12c.11-.25.17-.52.17-.8V11c0-1.1-.9-2-2-2h-5.5l.92-4.65c.05-.22.02-.46-.1-.66-.12-.21-.31-.37-.53-.46-.22-.1-.47-.11-.7-.03L9.67 6H7v14h11.28c.84 0 1.58-.5 1.87-1.25l2.68-7.87z"/></svg></div>'''

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dLat, dLon = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(dLat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dLon/2)**2
    return R * (2 * math.asin(math.sqrt(a)))

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
        diff = abs((wd - b["facing"] + 180) % 360 - 180)
        
        if b["name"] == "Plage des Sabias":
            is_good = True
            is_bad = False
        elif b["name"] in ["Grande Conche", "Petite Conche"]:
            is_good = False
            is_bad = False
        else:
            is_good = diff > 105
            is_bad = diff < 65

        if is_good:
            icon_html = svg_up
            status = "Recommandée (Abritée)"
        elif is_bad:
            icon_html = svg_down
            status = "Déconseillée (Exposée)"
        else:
            icon_html = svg_right
            status = "Moyenne (Vent de côté)"
        
        dist = haversine(start_coords["lat"], start_coords["lon"], b["lat"], b["lon"])
        speed = 15 if transport == "Vélo" else 30
        travel_time = int(dist * 1.3 / speed * 60)
        
        popup_text = f"<b>{b['name']}</b><br>{status}<br>{transport} : {travel_time} min"
        
        folium.Marker(
            [b["lat"], b["lon"]], 
            icon=folium.DivIcon(html=icon_html),
            popup=folium.Popup(popup_text, max_width=160)
        ).add_to(m)
    
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
    st.write(f"💨 Vent : **{ws} km/h** ({card} - {int(wd)}°)")
    
    fig, ax = plt.subplots(figsize=(6, 2.8))
    ax.plot(range(24), [get_tide_height(h) for h in range(24)], color="#0288d1")
    ax.scatter(hour, get_tide_height(hour), color="red", zorder=5)
    ax.axvline(x=hour, color='red', linestyle='--', alpha=0.5)
    ax.set_title("Cycle de la Marée (Heure actuelle en rouge)")
    st.pyplot(fig)

st.markdown("---")
if st.button("📍 Obtenir ma position GPS (Smartphone)"):
    components.html("""<script>navigator.geolocation.getCurrentPosition(p => {window.location.search="?lat="+p.coords.latitude+"&lon="+p.coords.longitude})</script>""", height=0)
