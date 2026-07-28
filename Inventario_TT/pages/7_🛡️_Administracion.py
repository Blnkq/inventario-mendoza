import streamlit as st
import sqlite3
import pandas as pd
import os
import io
import qrcode
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
            categoria TEXT,
            horas_uso REAL DEFAULT 0.0,
            stock INTEGER DEFAULT 1
        )
    ''')
    
    # Asegurar columnas si vienen de versiones previas
    cursor.execute("PRAGMA table_info(inventario)")
    cols = [col[1] for col in cursor.fetchall()]
    if 'cantidad' not in cols:
        cursor.execute("ALTER TABLE inventario ADD COLUMN cantidad INTEGER DEFAULT 1")
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
    
    tab_carga, tab_reg, tab_bajas, tab_respaldos = st.tabs([
        "📥 Carga Masiva (Formato MSI-FOR-TT-010)", 
        "🏷️ Regularizar Piezas y Generar QR",
        "🗑️ Bajas e Inventario Dañado",
        "💾 Respaldos y Exportación"
    ])

    # ---------------------------------------------------------
    # PESTAÑA 1: CARGA MASIVA ESPECÍFICA PARA FORMATO MENDOZA
    # ---------------------------------------------------------
    with tab_carga:
        st.markdown("#### 📥 Cargar Catálogo Maestro (Formato MSI-FOR-TT-010)")
        st.caption("Suba el libro Excel de inventario oficial. Se procesarán las 9 pestañas de categorías automáticamente.")
        
        archivo_subido = st.file_uploader("Subir Archivo Excel Mendoza (.xlsx / .xlsm):", type=["xlsx", "xlsm"])
        
        if archivo_subido is not None and st.button("🚀 Iniciar Carga Masiva de Herramientas", use_container_width=True):
            try:
                excel_file = pd.ExcelFile(archivo_subido)
                piezas_cargadas = 0
                resumen_hojas = []
                
                with conectar_db() as conn:
                    cursor = conn.cursor()
                    
                    for sheet in excel_file.sheet_names:
                        sheet_upper = sheet.upper().strip()
                        # Omitir carátula
                        if "INDICE" in sheet_upper or "ÍNDICE" in sheet_upper: 
                            continue
                            
                        # Determinar categoría exacta por pestaña
                        if "CONECTOR" in sheet_upper: cat = "Conectores"
                        elif "TROMPO" in sheet_upper: cat = "Trompos difusores"
                        elif "COMBINAC" in sheet_upper: cat = "Combinaciones"
                        elif "VARIAS" in sheet_upper: cat = "Herramientas varias"
                        elif "PESCA" in sheet_upper: cat = "Herramientas de pesca"
                        elif "MOLINO" in sheet_upper or "ZAPATA" in sheet_upper: cat = "Molinos y zapatas"
                        elif "CENTRADOR" in sheet_upper or "CORTA" in sheet_upper: cat = "Centradores y cortatubos"
                        elif "MOTOR" in sheet_upper: cat = "Motores"
                        elif "MARTILLO" in sheet_upper: cat = "Martillos de pesca"
                        else: cat = sheet.strip()

                        # Leer desde la Fila 4 de Excel (skiprows=3) donde están "No SERIE" y "HERRAMIENTA"
                        df_sheet = pd.read_excel(archivo_subido, sheet_name=sheet, skiprows=3)
                        
                        # Limpiar espacios en nombres de columnas
                        df_sheet.columns = [str(c).strip() for c in df_sheet.columns]
                        
                        # Buscar las columnas A y B sin importar diferencias de mayúsculas/minúsculas
                        col_s = [c for c in df_sheet.columns if "SERIE" in c.upper() or "NO." in c.upper()]
                        col_h = [c for c in df_sheet.columns if "HERRAMIENTA" in c.upper() or "DESCRIPCION" in c.upper()]

                        if col_s and col_h:
                            col_serie_name = col_s[0]
                            col_herram_name = col_h[0]
                            
                            df_clean = df_sheet.dropna(subset=[col_serie_name])
                            conteo_hoja = 0
                            
                            for _, row in df_clean.iterrows():
                                serie = str(row[col_serie_name]).strip()
                                herramienta = str(row[col_herram_name]).strip()
                                
                                # Omitir subtítulos de sistemas o celdas nulas
                                if not serie or serie.upper() in ["NAN", "NONE", "N/A", ""] or "SISTEMA" in serie.upper() or len(serie) < 2:
                                    continue
                                if not herramienta or herramienta.upper() in ["NAN", "NONE", "N/A", ""]:
                                    continue

                                cursor.execute('''
                                    INSERT OR REPLACE INTO inventario (id, descripcion, cantidad, ubicacion, categoria, horas_uso, stock) 
                                    VALUES (?, ?, 1, 'Taller Principal', ?, 0.0, 1)
                                ''', (serie, herramienta, cat))
                                
                                conteo_hoja += 1
                                piezas_cargadas += 1

                            resumen_hojas.append(f"🟢 **Pestaña '{sheet}'**: **{conteo_hoja}** herramientas cargadas ({cat}).")
                        else:
                            resumen_hojas.append(f"⚠️ **Pestaña '{sheet}'**: No se encontraron las columnas 'No SERIE' y 'HERRAMIENTA' en la fila 4.")

                    conn.commit()

                st.success(f"🎉 ¡Proceso Exitoso! Se registraron correctamente **{piezas_cargadas}** herramientas en el catálogo.")
                
                with st.expander("📋 Ver Desglose por Categoría", expanded=True):
                    for msg in resumen_hojas:
                        st.markdown(msg)

            except Exception as e:
                st.error(f"❌ Error al procesar el archivo Excel: {e}")

    # ---------------------------------------------------------
    # PESTAÑA 2: REGULARIZACIÓN DE DATOS Y GENERADOR DE QR
    # ---------------------------------------------------------
    with tab_reg:
        st.markdown("#### 🛠️ Regularizar Estatus de Herramientas en Campo y Generar QR")
        try:
            with conectar_db() as conn:
                df_inv_reg = pd.read_sql_query("SELECT id, descripcion, ubicacion, stock, COALESCE(horas_uso, 0.0) AS horas_uso FROM inventario", conn)
        except Exception:
            df_inv_reg = pd.DataFrame()
            
        if df_inv_reg.empty:
            st.info("Aún no hay herramientas registradas en la base de datos.")
        else:
            opciones_reg = [f"{row['id']} - {row['descripcion']}" for _, row in df_inv_reg.iterrows()]
            pieza_sel_reg = st.selectbox("Seleccione el No. de Serie de la herramienta:", opciones_reg)
            serie_reg = pieza_sel_reg.split(" - ")[0]
            
            info_pieza = df_inv_reg[df_inv_reg["id"] == serie_reg].iloc[0]
            
            col_r1, col_r2 = st.columns(2)
            
            with col_r1:
                st.markdown("##### **1. Actualizar Datos Iniciales / Reales**")
                
                stock_val = info_pieza['stock'] if pd.notnull(info_pieza['stock']) else 1
                hrs_val = float(info_pieza['horas_uso']) if pd.notnull(info_pieza['horas_uso']) else 0.0
                
                estado_fisico = st.radio("Ubicación Operativa Actual:", ["En Taller Principal", "En Pozo / Trabajo Exterior"], 
                                         index=0 if stock_val == 1 else 1)
                
                if estado_fisico == "En Taller Principal":
                    nueva_ubicacion = "Taller Principal"
                    nuevo_stock = 1
                else:
                    pozo_actual = st.text_input("Pozo / Campo donde se encuentra instalada:", value="POZO: 910 (5 PRESIDENTES)")
                    nueva_ubicacion = pozo_actual.strip()
                    nuevo_stock = 0
                    
                nuevas_hrs = st.number_input("Horas de Uso Acumuladas Previas (Históricas):", min_value=0.0, step=0.5, value=hrs_val)
                
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
                
                qr = qrcode.QRCode(version=1, box_size=8, border=2)
                qr.add_data(serie_reg)
                qr.make(fit=True)
                img_qr = qr.make_image(fill_color="#0f2a4a", back_color="white")
                
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
    # PESTAÑA 3: GESTIÓN DE BAJAS
    # ---------------------------------------------------------
    with tab_bajas:
        st.markdown("#### 🗑️ Dar de Baja Herramienta del Inventario")
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
                usuario_admin = st.text_input("👤 Nombre de Usuario / Ingeniero que autoriza la baja:", placeholder="Ej. Ing. David").strip()
            with c_u2:
                opciones_baja = [f"{row['id']} - {row['descripcion']} ({row['categoria']})" for _, row in df_piezas_activas.iterrows()]
                pieza_a_borrar = st.selectbox("🔧 Seleccione la herramienta a procesar:", opciones_baja)
            
            serie_baja = pieza_a_borrar.split(" - ")[0]
            motivo_baja = st.text_input("📝 Motivo técnico de la baja:", value="Vida útil finalizada").strip()
            
            col_b1, col_b2 = st.columns(2)
            fecha_hora_actual = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            with col_b1:
                if st.button("⚠️ Marcar como 'DADA DE BAJA'", use_container_width=True):
                    if not usuario_admin or not motivo_baja:
                        st.error("⛔ Complete el usuario y motivo técnico.")
                    else:
                        registro_auditoria = f"BAJA: {motivo_baja} | Autorizó: {usuario_admin} ({fecha_hora_actual})"
                        with conectar_db() as conn:
                            cursor = conn.cursor()
                            cursor.execute("UPDATE inventario SET ubicacion = ?, stock = 0 WHERE id = ?", (registro_auditoria, serie_baja))
                            conn.commit()
                        st.warning(f"⚠️ Herramienta {serie_baja} dada de baja.")
                        st.rerun()

            with col_b2:
                if st.button("🚨 ELIMINAR DEFINITIVAMENTE", type="primary", use_container_width=True):
                    if not usuario_admin:
                        st.error("⛔ Ingrese usuario para confirmar.")
                    else:
                        with conectar_db() as conn:
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM inventario WHERE id = ?", (serie_baja,))
                            conn.commit()
                        st.success(f"🗑️ Herramienta {serie_baja} eliminada.")
                        st.rerun()

    # ---------------------------------------------------------
    # PESTAÑA 4: RESPALDOS Y DESCARGA DE BD
    # ---------------------------------------------------------
    with tab_respaldos:
        st.markdown("#### 💾 Respaldos y Copias de Seguridad")
        col_res1, col_res2 = st.columns(2)
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_file = os.path.join(base_dir, "inventario_thrutubing.db")
        
        with col_res1:
            st.markdown("##### 📦 Copia de Seguridad Base de Datos (.db)")
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
                st.warning("⚠️ No se encontró la base de datos.")

        with col_res2:
            st.markdown("##### 📊 Exportar a Excel (.xlsx)")
            if st.button("📊 Generar Excel de Inventario", use_container_width=True):
                try:
                    with conectar_db() as conn:
                        df_inv = pd.read_sql_query("SELECT * FROM inventario", conn)
                    excel_out = f"Inventario_Maestro_Mendoza_{datetime.now().strftime('%Y%m%d')}.xlsx"
                    df_inv.to_excel(excel_out, index=False)
                    with open(excel_out, "rb") as f_ex:
                        st.download_button(
                            label="📥 Descargar Reporte Excel",
                            data=f_ex,
                            file_name=excel_out,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                except Exception as e:
                    st.error(f"❌ Error al exportar: {e}")

elif clave_acceso != "":
    st.error("❌ Clave de acceso incorrecta.")
