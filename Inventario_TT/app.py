import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import io
import os

st.set_page_config(page_title="Control de Inventario - Mendoza", layout="wide", page_icon="🛠️")

# Estilos globales corregidos para un alto contraste en títulos y tarjetas
st.markdown("""<style>
    .stApp { background-color: #f4f6f9; font-family: 'Segoe UI', sans-serif; }
    .main-title { color: #0f2a4a !important; font-size: 32px; font-weight: 800; margin-bottom: 0px; }
    .sub-title { color: #17b978 !important; font-size: 18px; font-weight: 600; margin-bottom: 20px; }
    .section-header { color: #0f2a4a !important; font-size: 20px; font-weight: 700; margin-top: 15px; }
    .metric-card { background-color: #ffffff; padding: 18px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.08); border-left: 6px solid #0f2a4a; margin-bottom: 15px; }
    .metric-title { font-size: 13px; color: #555555; text-transform: uppercase; font-weight: 700; }
    .metric-value { font-size: 30px; color: #0f2a4a; font-weight: bold; }
</style>""", unsafe_allow_html=True)

def conectar_db():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, 'inventario_thrutubing.db')
    return sqlite3.connect(db_path)

# Inicializar tablas base si no existen
with conectar_db() as conn:
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventario (
            id TEXT PRIMARY KEY,
            descripcion TEXT,
            cantidad INTEGER DEFAULT 1,
            ubicacion TEXT DEFAULT 'Taller Principal',
            categoria TEXT,
            horas_uso REAL DEFAULT 0.0,
            stock INTEGER DEFAULT 1
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historial (
            id_historial INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_hora TEXT,
            id_pieza TEXT,
            tipo_movimiento TEXT,
            cantidad INTEGER,
            operador TEXT,
            observaciones TEXT
        )
    ''')
    conn.commit()

# Encabezados con HTML nativo para garantizar legibilidad
st.markdown('<p class="main-title">Mendoza Servicios e Herramientas</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Sistema Integral de Control de Inventario — Thru Tubing</p>', unsafe_allow_html=True)
st.markdown("---")

# Carga de datos base de forma segura
try:
    with conectar_db() as conn:
        df_inv = pd.read_sql_query("SELECT id AS [No SERIE], descripcion AS [HERRAMIENTA], stock AS [STOCK], ubicacion AS [UBICACIÓN], categoria AS [CATEGORÍA] FROM inventario", conn)
        df_hist_total = pd.read_sql_query("SELECT id_historial FROM historial", conn)
except Exception:
    df_inv = pd.DataFrame(columns=["No SERIE", "HERRAMIENTA", "STOCK", "UBICACIÓN", "CATEGORÍA"])
    df_hist_total = pd.DataFrame()

# KPIs principales
c1, c2, c3, c4 = st.columns(4)
with c1: 
    st.markdown(f'<div class="metric-card" style="border-left-color: #0f2a4a;"><div class="metric-title">Total de Equipos</div><div class="metric-value">{len(df_inv)}</div></div>', unsafe_allow_html=True)
with c2: 
    st.markdown(f'<div class="metric-card" style="border-left-color: #28a745;"><div class="metric-title">Piezas en Stock</div><div class="metric-value">{df_inv["STOCK"].sum() if not df_inv.empty else 0}</div></div>', unsafe_allow_html=True)
with c3: 
    st.markdown(f'<div class="metric-card" style="border-left-color: #ffc107;"><div class="metric-title">Movimientos Registrados</div><div class="metric-value">{len(df_hist_total)}</div></div>', unsafe_allow_html=True)
with c4: 
    st.markdown(f'<div class="metric-card" style="border-left-color: #17a2b8;"><div class="metric-title">Familias Activas</div><div class="metric-value">{df_inv["CATEGORÍA"].nunique() if not df_inv.empty else 0}</div></div>', unsafe_allow_html=True)

st.markdown('<p class="section-header">🗃️ Consulta de Existencias en Taller</p>', unsafe_allow_html=True)

categorias = ["Todas", "Conectores", "Trompos difusores", "Combinaciones", "Herramientas varias", "Herramientas de pesca", "Molinos y zapatas", "Centradores y cortatubos", "Motores", "Martillos de pesca"]
cat_seleccionada = st.selectbox("Filtrar por Familia:", categorias)

df_mostrar = df_inv if cat_seleccionada == "Todas" else df_inv[df_inv["CATEGORÍA"] == cat_seleccionada]
st.dataframe(df_mostrar, use_container_width=True, hide_index=True)

if not df_mostrar.empty:
    towrite = io.BytesIO()
    df_mostrar.to_excel(towrite, index=False, header=True, sheet_name='Inventario')
    towrite.seek(0)
    st.download_button(
        label="📥 Exportar Vista Actual a Excel", 
        data=towrite, 
        file_name=f"Inventario_Mendoza_{datetime.now().strftime('%Y%m%d')}.xlsx", 
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
