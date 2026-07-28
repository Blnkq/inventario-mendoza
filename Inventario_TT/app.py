import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import io

st.set_page_config(page_title="Control de Inventario - Mendoza", layout="wide", page_icon="🛠️")

# Estilos globales (Se mantienen en cada página para consistencia corporativa)
st.markdown("""<style>
    .stApp { background-color: #f8f9fa; font-family: 'Segoe UI', sans-serif; }
    h1 { color: #1e3d59; font-weight: 700; }
    h3 { color: #17b978; font-weight: 400; }
    .metric-card { background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-left: 5px solid #1e3d59; margin-bottom: 20px; }
    .metric-title { font-size: 14px; color: #6c757d; text-transform: uppercase; font-weight: bold; }
    .metric-value { font-size: 28px; color: #1e3d59; font-weight: bold; }
</style>""", unsafe_allow_html=True)

import os

def conectar_db():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, 'inventario_thrutubing.db')
    return sqlite3.connect(db_path)
# Carga de datos base
with conectar_db() as conn:
    df_inv = pd.read_sql_query("SELECT id AS [No SERIE], descripcion AS [HERRAMIENTA], stock AS [STOCK], ubicacion AS [UBICACIÓN], categoria AS [CATEGORÍA] FROM inventario", conn)
    df_hist_total = pd.read_sql_query("SELECT id_movimiento FROM historial", conn)

st.title("Mendoza Servicios e Herramientas")
st.subheader("Sistema Integral de Control de Inventario — Thru Tubing")
st.markdown("---")

# KPIs principales
c1, c2, c3, c4 = st.columns(4)
with c1: st.markdown(f'<div class="metric-card"><div class="metric-title">Total de Equipos</div><div class="metric-value">{len(df_inv)}</div></div>', unsafe_allow_html=True)
with c2: st.markdown(f'<div class="metric-card"><div class="metric-title">Piezas en Stock</div><div class="metric-value">{df_inv["STOCK"].sum() if not df_inv.empty else 0}</div></div>', unsafe_allow_html=True)
with c3: st.markdown(f'<div class="metric-card"><div class="metric-title">Movimientos Registrados</div><div class="metric-value">{len(df_hist_total)}</div></div>', unsafe_allow_html=True)
with c4: st.markdown(f'<div class="metric-card"><div class="metric-title">Familias Activas</div><div class="metric-value">{df_inv["CATEGORÍA"].nunique() if not df_inv.empty else 0}</div></div>', unsafe_allow_html=True)

st.markdown("### 🗃️ Consulta de Existencias en Taller")
categorias = ["Todas", "Conectores", "Trompos difusores", "Combinaciones", "Herramientas varias", "Herramientas de pesca", "Molinos y zapatas", "Centradores y cortatubos", "Motores", "Martillos de pesca"]
cat_seleccionada = st.selectbox("Filtrar por Familia:", categorias)

df_mostrar = df_inv if cat_seleccionada == "Todas" else df_inv[df_inv["CATEGORÍA"] == cat_seleccionada]
st.dataframe(df_mostrar, use_container_width=True, hide_index=True)

if not df_mostrar.empty:
    towrite = io.BytesIO()
    df_mostrar.to_excel(towrite, index=False, header=True, sheet_name='Inventario')
    towrite.seek(0)
    st.download_button(label="📥 Exportar Vista Actual a Excel", data=towrite, file_name=f"Inventario_Mendoza_{datetime.now().strftime('%Y%m%d')}.xlsx", mime="application/vnd.ms-excel")
