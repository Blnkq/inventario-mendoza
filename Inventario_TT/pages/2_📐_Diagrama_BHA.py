import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import io
import os

# Importaciones de ReportLab para la réplica idéntica del PDF FOR-004
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

st.set_page_config(page_title="MSH-TT-FOR-004 - Diagrama BHA", layout="wide")

def conectar_db():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, 'inventario_thrutubing.db')
    return sqlite3.connect(db_path)

# --- GENERADOR DE PDF IDÉNTICO AL FORMATO FÍSICO MSH-TT-FOR-004 ---
def generar_pdf_for004_identico(datos_header, df_bha, long_total, preparado_por, img_bytes_diagrama=None):
    buffer = io.BytesIO()
    # Márgenes reducidos para ajustar exactamente como el formato original
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter, 
        rightMargin=20, 
        leftMargin=20, 
        topMargin=20, 
        bottomMargin=20
    )
    story = []
    styles = getSampleStyleSheet()

    # Estilos exactos
    style_th_dark = ParagraphStyle('THDark', fontName='Helvetica-Bold', fontSize=7, leading=8, alignment=1, textColor=colors.white)
    style_td_norm = ParagraphStyle('TDNorm', fontName='Helvetica', fontSize=7, leading=9, alignment=1)
    style_td_left = ParagraphStyle('TDLeft', fontName='Helvetica', fontSize=7, leading=9, alignment=0)
    style_td_bold = ParagraphStyle('TDBold', fontName='Helvetica-Bold', fontSize=7, leading=9, alignment=1)

    # 1. ENCABEZADO INSTITUCIONAL DE MENDOZA
    t_header_top_data = [
        [Paragraph("<b>MENDOZA</b><br/><font size=5>Servicios y Herramientas</font>", ParagraphStyle('HLogo', fontName='Helvetica-Bold', fontSize=10, alignment=1, textColor=colors.HexColor("#0f3460"))),
         Paragraph("<b>DIAGRAMA DE HERRAMIENTAS BHA</b>", ParagraphStyle('HTitle', fontName='Helvetica-Bold', fontSize=11, alignment=1, textColor=colors.HexColor("#222222")))]
    ]
    t_header_top = Table(t_header_top_data, colWidths=[150, 422])
    t_header_top.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#333333")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,0), (0,0), colors.HexColor("#f0f0f0")),
    ]))
    story.append(t_header_top)

    meta_table_data = [
        [Paragraph("NÚMERO DE DOCUMENTO", style_th_dark), Paragraph("PÁGINA", style_th_dark), Paragraph("FECHA DE EMISIÓN", style_th_dark), Paragraph("REV", style_th_dark), Paragraph("FECHA DE REVISIÓN", style_th_dark)],
        [Paragraph("MSH-TT-FOR-004", style_td_norm), Paragraph("1/1", style_td_norm), Paragraph("AGO-23", style_td_norm), Paragraph("01", style_td_norm), Paragraph("AGO-23", style_td_norm)],
        [Paragraph("ELABORADO POR:<br/>ING. DE CAMPO", style_th_dark), Paragraph("", style_th_dark), Paragraph("REVISADO POR:<br/>COORDINADOR DE OPERACIONES", style_th_dark), Paragraph("", style_th_dark), Paragraph("APROBADO POR:<br/>DIRECCIÓN GENERAL", style_th_dark)]
    ]
    t_meta = Table(meta_table_data, colWidths=[150, 80, 120, 60, 162])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#555555")),
        ('BACKGROUND', (0,2), (-1,2), colors.HexColor("#555555")),
        ('SPAN', (0,2), (1,2)),
        ('SPAN', (2,2), (3,2)),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#333333")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 4))

    # 2. CINTA DE OPERACIONES THRU TUBING
    story.append(Table([[Paragraph("<b>OPERACIONES THRU TUBING</b>", style_th_dark)]], colWidths=[572], style=[('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#444444")), ('ALIGN', (0,0), (-1,-1), 'CENTER')]))
    
    # Datos del pozo
    datos_pozo = [
        [Paragraph("CLIENTE", style_th_dark), Paragraph("DEPARTAMENTO SOLICITANTE", style_th_dark), Paragraph("CAMPO", style_th_dark), Paragraph("NÚM. DE POZO", style_th_dark)],
        [Paragraph(datos_header["cliente"], style_td_norm), Paragraph(datos_header["depto"], style_td_norm), Paragraph(datos_header["campo"], style_td_norm), Paragraph(datos_header["pozo"], style_td_norm)],
        [Paragraph("REALIZA SOLICITUD", style_th_dark), Paragraph("SUPERVISOR DE CAMPO", style_th_dark), Paragraph("NO. DE COTIZACIÓN", style_th_dark), Paragraph("FECHA", style_th_dark)],
        [Paragraph(datos_header["solicita"], style_td_norm), Paragraph(datos_header["supervisor"], style_td_norm), Paragraph(datos_header["cotizacion"], style_td_norm), Paragraph(datos_header["fecha"], style_td_norm)],
    ]
    t_pozo = Table(datos_pozo, colWidths=[143, 143, 143, 143])
    t_pozo.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#666666")),
        ('BACKGROUND', (0,2), (-1,2), colors.HexColor("#666666")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#333333")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_pozo)
    
    # Fila de Operación
    t_op = Table([
        [Paragraph("OPERACIÓN:", style_td_bold), Paragraph(datos_header["operacion"], style_td_left)]
    ], colWidths=[70, 502])
    t_op.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#333333")),
        ('BACKGROUND', (0,0), (0,0), colors.HexColor("#e0e0e0")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_op)
    story.append(Spacer(1, 4))

    # 3. TABLA PRINCIPAL BHA (CON COLUMNA DE DIAGRAMA)
    # Encabezados de la tabla
    headers_tabla = [
        Paragraph("No.", style_th_dark),
        Paragraph("DIAGRAMA", style_th_dark),
        Paragraph("TIPO DE HERRAMIENTA", style_th_dark),
        Paragraph("OD", style_th_dark),
        Paragraph("ID", style_th_dark),
        Paragraph("LONGITUD", style_th_dark),
        Paragraph("CUELLO DE PESCA", style_th_dark),
        Paragraph("CONEXIÓN", style_th_dark),
        Paragraph("NO. SERIE", style_th_dark)
    ]
    
    filas_cuerpo = [headers_tabla]
    
    # Procesar la imagen del BHA para la columna "DIAGRAMA" si existe
    img_element = ""
    if img_bytes_diagrama:
        try:
            img_io = io.BytesIO(img_bytes_diagrama)
            img_element = RLImage(img_io, width=40, height=280)
        except:
            img_element = "DIAGRAMA"

    # Si hay imagen, la ponemos en la primera fila de herramientas spans
    for idx, row in df_bha.iterrows():
        desc_completa = row["TIPO DE HERRAMIENTA"]
        if row.get("NOTAS_PRUEBAS"):
            desc_completa += f"<br/><font color='#444444'><i>{row['NOTAS_PRUEBAS']}</i></font>"

        col_diag = img_element if (idx == 0 and img_element != "") else ""

        filas_cuerpo.append([
            Paragraph(str(row["No."]), style_td_norm),
            col_diag,
            Paragraph(desc_completa, style_td_left),
            Paragraph(str(row["OD"]), style_td_norm),
            Paragraph(str(row["ID"]), style_td_norm),
            Paragraph(str(row["LONGITUD"]), style_td_norm),
            Paragraph(str(row["CUELLO"]), style_td_norm),
            Paragraph(str(row["CONEXION"]), style_td_norm),
            Paragraph(str(row["NO. SERIE"]), style_td_norm)
        ])

    # Rellenar filas vacías para mantener la estética fija del formato físico
    while len(filas_cuerpo) < 7:
        filas_cuerpo.append([Paragraph("", style_td_norm)] * 9)

    t_bha_main = Table(filas_cuerpo, colWidths=[22, 50, 180, 45, 45, 60, 80, 45, 45])
    
    # Estilos de la tabla e integración vertical de la columna Diagrama (SPAN)
    t_style = [
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#555555")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#333333")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('VALIGN', (1,1), (1,-1), 'CENTER'),
        ('ALIGN', (1,1), (1,-1), 'CENTER'),
    ]
    
    if len(filas_cuerpo) > 2 and img_bytes_diagrama:
        t_style.append(('SPAN', (1, 1), (1, len(filas_cuerpo) - 1)))

    t_bha_main.setStyle(TableStyle(t_style))
    story.append(t_bha_main)
    story.append(Spacer(1, 4))

    # 4. PIE DE PÁGINA (LONGITUD TOTAL Y FIRMAS)
    t_footer = Table([
        [Paragraph("1-BHA", style_th_dark), 
         Paragraph("LONGITUD TOTAL (mts)", style_th_dark), 
         Paragraph(f"<b>{long_total:.2f}</b>", style_td_bold), 
         Paragraph("PREPARADO POR:", style_th_dark), 
         Paragraph(preparado_por.upper(), style_td_bold)]
    ], colWidths=[40, 110, 80, 110, 232])
    t_footer.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (1,0), colors.HexColor("#555555")),
        ('BACKGROUND', (3,0), (3,0), colors.HexColor("#555555")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#333333")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_footer)

    doc.build(story)
    buffer.seek(0)
    return buffer

# --- INTERFAZ DE CAPTURA EN STREAMLIT ---
st.title("Mendoza Servicios e Herramientas")
st.subheader("Formato: MSH-TT-FOR-004 — Diagrama de Herramientas BHA")
st.markdown("---")

# Cargar herramientas fuera de taller
with conectar_db() as conn:
    df_inv = pd.read_sql_query("""
        SELECT id AS [SERIE], descripcion AS [HERRAMIENTA], ubicacion AS [UBICACION] 
        FROM inventario 
        WHERE stock = 0 AND TRIM(ubicacion) != 'Taller Principal'
    """, conn)

# 1. Datos Generales de la Ficha
st.markdown("#### 📝 Encabezado de Operaciones Thru Tubing")
c1, c2, c3, c4 = st.columns(4)
with c1:
    cliente = st.text_input("CLIENTE:", value="SEPEC")
    solicita = st.text_input("REALIZA SOLICITUD:", value="ING. DAVID REYES")
with c2:
    depto = st.text_input("DEPARTAMENTO:", value="TUBERIA FLEXIBLE")
    supervisor = st.text_input("SUPERVISOR DE CAMPO:", value="SAID RIVERA RICHA")
with c3:
    campo = st.text_input("CAMPO:", value="RIO NUEVO")
    cotizacion = st.text_input("NO. DE COTIZACIÓN:", value="N/A")
with c4:
    pozo = st.text_input("NÚM. DE POZO:", value="1051")
    fecha_doc = st.text_input("FECHA:", value=datetime.now().strftime("%d-%b-%y"))

operacion_txt = st.text_input("OPERACIÓN:", value="LIMPIEZA DE APAREJO CON MOTOR HPHT DE 2 1/8\" Y MOLINO SEMICONICO DE 2 1/4\"")

st.markdown("---")
st.markdown("#### 🖼️ Imagen del Diagrama Técnico del BHA")
uploaded_diag = st.file_uploader("Subir imagen del render / croquis del BHA (JPG o PNG):", type=["png", "jpg", "jpeg"])

st.markdown("---")
st.markdown("#### 🧩 Componentes de la Sarta BHA")

if df_inv.empty:
    st.warning("⚠️ **No hay herramientas registradas en pozo.** Primero debes registrar una salida desde el módulo Movimientos (MSH-TT-FOR-001).")
else:
    lista_series = ["-- Seleccionar --"] + [f"{row['SERIE']} - {row['HERRAMIENTA']} ({row['UBICACION']})" for _, row in df_inv.iterrows()]

    if "lista_bha" not in st.session_state:
        st.session_state.lista_bha = []

    with st.expander("➕ Añadir Herramienta a la Sarta BHA", expanded=True):
        col_a, col_b = st.columns([2, 2])
        with col_a:
            herramienta_sel = st.selectbox("Seleccionar Herramienta de Pozo:", lista_series)
            tipo_componente = st.text_input("Tipo de Herramienta:", placeholder="Ej. CONECTOR DOBLE CUÑAS DE 2 1/8 PARA TF 1 1/2\"")
            notas_pruebas = st.text_area("Pruebas / Observaciones en celda (Opcional):", placeholder="Ej. SE PROBO CON 2500 LBS DE TENSION. 5500 PSI DE HERMETICIDAD")
        with col_b:
            c_m1, c_m2 = st.columns(2)
            with c_m1:
                od_val = st.text_input("OD:", value="2 1/8\"")
                id_val = st.text_input("ID:", value="3/4\"")
                long_val = st.number_input("Longitud (m):", min_value=0.0, step=0.01, value=0.30)
            with c_m2:
                cuello_val = st.text_input("Cuello Pesca:", value="2 1/8\"")
                conexion_val = st.text_input("Conexión:", value="CAJA-PIN 1 1/2\"AMT")

        if st.button("➕ Agregar a la Tabla BHA", use_container_width=True):
            if herramienta_sel != "-- Seleccionar --" and tipo_componente.strip():
                serie_ext = herramienta_sel.split(" - ")[0]
                num_item = len(st.session_state.lista_bha) + 1
                st.session_state.lista_bha.append({
                    "No.": num_item,
                    "TIPO DE HERRAMIENTA": tipo_componente.strip(),
                    "OD": od_val,
                    "ID": id_val,
                    "LONGITUD": f"{long_val:.2f} M" if long_val >= 1 else f"{int(long_val*100)} CM",
                    "LONG_NUM": long_val,
                    "CUELLO": cuello_val,
                    "CONEXION": conexion_val,
                    "NO. SERIE": serie_ext,
                    "NOTAS_PRUEBAS": notas_pruebas.strip()
                })
                st.success("✅ Añadido a la sarta.")
                st.rerun()

    if st.session_state.lista_bha:
        df_bha_preview = pd.DataFrame(st.session_state.lista_bha)
        st.markdown("##### **Sarta de Fondo Registrada:**")
        st.dataframe(df_bha_preview.drop(columns=["LONG_NUM"]), use_container_width=True, hide_index=True)

        longitud_total = sum([item["LONG_NUM"] for item in st.session_state.lista_bha])
        st.info(f"📏 **LONGITUD TOTAL (mts):** `{longitud_total:.2f}`")

        c_p1, c_p2 = st.columns(2)
        with c_p1:
            preparado_por = st.text_input("PREPARADO POR (Nombre del Operador):", value="ROGER DIAZ CRUZ")
        with c_p2:
            st.write(" ")
            st.write(" ")
            if st.button("🗑️ Vaciar Lista", type="secondary"):
                st.session_state.lista_bha = []
                st.rerun()

        st.markdown("---")
        if st.button("📄 Generar Formato MSH-TT-FOR-004 Idéntico (PDF)", type="primary", use_container_width=True):
            datos_h = {
                "cliente": cliente, "depto": depto, "campo": campo, "pozo": pozo,
                "solicita": solicita, "supervisor": supervisor, "cotizacion": cotizacion,
                "fecha": fecha_doc, "operacion": operacion_txt
            }
            img_bytes = uploaded_diag.getvalue() if uploaded_diag else None
            
            pdf_for004 = generar_pdf_for004_identico(datos_h, df_bha_preview, longitud_total, preparado_por, img_bytes)
            
            st.download_button(
                label="📥 DESCARGAR FORMATO OFICIAL MSH-TT-FOR-004 (PDF)",
                data=pdf_for004,
                file_name=f"MSH-TT-FOR-004_{pozo}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
