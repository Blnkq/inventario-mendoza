import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import io
import os

st.set_page_config(page_title="Bitácora Histórica", layout="wide")

def conectar_db(): 
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, 'inventario_thrutubing.db')
    return sqlite3.connect(db_path)

st.markdown("### 📋 Auditoría e Historial Analítico de Movimientos (Taller y Pozo)")
st.markdown("Registro unificado de folios oficiales de despacho (FOR-001) y retornos de herramientas (FOR-002).")

# Consulta avanzada que jala los datos reales del historial
with conectar_db() as conn:
    df_hist = pd.read_sql_query('''
        SELECT h.fecha_hora AS [FECHA/HORA], 
               h.id_pieza AS [No SERIE], 
               i.descripcion AS [HERRAMIENTA], 
               h.tipo_movimiento AS [TIPO MOVIMIENTO], 
               h.cantidad AS [CANTIDAD], 
               h.operador AS [RESPONSABLE TÉCNICO], 
               h.observaciones AS [DETALLES / OBSERVACIONES]
        FROM historial h 
        JOIN inventario i ON h.id_pieza = i.id 
        ORDER BY h.id_historial DESC
    ''', conn)

if df_hist.empty:
    st.info("No se registran movimientos (entradas o salidas) en el sistema actualmente.")
else:
    # Función visual para pintar las filas: Verde si entra herramienta, Amarillo si sale
    def colorear_movimientos(row):
        styles = [''] * len(row)
        if 'Entrada' in str(row['TIPO MOVIMIENTO']):
            # Color verde tenue para ingresos al taller
            styles[3] = 'background-color: #e6ffed; color: #00802b; font-weight: bold;'
        elif 'Salida' in str(row['TIPO MOVIMIENTO']):
            # Color amarillo/naranja tenue para despachos a pozo
            styles[3] = 'background-color: #fff9db; color: #9e7d0a; font-weight: bold;'
        return styles

    # Mostrar la tabla estilizada en pantalla
    st.dataframe(df_hist.style.apply(colorear_movimientos, axis=1), use_container_width=True, hide_index=True)
    
    # Botón para descargar el reporte a Excel para auditorías
    towrite_h = io.BytesIO()
    df_hist.to_excel(towrite_h, index=False, header=True, sheet_name='Historial_General')
    towrite_h.seek(0)
    st.download_button(
        label="📥 Descargar Libro de Auditoría General (Excel)", 
        data=towrite_h, 
        file_name=f"Auditoria_General_Mendoza_{datetime.now().strftime('%Y%m%d')}.xlsx", 
        mime="application/vnd.ms-excel"
    )
