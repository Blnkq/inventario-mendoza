import streamlit as st
import sqlite3
import pandas as pd
import os
import io
import qrcode
from PIL import Image
from datetime import datetime

st.set_page_config(page_title="Panel de Administración", layout="wide")

# 1. DEFINICIÓN DE CONEXIÓN CON RUTA ABSOLUTA
def conectar_db(): 
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, 'inventario_thrutubing.db')
    return sqlite3.connect(db_path)

# 2. ASEGURAR QUE LA TABLA MAESTRA EXISTE Y TIENE TODAS LAS COLUMNAS
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
    # Verificar si faltan columnas acumulativas por versiones viejas
    cursor.execute("PRAGMA table_info(inventario)")
    cols = [col[1] for col in cursor.fetchall()]
    if 'horas_uso' not in cols:
        cursor.execute("ALTER TABLE inventario ADD COLUMN horas_uso REAL DEFAULT 0.0")
    if 'stock' not in cols:
        cursor.execute("ALTER TABLE inventario ADD COLUMN stock INTEGER DEFAULT 1")
    conn.commit()

st.title("Mendoza Servicios e Herramientas")
st.subheader("⚙️ Panel de Administración y Control de Base de Datos")
st.markdown("---")

st.markdown("### 🛡️ Acceso Restringido")
clave_acceso = st.text_input("Contraseña del Administrador:", type="password")

if clave_acceso == "MENDOZA2026":
    st.success("🔒 Acceso Autorizado.")
    
    tab_reg, tab_carga, tab_bajas, tab_respaldos = st.tabs([
        "🏷️ Regularizar Piezas y Generar QR",
        "📥 Carga Masiva (Excel)", 
        "🗑️ Bajas e Inventario Dañado",
        "💾 Respaldos y Exportación"
    ])
    
    # ---------------------------------------------------------
    # PESTAÑA 0: REGULARIZACIÓN DE DATOS Y GENERADOR DE QR
    # ---------------------------------------------------------
    with tab_reg:
        st.markdown("#### 🛠️ Regularizar Estatus de Herramientas en Campo y Generar QR")
        st.caption("Use este módulo temporal para ajustar las horas pasadas, pozos donde se encuentran las herramientas y descargar sus etiquetas QR.")
        
        with conectar_db() as conn:
            df_inv_reg = pd.read_sql_query("SELECT id, descripcion, ubicacion, stock, COALESCE(horas_uso, 0.0) AS horas_uso FROM inventario", conn)
            
        if df_inv_reg.empty:
            st.info("No hay herramientas registradas para regularizar.")
        else:
            opciones_reg = [f"{row['id']} - {row['descripcion']}" for _, row in df_inv_reg.iterrows()]
            pieza_sel_reg = st.selectbox("Seleccione el No. de Serie de la herramienta:", opciones_reg)
            serie_reg = pieza_sel_reg.split(" - ")[0]
            
            # Obtener datos actuales de la herramienta seleccionada
            info_pieza = df_inv_reg[df_inv_reg["id"] == serie_reg].iloc[0]
            
            col_r1, col_r2 = st.columns(2)
            
            with col_r1:
                st.markdown("##### **1. Actualizar Datos Iniciales / Reales**")
                
                estado_actual_opcion = "En Taller Principal" if info_pieza['stock'] == 1 else "En Pozo / Trabajo Exterior"
                estado_fisico = st.radio("Ubicación Operativa Actual:", ["En Taller Principal", "En Pozo / Trabajo Exterior"], 
                                         index=0 if info_pieza['stock'] == 1 else 1)
                
                if estado_fisico == "En Taller Principal":
                    nueva_ubicacion = "Taller Principal"
                    nuevo_stock = 1
                else:
                    pozo_actual = st.text_input("Pozo / Campo donde se encuentra instalada:", value="POZO: 910 (5 PRESIDENTES)")
                    nueva_ubicacion = pozo_actual.strip()
                    nuevo_stock = 0
                    
                nuevas_hrs = st.number_input("Horas de Uso Acumuladas Previas (Históricas):", min_value=0.0, step=0.5, value=float(info_pieza['horas_uso']))
                
                if st.button("💾 Guardar Actualización de Estatus", type="primary", use_container_width=True):
                    with conectar_db() as conn:
                        cursor = conn.cursor()
                        cursor.execute("UPDATE inventario SET ubicacion = ?, stock = ?, horas_uso = ? WHERE id = ?", 
                                       (nueva_ubicacion, nuevo_stock, nuevas_hrs, serie_reg))
                        conn.commit()
                    st.success(f"✔️ Herramienta {serie_reg} actualizada correctamente. Ubicación: '{nueva_ubicacion}' | Horas: {nuevas_hrs} hrs.")
                    st.rerun()

            with col_r2:
                st.markdown("##### **2. Código QR Oficial de la Pieza**")
                st.write(f"Serie codificada: **`{serie_reg}`**")
                
                # Generar QR dinámico
                qr = qrcode.QRCode(version=1, box_size=8, border=2)
                qr.add_data(serie_reg)
                qr.make(fit=True)
                img_qr = qr.make_image(fill_color="#0f2a4a", back_color="white")
                
                # Convertir imagen a Bytes para mostrar y descargar en Streamlit
                buf = io.BytesIO()
                img_qr.save(buf, format="PNG")
                byte_im = buf.getvalue()
                
                st.image(byte_im, caption=f"QR listo para etiqueta de la serie: {serie_reg}", width=180)
                
                st.download_button(
                    label=f"📥 Descargar QR ({serie_reg}.png)",
                    data=byte_im,
                    file_name=f"QR_{serie_reg}.png",
                    mime="image/png",
                    use_container_width=True
                )

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
                                
                                cursor.execute("INSERT OR REPLACE INTO inventario (id, descripcion, cantidad, ubicacion, categoria, stock) VALUES (?, ?, 1, 'Taller Principal', ?, 1)", (serie, herramienta, cat))
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
                            cursor.execute("UPDATE inventario SET ubicacion = ?, stock = 0 WHERE id = ?", (registro_auditoria, serie_baja))
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
