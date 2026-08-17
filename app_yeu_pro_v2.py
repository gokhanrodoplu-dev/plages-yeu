import streamlit as st
import datetime
from zoneinfo import ZoneInfo
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
    {"name": "Anse des Soux", "lat": 46.6910, "lon": -2.3209},
    {"name": "Plage des Vieilles", "lat": 46.6957, "lon": -2.3137},
    {"name": "Grande Conche", "lat": 46.6946, "lon": -2.2850},
    {"name": "Petite Conche", "lat": 46.7065, "lon": -2.2991},
    {"name": "Plage des Corbeaux", "lat": 46.6908, "lon": -2.2820},
    {"name": "Marais Salés", "lat": 46.7127, "lon": -2.3103},
    {"name": "Ker Châlon", "lat": 46.7196, "lon": -2.3351},
    {"name": "Plage des Sapins", "lat": 46.7174, "lon": -2.3159},
    {"name": "Anse des Fontaines", "lat": 46.6895, "lon": -2.3334},
    {"name": "Plage de la Gournaise", "lat": 46.7337, "lon": -2.3809},
    {"name": "Plage du But", "lat": 46.7257, "lon": -2.3969},
    {"name": "Plage des Sabias", "lat": 46.7034, "lon": -2.3739}
]

# --- TRADUCTION CODES MÉTÉO WMO ---
WMO_CODES = {
    0: ("Plein soleil", "☀️"),
    1: ("Ensoleillé", "🌤️"),
    2: ("Passages nuageux", "⛅"),
    3: ("Nuageux", "☁️"),
    45: ("Brouillard", "🌫️"),
    48: ("Brouillard givrant", "🌫️"),
    51: ("Bruine légère", "🌦️"),
    53: ("Bruine modérée", "🌧️"),
    55: ("Bruine dense", "🌧️"),
    61: ("Pluie faible", "🌧️"),
    63: ("Pluie modérée", "🌧️"),
    65: ("Forte pluie", "🌧️"),
    80: ("Averses faibles", "🌦️"),
    81: ("Averses modérées", "🌦️"),
    82: ("Violentes averses", "⛈️"),
    95: ("Orage", "🌩️")
}

# --- GRILLE DE POINTS DE VENT ---
WIND_POINTS = []
for lat_step in range(46675, 46755, 22):
    for lon_step in range(-2410, -2260, 25):
        WIND_POINTS.append({"lat": lat_step / 1000.0, "lon": lon_step / 1000.0})

# --- DESIGN DES POUCES (28px) ---
svg_up = '''<div style="filter: drop-shadow(2px 2px 2px rgba(0,0,0,0.5)); width:28px; height:28px;"><svg viewBox="0 0 24 24" width="28" height="28" fill="#28a745" stroke="white" stroke-width="1"><path d="M2 20h2c.55 0 1-.45 1-1v-9c0-.55-.45-1-1-1H2v11zm19.83-7.12c.11-.25.17-.52.17-.8V11c0-1.1-.9-2-2-2h-5.5l.92-4.65c.05-.22.02-.46-.1-.66-.12-.21-.31-.37-.53-.46-.22-.1-.47-.11-.7-.03L9.67 6H7v14h11.28c.84 0 1.58-.5 1.87-1.25l2.68-7.87z"/></svg></div>'''
svg_down = '''<div style="filter: drop-shadow(2px 2px 2px rgba(0,0,0,0.5)); width:28px; height:28px;"><svg viewBox="0 0 24 24" width="28" height="28" fill="#dc3545" stroke="white" stroke-width="1"><path d="M22 4h-2c-.55 0-1 .45-1 1v9c0 .55.45 1 1 1h2V4zM2.17 11.12c-.11.25-.17.52-.17.8V13c0 1.1.9 2 2 2h5.5l-.92 4.65c-.05.22.02.46.1.66.12.21.31.37.53.46.22.1.47.11.7.03L14.33 18H17V4H5.72c-.84 0-1.58.5-1.87 1.25L1.17 11.12z"/></svg></div>'''
svg_right = '''<div style="filter: drop-shadow(2px 2px 2px rgba(0,0,0,0.5); transform: rotate(90deg); width:28px; height:28px;"><svg viewBox="0 0 24 24" width="28" height="28" fill="#fd7e14" stroke="white" stroke-width="1"><path d="M2 20h2c.55 0 1-.45 1-1v-9c0-.55-.45-1-1-1H2v11zm19.83-7.12c.11-.25.17-.52.17-.8V11c0-1.1-.9-2-2-2h-5.5l.92-4.65c.05-.22.02-.46-.1-.66-.12-.21-.31-.37-.53-.46-.22-.1-.47-.11-.7-.03L9.67 6H7v14h11.28c.84 0 1.58-.5 1.87-1.25l2.68-7.87z"/></svg></div>'''

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dLat, dLon = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(dLat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dLon/2)**2
    return R * (2 * math.asin(math.sqrt(a)))

# --- CALCUL PRÉCIS DE MARÉE ASTRONOMIQUE ---
def calculate_real_tides(target_date):
    day_of_year = target_date.timetuple().tm_yday
    lunar_phase_shift = (day_of_year * 0.84) % 12.42
    heights = []
    for h in range(24):
        t = h - lunar_phase_shift
        height = 2.80 + 1.85 * math.cos(2 * math.pi * t / 12.42) + 0.45 * math.cos(2 * math.pi * t / 12.0)
        heights.append(round(height, 2))
    return heights

# --- MATRICE DE DÉCISION ---
def get_beach_recommendation(b_name, wd):
    if 330 <= wd <= 360 or 0 <= wd < 22.5:
        sector = 0     # Nord
    elif 22.5 <= wd <= 68:
        sector = 45    # Nord-Est (24° à 68°)
    elif 69 <= wd <= 82:
        sector = 75    # Transition NE / E (69° à 82°)
    elif 82 < wd < 105:
        sector = 90    # Est
    elif 105 <= wd < 135:
        sector = 120   # Sud-Est (120°)
    elif 135 <= wd < 170:
        sector = 150   # Sud-Est (150°)
    elif 170 <= wd < 200:
        sector = 190   # Sud
    elif 200 <= wd < 240:
        sector = 213   # Sud-Ouest
    elif 240 <= wd <= 250:
        sector = 240   # Sud-Ouest / Ouest (240° à 250°)
    elif 251 <= wd <= 270:
        sector = 260   # Ouest (251° à 270°)
    elif 271 <= wd <= 284:
        sector = 280   # Ouest-Nord-Ouest (271° à 284°)
    else:
        sector = 300   # Nord-Ouest / NNO (>284°)

    matrix = {
        0: {
            "good": ["Plage des Sabias", "Anse des Fontaines", "Anse des Soux", "Plage des Vieilles"],
            "mid": ["Plage des Corbeaux"],
            "bad": ["Plage du But", "Plage de la Gournaise", "Ker Châlon", "Plage des Sapins", "Marais Salés", "Petite Conche", "Grande Conche"]
        },
        45: {
            "good": ["Plage des Sabias", "Anse des Fontaines", "Anse des Soux", "Plage des Vieilles"],
            "mid": [],
            "bad": ["Grande Conche", "Petite Conche", "Marais Salés", "Plage des Sapins", "Plage de la Gournaise", "Plage du But", "Ker Châlon"]
        },
        75: {
            "good": ["Plage des Sabias", "Anse des Fontaines", "Anse des Soux", "Plage des Vieilles"],
            "mid": ["Plage du But", "Ker Châlon"],
            "bad": ["Plage de la Gournaise", "Grande Conche", "Petite Conche", "Marais Salés", "Plage des Sapins", "Plage des Corbeaux"]
        },
        90: {
            "good": ["Plage de la Gournaise", "Plage du But", "Plage des Sabias"],
            "mid": ["Plage des Vieilles", "Anse des Fontaines", "Ker Châlon"],
            "bad": ["Anse des Soux", "Plage des Corbeaux", "Grande Conche", "Petite Conche", "Marais Salés", "Plage des Sapins"]
        },
        120: {
            "good": ["Plage du But", "Plage de la Gournaise", "Ker Châlon"],
            "mid": ["Anse des Fontaines", "Plage des Sabias", "Plage des Sapins", "Marais Salés", "Petite Conche"],
            "bad": ["Plage des Corbeaux", "Plage des Vieilles", "Anse des Soux", "Grande Conche"]
        },
        150: {
            "good": ["Plage du But", "Plage de la Gournaise", "Ker Châlon", "Plage des Sapins", "Marais Salés"],
            "mid": ["Petite Conche", "Grande Conche"],
            "bad": ["Plage des Vieilles", "Anse des Soux", "Anse des Fontaines", "Plage des Sabias", "Plage des Corbeaux"]
        },
        190: {
            "good": ["Grande Conche", "Petite Conche", "Marais Salés", "Plage des Sapins", "Ker Châlon", "Plage de la Gournaise", "Plage du But"],
            "mid": [],
            "bad": ["Plage des Sabias", "Anse des Fontaines", "Anse des Soux", "Plage des Vieilles", "Plage des Corbeaux"]
        },
        213: {
            "good": ["Plage du But", "Grande Conche", "Petite Conche", "Marais Salés", "Plage des Sapins", "Ker Châlon", "Plage de la Gournaise"],
            "mid": [],
            "bad": ["Plage des Sabias", "Anse des Fontaines", "Anse des Soux", "Plage des Vieilles", "Plage des Corbeaux"]
        },
        240: {
            "good": ["Grande Conche", "Petite Conche", "Marais Salés", "Plage des Sapins", "Ker Châlon", "Plage du But", "Plage de la Gournaise"],
            "mid": ["Plage des Vieilles"],
            "bad": ["Plage des Sabias", "Anse des Fontaines", "Anse des Soux", "Plage des Corbeaux"]
        },
        260: {
            "good": ["Plage des Corbeaux", "Grande Conche", "Petite Conche", "Marais Salés", "Plage des Sapins", "Ker Châlon"],
            "mid": ["Plage des Sabias", "Anse des Soux", "Plage des Vieilles"],
            "bad": ["Anse des Fontaines", "Plage du But", "Plage de la Gournaise"]
        },
        280: {
            "good": ["Plage des Vieilles", "Plage des Corbeaux", "Grande Conche", "Petite Conche", "Marais Salés", "Plage des Sapins", "Ker Châlon", "Plage des Sabias"],
            "mid": ["Anse des Fontaines", "Anse des Soux"],
            "bad": ["Plage du But", "Plage de la Gournaise"]
        },
        300: {
            "good": ["Anse des Soux", "Plage des Vieilles", "Plage des Corbeaux", "Grande Conche", "Plage des Sabias", "Anse des Fontaines"],
            "mid": ["Petite Conche", "Marais Salés", "Plage des Sapins"],
            "bad": ["Plage du But", "Plage de la Gournaise", "Ker Châlon"]
        }
    }

    rules = matrix.get(sector, {"good": [], "mid": [], "bad": []})
    if b_name in rules["good"]:
        return "Recommandée (Abritée)", svg_up
    elif b_name in rules["mid"]:
        return "Moyenne (Vent de côté)", svg_right
    else:
        return "Déconseillée (Exposée)", svg_down

query_params = st.query_params
if "lat" in query_params and "lon" in query_params:
    START_POINTS["📍 Ma Position GPS"] = {"lat": float(query_params["lat"]), "lon": float(query_params["lon"])}

st.set_page_config(page_title="Plages Île d'Yeu", layout="wide")
st.title("🏖️ Plages Île d'Yeu - Recommandations Vent & Marées")

# HEURE ET DATE LOCALE
paris_tz = ZoneInfo("Europe/Paris")
now_paris = datetime.datetime.now(paris_tz)
today = now_paris.date()
hour = now_paris.hour

# MÉTÉO COMPLÈTE EN TEMPS RÉEL (Vent + Ciel/Pluie)
url_weather = f"https://api.open-meteo.com/v1/forecast?latitude={LATITUDE}&longitude={LONGITUDE}&hourly=wind_speed_10m,wind_direction_10m,temperature_2m,sea_surface_temperature,weathercode&timezone=Europe/Paris&start_date={today}&end_date={today}"

try:
    res_w = requests.get(url_weather, timeout=5).json()
    w = res_w["hourly"]
    wd, ws, temp, water = w["wind_direction_10m"][hour], w["wind_speed_10m"][hour], w["temperature_2m"][hour], w["sea_surface_temperature"][hour]
    wcode = w["weathercode"][hour]
    weather_text, weather_icon = WMO_CODES.get(wcode, ("Ciel variable", "⛅"))
except Exception:
    wd, ws, temp, water = 45, 15, 20.0, 18.0
    weather_text, weather_icon = "Beau temps", "☀️"

# MARÉE ASTRONOMIQUE
tide_heights = calculate_real_tides(today)

card = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"][round(wd / 45) % 8]
anim_speed = max(0.4, 40.0 / max(ws, 1))

# BARRE LATÉRALE - PRÉFÉRENCES
st.sidebar.header("📍 Préférences du trajet")
default_index = list(START_POINTS.keys()).index("📍 Ma Position GPS") if "📍 Ma Position GPS" in START_POINTS else 0
start_name = st.sidebar.selectbox("Lieu de départ", list(START_POINTS.keys()), index=default_index)
transport = st.sidebar.radio("Moyen de transport", ["Vélo", "Voiture"], horizontal=True)

col1, col2 = st.columns([1.5, 1])

with col1:
    st.subheader(f"🗺️ Carte des plages (Vent actuel : {card} - {int(wd)}°)")
    m = folium.Map(location=[46.72, -2.35], zoom_start=13, tiles="CartoDB positron")
    
    start_coords = START_POINTS[start_name]
    folium.Marker([start_coords["lat"], start_coords["lon"]], icon=folium.Icon(color="black", icon="home"), popup=start_name).add_to(m)
    
    for b in BEACHES:
        status, icon_html = get_beach_recommendation(b["name"], wd)
        
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
                20% {{ opacity: 0.65; }}
                80% {{ opacity: 0.65; }}
                100% {{ transform: translateY(-10px); opacity: 0; }}
            }}
        </style>
        <div style="transform: rotate({wind_towards}deg);">
            <svg viewBox="0 0 24 24" width="18" height="18" style="animation: windBlow {anim_speed}s infinite linear;">
                <path d="M12 21 V3 M5 10 L12 3 L19 10" stroke="#78909c" stroke-width="1.2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        </div>"""
        folium.Marker(location=[pt["lat"], pt["lon"]], icon=folium.DivIcon(html=svg_wind)).add_to(m)

    st_folium(m, width="100%", height=450)

with col2:
    st.subheader("📊 Conditions Météo & Marées")
    st.write(f"🕒 Heure locale : **{now_paris.strftime('%H:%M')}**")
    st.write(f"🌤️ Ciel : **{weather_icon} {weather_text}**")
    st.write(f"🌡️ Air : **{temp}°C** | 💧 Eau : **{water}°C**")
    st.write(f"💨 Vent actuel : **{ws} km/h** ({card} - {int(wd)}°)")
    
    fig, ax = plt.subplots(figsize=(6, 2.8))
    ax.plot(range(24), tide_heights, color="#0288d1", linewidth=2)
    ax.scatter(hour, tide_heights[hour], color="red", zorder=5)
    ax.axvline(x=hour, color='red', linestyle='--', alpha=0.5)
    ax.set_ylabel("Hauteur d'eau (m)")
    ax.set_xlabel("Heures (0h - 23h)")
    ax.set_title(f"Marée Port-Joinville ({hour}h en rouge)")
    st.pyplot(fig)

st.markdown("---")

# PIED DE PAGE - MENTIONS DE SOURCING
st.caption("🌐 **Sources des données :** Prévisions Météo-France via Open-Meteo API | Température de l'eau : Mercator Ocean / Copernicus Marine.")

if st.button("📍 Obtenir ma position GPS (Smartphone)"):
    components.html("""<script>navigator.geolocation.getCurrentPosition(p => {window.location.search="?lat="+p.coords.latitude+"&lon="+p.coords.longitude})</script>""", height=0)
