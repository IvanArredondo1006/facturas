import os
import pytesseract
from pdf2image import convert_from_path
import ollama
import tempfile
import pandas as pd
import json

# Configurar ruta de Tesseract si es necesario
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\arredondoivan\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'

def extraer_texto_ocr(pdf_path):
    imagenes = convert_from_path(pdf_path)
    texto_completo = ""
    for imagen in imagenes:
        texto = pytesseract.image_to_string(imagen, lang='spa')
        texto_completo += texto + "\n"
    return texto_completo

def extraer_datos_factura(texto_factura):
    prompt = f"""
Extrae la siguiente información de esta factura y responde en formato JSON:
- Nombre del productor
- NIT del productor
- Fecha de liquidación
- Total a pagar

Factura:
\"\"\"
{texto_factura}
\"\"\"

Solo responde el JSON, sin explicaciones.
    """
    respuesta = ollama.chat(
        model='deepseek-coder',  # o deepseek-llm, mistral, etc.
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return respuesta['message']['content']

# Ruta de la carpeta con los PDF
carpeta_pdfs = r"\\nas\compartida\Controles de inversión\PRUEBA  FACTURAS\RELACION FACTURAS REPUESTOS 9 MARZO 2024 A 4 MARZO 2025"

# Lista para guardar los resultados
datos_facturas = []

# Procesar todos los PDFs en la carpeta
for nombre_archivo in os.listdir(carpeta_pdfs):
    if nombre_archivo.lower().endswith('.pdf'):
        ruta_pdf = os.path.join(carpeta_pdfs, nombre_archivo)
        print(f"🔄 Procesando: {nombre_archivo}")
        try:
            texto = extraer_texto_ocr(ruta_pdf)
            datos_json = extraer_datos_factura(texto)
            datos = json.loads(datos_json)
            datos['Archivo'] = nombre_archivo
            datos_facturas.append(datos)
        except Exception as e:
            print(f"❌ Error procesando {nombre_archivo}: {e}")

# Crear un DataFrame y exportar a Excel
df = pd.DataFrame(datos_facturas)
df.to_excel("facturas_extraidas.xlsx", index=False)

print("✅ ¡Extracción finalizada! Revisa el archivo 'facturas_extraidas.xlsx'")
