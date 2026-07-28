import streamlit as st
import sqlite3
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="Panel de Administración", layout="wide")

# 1. DEFINICIÓN DE CONEXIÓN CON RUTA ABSOLUTA
def conectar_db(): 
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, 'inventario_thrutubing.db')
    return sqlite3.connect(db_path)

# 2. ASEGURAR QUE LA TABLA MAESTRA EXISTE
with conectar_db() as conn:
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventario (
            id TEXT PRIMARY KEY,
            descripcion TEXT,
            cantidad INTEGER DEFAULT 1,
            ubicacion TEXT DEFAULT 'Taller Principal',
            categoria TEXT
        )
    ''')
    conn.commit()

st.title("Mendoza Servicios e Herramientas")
st.subheader("⚙️ Panel de Administración y Control de Base de Datos")
st.markdown("---")

st.markdown("### 🛡️ Acceso Restringido")
clave_acceso = st.text_input("Contraseña del Administrador:", type="password")

if clave_acceso == "MENDOZA2026":
    st.success("🔒 Acceso Autorizado.")
    
    tab_carga, tab_bajas, tab_respaldos = st.tabs([
        "📥 Carga Masiva (Excel)", 
        "🗑️ Bajas e Inventario Dañado",
        "💾 Respaldos y Exportación"
    ])
    
    # ---------------------------------------------------------
    # PESTAÑA 1: CARGA MASIVA DE CATÁLOGO DESDE EXCEL
    # ---------------------------------------------------------
    with tab_carga:
        st.markdown("#### 📥 Cargar / Actualizar Catálogo Maestro")
        st.caption("Suba el archivo oficial de inventario para actualizar o poblar automáticamente las categorías de herramientas.")
        
        archivo_subido = st.file_uploader("Subir Archivo Excel Mendoza:", type=["xlsx", "xlsm"])
        
        if archivo_subido is not None and st.button("🚀 Iniciar Carga Masiva", use_container_width=True):
            try:
                excel_file = pd.ExcelFile(archivo_subido)
                piezas_cargadas = 0
                
                with conectar_db() as conn:
                    cursor = conn.cursor()
                    
                    for sheet in excel_file.sheet_names:
                        if "INDICE" in sheet.upper() or "ÍNDICE" in sheet.upper(): 
                            continue
                            
                        df_sheet = pd.read_excel(archivo_subido, sheet_name=sheet, skiprows=3)
                        
                        if "No SERIE" in df_sheet.columns and "HERRAMIENTA" in df_sheet.columns:
                            df_sheet = df_sheet.dropna(subset=["No SERIE"])
                            
                            for _, row in df_sheet.iterrows():
                                serie = str(row["No SERIE"]).strip()
                                herramienta = str(row["HERRAMIENTA"]).strip()
                                
                                if "SISTEMA" in serie.upper() or len(serie) < 2 or serie.upper() == "NAN": 
                                    continue
                                
                                sheet_upper = sheet.upper()
                                if "CONECTORES" in sheet_upper: cat = "Conectores"
                                elif "TROMPOS" in sheet_upper: cat = "Trompos difusores"
                                elif "COMBINACIONES" in sheet_upper: cat = "Combinaciones"
                                elif "VARIAS" in sheet_upper: cat = "Herramientas varias"
                                elif "HERRAMIENTAS DE PESCA" in sheet_upper: cat = "Herramientas de pesca"
                                elif "MOLINOS" in sheet_upper: cat = "Molinos y zapatas"
                                elif "CENTRADORES" in sheet_upper: cat = "Centradores y cortatubos"
                                elif "MOTORES" in sheet_upper: cat = "Motores"
                                elif "MARTILLOS" in sheet_upper: cat = "Martillos de pesca"
                                else: cat = "Herramientas varias"
                                
                                cursor.execute("INSERT OR REPLACE INTO inventario VALUES (?, ?, 1, 'Taller Principal', ?)", (serie, herramienta, cat))
                                piezas_cargadas += 1
                                
                    conn.commit()
                st.success(f"⚡ Base de datos actualizada exitosamente con {piezas_cargadas} registros.")
            except Exception as e:
                st.error(f"❌ Error al procesar el archivo Excel: {e}")

    # ---------------------------------------------------------
    # PESTAÑA 2: GESTIÓN DE BAJAS CON AUDITORÍA DE USUARIO
    # ---------------------------------------------------------
    with tab_bajas:
        st.markdown("#### 🗑️ Dar de Baja Herramienta del Inventario")
        st.caption("Módulo de descarte formal con trazabilidad de usuario y motivo técnico.")
        
        try:
            with conectar_db() as conn:
                df_piezas_activas = pd.read_sql_query("SELECT id, descripcion, categoria, ubicacion FROM inventario", conn)
        except Exception:
            df_piezas_activas = pd.DataFrame()
            
        if df_piezas_activas.empty:
            st.info("No hay herramientas registradas en la base de datos.")
        else:
            c_u1, c_u2 = st.columns(2)
            with c_u1:
                usuario_admin = st.text_input("👤 Nombre de Usuario / Ingeniero que autoriza la baja:", placeholder="Ej. Ing. David / Ing. Mosqueda").strip()
            with c_u2:
                opciones_baja = [f"{row['id']} - {row['descripcion']} ({row['categoria']})" for _, row in df_piezas_activas.iterrows()]
                pieza_a_borrar = st.selectbox("🔧 Seleccione la herramienta a procesar:", opciones_baja)
            
            serie_baja = pieza_a_borrar.split(" - ")[0]
            motivo_baja = st.text_input("📝 Motivo técnico de la baja (Ej. Rosca barrida, Fisura NDT, Límite de horas):", value="Vida útil finalizada").strip()
            
            st.markdown("---")
            col_b1, col_b2 = st.columns(2)
            
            fecha_hora_actual = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            with col_b1:
                if st.button("⚠️ Marcar como 'DADA DE BAJA' (Conservar Histórico)", use_container_width=True):
                    if not usuario_admin:
                        st.error("⛔ ERROR: Debe ingresar su Nombre de Usuario para firmar la baja.")
                    elif not motivo_baja:
                        st.error("⛔ ERROR: Debe ingresar el motivo técnico de la baja.")
                    else:
                        registro_auditoria = f"BAJA: {motivo_baja} | Autorizó: {usuario_admin} ({fecha_hora_actual})"
                        with conectar_db() as conn:
                            cursor = conn.cursor()
                            cursor.execute("UPDATE inventario SET ubicacion = ? WHERE id = ?", (registro_auditoria, serie_baja))
                            conn.commit()
                        st.warning(f"⚠️ La herramienta {serie_baja} quedó registrada como DADA DE BAJA por {usuario_admin}.")
                        st.rerun()

            with col_b2:
                if st.button("🚨 ELIMINAR DEFINITIVAMENTE del Sistema", type="primary", use_container_width=True):
                    if not usuario_admin:
                        st.error("⛔ ERROR: Debe ingresar su Nombre de Usuario para confirmar la eliminación.")
                    else:
                        with conectar_db() as conn:
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM inventario WHERE id = ?", (serie_baja,))
                            conn.commit()
                        st.success(f"🗑️ La herramienta {serie_baja} fue eliminada permanentemente por {usuario_admin}.")
                        st.rerun()

    # ---------------------------------------------------------
    # PESTAÑA 3: RESPALDOS LOCALES Y EXPORTACIÓN
    # ---------------------------------------------------------
    with tab_respaldos:
        st.markdown("#### 💾 Respaldos y Descargas Directas")
        st.write("Proteja su información descargando copias locales de la base de datos o reportes ejecutivos en Excel.")
        
        col_res1, col_res2 = st.columns(2)
        
        # Obtener ruta absoluta de la base de datos para descarga
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_file = os.path.join(base_dir, "inventario_thrutubing.db")
        
        with col_res1:
            st.markdown("##### 📦 Copia de Seguridad de Base de Datos (.db)")
            if os.path.exists(db_file):
                with open(db_file, "rb") as f:
                    st.download_button(
                        label="📥 Descargar Base de Datos Completa (.db)",
                        data=f,
                        file_name=f"Backup_Inventario_TT_{datetime.now().strftime('%Y%m%d_%H%M')}.db",
                        mime="application/x-sqlite3",
                        use_container_width=True
                    )
            else:
                st.warning("⚠️ No se encontró la base de datos local.")

        with col_res2:
            st.markdown("##### 📊 Reporte Maestro Consolidado (.xlsx)")
            if st.button("📊 Generar Excel de Inventario", use_container_width=True):
                try:
                    with conectar_db() as conn:
                        df_inv = pd.read_sql_query("SELECT * FROM inventario", conn)
                    
                    excel_out = f"Inventario_Maestro_Mendoza_{datetime.now().strftime('%Y%m%d')}.xlsx"
                    df_inv.to_excel(excel_out, index=False)
                    
                    with open(excel_out, "rb") as f_ex:
                        st.download_button(
                            label="📥 Descargar Reporte Maestro Excel",
                            data=f_ex,
                            file_name=excel_out,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                except Exception as e:
                    st.error(f"❌ Error al exportar: {e}")

elif clave_acceso != "":
    st.error("❌ Clave de acceso incorrecta.")
