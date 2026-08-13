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

# --- LISTE COMPLÈTE DES PLAGES ---
BEACHES = [
    # Côte Sauvage (Sud)
    {"name": "Anse des Soux", "lat": 46.7011, "lon": -2.3165, "good": ["N", "NE", "E", "NO"], "bad": ["S", "SO", "O"]},
    {"name": "Plage des Vieilles", "lat": 46.7032, "lon": -2.3019, "good": ["N", "NE", "E", "NO"], "bad": ["S", "SO", "SE"]},
    {"name": "Plage de la Grande Conche", "lat": 46.6990, "lon": -2.3000, "good": ["N", "NO", "O"], "bad": ["S", "SE", "E"]},
    {"name": "Plage des Petites Conches", "lat": 46.6970, "lon": -2.2980, "good": ["N", "NO", "O"], "bad": ["S", "SE", "E"]},
    
    # Pointe Est
    {"name": "Plage des Corbeaux", "lat": 46.6961, "lon": -2.2939, "good": ["O", "NO", "SO"], "bad": ["E", "NE", "SE"]},
    {"name": "Plage des Marais Salés", "lat": 46.7110, "lon": -2.3150, "good": ["S", "SO", "O"], "bad": ["N", "NE", "E"]},
    
    # Côte Nord-Est
    {"name": "Plage de Ker Chalon", "lat": 46.7188, "lon": -2.3292, "good": ["S", "SO", "SE"], "bad": ["N", "NE", "E", "NO"]},
    {"name": "Plage des Sapins", "lat": 46.7224, "lon": -2.3400, "good": ["S", "SO", "SE"], "bad": ["N", "NE", "E", "NO"]},
    
    # Côte Nord / Pointe Nord-Ouest
    {"name": "Plage de la Gournaise", "lat": 46.7289, "lon": -2.3673, "good": ["S", "SE", "SO"], "bad": ["N", "NE", "NO"]},
    {"name": "Plage du But", "lat": 46.7210, "lon": -2.3880, "good": ["S", "SE", "E"], "bad": ["N", "NO", "O"]},
    
    # Côte Ouest
    {"name": "Plage de la Belle Maison", "lat": 46.7081, "lon": -2.3844, "good": ["E", "NE", "SE"], "bad": ["O", "SO", "NO"]},
    {"name": "Plage des Sabias", "lat": 46.7172, "lon": -2.3671, "good": ["E", "SE", "NE"], "bad": ["O", "NO", "SO"]},
    {"name": "Plage des Sables Roux", "lat": 46.7130, "lon": -2.3780, "good": ["E", "SE", "NE"], "bad": ["O", "NO", "SO"]}
]

# Quadrillage de flèches sur toute l'île
WIND_POINTS = [
    {"lat": 46.728, "lon": -2.351}, {"lat": 46.721, "lon": -2.388},
    {"lat": 46.695, "lon": -2.292}, {"lat": 46.710, "lon": -2.330},
    {"lat": 46.700, "lon": -2.319}, {"lat": 46.718, "lon": -2.360},
    {"lat": 46.705, "lon": -2.350}, {"lat": 46.710, "lon": -2.300},
    {"lat": 46.735, "lon": -2.330}, {"lat": 46.685, "lon": -2.330},
    {"lat": 46.715, "lon": -2.310}, {"lat": 46.705, "lon": -2.375},
]

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371
    dLat, dLon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dLat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon/2)**2
    return R * (2 * math.asin(math.sqrt(a)))

def calculate_times(distance_km):
    route_dist = distance_km * 1.3
    bike_time = int((route_dist / 14.0) * 60)
    car_time = int((route_dist / 30.0) * 60)
    return bike_time, car_time

@st.cache_data(ttl=3600)
def fetch_weather(date_str):
    w_url = f"https://api.open-meteo.com/v1/forecast?latitude={LATITUDE}&longitude={LONGITUDE}&hourly=temperature_2m,wind_speed_10m,wind_direction_10m&timezone=Europe/Paris&start_date={date_str}&end_date={date_str}"
    res = requests.get(w_url).json()
    if "error" in res:
        raise Exception(f"Erreur Météo : {res.get('reason')}")
    return res["hourly"]

def generate_mock_tide(date_str):
    base_time = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    times = [(base_time + datetime.timedelta(hours=i)).strftime("%Y-%m-%dT%H:00") for i in range(24)]
    heights = [3.0 + 2.0 * math.sin((i - 4) * math.pi / 6.2) for i in range(24)]
    return {"time": times, "sea_surface_height_above_sea_level": heights}

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

try:
    date_str = target_datetime.strftime("%Y-%m-%d")
    weather_data = fetch_weather(date_str)
    marine_data = generate_mock_tide(date_str)
    
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
        hours = [int(t.split("T")[1].split(":")[0]) for t in weather_data["time"]]
        ax.plot(hours, tide_heights, color="#0288d1", linewidth=2)
        ax.plot(hours[idx], current_height, 'ro', markersize=8)
        ax.set_title(f"Cycle de la Marée ({tide_category})", fontsize=10)
        ax.grid(True, linestyle="--", alpha=0.4)
        st.pyplot(fig)

    with col2:
        st.subheader("🗺️ Carte de recommandation instantanée")
        m = folium.Map(location=[LATITUDE, LONGITUDE], zoom_start=13, tiles="CartoDB positron")
        
        folium.Marker(
            location=[start_coords["lat"], start_coords["lon"]],
            icon=folium.Icon(color="black", icon="home"),
            popup="Votre point de départ"
        ).add_to(m)

        for beach in BEACHES:
            if card_short in beach["good"]:
                b_color, b_icon, status = "green", "thumbs-up", "Recommandée (Abritée)"
            elif card_short in beach["bad"]:
                b_color, b_icon, status = "red", "thumbs-down", "Déconseillée (Exposée)"
            else:
                b_color, b_icon, status = "orange", "info-sign", "Moyenne (Vent de travers)"

            dist_km = haversine_distance(start_coords["lat"], start_coords["lon"], beach["lat"], beach["lon"])
            t_bike, t_car = calculate_times(dist_km)

            popup_html = f"<b>{beach['name']}</b><br>État : <b>{status}</b><br><hr style='margin:5px 0;'>🚲 Vélo : ~{t_bike} min<br>🚗 Voiture : ~{t_car} min"
            
            folium.Marker(
                location=[beach["lat"], beach["lon"]],
                icon=folium.Icon(color=b_color, icon=b_icon),
                popup=folium.Popup(popup_html, max_width=250)
            ).add_to(m)

        wind_towards = (wind_deg + 180) % 360
        for pt in WIND_POINTS:
            svg = f"""
            <style>
                @keyframes windBlow {{
                    0% {{ transform: translateY(8px); opacity: 0; }}
                    40% {{ opacity: 1; }}
                    60% {{ opacity: 1; }}
                    100% {{ transform: translateY(-8px); opacity: 0; }}
                }}
            </style>
            <div style="transform: rotate({wind_towards}deg); width: 24px; height: 24px;">
                <svg viewBox="0 0 24 24" width="24" height="24" stroke="rgba(100, 100, 100, 0.7)" stroke-width="2.5" fill="none" style="animation: windBlow 1.5s infinite linear;">
                    <line x1="12" y1="19" x2="12" y2="5"></line>
                    <polyline points="7 10 12 5 17 10"></polyline>
                </svg>
            </div>
            """
            folium.Marker(location=[pt["lat"], pt["lon"]], icon=folium.DivIcon(html=svg)).add_to(m)

        st_folium(m, width=600, height=350)

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
            1. Plage idéale : Confirme la meilleure option parmi celles qui sont abritées du vent actuel (parmi la liste complète des plages de l'île).
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
