import streamlit as st
import random
import json
from supabase import create_client

# 1. CONEXIÓN SUPABASE (Mantenemos tus secrets)
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# Configuración de página con tema oscuro
st.set_page_config(page_title="Rama Juegos - Draft Pro", layout="wide", initial_sidebar_state="collapsed")

# 2. CARGAR DATA (Tu lista de 681 jugadores)
@st.cache_data
def cargar_db():
    with open('jugadores.json', 'r', encoding='utf-8') as f:
        return json.load(f)

DB = cargar_db()

# 3. FUNCIONES DE RED
def obtener_estado():
    try:
        res = supabase.table("partidas").select("*").eq("id", 1).execute()
        return res.data[0] if res.data else None
    except:
        st.error("Error de conexión con Supabase. Verifica tus Secrets.")
        return None

def actualizar_nube(datos):
    supabase.table("partidas").update(datos).eq("id", 1).execute()

# --- 4. NUEVOS ESTILOS CSS PROFESIONALES ---
st.markdown("""
    <style>
    /* Fondo general de la app */
    .stApp {
        background-color: #101010;
        color: white;
    }
    
    /* Contenedor principal de la cancha */
    .cancha-container {
        background-image: url('https://images.unsplash.com/photo-1556056504-51717364d019?q=80&w=2000'); /* Imagen de césped real */
        background-size: cover;
        background-position: center;
        border: 5px solid #ffffff;
        border-radius: 25px;
        padding: 40px;
        position: relative;
        box-shadow: 0 0 30px rgba(0,255,0,0.2);
        margin-top: 20px;
        overflow: hidden;
    }
    
    /* Superposición de líneas de cal blancas */
    .cancha-lines {
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        background-image: 
            linear-gradient(white 2px, transparent 2px), /* Línea central */
            radial-gradient(circle at center, transparent 40%, white 41%, white 43%, transparent 44%), /* Círculo central */
            linear-gradient(90deg, white 2px, transparent 2px),
            linear-gradient(transparent 90%, white 91%, white 93%, transparent 94%);
        background-size: 100% 50%, 200px 200px, 50% 100%, 100% 100%;
        background-position: center;
        background-repeat: no-repeat;
        opacity: 0.5;
        z-index: 1;
    }

    /* Tarjeta de Jugador ESTILO CARTA FUT */
    .player-card {
        background: rgba(0, 0, 0, 0.7); /* Fondo oscuro semi-transparente */
        border-radius: 12px;
        padding: 15px;
        text-align: center;
        position: relative;
        z-index: 2; /* Por encima de las líneas */
        transition: transform 0.2s;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
        min-height: 90px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    
    /* Efecto hover */
    .player-card:hover {
        transform: scale(1.05);
        box-shadow: 0 0 20px rgba(255,255,255,0.5);
    }
    
    /* Borde normal (Cromo/Plata) */
    .border-normal {
        border: 2px solid #C0C0C0;
    }
    
    /* Borde BALÓN DE ORO (Dorado) */
    .border-gold {
        border: 3px solid #D4AF37;
        box-shadow: 0 0 15px rgba(212, 175, 55, 0.7);
    }
    
    /* Estilos de texto dentro de la carta */
    .card-pos {
        color: #aaaaaa;
        font-size: 12px;
        font-weight: bold;
        text-transform: uppercase;
        margin-bottom: 5px;
    }
    .card-name {
        color: #ffffff;
        font-size: 16px;
        font-weight: 800; /* Extra negrita */
        text-shadow: 1px 1px 2px rgba(0,0,0,0.8);
    }
    .card-empty {
        color: #555555;
        font-style: italic;
    }
    
    /* Títulos de las líneas tácticas */
    .linea-titulo {
        color: rgba(255,255,255,0.6);
        text-align: center;
        font-weight: bold;
        margin-top: 20px;
        margin-bottom: 5px;
        text-transform: uppercase;
        letter-spacing: 2px;
        z-index: 2;
        position: relative;
    }
    
    /* Botones personalizados */
    .stButton>button {
        background-color: #2e7d32;
        color: white;
        border-radius: 10px;
        border: none;
        padding: 10px 20px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #1a472a;
        color: #D4AF37;
    }
    </style>
    """, unsafe_allow_html=True)

# 5. INTERFAZ DE USUARIO
# Centramos el título y le damos color dorado marketing
st.markdown("<h1 style='text-align: center; color: #D4AF37; text-shadow: 0 0 10px rgba(212,175,55,0.5);'>RAMA JUEGOS: DRAFT LIVE 🏆</h1>", unsafe_allow_html=True)
st.divider()

# Barra lateral más limpia
st.sidebar.markdown("<h2 style='color: #D4AF37;'>Panel de Manager</h2>", unsafe_allow_html=True)
usuario = st.sidebar.radio("¿Quién eres?", ["Ram", "Amigo"])
estado = obtener_estado()

# MAPEO DE POSICIONES 4-3-3 (Igual que antes para lógica)
MAPEO_POSICIONES = {
    "GK": ["GK"], "LB": ["LB"], "RB": ["RB"], "CT": ["CT 1", "CT 2"],
    "MCD": ["MCD"], "MC": ["MC 1", "MC 2"], "LW": ["LW"], "RW": ["RW"], "ST": ["ST"]
}

if estado:
    # --- SECCIÓN DE FICHAR ---
    with st.expander(f"📥 Fichar para el Club Asignado: {estado['club_actual']}", expanded=True):
        club = estado['club_actual']
        nombres_jugadores = [j['nombre'] for j in DB.get(club, [])]
        seleccion = st.selectbox("Busca tu jugador de este club:", [""] + nombres_jugadores)
        
        if seleccion:
            info = next(j for j in DB[club] if j['nombre'] == seleccion)
            equipo_actual = estado['equipo_ram'] if usuario == "Ram" else estado['equipo_amigo']
            
            # Lógica de validación
            slots_disponibles = []
            for p_pdf in info['posiciones']:
                if p_pdf in MAPEO_POSICIONES:
                    for slot in MAPEO_POSICIONES[p_pdf]:
                        if slot not in equipo_actual:
                            slots_disponibles.append(slot)
            
            if not slots_disponibles:
                st.error(f"⚠️ {seleccion} no encaja en las posiciones libres de tu 4-3-3.")
            else:
                col_radio, col_btn = st.columns([3, 1])
                with col_radio:
                    pos_final = st.radio(f"¿Dónde ubicas a {seleccion}?", slots_disponibles, horizontal=True)
                with col_btn:
                    st.write("") # Espaciador
                    if st.button("CONFIRMAR FICHAJE", use_container_width=True):
                        campo_equipo = "equipo_ram" if usuario == "Ram" else "equipo_amigo"
                        nuevo_equipo = equipo_actual
                        nuevo_equipo[pos_final] = seleccion
                        
                        nuevo_club = random.choice(list(DB.keys()))
                        actualizar_nube({campo_equipo: nuevo_equipo, "club_actual": nuevo_club})
                        st.balloons() # ¡Festejo!
                        st.rerun()

    # --- 6. RENDERIZADO VISUAL DE LA CANCHA 4-3-3 ---
    st.write(f"### 🏟️ Pizarra Táctica de {usuario}")
    
    # Función para dibujar una carta de jugador con estilo dinámico
    def render_carta(slot, equipo):
        jugador = equipo.get(slot)
        
        # Lógica de Marketing: Si es Balón de Oro, carta dorada
        clase_borde = "border-normal"
        if jugador:
            # Buscamos si el jugador está en la categoría 'Balones de Oro' en el JSON
            # Nota: Esto requiere que tu JSON tenga una estructura que lo permita fácilmente,
            # asumiremos que si el club actual es 'BALONES DE ORO' o si el jugador está ahí, es dorado.
            es_gold = False
            for bd_jugador in DB.get("BALONES DE ORO", []):
                if bd_jugador['nombre'] == jugador:
                    es_gold = True
                    break
            
            if es_gold:
                clase_borde = "border-gold"
            
            # HTML de la carta con jugador
            html_carta = f"""
                <div class='player-card {clase_borde}'>
                    <div class='card-pos'>{slot}</div>
                    <div class='card-name'>{jugador}</div>
                </div>
            """
        else:
            # HTML de la carta vacía
            html_carta = f"""
                <div class='player-card {clase_borde}'>
                    <div class='card-pos'>{slot}</div>
                    <div class='card-name card-empty'>—</div>
                </div>
            """
        st.markdown(html_carta, unsafe_allow_html=True)

    equipo_visual = estado['equipo_ram'] if usuario == "Ram" else estado['equipo_amigo']

    # EL CAMPO DE JUEGO (Contenedor HTML)
    with st.container():
        st.markdown('<div class="cancha-container"><div class="cancha-lines"></div>', unsafe_allow_html=True)
        
        # --- ATAQUE ---
        st.markdown('<div class="linea-titulo">Delanteros</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1: render_carta("LW", equipo_visual)
        with c2: render_carta("ST", equipo_visual)
        with c3: render_carta("RW", equipo_visual)
        
        # --- MEDIOCAMPO --- (4-3-3: 1 MCD atrasado, 2 MC adelantados)
        st.markdown('<div class="linea-titulo">Mediocampo</div>', unsafe_allow_html=True)
        # Usamos columnas vacías laterales para centrar el MCD
        c_v1, c_mc1, c_mcd, c_mc2, c_v2 = st.columns([1, 2, 2, 2, 1])
        with c_mc1: render_carta("MC 1", equipo_visual)
        with c_mcd: 
            st.write("") # Espaciador para atrasarlo visualmente
            render_carta("MCD", equipo_visual)
        with c_mc2: render_carta("MC 2", equipo_visual)
        
        # --- DEFENSA ---
        st.markdown('<div class="linea-titulo">Defensa</div>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        with c1: render_carta("LB", equipo_visual)
        with c2: render_carta("CT 1", equipo_visual)
        with c3: render_carta("CT 2", equipo_visual)
        with c4: render_carta("RB", equipo_visual)
        
        # --- PORTERO ---
        st.markdown('<div class="linea-titulo">Arquero</div>', unsafe_allow_html=True)
        _, c_gk, _ = st.columns([1, 1, 1])
        with c_gk: render_carta("GK", equipo_visual)
        
        st.markdown('</div>', unsafe_allow_html=True) # Cierre de cancha-container

    st.divider()
    col_v, col_sync = st.columns([4, 1])
    with col_sync:
        if st.button("🔄 Sincronizar Cancha", use_container_width=True):
            st.rerun()

else:
    st.warning("Cargando estado del juego... Verifica que Supabase tenga la fila ID=1 creada.")
