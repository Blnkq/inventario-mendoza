import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import io
import os

# Importaciones de ReportLab (incluyendo el motor gráfico de dibujo vectorial)
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Group

st.set_page_config(page_title="MSH-TT-FOR-004 - Diagrama BHA", layout="wide")

def conectar_db():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, 'inventario_thrutubing.db')
    return sqlite3.connect(db_path)

# --- FUNCIÓN PARA DIBUJAR EL BHA ESQUEMÁTICO EN VECTORIAL ---
def crear_esquema_vectorial_bha(df_bha):
    num_piezas = len(df_bha)
    alto_pieza = 28
    alto_total_drawing = max(120, num_piezas * alto_pieza + 40)
    
    d = Drawing(500, alto_total_drawing)
    
    # Línea de centro / Eje de la sarta (punteada)
    eje_x = 140
    d.add(Line(eje_x, 10, eje_x, alto_total_drawing - 10, strokeDashArray=[3, 3], strokeColor=colors.HexColor("#777777"), strokeWidth=1))
    
    y_actual = alto_total_drawing - 30

    for idx, row in df_bha.iterrows():
        # Representación según tipo de herramienta
        ancho_bloque = 50
        fill_color = colors.HexColor("#0f3460")
        
        tipo_lower = str(row["TIPO DE HERRAMIENTA"]).lower()
        if "motor" in tipo_lower:
            ancho_bloque = 42
            fill_color = colors.HexColor("#16213e")
        elif "molino" in tipo_lower or "zapata" in tipo_lower:
            ancho_bloque = 60
            fill_color = colors.HexColor("#e94560")
        elif "conector" in tipo_lower:
            ancho_bloque = 46
            fill_color = colors.HexColor("#533483")

        x_bloque = eje_x - (ancho_bloque / 2)
        
        # Bloque físico de la herramienta
        d.add(Rect(x_bloque, y_actual - alto_pieza + 5, ancho_bloque, alto_pieza - 5, fillColor=fill_color, strokeColor=colors.black, strokeWidth=1, rx=2, ry=2))
        
        # Rosca / Acople de unión
        d.add(Rect(eje_x - 10, y_actual - alto_pieza, 20, 5, fillColor=colors.HexColor("#cccccc"), strokeColor=colors.black, strokeWidth=0.5))

        # Texto indicador a la derecha (PDA, Tipo, Serie y OD)
        label_txt = f"PDA {row['No.']}: {row['NO. SERIE']} — {row['TIPO DE HERRAMIENTA']} (OD: {row['OD']})"
        d.add(String(eje_x + (ancho_bloque / 2) + 15, y_actual - (alto_pieza / 2) - 2, label_txt, fontName="Helvetica-Bold", fontSize=8, fillColor=colors.HexColor("#222222")))
        
        # Cota de longitud a la izquierda
        d.add(String(20, y_actual - (alto_pieza / 2) - 2, f"L: {row['LONGITUD']}", fontName="Helvetica", fontSize=8, fillColor=colors.HexColor("#555555")))

        y_actual -= alto_pieza

    return d

# --- GENERADOR DE PDF (FORMATO MSH-TT-FOR-004 CON DIAGRAMA) ---
def generar_pdf_bha(folio, cliente, campo, pozo, operador, operacion_txt, df_bha, long_total, prueba_tension, prueba_hermeticidad, pruebas_motor):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter, 
        rightMargin=30, 
        leftMargin=30, 
        topMargin=30, 
        bottomMargin=30
    )
    story = []
    styles = getSampleStyleSheet()

    style_titulo = ParagraphStyle('T1', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=12, alignment=1, textColor=colors.HexColor("#0f3460"))
    style_sub = ParagraphStyle('T2', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, alignment=1)
    style_cell = ParagraphStyle('Cell', fontName='Helvetica', fontSize=8, leading=10, alignment=1)
    style_cell_bold = ParagraphStyle('CellB', fontName='Helvetica-Bold', fontSize=8, leading=10, alignment=1)

    # 1. Encabezado
    story.append(Paragraph("MENDOZA SERVICIOS Y HERRAMIENTAS S.A. DE C.V.", style_titulo))
    story.append(Paragraph("DIVISIÓN THRU-TUBING & HERRAMIENTAS DE FONDO", style_sub))
    story.append(Paragraph("<b>FORMATO MSH-TT-FOR-004 — DIAGRAMA DE HERRAMIENTAS BHA</b>", style_sub))
    story.append(Spacer(1, 8))

    # 2. Header Datos
    datos_h = [
        [Paragraph("<b>CLIENTE:</b>", style_cell_bold), Paragraph(str(cliente), style_cell), Paragraph("<b>CAMPO / POZO:</b>", style_cell_bold), Paragraph(f"{campo} / {pozo}", style_cell)],
        [Paragraph("<b>OPERACIÓN:</b>", style_cell_bold), Paragraph(str(operacion_txt), style_cell), Paragraph("<b>FECHA:</b>", style_cell_bold), Paragraph(datetime.now().strftime("%d/%m/%Y"), style_cell)],
        [Paragraph("<b>PREPARADO POR:</b>", style_cell_bold), Paragraph(str(operador), style_cell), Paragraph("<b>FOLIO:</b>", style_cell_bold), Paragraph(str(folio), style_cell)]
    ]
    t_h = Table(datos_h, colWidths=[90, 180, 90, 190])
    t_h.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8f9fa")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cccccc")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_h)
    story.append(Spacer(1, 10))

    # 3. DIAGRAMA ESQUEMÁTICO VECTORIAL (DIBUJO AUTOMÁTICO)
    story.append(Paragraph("<b>ESQUEMA VISUAL DE LA SARTA (BHA):</b>", style_cell_bold))
    story.append(Spacer(1, 4))
    drawing_bha = crear_esquema_vectorial_bha(df_bha)
    story.append(drawing_bha)
    story.append(Spacer(1, 10))

    # 4. Tabla de Piezas del BHA
    story.append(Paragraph("<b>COMPONENETES Y DIMENSIONES DETALLADAS:</b>", style_cell_bold))
    story.append(Spacer(1, 4))

    tabla_bha = [[
        Paragraph("<b>No.</b>", style_cell_bold),
        Paragraph("<b>TIPO DE HERRAMIENTA</b>", style_cell_bold),
        Paragraph("<b>O.D.</b>", style_cell_bold),
        Paragraph("<b>I.D.</b>", style_cell_bold),
        Paragraph("<b>LONGITUD</b>", style_cell_bold),
        Paragraph("<b>CUELLO PESCA</b>", style_cell_bold),
        Paragraph("<b>CONEXIÓN</b>", style_cell_bold),
        Paragraph("<b>NO. SERIE</b>", style_cell_bold)
    ]]

    for idx, row in df_bha.iterrows():
        tabla_bha.append([
            Paragraph(str(row["No."]), style_cell),
            Paragraph(str(row["TIPO DE HERRAMIENTA"]), style_cell),
            Paragraph(str(row["OD"]), style_cell),
            Paragraph(str(row["ID"]), style_cell),
            Paragraph(str(row["LONGITUD"]), style_cell),
            Paragraph(str(row["CUELLO"]), style_cell),
            Paragraph(str(row["CONEXION"]), style_cell),
            Paragraph(str(row["NO. SERIE"]), style_cell)
        ])

    t_bha = Table(tabla_bha, colWidths=[25, 145, 45, 45, 60, 70, 80, 80])
    t_bha.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0f3460")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#0f3460")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_bha)
    story.append(Spacer(1, 6))

    # Total Longitud
    story.append(Paragraph(f"<b>LONGITUD TOTAL BHA: {long_total:.2f} MTS</b>", ParagraphStyle('LT', fontName='Helvetica-Bold', fontSize=9, alignment=2, textColor=colors.HexColor("#0f3460"))))
    story.append(Spacer(1, 8))

    # 5. Pruebas Operativas
    story.append(Paragraph("<b>PRUEBAS OPERATIVAS EN SUPERFICIE:</b>", style_cell_bold))
    story.append(Spacer(1, 4))

    p_datos = [
        [Paragraph("<b>PRUEBA DE TENSIÓN:</b>", style_cell_bold), Paragraph(f"{prueba_tension} LBS", style_cell)],
        [Paragraph("<b>PRUEBA DE HERMETICIDAD:</b>", style_cell_bold), Paragraph(f"{prueba_hermeticidad} PSI", style_cell)],
        [Paragraph("<b>PRUEBA DE MOTOR (BPM vs PSI):</b>", style_cell_bold), Paragraph(pruebas_motor, style_cell)]
    ]
    t_p = Table(p_datos, colWidths=[150, 400])
    t_p.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cccccc")),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor("#f8f9fa")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_p)
    story.append(Spacer(1, 20))

    # 6. Firmas
    firmas = [
        ["_______________________________________", "_______________________________________"],
        ["ELABORÓ (OPERADOR MENDOZA)", "REVISÓ / CLIENTE (SUPERVISOR)"],
        [Paragraph(f"<b>Ing:</b> {operador}", style_cell), Paragraph(f"<b>Cliente:</b> {cliente}", style_cell)]
    ]
    t_f = Table(firmas, colWidths=[275, 275])
    t_f.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER')]))
    story.append(t_f)

    doc.build(story)
    buffer.seek(0)
    return buffer

# --- INTERFAZ STREAMLIT ---
st.title("Mendoza Servicios e Herramientas")
st.subheader("Formato MSH-TT-FOR-004 — Diagrama de Herramientas BHA")
st.markdown("---")

# Cargar ÚNICAMENTE las herramientas que salieron a pozo (stock = 0 y fuera de Taller Principal)
with conectar_db() as conn:
    df_inv = pd.read_sql_query("""
        SELECT id AS [SERIE], descripcion AS [HERRAMIENTA], ubicacion AS [UBICACION] 
        FROM inventario 
        WHERE stock = 0 AND TRIM(ubicacion) != 'Taller Principal'
    """, conn)

st.markdown("#### 📝 Datos Generales del Pozo y Operación")
c1, c2, c3 = st.columns(3)
with c1:
    folio_bha = st.text_input("Folio BHA:", value=f"BHA-FOR004-{datetime.now().strftime('%Y%m%d-%H%M')}")
    cliente_bha = st.text_input("Cliente:", value="SEPEC")
with c2:
    campo_bha = st.text_input("Campo:", value="RIO NUEVO")
    pozo_bha = st.text_input("Num. de Pozo:", value="1051")
with c3:
    operador_bha = st.text_input("Preparado Por (Ing. Mendoza):", value="Roger Díaz Cruz")
    operacion_txt = st.text_input("Descripción de Operación:", value="Limpieza de aparejo con Motor HPHT de 2 1/8 y Molino Semicónico")

st.markdown("---")
st.markdown("#### 🧩 Ensamblado del BHA (Sarta de Fondo)")

if df_inv.empty:
    st.warning("⚠️ **No hay herramientas registradas en pozo/campo.** Primero debes registrar una salida a pozo desde el módulo **Movimientos (MSH-TT-FOR-001)** para poder armar el BHA.")
else:
    lista_series = ["-- Seleccionar --"] + [f"{row['SERIE']} - {row['HERRAMIENTA']} ({row['UBICACION']})" for _, row in df_inv.iterrows()]

    if "lista_bha" not in st.session_state:
        st.session_state.lista_bha = []

    with st.expander("➕ Agregar Componente al BHA", expanded=True):
        col_a, col_b, col_c = st.columns([2, 1, 1])
        with col_a:
            herramienta_sel = st.selectbox("Seleccionar Herramienta (Solo en Pozo):", lista_series)
            tipo_componente = st.text_input("Tipo / Descripción Técnica BHA:", placeholder="Ej. CONECTOR EZ DOBLE CUÑAS DE 2 1/8")
        with col_b:
            od_val = st.text_input("O.D. (Pulgadas):", value="2 1/8\"")
            id_val = st.text_input("I.D. (Pulgadas):", value="3/4\"")
            long_val = st.number_input("Longitud (Metros):", min_value=0.0, step=0.1, value=0.30)
        with col_c:
            cuello_val = st.text_input("Cuello de Pesca:", value="2 1/8\"")
            conexion_val = st.text_input("Conexión:", value="1 1/2\" AMT")
            
        if st.button("➕ Añadir Herramienta al Diagrama", use_container_width=True):
            if herramienta_sel != "-- Seleccionar --" and tipo_componente.strip():
                serie_ext = herramienta_sel.split(" - ")[0]
                num_item = len(st.session_state.lista_bha) + 1
                st.session_state.lista_bha.append({
                    "No.": num_item,
                    "TIPO DE HERRAMIENTA": tipo_componente.strip(),
                    "OD": od_val,
                    "ID": id_val,
                    "LONGITUD": f"{long_val:.2f} MTS",
                    "LONG_NUM": long_val,
                    "CUELLO": cuello_val,
                    "CONEXION": conexion_val,
                    "NO. SERIE": serie_ext
                })
                st.success("✅ Componente añadido.")
                st.rerun()

    # Vista previa
    if st.session_state.lista_bha:
        df_bha_preview = pd.DataFrame(st.session_state.lista_bha)
        st.markdown("##### **Sarta de Fondo Configurada:**")
        st.dataframe(df_bha_preview.drop(columns=["LONG_NUM"]), use_container_width=True, hide_index=True)

        longitud_total = sum([item["LONG_NUM"] for item in st.session_state.lista_bha])
        st.info(f"📏 **LONGITUD TOTAL DEL BHA:** `{longitud_total:.2f} Metros`")

        if st.button("🗑️ Vaciar Sarta BHA"):
            st.session_state.lista_bha = []
            st.rerun()

        st.markdown("---")
        st.markdown("#### 🧪 Registro de Pruebas en Superficie")
        p1, p2 = st.columns(2)
        with p1:
            prueba_tension = st.text_input("Prueba de Tensión (Lbs):", value="25,000")
            prueba_hermeticidad = st.text_input("Prueba de Hermeticidad (PSI):", value="5,500")
        with p2:
            prueba_motor = st.text_area("Prueba de Motor (Gasto vs Presión):", value="1 BPM - 4,600 PSI | 3/4 BPM - 3,700 PSI | 1/2 BPM - 2,500 PSI | 1/4 BPM - 1,300 PSI")

        st.markdown("---")
        if st.button("📄 Generar Formato MSH-TT-FOR-004 con Diagrama (PDF)", type="primary", use_container_width=True):
            pdf_bha = generar_pdf_bha(
                folio_bha, cliente_bha, campo_bha, pozo_bha, operador_bha, 
                operacion_txt, df_bha_preview, longitud_total, prueba_tension, 
                prueba_hermeticidad, prueba_motor
            )
            st.download_button(
                label="📥 DESCARGAR DIAGRAMA BHA (FOR-004 PDF)",
                data=pdf_bha,
                file_name=f"{folio_bha}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
