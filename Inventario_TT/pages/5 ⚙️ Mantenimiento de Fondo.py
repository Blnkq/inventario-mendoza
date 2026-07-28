import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="MSH-TT-FOR-009 - Mantenimiento de Fondo", layout="wide")

# 1. DEFINICIÓN DE CONEXIÓN CON RUTA ABSOLUTA DINÁMICA
def conectar_db(): 
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, 'inventario_thrutubing.db')
    return sqlite3.connect(db_path)

# 2. CREAR TABLA BASE SI NO EXISTE
with conectar_db() as conn:
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mtto_herramientas (
            id_mtto INTEGER PRIMARY KEY AUTOINCREMENT,
            no_serie TEXT,
            fecha_op TEXT,
            pozo TEXT,
            tipo_op TEXT,
            tipo_fluido TEXT,
            horas_viaje REAL,
            horas_carga REAL,
            detalles_mtto TEXT,
            mecanico TEXT
        )
    ''')
    conn.commit()

# 3. MIGRACIÓN AUTOMÁTICA (Agrega columnas faltantes si la tabla es antigua)
with conectar_db() as conn:
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(mtto_herramientas)")
    columnas_existentes = [col[1] for col in cursor.fetchall()]
    
    nuevas_columnas = {
        'fecha_mtto': 'TEXT',
        'operador_campo': 'TEXT',
        'horas_circulacion': 'REAL',
        'horas_estatico': 'REAL',
        'estatus_ndt': "TEXT DEFAULT 'ACEPTADO'"
    }
    
    for col_nombre, col_tipo in nuevas_columnas.items():
        if col_nombre not in columnas_existentes:
            cursor.execute(f"ALTER TABLE mtto_herramientas ADD COLUMN {col_nombre} {col_tipo}")
    
    conn.commit()

# 4. CARGAR CATÁLOGO DE HERRAMIENTAS
with conectar_db() as conn:
    df_piezas = pd.read_sql_query("SELECT id AS [No SERIE], descripcion AS [HERRAMIENTA] FROM inventario", conn)

st.title("Mendoza Servicios e Herramientas")
st.subheader("Formato: MSH-TT-FOR-009 — Control de Mantenimiento a Herramienta de Fondo")
st.markdown("---")

if df_piezas.empty:
    st.info("No hay herramientas registradas en el catálogo maestro.")
else:
    # SELECCIÓN DE LA PIEZA A REVISAR
    st.markdown("#### 🔍 1. Identificación del Equipo en Taller")
    opciones_piezas = [f"{row['No SERIE']} - {row['HERRAMIENTA']}" for _, row in df_piezas.iterrows()]
    pieza_seleccionada = st.selectbox("Seleccione el No. de Serie de la herramienta que entró a taller:", opciones_piezas)
    
    id_serie = pieza_seleccionada.split(" - ")[0]
    
    st.markdown("---")
    
    # FORMULARIO DE MANTENIMIENTO
    st.markdown("#### 🔧 2. Registro de Inspección y Servicio Realizado")
    
    with st.form("form_mantenimiento", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            fecha_op = st.date_input("Fecha de la Operación / Corrida:", value=datetime.today())
            fecha_mtto = st.date_input("Fecha de Mantenimiento en Taller:", value=datetime.today())
            pozo = st.text_input("Pozo donde operó:", value="Puerto Ceiba 157")
            tipo_op = st.text_input("Tipo de operación:", value="Limpieza de Aparejo")
        
        with c2:
            tipo_fluido = st.text_input("Tipo de fluido usado:", value="Agua, Solvente")
            operador_campo = st.text_input("Operador de Herramientas (Campo):", placeholder="Ej. Arcenio Jimenez Morgan")
            mecanico = st.text_input("Técnico / Mecánico responsable (Taller):")
            estatus_ndt = st.selectbox("Dictamen Inspección NDT (Partículas Magnéticas):", ["ACEPTADO", "RECHAZADO", "PENDIENTE"])

        with c3:
            h_viaje = st.number_input("Horas de viaje:", min_value=0.0, step=0.1, value=18.0)
            h_circ = st.number_input("Horas de circulación:", min_value=0.0, step=0.1, value=15.0)
            h_carga = st.number_input("Horas de carga (Trabajando):", min_value=0.0, step=0.1, value=0.0)
            h_estatico = st.number_input("Horas en estático:", min_value=0.0, step=0.1, value=0.0)
            
        detalles_mtto = st.text_area("Mantenimiento realizado / Diagnóstico técnico:", placeholder="Describa limpieza, inspección de roscas, cambio de elastómeros...")
        
        btn_guardar_mtto = st.form_submit_button("💾 Registrar Mantenimiento Oficial")
        
        if btn_guardar_mtto:
            if not mecanico.strip() or not detalles_mtto.strip():
                st.error("❌ Error: Es obligatorio especificar el Técnico responsable y los Detalles del Mantenimiento.")
            else:
                with conectar_db() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO mtto_herramientas (
                            no_serie, fecha_op, fecha_mtto, pozo, tipo_op, tipo_fluido, 
                            operador_campo, horas_viaje, horas_circulacion, horas_carga, 
                            horas_estatico, detalles_mtto, mecanico, estatus_ndt
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        id_serie, str(fecha_op), str(fecha_mtto), pozo.strip(), tipo_op.strip(), 
                        tipo_fluido.strip(), operador_campo.strip(), h_viaje, h_circ, h_carga, 
                        h_estatico, detalles_mtto.strip(), mecanico.strip(), estatus_ndt
                    ))
                    
                    horas_totales_trabajo = h_carga + h_circ
                    cursor.execute("UPDATE inventario SET horas_uso = horas_uso + ? WHERE id = ?", (horas_totales_trabajo, id_serie))
                    conn.commit()
                    
                st.success(f"🎉 Registro de mantenimiento guardado exitosamente para la serie {id_serie}. Horas acumuladas actualizadas (+{horas_totales_trabajo} hrs).")

    st.markdown("---")
    
    # HISTORIAL CLÍNICO
    st.markdown(f"#### 📜 Historial Clínico de Mantenimiento (No. Serie: {id_serie})")
    
    with conectar_db() as conn:
        df_hist_mtto = pd.read_sql_query('''
            SELECT fecha_op AS [FECHA OP], 
                   fecha_mtto AS [FECHA MTTO],
                   pozo AS [POZO], 
                   tipo_op AS [OPERACIÓN], 
                   tipo_fluido AS [FLUIDO], 
                   operador_campo AS [OPERADOR CAMPO],
                   horas_viaje AS [HRS VIAJE], 
                   horas_circulacion AS [HRS CIRC],
                   horas_carga AS [HRS CARGA], 
                   horas_estatico AS [HRS ESTÁTICO],
                   estatus_ndt AS [NDT],
                   detalles_mtto AS [DIAGNÓSTICO / SERVICIO], 
                   mecanico AS [TÉCNICO]
            FROM mtto_herramientas 
            WHERE no_serie = ?
            ORDER BY id_mtto DESC
        ''', conn, params=(id_serie,))
        
    if df_hist_mtto.empty:
        st.info(f"Esta herramienta ({id_serie}) no cuenta con registros de mantenimiento previos en el sistema.")
    else:
        st.dataframe(df_hist_mtto, use_container_width=True, hide_index=True)
