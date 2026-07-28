import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import io
import os

# Importaciones de ReportLab para la remisión oficial PDF de Retorno
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

st.set_page_config(page_title="MSH-TT-FOR-002 - Retorno de Herramientas", layout="wide")

def conectar_db(): 
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, 'inventario_thrutubing.db')
    return sqlite3.connect(db_path)

# Inicializar tablas si no existen
with conectar_db() as conn:
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vales_retorno (
            id_retorno INTEGER PRIMARY KEY AUTOINCREMENT,
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

# --- FUNCIÓN GENERADORA DEL PDF OFICIAL MENDOZA (FOR-002) ---
def generar_pdf_remision_retorno(folio, cliente, campo, pozo, ingeniero, df_carrito):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter, 
        rightMargin=36, 
        leftMargin=36, 
        topMargin=36, 
        bottomMargin=36
    )
    story = []
    styles = getSampleStyleSheet()

    # Estilos de Texto
    style_titulo_empresa = ParagraphStyle(
        'TituloEmpresa',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=15,
        alignment=1,
        textColor=colors.HexColor("#0f3460")
    )
    style_subtitulo = ParagraphStyle(
        'SubTitulo',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=12,
        alignment=1,
        textColor=colors.HexColor("#333333")
    )
    style_normal = ParagraphStyle('TextoNormal', fontName='Helvetica', fontSize=9, leading=11)
    style_bold = ParagraphStyle('TextoBold', fontName='Helvetica-Bold', fontSize=9, leading=11)

    # 1. ENCABEZADO INSTITUCIONAL
    story.append(Paragraph("MENDOZA SERVICIOS Y HERRAMIENTAS S.A. DE C.V.", style_titulo_empresa))
    story.append(Paragraph("DIVISIÓN THRU-TUBING & HERRAMIENTAS DE FONDO", style_subtitulo))
    story.append(Paragraph("<b>FORMATO MSH-TT-FOR-002 — VALE DE RETORNO Y RECEPCIÓN EN TALLER</b>", style_subtitulo))
    story.append(Spacer(1, 10))

    # 2. DATOS GENERALES Y DE POZO
    fecha_actual_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    datos_header = [
        [Paragraph("<b>FOLIO RETORNO:</b>", style_bold), Paragraph(str(folio), style_normal), Paragraph("<b>FECHA EMISIÓN:</b>", style_bold), Paragraph(fecha_actual_str, style_normal)],
        [Paragraph("<b>CLIENTE:</b>", style_bold), Paragraph(str(cliente), style_normal), Paragraph("<b>CAMPO / POZO:</b>", style_bold), Paragraph(f"{campo} - {pozo}", style_normal)],
        [Paragraph("<b>RECIBIDO POR:</b>", style_bold), Paragraph(str(ingeniero), style_normal), Paragraph("<b>ESTATUS:</b>", style_bold), Paragraph("REINGRESO A TALLER", style_normal)]
    ]
    
    t_header = Table(datos_header, colWidths=[130, 160, 110, 140])
    t_header.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8f9fa")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#dcdcdc")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_header)
    story.append(Spacer(1, 12))

    # 3. TABLA DE DETALLE DE HERRAMIENTAS QUE INGRESAN
    story.append(Paragraph("<b>DETALLE DE HERRAMIENTAS QUE INGRESAN AL TALLER:</b>", style_bold))
    story.append(Spacer(1, 4))

    tabla_datos = [[
        Paragraph("<b>PDA</b>", style_bold),
        Paragraph("<b>NO. DE SERIE</b>", style_bold),
        Paragraph("<b>DESCRIPCIÓN DE LA HERRAMIENTA</b>", style_bold),
        Paragraph("<b>CANT.</b>", style_bold)
    ]]
    
    for idx, row in df_carrito.iterrows():
        tabla_datos.append([
            Paragraph(str(row["PDA"]), style_normal),
            Paragraph(str(row["No SERIE"]), style_normal),
            Paragraph(str(row["HERRAMIENTA"]), style_normal),
            Paragraph("1 PZA", style_normal)
        ])

    t_piezas = Table(tabla_datos, colWidths=[40, 130, 310, 60])
    t_piezas.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0f3460")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (3, 0), (3, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#0f3460")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_piezas)
    story.append(Spacer(1, 35))

    # 4. CUADRO DE FIRMAS
    firmas = [
        ["_______________________________________", "_______________________________________"],
        ["RECIBIÓ EN TALLER MENDOZA", "ENTREGÓ / SUPERVISOR DE CAMPO"],
        [Paragraph(f"<b>Ing:</b> {ingeniero}", style_normal), Paragraph(f"<b>Cliente:</b> {cliente}", style_normal)]
    ]
    t_firmas = Table(firmas, colWidths=[270, 270])
    t_firmas.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(t_firmas)

    doc.build(story)
    buffer.seek(0)
    return buffer

# Cargar piezas que están fuera del taller (stock = 0)
with conectar_db() as conn:
    df_inv = pd.read_sql_query("SELECT id AS [No SERIE], descripcion AS [HERRAMIENTA], stock AS [STOCK] FROM inventario WHERE stock = 0", conn)

st.title("Mendoza Servicios e Herramientas")
st.subheader("Formato: MSH-TT-FOR-002 — Retorno de Herramientas (Entrada al Taller)")
st.markdown("---")

if df_inv.empty:
    st.success("🟢 Actualmente no hay herramientas operando en pozo. Todo el catálogo se encuentra disponible en el Taller Principal.")
else:
    # 1. ENCABEZADO DEL FORMATO MSH-TT-FOR-002
    st.markdown("#### 📝 Datos Generales del Retorno / Pozo")
    with st.container():
        c1, c2, c3 = st.columns(3)
        with c1:
            folio_doc = st.text_input("NÚMERO DE DOCUMENTO (Folio Retorno):", value=f"MSH-TT-FOR-002-{datetime.now().strftime('%Y%m%d-%H%M')}")
            cliente = st.text_input("CLIENTE:", value="SEPEC")
        with c2:
            campo = st.text_input("CAMPO:", value="5 PRESIDENTES")
            pozo = st.text_input("NUM. DE POZO:", value="910")
        with c3:
            ingeniero = st.text_input("RECIBIDO POR (ING. DE TALLER):", value="Ing. David")
            fecha_hoy = st.date_input("FECHA DE RETORNO:", value=datetime.today())

    st.markdown("---")
    st.markdown("#### 📥 Selección de Herramientas que Regresan al Taller")

    # Inicializar la lista del "carrito" de retorno usando Session State
    if "carrito_retorno" not in st.session_state:
        st.session_state.carrito_retorno = []

    # Selector de piezas (Solo mostrará las que están en pozo / stock = 0)
    lista_opciones = [f"{row['No SERIE']} - {row['HERRAMIENTA']} (En Pozo)" for _, row in df_inv.iterrows()]
    
    col_sel, col_btn = st.columns([3, 1])
    with col_sel:
        herramienta_sel = st.selectbox("Buscar y agregar pieza por No. de Serie:", ["-- Selecciona una pieza --"] + lista_opciones)
    with col_btn:
        st.write(" ") 
        st.write(" ") 
        if st.button("➕ Añadir a la Lista", use_container_width=True):
            if herramienta_sel != "-- Selecciona una pieza --":
                id_ext = herramienta_sel.split(" - ")[0]
                if not any(item['No SERIE'] == id_ext for item in st.session_state.carrito_retorno):
                    pieza_info = df_inv[df_inv["No SERIE"] == id_ext].iloc[0]
                    st.session_state.carrito_retorno.append({
                        "No SERIE": pieza_info["No SERIE"],
                        "HERRAMIENTA": pieza_info["HERRAMIENTA"],
                        "CANTIDAD": 1
                    })
                else:
                    st.warning("Esta herramienta ya está en la lista de retorno.")

    # 2. TABLA DE VISTA PREVIA DEL RETORNO
    if st.session_state.carrito_retorno:
        st.markdown("##### **Lista de Herramientas que Entran (Vista Previa)**")
        df_carrito = pd.DataFrame(st.session_state.carrito_retorno)
        df_carrito.insert(0, 'PDA', range(1, len(df_carrito) + 1))
        
        st.dataframe(df_carrito, use_container_width=True, hide_index=True)
        
        if st.button("🗑️ Limpiar Lista", type="secondary"):
            st.session_state.carrito_retorno = []
            st.session_state.pdf_retorno_generado = None
            st.rerun()

        st.markdown("---")
        
        # 3. PROCESAMIENTO Y ACTUALIZACIÓN EN LOTE (SUMAR AL STOCK)
        if st.button("💾 Procesar Entrada y Aumentar Stock", type="primary", use_container_width=True):
            if not ingeniero.strip():
                st.error("❌ No se puede procesar: Debe especificar quién recibe el equipo.")
            elif not folio_doc.strip():
                st.error("❌ No se puede procesar: El número de documento es obligatorio.")
            else:
                try:
                    with conectar_db() as conn:
                        cursor = conn.cursor()
                        
                        # Guardar maestro del vale FOR-002
                        cursor.execute('''
                            INSERT INTO vales_retorno (folio, fecha, cliente, campo, pozo, ingeniero)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (folio_doc.strip(), str(fecha_hoy), cliente.strip(), campo.strip(), pozo.strip(), ingeniero.strip()))
                        
                        # Procesar lote
                        fecha_hora_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        for item in st.session_state.carrito_retorno:
                            # Reingresar a stock (1 = En Taller Principal) y actualizar ubicación
                            cursor.execute("UPDATE inventario SET stock = 1, ubicacion = 'Taller Principal' WHERE id = ?", (item["No SERIE"],))
                            
                            # Asentar en Bitácora general
                            obs_detalle = f"Retorno de Pozo Folio: {folio_doc}. Pozo: {pozo}. Campo: {campo}."
                            cursor.execute('''
                                INSERT INTO historial (fecha_hora, id_pieza, tipo_movimiento, cantidad, operador, observaciones)
                                VALUES (?, ?, 'Entrada (Retorno de Pozo / Compra)', 1, ?, ?)
                            ''', (fecha_hora_actual, item["No SERIE"], ingeniero.strip(), obs_detalle))
                            
                        conn.commit()
                        
                    st.success(f"🎉 ¡Éxito! El documento de retorno {folio_doc} ha sido registrado e ingresado al taller.")
                    
                    # Generar PDF oficial MSH-TT-FOR-002
                    pdf_bytes = generar_pdf_remision_retorno(folio_doc.strip(), cliente.strip(), campo.strip(), pozo.strip(), ingeniero.strip(), df_carrito)
                    st.session_state.pdf_retorno_generado = pdf_bytes
                    st.session_state.pdf_retorno_nombre = f"{folio_doc.strip()}.pdf"
                    
                except sqlite3.IntegrityError:
                    st.error(f"❌ Error: El folio '{folio_doc}' ya existe. Usa uno único.")
                except Exception as e:
                    st.error(f"❌ Error inesperado: {e}")

        # Botón de descarga de PDF oficial
        if "pdf_retorno_generado" in st.session_state and st.session_state.pdf_retorno_generado:
            st.markdown("### 📄 Documento Oficial de Retorno Listo")
            st.download_button(
                label="📥 DESCARGAR COMPROBANTE OFICIAL MSH-TT-FOR-002 (PDF)",
                data=st.session_state.pdf_retorno_generado,
                file_name=st.session_state.pdf_retorno_nombre,
                mime="application/pdf",
                use_container_width=True
            )
