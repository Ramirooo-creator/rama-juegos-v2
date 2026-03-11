import streamlit as st
import random
import json
from supabase import create_client

# 1. CONEXIÓN SUPABASE (Mantiene tus secretos)
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Rama Juegos - Draft Pro", layout="wide")

# 2. CARGAR DATA (Tu lista de 681 jugadores) 
@st.cache_data
def cargar_db():
    with open('jugadores.json', 'r', encoding='utf-8') as f:
        return json.load(f)

DB = cargar_db()

# 3. FUNCIONES DE RED
def obtener_estado():
    res = supabase.table("partidas").select("*").eq("id", 1).execute()
    return res.data[0] if res.data else None

def actualizar_nube(datos):
    supabase.table("partidas").update(datos).eq("id", 1).execute()

# --- ESTILOS CSS PARA LA CANCHA ---
st.markdown("""
    <style>
    .cancha-container {
        background-color: #1a472a;
        background-image: linear-gradient(rgba(255,255,255,.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.1) 1px, transparent 1px);
        background-size: 50px 50px;
        border: 4px solid white;
        border-radius: 20px;
        padding: 30px;
        text-align: center;
        margin-top: 20px;
    }
    .player-card {
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid #ffffff;
        border-radius: 8px;
        color: white;
        padding: 8px;
        margin: 5px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.5);
        min-height: 60px;
    }
    </style>
    """, unsafe_allow_html=True)

# 4. INTERFAZ RAMA JUEGOS
st.title("⚽ RAMA JUEGOS: DRAFT LIVE")
usuario = st.sidebar.radio("¿Quién eres?", ["Ram", "Amigo"])
estado = obtener_estado()

# 5. LÓGICA DE FORMACIÓN
formaciones_dict = {
    "4-3-3": ["GK", "LB", "CT", "CT", "RB", "MC", "MCD", "MO", "LW", "ST", "RW"],
    "4-4-2": ["GK", "LB", "CT", "CT", "RB", "LM", "MC", "MC", "RM", "ST", "ST"],
    "3-5-2": ["GK", "CT", "CT", "CT", "LWB", "RWB", "MC", "MCD", "MC", "ST", "ST"]
}

if 'formacion_partida' not in st.session_state:
    st.session_state.formacion_partida = st.sidebar.selectbox("Elige la formación del partido:", list(formaciones_dict.keys()))

posiciones_validas = formaciones_dict[st.session_state.formacion_partida]

if estado:
    club = estado['club_actual']
    st.subheader(f"Club asignado: {club}")
    
    # Buscador dinámico con tu lista 
    nombres_jugadores = [j['nombre'] for j in DB.get(club, [])]
    seleccion = st.selectbox("Busca tu jugador:", [""] + nombres_jugadores)
    
    if seleccion:
        info = next(j for j in DB[club] if j['nombre'] == seleccion)
        # Solo mostrar posiciones que existan en la formación elegida y no estén ocupadas
        pos_jugador_formacion = [p for p in info['posiciones'] if p in posiciones_validas]
        equipo_actual = estado['equipo_ram'] if usuario == "Ram" else estado['equipo_amigo']
        pos_libres = [p for p in pos_jugador_formacion if p not in equipo_actual]

        if not pos_libres:
            st.error("⚠️ Este jugador no encaja en las posiciones libres de tu formación.")
        else:
            pos = st.radio(f"Ubicar a {seleccion} en:", pos_libres)
            if st.button("Confirmar Fichaje"):
                campo_equipo = "equipo_ram" if usuario == "Ram" else "equipo_amigo"
                nuevo_equipo = estado[campo_equipo]
                nuevo_equipo[pos] = f"{seleccion}"
                
                nuevo_club = random.choice(list(DB.keys()))
                actualizar_nube({campo_equipo: nuevo_equipo, "club_actual": nuevo_club})
                st.rerun()

# 6. RENDERIZADO DE LA CANCHA
st.divider()
st.write(f"### 🏟️ Pizarra Táctica: {st.session_state.formacion_partida}")

def dibujar_linea(pos_linea, equipo):
    # Solo mostramos las posiciones que pertenecen a la formación actual
    pos_activas = [p for p in pos_linea if p in posiciones_validas]
    if pos_activas:
        cols = st.columns(len(pos_activas))
        for i, p in enumerate(pos_activas):
            with cols[i]:
                jugador = equipo.get(p, "—")
                st.markdown(f"<div class='player-card'><small>{p}</small><br><b>{jugador}</b></div>", unsafe_allow_html=True)

equipo_visual = estado['equipo_ram'] if usuario == "Ram" else estado['equipo_amigo']

with st.container():
    st.markdown('<div class="cancha-container">', unsafe_allow_html=True)
    dibujar_linea(["LW", "ST", "RW", "ST"], equipo_visual) # Ataque
    dibujar_linea(["MO", "MC", "MCD", "LM", "RM", "LWB", "RWB"], equipo_visual) # Medio
    dibujar_linea(["LB", "CT", "RB"], equipo_visual) # Defensa
    dibujar_linea(["GK"], equipo_visual) # Portero
    st.markdown('</div>', unsafe_allow_html=True)

if st.button("🔄 Sincronizar"):
    st.rerun()
