import streamlit as st
import random
import json
from supabase import create_client
from streamlit_autorefresh import st_autorefresh
import google.generativeai as genai # IMPORTANTE

# 1. CONFIGURACIÓN INICIAL (Supabase + Gemini)
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# Configurar IA
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-pro')

st.set_page_config(page_title="Rama Juegos - IA Edition", layout="wide")
st_autorefresh(interval=10000, key="datarefresh")

# 2. CARGAR DB
@st.cache_data
def cargar_db():
    with open('jugadores.json', 'r', encoding='utf-8') as f:
        return json.load(f)
DB = cargar_db()

def obtener_estado():
    res = supabase.table("partidas").select("*").eq("id", 1).execute()
    return res.data[0] if res.data else None

def actualizar_nube(datos):
    supabase.table("partidas").update(datos).eq("id", 1).execute()

# --- 3. ESTILOS ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .cancha-container {
        background-image: url('https://images.unsplash.com/photo-1556056504-51717364d019?q=80&w=2000');
        background-size: cover; border: 2px solid white; border-radius: 15px; padding: 15px;
    }
    .player-card {
        background: rgba(0, 0, 0, 0.85); border: 1px solid #D4AF37; border-radius: 8px;
        color: white; padding: 5px; text-align: center; min-height: 60px;
    }
    /* Estilo para el relato de la IA */
    .ia-relato {
        background-color: #1c2128; border-left: 5px solid #D4AF37;
        padding: 20px; border-radius: 10px; font-style: italic; color: #e6edf3;
    }
    </style>
    """, unsafe_allow_html=True)

# 4. LÓGICA DE JUEGO
st.markdown("<h1 style='text-align: center; color: #D4AF37;'>🏆 RAMA JUEGOS: IA EDITION</h1>", unsafe_allow_html=True)

col_t, col_r = st.columns([3, 1])
with col_r:
    if st.button("🔥 REINICIAR"):
        actualizar_nube({"equipo_ram": {}, "equipo_amigo": {}, "club_actual": "BARCELONA"})
        st.rerun()

usuario = st.radio("Manager:", ["Ram", "Amigo"], horizontal=True)
estado = obtener_estado()

MAPEO = {"GK": ["GK"], "LB": ["LB"], "RB": ["RB"], "CT": ["CT 1", "CT 2"], "MCD": ["MCD"], "MC": ["MC 1", "MC 2"], "LW": ["LW"], "RW": ["RW"], "ST": ["ST"]}

if estado:
    equipo_propio = estado['equipo_ram'] if usuario == "Ram" else estado['equipo_amigo']
    
    # BUSCADOR
    if len(equipo_propio) < 11:
        club = estado['club_actual']
        st.markdown(f"### 🚩 Club: {club}")
        nombres = [j['nombre'] for j in DB.get(club, [])]
        seleccion = st.selectbox("Elegir jugador:", [""] + nombres)
        
        if seleccion:
            info = next(j for j in DB[club] if j['nombre'] == seleccion)
            slots_libres = [s for p in info['posiciones'] if p in MAPEO for s in MAPEO[p] if s not in equipo_propio]
            if slots_libres:
                pos = st.radio("Ubicación:", slots_libres, horizontal=True)
                if st.button("CONFIRMAR"):
                    campo = "equipo_ram" if usuario == "Ram" else "equipo_amigo"
                    equipo_propio[pos] = seleccion
                    actualizar_nube({campo: equipo_propio, "club_actual": random.choice(list(DB.keys()))})
                    st.rerun()

    # --- 5. VISUALIZACIÓN ---
    st.divider()
    c1, c2 = st.columns(2)
    def dibujar_cancha(equipo, titulo):
        st.markdown(f"<h3 style='text-align:center;'>{titulo}</h3>", unsafe_allow_html=True)
        with st.container():
            st.markdown('<div class="cancha-container">', unsafe_allow_html=True)
            for fila in [["LW", "ST", "RW"], ["MC 1", "MCD", "MC 2"], ["LB", "CT 1", "CT 2", "RB"], ["GK"]]:
                cols = st.columns(len(fila))
                for i, p in enumerate(fila):
                    with cols[i]:
                        n = equipo.get(p, "—")
                        st.markdown(f"<div class='player-card'><div class='card-pos'>{p}</div><div class='card-name'>{n}</div></div>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    with c1: dibujar_cancha(estado['equipo_ram'], "🟦 RAM")
    with c2: dibujar_cancha(estado['equipo_amigo'], "🟥 AMIGO")

    # --- 6. FUNCIÓN DE IA (EL PLATO FUERTE) ---
    st.divider()
    if len(estado['equipo_ram']) == 11 and len(estado['equipo_amigo']) == 11:
        st.markdown("### 🤖 Análisis de Gemini Pro")
        if st.button("✨ SIMULAR PARTIDO CON IA"):
            with st.spinner("Gemini está analizando las tácticas..."):
                prompt = f"""
                Actúa como un relator de fútbol épico y analista técnico. 
                Se enfrentan dos equipos en la final de la 'Rama Cup':
                TEAM RAM: {list(estado['equipo_ram'].values())}
                TEAM AMIGO: {list(estado['equipo_amigo'].values())}
                
                Instrucciones:
                1. Da un resultado final (ej: 3-2).
                2. Narra 2 jugadas clave usando las habilidades reales de los jugadores mencionados.
                3. Nombra al jugador del partido.
                4. Sé creativo y emocionante. Usa lenguaje de fútbol argentino.
                """
                respuesta = model.generate_content(prompt)
                st.markdown(f"<div class='ia-relato'>{respuesta.text}</div>", unsafe_allow_html=True)
