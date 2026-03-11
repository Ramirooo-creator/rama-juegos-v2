import streamlit as st
import random
import json
from supabase import create_client

# 1. CONEXIÓN SUPABASE
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Rama Juegos", layout="wide")

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

# 4. INTERFAZ RAMA JUEGOS
st.title("⚽ RAMA JUEGOS: DRAFT LIVE")
usuario = st.sidebar.radio("¿Quién eres?", ["Ram", "Amigo"])
estado = obtener_estado()

if estado:
    club = estado['club_actual']
    st.subheader(f"Club asignado: {club}")
    
    # Buscador dinámico con tu lista
    nombres_jugadores = [j['nombre'] for j in DB.get(club, [])]
    seleccion = st.selectbox("Busca tu jugador:", [""] + nombres_jugadores)
    
    if seleccion:
        # Obtener posiciones del PDF
        info = next(j for j in DB[club] if j['nombre'] == seleccion)
        pos = st.radio(f"Posición para {seleccion}:", info['posiciones'])
        
        if st.button("Confirmar Fichaje"):
            campo_equipo = "equipo_ram" if usuario == "Ram" else "equipo_amigo"
            nuevo_equipo = estado[campo_equipo]
            nuevo_equipo[pos] = f"{seleccion} ({club})"
            
            # Algoritmo de nuevo club al azar
            nuevo_club = random.choice(list(DB.keys()))
            actualizar_nube({campo_equipo: nuevo_equipo, "club_actual": nuevo_club})
            st.rerun()

# 5. PIZARRA TÁCTICA VISUAL
st.divider()
c1, c2 = st.columns(2)
with c1:
    st.header("🟦 RAM")
    st.json(estado['equipo_ram'])
with c2:
    st.header("🟥 AMIGO")
    st.json(estado['equipo_amigo'])

if st.button("🔄 Sincronizar"):
    st.rerun()
