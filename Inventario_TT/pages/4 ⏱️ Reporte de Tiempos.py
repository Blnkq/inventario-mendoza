import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="MSH-TT-FOR-007 - Reporte de Tiempos", layout="wide")

def conectar_db(): 
    return sqlite3.connect('inventario_thrutubing.db')

# Crear tabla en base de datos para almacenar las actividades diarias si no existe
with conectar_db() as conn:
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reporte_tiempos (
            id_tiempo INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            pozo TEXT,
            hora_inicio TEXT,
            hora_fin TEXT,
            actividad TEXT,
            categoria TEXT,
            ingeniero TEXT
        )
    ''')
    conn.commit()

st.title("Mendoza Servicios e Herramientas")
st.subheader("Formato: MSH-TT-FOR-007 — Reporte de Tiempos Operativos Diario")
st.markdown("---")

# 1. DATOS GENERALES DEL DÍA
st.markdown("#### 📝 Encabezado del Reporte Diario")
with st.container():
    c1, c2, c3 = st.columns(3)
    with c1:
        fecha_rep = st.date_input("FECHA DEL REPORTE:", value=datetime.now())
    with c2:
        pozo_rep = st.text_input("NUM. DE POZO:", value="910")
    with c3:
        ing_rep = st.text_input("OPERADOR / INGENIEERO DE CAMPO:", value="ARCENIO JIMENEZ MORGAN")

st.markdown("---")

# 2. CAPTURA DE ACTIVIDADES EN EL DÍA
st.markdown("#### 📥 Registrar Tramo de Actividad (24 Horas)")

with st.form("form_actividad", clear_on_submit=True):
    col_h1, col_h2, col_cat = st.columns(3)
    with col_h1:
        h_inicio = st.text_input("Hora de Inicio (Ej. 06:00):", placeholder="HH:MM")
    with col_h2:
        h_fin = st.text_input("Hora de Fin (Ej. 07:00):", placeholder="HH:MM")
    with col_cat:
        categoria = st.selectbox("Clasificación del Tiempo:", [
            "Tiempo Operativo (Actividad Normal)",
            "Tiempo Muerto / Espera (Logística)",
            "Tiempo Muerto / Espera (Compañía)",
            "Espera de Condiciones / Clima"
        ])
        
    actividad_desc = st.text_area("Descripción detallada de la actividad en pozo:")
    
    btn_agregar = st.form_submit_button("➕ Agregar Actividad al Día")
    
    if btn_agregar:
        if not h_inicio or not h_fin or not actividad_desc.strip():
            st.error("❌ Todos los campos son obligatorios para registrar el intervalo de tiempo.")
        else:
            with conectar_db() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO reporte_tiempos (fecha, pozo, hora_inicio, hora_fin, actividad, categoria, ingeniero)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (str(fecha_rep), pozo_rep.strip(), h_inicio.strip(), h_fin.strip(), actividad_desc.strip(), categoria, ing_rep.strip()))
                conn.commit()
            st.success(f"✔️ Intervalo {h_inicio} - {h_fin} guardado correctamente.")

st.markdown("---")

# 3. VISUALIZACIÓN DE LA JORNADA DIARIA
st.markdown(f"#### 📊 Cronograma de Actividades del Pozo {pozo_rep} ({fecha_rep})")

with conectar_db() as conn:
    df_dia = pd.read_sql_query('''
        SELECT hora_inicio AS [HORA INICIO], 
               hora_fin AS [HORA FIN], 
               actividad AS [DESCRIPCIÓN DE LA ACTIVIDAD], 
               categoria AS [CLASIFICACIÓN],
               ingeniero AS [INGENIERO RESIDENCIA]
        FROM reporte_tiempos 
        WHERE fecha = ? AND pozo = ?
        ORDER BY hora_inicio ASC
    ''', conn, params=(str(fecha_rep), pozo_rep.strip()))

if df_dia.empty:
    st.info("No se han capturado eventos o actividades para este pozo en la fecha seleccionada.")
else:
    # Función para colorear de rojo los tiempos muertos y gris/azul el operativo
    def colorear_tiempos(row):
        styles = [''] * len(row)
        if "Tiempo Muerto" in str(row['CLASIFICACIÓN']):
            styles[3] = 'background-color: #ffebe6; color: #cc3300; font-weight: bold;'
        else:
            styles[3] = 'background-color: #f0f7ff; color: #0056b3; font-weight: bold;'
        return styles

    st.dataframe(df_dia.style.apply(colorear_tiempos, axis=1), use_container_width=True, hide_index=True)
