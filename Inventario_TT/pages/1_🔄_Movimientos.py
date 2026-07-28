import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import io
import os

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

st.set_page_config(page_title="MSH-TT-FOR-001 - Salida de Herramientas", layout="wide")

def conectar_db(): 
    return sqlite3.connect('inventario_thrutubing.db')

with conectar_db() as conn:
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vales_salida (
            id_vale INTEGER PRIMARY KEY AUTOINCREMENT,
            folio TEXT UNIQUE,
            fecha TEXT,
            cliente TEXT,
            campo TEXT,
            pozo TEXT,
            ingeniero TEXT
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

# --- GENERADOR DE PDF CON FIRMAS AL PIE Y ENCABEZADO ALINEADO ---
def generar_pdf_oficial_mendoza(folio, cliente, depto, realiza_sol, campo, pozo, distrito, cotizacion, lugar_salida, fecha_doc, solicita_nom, revisa_nom, autoriza_nom, df_carrito):
    buffer = io.BytesIO()
    # Ancho total disponible en carta con estos márgenes = 612 - 50 = 562 pt
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=25, leftMargin=25, topMargin=25, bottomMargin=25)
    story = []
    styles = getSampleStyleSheet()

    # Estilos de Texto
    style_hdr_title = ParagraphStyle('HdrTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, leading=9, alignment=1, textColor=colors.white)
    style_hdr_val = ParagraphStyle('HdrVal', parent=styles['Normal'], fontName='Helvetica', fontSize=8, leading=9, alignment=1)
    
    style_tbl_head = ParagraphStyle('TblHead', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, leading=9, alignment=1, textColor=colors.white)
    style_tbl_cell = ParagraphStyle('TblCell', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, leading=10, alignment=0)
    style_tbl_center = ParagraphStyle('TblCenter', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, leading=10, alignment=1)

    AZUL_MARINO = colors.HexColor("#0f2a4a")
    AZUL_CLARO = colors.HexColor("#adcbe3")

    # 1. ENCABEZADO SUPERIOR (Ancho exacto alineado a 550 pt)
    ruta_logo = "logo_mendoza.png" if os.path.exists("logo_mendoza.png") else "mendozalogo (1).png"
    
    tabla_top_roles = [
        [Paragraph("<b>ELABORADO POR:</b>", style_tbl_center), Paragraph("<b>REVISADO POR:</b>", style_tbl_center), Paragraph("<b>APROBADO POR:</b>", style_tbl_center)],
        [Paragraph("ING. DE CAMPO", style_tbl_center), Paragraph("COORDINADOR DE OPERACIONES", style_tbl_center), Paragraph("DIRECCIÓN GENERAL", style_tbl_center)]
    ]
    t_top = Table(tabla_top_roles, colWidths=[150, 160, 160])
    t_top.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('BACKGROUND', (0,0), (-1,0), AZUL_MARINO),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    
    if os.path.exists(ruta_logo):
        img_logo = Image(ruta_logo)
        img_logo.drawWidth = 70
        img_logo.drawHeight = 35
        t_encabezado_principal = Table([[img_logo, t_top]], colWidths=[80, 470])
        t_encabezado_principal.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(t_encabezado_principal)
    else:
        story.append(t_top)
        
    story.append(Spacer(1, 4))

    # 2. TÍTULO OPERACIONES THRU TUBING
    t_banner = Table([[Paragraph("<b>OPERACIONES THRU TUBING</b>", ParagraphStyle('Banner', fontName='Helvetica-Bold', fontSize=10, alignment=1, textColor=AZUL_MARINO))]], colWidths=[550])
    t_banner.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), AZUL_CLARO),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_banner)

    # 3. BLOQUE DE DATOS DE CAMPO
    datos_operacion = [
        [Paragraph("CLIENTE:", style_hdr_title), Paragraph("DEPARTAMENTO SOLICITANTE:", style_hdr_title), Paragraph("REALIZA SOLICITUD:", style_hdr_title)],
        [Paragraph(str(cliente), style_hdr_val), Paragraph(str(depto), style_hdr_val), Paragraph(str(realiza_sol), style_hdr_val)],
        [Paragraph("CAMPO:", style_hdr_title), Paragraph("NUM. DE POZO:", style_hdr_title), Paragraph("DISTRITO:", style_hdr_title), Paragraph("No. DE COTIZACIÓN:", style_hdr_title), Paragraph("LUGAR DE SALIDA:", style_hdr_title), Paragraph("FECHA:", style_hdr_title)],
        [Paragraph(str(campo), style_hdr_val), Paragraph(str(pozo), style_hdr_val), Paragraph(str(distrito), style_hdr_val), Paragraph(str(cotizacion), style_hdr_val), Paragraph(str(lugar_salida), style_hdr_val), Paragraph(str(fecha_doc), style_hdr_val)]
    ]
    
    t_datos = Table(datos_operacion, colWidths=[100, 100, 100, 80, 90, 80])
    t_datos.setStyle(TableStyle([
        ('SPAN', (0,0), (0,0)), ('SPAN', (1,0), (1,0)), ('SPAN', (2,0), (5,0)),
        ('SPAN', (0,1), (0,1)), ('SPAN', (1,1), (1,1)), ('SPAN', (2,1), (5,1)),
        ('BACKGROUND', (0,0), (-1,0), AZUL_MARINO),
        ('BACKGROUND', (0,2), (-1,2), AZUL_MARINO),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_datos)
    story.append(Spacer(1, 6))

    # 4. TABLA DE PIEZAS SOLICITADAS
    tabla_piezas_data = [[
        Paragraph("PDA", style_tbl_head),
        Paragraph("No. DE SERIE", style_tbl_head),
        Paragraph("DESCRIPCIÓN DE HERRAMIENTA", style_tbl_head),
        Paragraph("DESTINO", style_tbl_head)
    ]]

    destino_str = f"5P {pozo}" if "5" in str(campo) else f"{campo} {pozo}"
    
    for idx, row in df_carrito.iterrows():
        tabla_piezas_data.append([
            Paragraph(str(idx + 1), style_tbl_center),
            Paragraph(str(row["No SERIE"]), style_tbl_cell),
            Paragraph(str(row["HERRAMIENTA"]), style_tbl_cell),
            Paragraph(destino_str, style_tbl_center)
        ])

    t_piezas = Table(tabla_piezas_data, colWidths=[35, 115, 320, 80])
    t_piezas.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), AZUL_MARINO),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_piezas)

    # 5. CÁLCULO DE ESPACIO PARA EMPUJAR LAS FIRMAS HASTA ABAJO (AL PIE DE LA PÁGINA)
    num_filas_piezas = len(df_carrito)
    # Altura estándar de la hoja = 792 pt. Le restamos los elementos superiores y el cuadro de firmas
    espacio_firmas_pie = max(20, 480 - (num_filas_piezas * 22))
    story.append(Spacer(1, espacio_firmas_pie))

    # BLOQUE INFERIOR DE RESPONSABLES Y FIRMAS
    firmas_data = [
        [Paragraph("SOLICITA SALIDA:", style_hdr_title), Paragraph("REVISA HERRAMIENTA:", style_hdr_title), Paragraph("AUTORIZA SALIDA:", style_hdr_title)],
        [Paragraph(f"<b>Nombre:</b> {solicita_nom}", style_tbl_cell), Paragraph(f"<b>Nombre:</b> {revisa_nom}", style_tbl_cell), Paragraph(f"<b>Nombre:</b> {autoriza_nom}", style_tbl_cell)],
        ["\n\n___________________________", "\n\n___________________________", "\n\n___________________________"],
        [Paragraph("FIRMA:", style_tbl_center), Paragraph("FIRMA:", style_tbl_center), Paragraph("FIRMA:", style_tbl_center)]
    ]
    t_firmas = Table(firmas_data, colWidths=[183, 184, 183])
    t_firmas.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), AZUL_MARINO),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_firmas)

    doc.build(story)
    buffer.seek(0)
    return buffer

# --- INTERFAZ STREAMLIT ---
st.title("Mendoza Servicios e Herramientas")
st.subheader("Formato: MSH-TT-FOR-001 — Salida de Herramientas (Despacho a Pozo)")
st.markdown("---")

with conectar_db() as conn:
    df_inv = pd.read_sql_query("SELECT id AS [No SERIE], descripcion AS [HERRAMIENTA], stock AS [STOCK] FROM inventario WHERE stock > 0", conn)

if df_inv.empty:
    st.info("No hay herramientas con existencias disponibles en el taller para generar una salida.")
else:
    st.markdown("#### 📝 Encabezado del Formato Oficial Mendoza")
    
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        folio_doc = st.text_input("NÚMERO DE FOLIO:", value=f"MSH-TT-FOR-001-{datetime.now().strftime('%Y%m%d-%H%M')}")
        cliente = st.text_input("CLIENTE:", value="SEPEC")
        campo = st.text_input("CAMPO:", value="5 PRESIDENTES")
        solicita_nom = st.text_input("SOLICITA SALIDA (NOMBRE):", value="Arcenio Jimenez Morgan")
    with col_b:
        depto = st.text_input("DEPARTAMENTO SOLICITANTE:", value="TUBERIA FLEXIBLE")
        pozo = st.text_input("NUM. DE POZO:", value="910")
        distrito = st.text_input("DISTRITO:", value="5 PRESIDENTES")
        revisa_nom = st.text_input("REVISA HERRAMIENTA (NOMBRE):", value="Alfredo Mosqueda Torres")
    with col_c:
        realiza_sol = st.text_input("REALIZA SOLICITUD:", value="DAVID REYES URESTI")
        cotizacion = st.text_input("NO. DE COTIZACIÓN:", value="N/A")
        lugar_salida = st.text_input("LUGAR DE SALIDA:", value="BASE MENDOZA")
        autoriza_nom = st.text_input("AUTORIZA SALIDA (NOMBRE):", value="Olimpia Roque Priego")
        fecha_doc = st.date_input("FECHA DE EMISIÓN:", value=datetime.today())

    st.markdown("---")
    st.markdown("#### 🛠️ Selección de Herramientas para la Sarta")

    if "carrito_salida" not in st.session_state:
        st.session_state.carrito_salida = []

    lista_opciones = [f"{row['No SERIE']} - {row['HERRAMIENTA']} (Disponibles: {row['STOCK']})" for _, row in df_inv.iterrows()]
    
    col_sel, col_btn = st.columns([3, 1])
    with col_sel:
        herramienta_sel = st.selectbox("Buscar y agregar herramienta por No. de Serie:", ["-- Selecciona una pieza --"] + lista_opciones)
    with col_btn:
        st.write(" ") 
        st.write(" ") 
        if st.button("➕ Añadir a la Lista", use_container_width=True):
            if herramienta_sel != "-- Selecciona una pieza --":
                id_ext = herramienta_sel.split(" - ")[0]
                if not any(item['No SERIE'] == id_ext for item in st.session_state.carrito_salida):
                    pieza_info = df_inv[df_inv["No SERIE"] == id_ext].iloc[0]
                    st.session_state.carrito_salida.append({
                        "No SERIE": pieza_info["No SERIE"],
                        "HERRAMIENTA": pieza_info["HERRAMIENTA"]
                    })
                else:
                    st.warning("Esta herramienta ya está en la lista.")

    if st.session_state.carrito_salida:
        st.markdown("##### **Vista Previa de Herramientas Agregadas**")
        df_carrito = pd.DataFrame(st.session_state.carrito_salida)
        df_carrito.insert(0, 'PDA', range(1, len(df_carrito) + 1))
        st.dataframe(df_carrito, use_container_width=True, hide_index=True)
        
        if st.button("🗑️ Limpiar Lista", type="secondary"):
            st.session_state.carrito_salida = []
            st.session_state.pdf_salida_generado = None
            st.rerun()

        st.markdown("---")
        
        if st.button("🚀 Procesar Despacho y Generar Formato Oficial Mendoza PDF", type="primary", use_container_width=True):
            try:
                fecha_hora_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with conectar_db() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO vales_salida (folio, fecha, cliente, campo, pozo, ingeniero)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (folio_doc.strip(), str(fecha_doc), cliente.strip(), campo.strip(), pozo.strip(), realiza_sol.strip()))
                    
                    for item in st.session_state.carrito_salida:
                        cursor.execute("SELECT stock FROM inventario WHERE id = ?", (item["No SERIE"],))
                        stock_actual = cursor.fetchone()[0]
                        nuevo_stock = stock_actual - 1
                        
                        ubicacion_pozo = f"POZO: {pozo} ({campo}) | Cliente: {cliente}"
                        cursor.execute("UPDATE inventario SET stock = ?, ubicacion = ? WHERE id = ?", (nuevo_stock, ubicacion_pozo, item["No SERIE"]))
                        
                        obs_detalle = f"Salida Folio: {folio_doc}. Pozo: {pozo}. Campo: {campo}."
                        cursor.execute('''
                            INSERT INTO historial (fecha_hora, id_pieza, tipo_movimiento, cantidad, operador, observaciones)
                            VALUES (?, ?, 'Salida (Envío a Pozo / Mantenimiento exterior)', 1, ?, ?)
                        ''', (fecha_hora_actual, item["No SERIE"], realiza_sol.strip(), obs_detalle))
                        
                    conn.commit()
                
                st.success(f"🎉 ¡Éxito! El formato oficial {folio_doc} ha sido registrado.")
                
                fecha_str_fmt = fecha_doc.strftime("%d-%b-%y")
                pdf_bytes = generar_pdf_oficial_mendoza(
                    folio_doc.strip(), cliente.strip(), depto.strip(), realiza_sol.strip(),
                    campo.strip(), pozo.strip(), distrito.strip(), cotizacion.strip(), lugar_salida.strip(),
                    fecha_str_fmt, solicita_nom.strip(), revisa_nom.strip(), autoriza_nom.strip(), df_carrito
                )
                
                st.session_state.pdf_salida_generado = pdf_bytes
                st.session_state.pdf_salida_nombre = f"FORMATO_OFICIAL_{folio_doc.strip()}.pdf"
                
            except sqlite3.IntegrityError:
                st.error(f"❌ Error: El folio '{folio_doc}' ya existe. Usa un folio único.")
            except Exception as e:
                st.error(f"❌ Error inesperado: {e}")

        if "pdf_salida_generado" in st.session_state and st.session_state.pdf_salida_generado:
            st.markdown("### 📄 Formato Oficial Imprimible Generado")
            st.download_button(
                label="📥 DESCARGAR FORMATO MENDOZA MSH-TT-FOR-001 (PDF)",
                data=st.session_state.pdf_salida_generado,
                file_name=st.session_state.pdf_salida_nombre,
                mime="application/pdf",
                use_container_width=True
            )
