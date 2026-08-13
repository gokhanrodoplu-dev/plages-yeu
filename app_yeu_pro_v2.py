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
LATITUDE = 46.7236
LONGITUDE = -2.3503

START_POINTS = {
    "Port-Joinville": {"lat": 46.7280, "lon": -2.3510},
    "Saint-Sauveur": {"lat": 46.7110, "lon": -2.3300},
    "Port de la Meule": {"lat": 46.6970, "lon": -2.3190}
}

BEACHES = [
    {"name": "Anse des Soux (Côte Sauvage)", "lat": 46.7080, "lon": -2.3680, "good": ["N", "NE", "E"], "bad": ["S", "SO", "O"]},
    {"name": "Plage des Vieilles (Côte Sauvage)", "lat": 46.6990, "lon": -2.3450, "good": ["N", "NE", "E", "NO"], "bad": ["S", "SO", "SE"]},
    {"name": "Plage de Ker Chalon (Nord-Est)", "lat": 46.7210, "lon": -2.3300, "good": ["S", "SO", "SE"], "bad": ["N", "NE", "E", "NO"]},
    {"name": "Plage des Sabias (Nord-Ouest)", "lat": 46.7220, "lon": -2.3780, "good": ["S", "SE", "E"], "bad": ["N", "NO", "O"]},
    {"name": "Plage des Corbeaux (Est)", "lat": 46.6950, "lon": -2.2920, "good": ["O", "NO", "SO"], "bad": ["E", "NE", "SE"]}
]

WIND_POINTS = [
    {"name": "Port-Joinville", "lat": 46.7280, "lon": -2.3510, "factor": 1.0},
    {"name": "Pointe du But", "lat": 46.7210, "lon": -2.3880, "factor": 1.2}, 
    {"name": "Pointe des Corbeaux", "lat": 46.6950, "lon": -2.2920, "factor": 1.1},
]

# --- FONCTIONS UTILITAIRES ---
def haversine_distance(lat1, lon1, lat2, lon2):
    """Calcule la distance à vol d'oiseau entre deux points en km"""
    R = 6371
    dLat, dLon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dLat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon/2)**2
    return R * (2 * math.asin(math.sqrt(a)))

def calculate_times(distance_km):
    """Retourne le temps estimé (vélo musculaire et voiture) incluant un facteur de détour de route (x1.3)"""
    route_dist = distance_km * 1.3
    bike_time = int((route_dist / 14.0) * 60) # Allure vélo musculaire : 14 km/h
    car_time = int((route_dist / 30.0) * 60)  # Allure voiture sur l'île : 30 km/h
    return bike_time, car_time

@st.cache_data(ttl=3600)
def fetch_weather_and_marine(date_str):
    w_url = f"https://api.open-meteo.com/v1/forecast?latitude={LATITUDE}&longitude={LONGITUDE}&hourly=temperature_2m,wind_speed_10m,wind_direction_10m&timezone=Europe/Paris&start_date={date_str}&end_date={date_str}"
    res_w = requests.get(w_url).json()["hourly"]
    m_url = f"https://marine-api.open-meteo.com/v1/marine?latitude={LATITUDE}&longitude={LONGITUDE}&hourly=sea_surface_height_above_sea_level&timezone=Europe/Paris&start_date={date_str}&end_date={date_str}"
    res_m = requests.get(m_url).json()["hourly"]
    return res_w, res_m

# --- CONFIGURATION INTERFACE ---
st.set_page_config(page_title="Plages Île d'Yeu - PRO", page_icon="🏝️", layout="wide")
st.title("🏝️ Plages Idéales - Île d'Yeu (Agent Pro)")

st.sidebar.header("⚙️ Configuration")
start_point_name = st.sidebar.selectbox("📍 Point de départ", list(START_POINTS.keys()))
selected_date = st.sidebar.date_input("📅 Date", datetime.date.today())
selected_time = st.sidebar.time_input("⏰ Heure de sortie", datetime.time(15, 0))

activity = st.sidebar.selectbox("🏖️ Activité prévue", [
    "Plage en famille (avec Côme, Paul et Julia)",
    "Course à pied / Trail côtier",
    "Balade à vélo vers la plage",
    "Farniente au calme"
])

target_datetime = datetime.datetime.combine(selected_date, selected_time)
start_coords = START_POINTS[start_point_name]

# --- TRAITEMENT DES DONNÉES ---
try:
    date_str = target_datetime.strftime("%Y-%m-%d")
    weather_data, marine_data = fetch_weather_and_marine(date_str)
    
    target_hour_str = target_datetime.strftime("%Y-%m-%dT%H:00")
    idx = weather_data["time"].index(target_hour_str) if target_hour_str in weather_data["time"] else 12
    
    temp = weather_data["temperature_2m"][idx]
    wind_speed = weather_data["wind_speed_10m"][idx]
    wind_deg = weather_data["wind_direction_10m"][idx]
    
    cardinals = ["Nord (N)", "Nord-Est (NE)", "Est (E)", "Sud-Est (SE)", "Sud (S)", "Sud-Ouest (SO)", "Ouest (O)", "Nord-Ouest (NO)"]
    cardinals_short = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]
    
    cardinal = cardinals[round(wind_deg / 45) % 8]
    card_short = cardinals_short[round(wind_deg / 45) % 8]
    
    tide_heights = marine_data["sea_surface_height_above_sea_level"]
    current_height = tide_heights[idx]
    next_height = tide_heights[idx + 1] if idx + 1 < len(tide_heights) else current_height
    tide_state = "montante 📈" if next_height > current_height else "descendante 📉"
    
    amp = max(tide_heights) - min(tide_heights)
    tide_category = "⚡ Grande Marée" if amp > 4.2 else ("🌊 Vive-eau" if amp > 3.2 else "💧 Morte-eau")

    col1, col2 = st.columns([1, 1.2])

    with col1:
        st.subheader("📊 Conditions actuelles")
        st.write(f"🌡️ **Température :** {temp}°C | 💨 **Vent :** {wind_speed} km/h ({cardinal})")
        st.write(f"🌊 **Marée :** {current_height:.2f} m ({tide_state}) | {tide_category}")

        fig, ax = plt.subplots(figsize=(6, 2))
        hours = [int(t.split("T")[1].split(":")[0]) for t in marine_data["time"]]
        ax.plot(hours, tide_heights, color="#0288d1", linewidth=2)
        ax.plot(hours[idx], current_height, 'ro', markersize=8)
        ax.set_title(f"Cycle de la Marée ({tide_category})", fontsize=10)
        ax.grid(True, linestyle="--", alpha=0.4)
        st.pyplot(fig)

    with col2:
        st.subheader("🗺️ Carte de recommandation instantanée")
        m = folium.Map(location=[LATITUDE, LONGITUDE], zoom_start=13, tiles="CartoDB positron")
        
        # 1. Marqueur du point de départ
        folium.Marker(
            location=[start_coords["lat"], start_coords["lon"]],
            icon=folium.Icon(color="black", icon="home"),
            popup="Votre point de départ"
        ).add_to(m)

        # 2. Indicateurs de plages (Couleurs + Temps de trajet)
        for beach in BEACHES:
            # Algorithme de coloration
            if card_short in beach["good"]:
                b_color, b_icon, status = "green", "thumbs-up", "Recommandée (Abritée)"
            elif card_short in beach["bad"]:
                b_color, b_icon, status = "red", "thumbs-down", "Déconseillée (Exposée)"
            else:
                b_color, b_icon, status = "orange", "info-sign", "Moyenne (Vent de travers)"

            # Temps de trajet
            dist_km = haversine_distance(start_coords["lat"], start_coords["lon"], beach["lat"], beach["lon"])
            t_bike, t_car = calculate_times(dist_km)

            popup_html = f"""
            <b>{beach['name']}</b><br>
            État vis-à-vis du vent : <b>{status}</b><br><hr style="margin:5px 0;">
            🚲 Vélo : ~{t_bike} min<br>
            🚗 Voiture : ~{t_car} min
            """
            
            folium.Marker(
                location=[beach["lat"], beach["lon"]],
                icon=folium.Icon(color=b_color, icon=b_icon),
                popup=folium.Popup(popup_html, max_width=250)
            ).add_to(m)

        # 3. Flèches vectorielles de vent
        wind_towards = (wind_deg + 180) % 360
        for pt in WIND_POINTS:
            l_speed = round(wind_speed * pt["factor"], 1)
            svg = f"""<div style="transform: rotate({wind_towards}deg); width: 20px;"><svg viewBox="0 0 24 24" width="20" height="20" stroke="gray" stroke-width="2" fill="none"><line x1="12" y1="19" x2="12" y2="5"></line><polyline points="5 12 12 5 19 12"></polyline></svg></div>"""
            folium.Marker(location=[pt["lat"], pt["lon"]], icon=folium.DivIcon(html=svg)).add_to(m)

        st_folium(m, width=600, height=350)

    # --- ANALYSE GEMINI ---
    st.markdown("---")
    st.subheader("🤖 Diagnostic Gemini Pro")

    if st.button("🔍 Lancer l'analyse logistique"):
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            st.error("Clé GEMINI_API_KEY manquante.")
        else:
            client = genai.Client(api_key=api_key)
            prompt = f"""
            Tu es un expert logistique de l'Île d'Yeu.
            
            Contexte actuel :
            - Départ : {start_point_name}
            - Activité : {activity}
            - Météo : {temp}°C, Vent {wind_speed} km/h (Secteur {cardinal}, {wind_deg}°)
            - Marée : {current_height:.2f} m ({tide_state}). Régime : {tide_category}.
            
            Mission : Rédige une analyse concise et de haut niveau en 3 points :
            1. Plage idéale : Confirme la meilleure option parmi celles qui sont abritées du vent actuel, en tenant compte du niveau d'eau.
            2. Trajet depuis {start_point_name} : Un bref commentaire sur l'accessibilité ou le vent de face au retour en fonction de l'activité choisie.
            3. Sécurité / Ambiance : Un conseil spécifique lié à l'activité sélectionnée.
            """
            
            with st.spinner("Analyse approfondie en cours..."):
                response = client.models.generate_content(
                    model="gemini-1.5-pro",
                    contents=prompt
                )
                st.info(response.text)

except Exception as e:
    st.error(f"Erreur : {e}")
