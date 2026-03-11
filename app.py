import streamlit as st
import random
import json
from supabase import create_client
from streamlit_autorefresh import st_autorefresh
import google.generativeai as genai

# 1. CONFIGURACIÓN DE CONEXIONES
# Supabase
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# Gemini (IA) - Configuración para evitar errores 404
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# Intentamos cargar el modelo Flash; si falla, usamos el Pro estándar
try:
    model = genai.GenerativeModel('gemini-1.5-flash')
except:
    model = genai.GenerativeModel('gemini-pro')

# Configuración de página y Auto-refresco (10 seg)
st.set_page_config(page_title="Rama Juegos - IA Edition", layout="wide")
st_autorefresh(interval=10000, key="datarefresh")

# 2. CARGAR BASE DE DATOS DE JUGADORES
@st.cache_data
def cargar_db():
    try:
        with open('jugadores.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("No se encontró el archivo jugadores.json")
        return {}

DB = cargar_db()

def obtener_estado():
    res = supabase.table("partidas").select("*").eq("id", 1).execute()
    return res.data[0] if res.data else None

def actualizar_nube(datos):
    supabase.table("partidas").update(datos).eq("id", 1).execute()

# --- 3. DISEÑO VISUAL (CSS) ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .cancha-container {
        background-image: url('https://images.unsplash.com/photo-1556056504-51717364d019?q=80&w=2000');
        background-size: cover; border: 3px solid white; border-radius: 15px; padding: 15px;
        box-shadow: 0 0 25px rgba(0,0,0,0.6);
    }
    .player-card {
        background: rgba(0, 0, 0, 0.85); border: 1px solid #D4AF37; border-radius: 8px;
        color: white; padding: 8px; text-align: center; min-height: 70px; margin-bottom: 5px;
    }
    .card-name { font-size: 13px; font-weight: bold; }
    .card-pos { color: #D4AF37; font-size: 10px; font-weight: bold; }
    .ia-relato {
        background-color: #1c2128; border-left: 5px solid #D4AF37;
        padding: 20px; border-radius: 10px; font-style: italic; color: #e6edf3;
        line-height: 1.6; font-size: 1.1rem;
    }
    /* Estilo botón reinicio */
    div.stButton > button:first-child { background-color: #d32f2f; color: white; border: none; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 4. ENCABEZADO Y CONTROL DE PARTIDA
col_t, col_r = st.columns([3, 1])
with col_t:
    st.markdown("<h1 style='color: #D4AF37;'>🏆 RAMA JUEGOS: IA EDITION</h1>", unsafe_allow_html=True)
with col_r:
    if st.button("🔥 REINICIAR TODO"):
        actualizar_nube({"equipo_ram": {}, "equipo_amigo": {}, "club_actual": "BARCELONA"})
        st.success("¡Cancha limpia!")
        st.rerun()

usuario = st.radio("¿Quién maneja el equipo?", ["Ram", "Amigo"], horizontal=True)
estado = obtener_estado()

# MAPEO 4-3-3 (Ram, recuerda que usamos CT 1, CT 2 y MC 1, MC 2)
MAPEO = {
    "GK": ["GK"], "LB": ["LB"], "RB": ["RB"], "CT": ["CT 1", "CT 2"],
    "MCD": ["MCD"], "MC": ["MC 1", "MC 2"], "LW": ["LW"], "RW": ["RW"], "ST": ["ST"]
}

# 5. LÓGICA DE SELECCIÓN DE JUGADORES
if estado:
    equipo_propio = estado['equipo_ram'] if usuario == "Ram" else estado['equipo_amigo']
    
    st.divider()
    
    if len(equipo_propio) < 11:
        club = estado['club_actual']
        st.markdown(f"### 🚩 Club Actual: **{club}**")
        nombres_jugadores = [j['nombre'] for j in DB.get(club, [])]
        seleccion = st.selectbox("Busca tu jugador ideal de la lista:", [""] + nombres_jugadores)
        
        if seleccion:
            info = next(j for j in DB[club] if j['nombre'] == seleccion)
            # Filtrar slots libres que coincidan con las posiciones del PDF
            slots_libres = [s for p in info['posiciones'] if p in MAPEO for s in MAPEO[p] if s not in equipo_propio]
            
            if not slots_libres:
                st.error(f"⚠️ {seleccion} no cabe en tu formación táctica actual.")
            else:
                pos_final = st.radio(f"¿Dónde quieres poner a {seleccion}?", slots_libres, horizontal=True)
                if st.button(f"CONFIRMAR FICHAJE"):
                    campo_bd = "equipo_ram" if usuario == "Ram" else "equipo_amigo"
                    equipo_propio[pos_final] = seleccion
                    
                    # Salto aleatorio a otro club de la DB
                    nuevo_club = random.choice(list(DB.keys()))
                    actualizar_nube({campo_bd: equipo_propio, "club_actual": nuevo_club})
                    st.balloons()
                    st.rerun()
    else:
        st.success(f"✅ ¡{usuario}, has completado tu 11! Espera el análisis de la IA.")

    # --- 6. VISUALIZACIÓN DE LAS DOS CANCHAS ---
    st.divider()
    col_izq, col_der = st.columns(2)

    def dibujar_cancha(equipo, titulo, color_borde):
        st.markdown(f"<h3 style='text-align:center;'>{titulo}</h3>", unsafe_allow_html=True)
        with st.container():
            st.markdown(f'<div class="cancha-container" style="border-color: {color_borde};">', unsafe_allow_html=True)
            # Ordenamos las filas para que se vea el 4-3-3 real
            filas = [["LW", "ST", "RW"], ["MC 1", "MCD", "MC 2"], ["LB", "CT 1", "CT 2", "RB"], ["GK"]]
            for fila in filas:
                cols = st.columns(len(fila))
                for i, p in enumerate(fila):
                    with cols[i]:
                        nombre = equipo.get(p, "—")
                        st.markdown(f"<div class='player-card'><div class='card-pos'>{p}</div><div class='card-name'>{nombre}</div></div>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    with col_izq: dibujar_cancha(estado['equipo_ram'], "🟦 TEAM RAM", "#3b82f6")
    with col_der: dibujar_cancha(estado['equipo_amigo'], "🟥 TEAM AMIGO", "#ef4444")

    # --- 7. EL GRAN SIMULADOR CON IA (Relato épico) ---
    st.divider()
    if len(estado['equipo_ram']) == 11 and len(estado['equipo_amigo']) == 11:
        st.markdown("### 🤖 Sala de Prensa: Análisis de Gemini Pro")
        if st.button("✨ SIMULAR PARTIDO CON IA"):
            with st.spinner("Analizando plantillas y simulando resultado..."):
                try:
                    # Prompt optimizado para IA
                    prompt_ia = f"""
                    Narra una final de fútbol épica entre:
                    TEAM RAM: {list(estado['equipo_ram'].values())}
                    TEAM AMIGO: {list(estado['equipo_amigo'].values())}
                    
                    Instrucciones:
                    1. Resultado final (ej: 3-2).
                    2. Describe 2 jugadas clave (una de cada equipo).
                    3. Menciona la figura del partido.
                    4. Usa lenguaje futbolero argentino muy apasionado.
                    """
                    
                    response = model.generate_content(prompt_ia)
                    st.markdown(f"<div class='ia-relato'>{response.text}</div>", unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error de conexión con la IA: {e}")
                    st.info("Revisa si tu API Key de AI Studio sigue activa.")
