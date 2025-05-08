import streamlit as st
import os
import pandas as pd
from pdf2image import convert_from_path
import pytesseract
import re
import tempfile
import zipfile

st.set_page_config(page_title="Extractor de Facturas", layout="centered")
st.title("🧾 Extractor de Datos desde Facturas en PDF")

st.write("Sube un archivo ZIP que contenga facturas en PDF. El sistema aplicará OCR para extraer: proveedor, NIT, fecha de emisión y total a pagar.")

uploaded_zip = st.file_uploader("Sube un archivo ZIP", type="zip")

if uploaded_zip:
    if "nombre_zip" not in st.session_state or st.session_state["nombre_zip"] != uploaded_zip.name:
        st.session_state["nombre_zip"] = uploaded_zip.name
        st.session_state.pop("df_resultado", None)

def extraer_campos_factura(texto):
    texto = re.sub(r'[ \t]+', ' ', texto)
    texto = re.sub(r'\n+', '\n', texto)

    proveedor = (
        re.search(r'Exportador\s+\d+\s*-\s*(.+)', texto, re.IGNORECASE) or
        re.search(r'Proveedor\s*[:\-]?\s*(.+)', texto, re.IGNORECASE) or
        re.search(r'Nombre\s*[:\-]?\s*([A-ZÁÉÍÓÚÑ ]{5,})\s*NIT', texto, re.IGNORECASE) or
        re.search(r'Name\s*[:\-]?\s*([A-Z ]+)', texto, re.IGNORECASE)
    )

    nit = (
        re.search(r'NIT[:\-]?\s*([0-9\-\.]{7,20})', texto, re.IGNORECASE) or
        re.search(r'Document.*[:\-]?\s*([0-9\-\.]{7,20})', texto, re.IGNORECASE) or
        re.search(r'\b(\d{7,14}[-]?\d?)\b', texto)
    )

    fecha = (
        re.search(r'Fecha\s+de\s+Liquidaci[oó]n[:\-]?\s*(\d{1,2}\s*/\s*\d{1,2}\s*/\s*\d{4})', texto, re.IGNORECASE) or
        re.search(r'Fecha[:\-]?\s*(\d{1,2}/\d{1,2}/\d{4})', texto) or
        re.search(r'Date[:\-]?\s*(\d{1,2}/\d{1,2}/\d{4})', texto, re.IGNORECASE)
    )

    valor_total = (
        re.search(r'Total\s+a\s+Pagar[:\-]?\s*([0-9\.,]+)', texto, re.IGNORECASE) or
        re.search(r'Valor\s+Total\s+(?:CPT|EXW|FOB)?[:\-]?\s*([0-9\.,]+)', texto, re.IGNORECASE) or
        re.search(r'Total\s+Amount[:\-]?\s*([0-9\.,]+)', texto, re.IGNORECASE) or
        re.search(r'Montant\s+Total[:\-]?\s*([0-9\.,]+)', texto, re.IGNORECASE)
    )

    return {
        "proveedor": proveedor.group(1).strip() if proveedor else "",
        "nit": nit.group(1).strip() if nit else "",
        "fecha": fecha.group(1).replace(" ", "") if fecha else "",
        "valor_total": valor_total.group(1).strip() if valor_total else ""
    }

if uploaded_zip and "df_resultado" not in st.session_state:
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, "facturas.zip")
        with open(zip_path, "wb") as f:
            f.write(uploaded_zip.read())

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(tmpdir)

        pdf_files = []
        for root, _, files in os.walk(tmpdir):
            for f in files:
                if f.lower().endswith(".pdf"):
                    pdf_files.append(os.path.join(root, f))

        st.write("Archivos PDF detectados:", len(pdf_files))
        datos_facturas = []
        progress = st.progress(0)

        for i, ruta_pdf in enumerate(pdf_files):
            nombre_archivo = os.path.basename(ruta_pdf)
            try:
                imagenes = convert_from_path(ruta_pdf, first_page=1, last_page=1)
                pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"
                texto_ocr = pytesseract.image_to_string(imagenes[0], lang='spa')
                datos = extraer_campos_factura(texto_ocr)
                datos["archivo"] = nombre_archivo
                datos_facturas.append(datos)
            except Exception as e:
                st.error(f"❌ Error procesando {nombre_archivo}: {e}")
            progress.progress((i + 1) / len(pdf_files))

        df_resultado = pd.DataFrame(datos_facturas)
        st.session_state["df_resultado"] = df_resultado

if "df_resultado" in st.session_state:
    st.success("Extracción completada. Descarga el archivo:")
    st.download_button(
        label="📥 Descargar Excel",
        data=st.session_state["df_resultado"].to_csv(index=False, encoding="utf-8-sig"),
        file_name="facturas_extraidas.csv",
        mime="text/csv"
    )
