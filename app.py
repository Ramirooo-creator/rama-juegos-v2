import streamlit as st
import random
import json
from supabase import create_client
from streamlit_autorefresh import st_autorefresh

# 1. CONEXIÓN SUPABASE
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# Configuración y Auto-Refresh (Cada 10 seg)
st.set_page_config(page_title="Rama Juegos - Duelo Live", layout="wide")
st_autorefresh(interval=10000, key="datarefresh")

# 2. CARGAR BASE DE DATOS 
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

# --- 3. ESTILOS VISUALES MEJORADOS ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .cancha-container {
        background-image: url('https://images.unsplash.com/photo-1556056504-51717364d019?q=80&w=2000');
        background-size: cover; border: 2px solid white; border-radius: 15px; padding: 15px;
    }
    .player-card {
        background: rgba(0, 0, 0, 0.75); border: 1px solid #D4AF37; border-radius: 5px;
        color: white; padding: 5px; text-align: center; min-height: 55px; margin-bottom: 5px;
    }
    .card-name { font-size: 11px; font-weight: bold; overflow: hidden; }
    </style>
    """, unsafe_allow_html=True)

# 4. LÓGICA DE JUEGO
st.markdown("<h1 style='text-align: center; color: #D4AF37;'>🏆 RAMA JUEGOS: EL DUELO</h1>", unsafe_allow_html=True)
usuario = st.sidebar.radio(" MANAGER ACTUAL:", ["Ram", "Amigo"])
estado = obtener_estado()

MAPEO = {
    "GK": ["GK"], "LB": ["LB"], "RB": ["RB"], "CT": ["CT 1", "CT 2"],
    "MCD": ["MCD"], "MC": ["MC 1", "MC 2"], "LW": ["LW"], "RW": ["RW"], "ST": ["ST"]
}

if estado:
    equipo_propio = estado['equipo_ram'] if usuario == "Ram" else estado['equipo_amigo']
    
    # CONTROL DE FINALIZACIÓN
    if len(equipo_propio) >= 11:
        st.success(f"✅ ¡{usuario}, tu 11 ideal está completo!")
        if st.sidebar.button("🔄 REINICIAR PARTIDA"):
            actualizar_nube({"equipo_ram": {}, "equipo_amigo": {}, "club_actual": "BARCELONA"})
            st.rerun()
    else:
        # SECCIÓN DE FICHAR 
        club = estado['club_actual']
        st.sidebar.info(f"Fichando del: {club}")
        nombres = [j['nombre'] for j in DB.get(club, [])]
        seleccion = st.sidebar.selectbox("Busca jugador:", [""] + nombres)
        
        if seleccion:
            info = next(j for j in DB[club] if j['nombre'] == seleccion)
            slots_libres = [s for p in info['posiciones'] if p in MAPEO for s in MAPEO[p] if s not in equipo_propio]
            
            if slots_libres:
                pos = st.sidebar.radio("Posición:", slots_libres, horizontal=True)
                if st.sidebar.button("CONFIRMAR FICHAJE"):
                    campo = "equipo_ram" if usuario == "Ram" else "equipo_amigo"
                    equipo_propio[pos] = seleccion
                    nuevo_club = random.choice(list(DB.keys()))
                    actualizar_nube({campo: equipo_propio, "club_actual": nuevo_club})
                    st.rerun()
            else:
                st.sidebar.error("Sin lugar en tu formación.")

    # --- 5. VISUALIZACIÓN DE DUELO (DOS CANCHAS) ---
    col_izq, col_der = st.columns(2)

    def dibujar_cancha(equipo, titulo):
        st.markdown(f"<h4 style='text-align:center;'>{titulo}</h4>", unsafe_allow_html=True)
        with st.container():
            st.markdown('<div class="cancha-container">', unsafe_allow_html=True)
            filas = [["LW", "ST", "RW"], ["MC 1", "MCD", "MC 2"], ["LB", "CT 1", "CT 2", "RB"], ["GK"]]
            for fila in filas:
                cols = st.columns(len(fila))
                for i, p in enumerate(fila):
                    with cols[i]:
                        nombre = equipo.get(p, "—")
                        st.markdown(f"<div class='player-card'><small>{p}</small><br><div class='card-name'>{nombre}</div></div>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    with col_izq: dibujar_cancha(estado['equipo_ram'], "🟦 TEAM RAM")
    with col_der: dibujar_cancha(estado['equipo_amigo'], "🟥 TEAM AMIGO")
