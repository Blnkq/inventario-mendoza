import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Trazabilidad e Inspección NDT - Motores", layout="wide")

def conectar_db(): 
    return sqlite3.connect('inventario_thrutubing.db')

# --- INICIALIZACIÓN DE TABLAS (TRAZABILIDAD + NDT) ---
with conectar_db() as conn:
    cursor = conn.cursor()
    
    # Tablas de Trazabilidad y Corridas (Código Existente)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS motores_trazabilidad (
            id_motor TEXT PRIMARY KEY,
            horas_acumuladas REAL DEFAULT 0.0,
            horas_limite REAL DEFAULT 100.0,
            estado_vida TEXT DEFAULT 'Óptimo'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historial_corridas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_motor TEXT,
            fecha_operacion TEXT,
            pozo TEXT,
            horas_corridas REAL,
            tipo_fluido TEXT,
            factor_severidad REAL,
            horas_equivalentes REAL,
            comentarios TEXT
        )
    ''')

    # Tablas de Inspección NDT / Partículas Magnéticas SSI (Formato SSI-INS-FOR-003)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inspecciones_ndt (
            id_ndt INTEGER PRIMARY KEY AUTOINCREMENT,
            reporte_no TEXT UNIQUE,
            no_serie_motor TEXT,
            fecha_insp TEXT,
            cliente TEXT,
            descripcion_trabajo TEXT,
            norma TEXT,
            inspector TEXT,
            nivel_inspector TEXT,
            condicion_final TEXT,
            luz_negra REAL,
            luz_visible REAL,
            concentracion_particulas REAL,
            observaciones TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ndt_componentes_motor (
            id_comp INTEGER PRIMARY KEY AUTOINCREMENT,
            reporte_no TEXT,
            componente TEXT,
            tipo_conexion TEXT,
            od TEXT,
            id_medida TEXT,
            longitud TEXT,
            eval_cuerpo TEXT,
            eval_rosca TEXT,
            FOREIGN KEY(reporte_no) REFERENCES inspecciones_ndt(reporte_no)
        )
    ''')
    conn.commit()

st.title("Mendoza Servicios e Herramientas")
st.subheader("Módulo de Trazabilidad, Salud Operativa e Inspecciones NDT para Motores")
st.markdown("---")

# Cargar catálogo de motores activos
with conectar_db() as conn:
    df_motores_activos = pd.read_sql_query("SELECT id, descripcion FROM inventario WHERE categoria = 'Motores'", conn)
    if df_motores_activos.empty:
        df_motores_activos = pd.read_sql_query("SELECT id, descripcion FROM inventario WHERE descripcion LIKE '%MOTOR%' OR id LIKE '54%'", conn)

# --- ESTRUCTURA DE PESTAÑAS (TABS) ---
tab1, tab2, tab3 = st.tabs([
    "🩺 Salud y Corridas en Pozo", 
    "📝 Registrar Inspección NDT (SSI)", 
    "📜 Histórico de Certificados NDT"
])

# ==========================================
# PESTAÑA 1: CÓDIGO EXISTENTE DE TRAZABILIDAD
# ==========================================
with tab1:
    st.markdown("### 🔄 Control de Horas de Operación y Vida Útil (Motores)")

    if df_motores_activos.empty:
        st.info("No existen herramientas registradas bajo la categoría 'Motores' en el inventario.")
    else:
        with conectar_db() as conn:
            cursor = conn.cursor()
            for _, row in df_motores_activos.iterrows():
                cursor.execute("INSERT OR IGNORE INTO motores_trazabilidad (id_motor, horas_limite) VALUES (?, 100.0)", (row["id"],))
            conn.commit()
            
            df_salud = pd.read_sql_query('''
                SELECT m.id_motor AS [No SERIE], i.descripcion AS [MOTOR], 
                       ROUND(m.horas_acumuladas, 1) AS [HRS ACUMULADAS], ROUND(m.horas_limite, 1) AS [HRS LÍMITE], m.estado_vida AS [ESTADO DE SALUD]
                FROM motores_trazabilidad m JOIN inventario i ON m.id_motor = i.id
            ''', conn)

        def colorear_semaforo(val):
            if val == "Crítico (Overhaul Requerido)": return "background-color: #ffcccc; color: #cc0000; font-weight: bold;"
            elif val == "Precaución (Próximo a Límite)": return "background-color: #ffe6cc; color: #cc6600; font-weight: bold;"
            return "background-color: #e6ffed; color: #00802b; font-weight: bold;"

        st.markdown("#### 🩺 Estatus de Salud Operativa")
        st.dataframe(df_salud.style.map(colorear_semaforo, subset=["ESTADO DE SALUD"]), use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("#### 📝 Registrar Nueva Corrida / Operación en Pozo")
        
        with st.form("registro_corrida_form", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                motor_sel = st.selectbox("Seleccionar No. Serie del Motor:", df_salud["No SERIE"].unique())
                pozo_nombre = st.text_input("Nombre del Pozo / Campo:").strip()
            with col2:
                hrs_reales = st.number_input("Horas Reales de Circulación:", min_value=0.1, max_value=48.0, step=0.1, value=5.0)
                tipo_fluido = st.selectbox("Fluido Utilizado:", [
                    "Agua Clara / Salmueras Limpias (Factor 1.0x)", 
                    "Fluidos Espumados / Nitrógeno (Factor 1.2x)", 
                    "Lodos de Perforación con Sólidos < 2% (Factor 1.5x)", 
                    "Sistemas Ácidos / Solventes Aromáticos (Factor 2.0x)"
                ])
            with col3:
                fecha_corrida = st.date_input("Fecha de la Operación:", value=datetime.today())
                comentarios = st.text_area("Comentarios técnicos:")
                
            btn_registrar_corrida = st.form_submit_button("🚀 Aplicar Corrida")
            
            if btn_registrar_corrida:
                if not pozo_nombre:
                    st.error("⛔ Debe ingresar el nombre del pozo.")
                else:
                    mapeo_factores = {
                        "Agua Clara / Salmueras Limpias (Factor 1.0x)": 1.0,
                        "Fluidos Espumados / Nitrógeno (Factor 1.2x)": 1.2,
                        "Lodos de Perforación con Sólidos < 2% (Factor 1.5x)": 1.5,
                        "Sistemas Ácidos / Solventes Aromáticos (Factor 2.0x)": 2.0
                    }
                    fs = mapeo_factores[tipo_fluido]
                    horas_equivalentes = hrs_reales * fs
                    
                    with conectar_db() as conn:
                        cursor = conn.cursor()
                        cursor.execute('INSERT INTO historial_corridas (id_motor, fecha_operacion, pozo, horas_corridas, tipo_fluido, factor_severidad, horas_equivalentes, comentarios) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                                       (motor_sel, str(fecha_corrida), pozo_nombre, hrs_reales, tipo_fluido, fs, horas_equivalentes, comentarios))
                        
                        cursor.execute("SELECT horas_acumuladas, horas_limite FROM motores_trazabilidad WHERE id_motor = ?", (motor_sel,))
                        h_acum, h_lim = cursor.fetchone()
                        nuevas_horas = h_acum + horas_equivalentes
                        
                        porcentaje_desgaste = nuevas_horas / h_lim
                        estado_salud = "Crítico (Overhaul Requerido)" if porcentaje_desgaste >= 0.90 else "Precaución (Próximo a Límite)" if porcentaje_desgaste >= 0.75 else "Óptimo"
                            
                        cursor.execute('UPDATE motores_trazabilidad SET horas_acumuladas = ?, estado_vida = ? WHERE id_motor = ?', (nuevas_horas, estado_salud, motor_sel))
                        conn.commit()
                    st.success("✔️ Registro guardado con éxito.")
                    st.rerun()

# ==========================================
# PESTAÑA 2: FORMULARIO NDT (SSI)
# ==========================================
with tab2:
    st.markdown("### 📋 Formato SSI-INS-FOR-003: Inspección por Partículas Magnéticas Fluorescentes")
    
    with st.form("form_inspeccion_ndt", clear_on_submit=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            reporte_no = st.text_input("No. de Reporte SSI:", value="SSI-MSH-TT-016-06-2026 REQ-913")
            fecha_insp = st.date_input("Fecha de Inspección:", value=datetime.today())
            cliente = st.text_input("Cliente:", value="MENDOZA SERVICIOS Y HERRAMIENTAS S.A. DE C.V.")
        
        with c2:
            opciones_m = [f"{row['id']} - {row['descripcion']}" for _, row in df_motores_activos.iterrows()] if not df_motores_activos.empty else ["540048 - MOTOR DE FONDO"]
            motor_sel_ndt = st.selectbox("Seleccione Motor de Fondo (Ensamble):", opciones_m)
            no_serie_motor_ndt = motor_sel_ndt.split(" - ")[0]
                
            norma = st.text_input("Norma / Especificación:", value="SSI-INS-PRO-005 API RP 7G-2, ASTM E-3024")
            inspector = st.text_input("Inspector ASNT Nivel II:", value="ADRIAN BLANCO SANCHEZ")

        with c3:
            desc_trabajo = st.text_input("Descripción del Trabajo:", value="INSPECCION CON PARTICULAS MAGNETICAS HUMEDAS FLUORESCENTES A MOTOR DE FONDO HP/HT 2 1/8\"")
            condicion_final = st.selectbox("DICTAMEN TÉCNICO FINAL:", ["ACEPTADO", "RECHAZADO"])
            observaciones = st.text_area("Comentarios / Observaciones NDT:", value="Sin defectos detectados en componentes inspeccionados.")

        st.markdown("---")
        st.markdown("### ⚙️ Desglose Técnico por Sub-Componente (Motor HP/HT 2 1/8\")")

        componentes_default = [
            {"Componente": "STATOR", "Conexión": "BOX / BOX", "OD": "2 1/8\"", "ID": "1 13/16\"", "Longitud": "2.19 M", "Cuerpo": "ACEPTADO", "Rosca": "ACEPTADO"},
            {"Componente": "BARRIL / ROTOR", "Conexión": "N/A", "OD": "2 1/8\"", "ID": "-", "Longitud": "-", "Cuerpo": "ACEPTADO", "Rosca": "ACEPTADO"},
            {"Componente": "SECCIÓN DE BALEROS", "Conexión": "PIÑON / PIÑON", "OD": "2 1/8\"", "ID": "1 5/8\"", "Longitud": "49 CM", "Cuerpo": "ACEPTADO", "Rosca": "ACEPTADO"},
            {"Componente": "FLECHA FLEXIBLE", "Conexión": "BOX / PIÑON", "OD": "2 1/8\"", "ID": "1 13/16\"", "Longitud": "70 CM", "Cuerpo": "ACEPTADO", "Rosca": "ACEPTADO"},
            {"Componente": "FLECHA DE MANDO", "Conexión": "BOX 1 1/2\" AMT", "OD": "2 1/8\"", "ID": "5/8\"", "Longitud": "38 CM", "Cuerpo": "ACEPTADO", "Rosca": "ACEPTADO"},
            {"Componente": "TOP SUB", "Conexión": "PIÑON 2 1/8\" / BOX 1 1/2\"", "OD": "2 1/8\"", "ID": "1 3/8\"", "Longitud": "17 CM", "Cuerpo": "ACEPTADO", "Rosca": "ACEPTADO"},
        ]
        
        df_editor = st.data_editor(
            pd.DataFrame(componentes_default),
            num_rows="dynamic",
            use_container_width=True,
            key="editor_componentes_ndt"
        )

        st.markdown("---")
        st.markdown("### 🔬 Parámetros de Laboratorio NDT")
        p1, p2, p3 = st.columns(3)
        with p1:
            luz_negra = st.number_input("Intensidad Luz Negra (µW/cm²):", value=2420)
        with p2:
            luz_visible = st.number_input("Intensidad Luz Visible (Lux):", value=540)
        with p3:
            conc_part = st.number_input("Conc. Partículas (ml / 100ml):", value=0.3, step=0.05)

        btn_guardar_ndt = st.form_submit_button("💾 Guardar Certificado NDT Oficial")

        if btn_guardar_ndt:
            try:
                with conectar_db() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO inspecciones_ndt (
                            reporte_no, no_serie_motor, fecha_insp, cliente, descripcion_trabajo,
                            norma, inspector, nivel_inspector, condicion_final, luz_negra,
                            luz_visible, concentracion_particulas, observaciones
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        reporte_no.strip(), no_serie_motor_ndt, str(fecha_insp), cliente.strip(),
                        desc_trabajo.strip(), norma.strip(), inspector.strip(), "N-II ASNT",
                        condicion_final, luz_negra, luz_visible, conc_part, observaciones.strip()
                    ))

                    for _, row in df_editor.iterrows():
                        cursor.execute('''
                            INSERT INTO ndt_componentes_motor (
                                reporte_no, componente, tipo_conexion, od, id_medida, longitud, eval_cuerpo, eval_rosca
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            reporte_no.strip(), row['Componente'], row['Conexión'], str(row['OD']),
                            str(row['ID']), str(row['Longitud']), row['Cuerpo'], row['Rosca']
                        ))
                    
                    conn.commit()
                st.success(f"🎉 Certificado NDT {reporte_no} registrado con éxito para el motor {no_serie_motor_ndt}.")
            except Exception as e:
                st.error(f"❌ Error al registrar certificado: {e}. Verifique que el número de reporte no esté repetido.")

# ==========================================
# PESTAÑA 3: HISTÓRICO Y CONSULTA NDT
# ==========================================
with tab3:
    st.markdown("### 🔍 Expediente de Certificados de Inspección NDT")
    
    with conectar_db() as conn:
        df_certificados = pd.read_sql_query('''
            SELECT reporte_no AS [REPORTE NO], 
                   no_serie_motor AS [NO. SERIE MOTOR], 
                   fecha_insp AS [FECHA INSP], 
                   condicion_final AS [DICTAMEN], 
                   inspector AS [INSPECTOR N-II], 
                   norma AS [NORMA]
            FROM inspecciones_ndt 
            ORDER BY id_ndt DESC
        ''', conn)
        
    if df_certificados.empty:
        st.info("Aún no se han guardado reportes NDT en la base de datos.")
    else:
        st.dataframe(df_certificados, use_container_width=True, hide_index=True)
        
        rep_sel = st.selectbox("Seleccione No. de Reporte para ver desglose por sub-componentes:", df_certificados['REPORTE NO'].tolist())
        
        if rep_sel:
            with conectar_db() as conn:
                df_detalles_comp = pd.read_sql_query('''
                    SELECT componente AS [COMPONENTE], 
                           tipo_conexion AS [CONEXIÓN], 
                           od AS [OD], 
                           id_medida AS [ID], 
                           longitud AS [LONGITUD], 
                           eval_cuerpo AS [EVAL. CUERPO], 
                           eval_rosca AS [EVAL. ROSCA]
                    FROM ndt_componentes_motor 
                    WHERE reporte_no = ?
                ''', conn, params=(rep_sel,))
                
                st.markdown(f"#### 🔩 Desglose de Inspección para Reporte: `{rep_sel}`")
                st.table(df_detalles_comp)
