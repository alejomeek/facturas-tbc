# Comparador de Facturas vs TBC

Aplicación web desarrollada con Streamlit para comparar facturas de proveedores contra el sistema TBC (ERP).

## Funcionalidades

- Comparación automática de facturas de proveedores vs registros en TBC
- Identificación de cambios de precio
- Detección de productos nuevos (no registrados en TBC)
- Asociación de SKUs a productos de la factura
- Generación de reporte Excel con 3 hojas de análisis

## Requisitos

- Python 3.9+
- Streamlit
- Pandas
- openpyxl

## Instalación

```bash
pip install -r requirements.txt
```

## Uso

### Ejecutar localmente

```bash
streamlit run app.py
```

### Archivos de entrada

1. **Excel Factura Proveedor** (`.xlsx` o `.xls`)
   - Debe contener las columnas: `Codigo de barras`, `Nombre producto`, `Cantidad`, `Precio unitario`

2. **CSV TBC (ERP)** (`.csv`)
   - Delimitador: `;` (punto y coma)
   - Encoding: `latin1`
   - Columnas utilizadas: `Codean`, `Codpro`, `Nompro`, `Valuni`

### Salida

Archivo Excel con 3 hojas:

1. **Cambios de Precio**: Productos con diferencias de precio entre factura y TBC
2. **Productos Nuevos**: Productos en la factura que no existen en TBC
3. **Resumen Completo**: Todos los productos con su estado (Nuevo, Sin cambios, Cambio de precio)

## Deployment

La aplicación está lista para ser desplegada en Streamlit Cloud:

1. Conectar el repositorio a Streamlit Cloud
2. Seleccionar `app.py` como archivo principal
3. La app estará disponible en línea

## Estructura del Proyecto

```
facturas-tbc/
├── app.py              # Aplicación principal
├── requirements.txt    # Dependencias
├── README.md          # Este archivo
├── CLAUDE.md          # Especificaciones técnicas
└── .gitignore         # Archivos ignorados por Git
```

## Licencia

Uso interno
