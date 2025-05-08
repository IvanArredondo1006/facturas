# Facturas Scanner OCR

Esta aplicación permite subir un archivo `.zip` con múltiples facturas en PDF, aplicar OCR con Tesseract, extraer datos clave como:

- Nombre del proveedor/productor
- NIT o número de identificación
- Fecha de emisión o liquidación
- Total a pagar

y descargar el resultado como archivo CSV.

## Requisitos

Esta app está diseñada para ser desplegada en [Streamlit Community Cloud](https://streamlit.io/cloud) y utiliza:

- Tesseract OCR (con idioma español)
- Poppler-utils
