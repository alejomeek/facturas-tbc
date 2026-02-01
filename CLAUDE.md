# 🎯 PROYECTO: Comparador de Facturas vs TBC (ERP)

## 📋 DESCRIPCIÓN DEL PROYECTO

Crear una aplicación web con **Streamlit** que permita comparar facturas de proveedores contra el sistema TBC (ERP) para identificar:
1. Cambios de precio
2. Productos nuevos (no registrados en TBC)
3. Asociar SKUs a productos de la factura

---

## 🏗️ ARQUITECTURA

**Stack:**
- Python 3.9+
- Streamlit (para UI)
- Pandas (procesamiento de datos)
- openpyxl (manejo de Excel)

**Deployment:** Streamlit Cloud

**Repositorio:** https://github.com/alejomeek/facturas-tbc

---

## 📁 ARCHIVOS DE ENTRADA

### **1. Excel Factura Proveedor**
- **Formato:** `.xlsx` o `.xls`
- **Encoding:** Default de Excel (no especificar)
- **Columnas EXACTAS requeridas:**
  - `Codigo de barras`
  - `Nombre producto`
  - `Cantidad`
  - `Precio unitario`

**Validación:** Si falta alguna columna → mostrar error indicando cuáles columnas esperadas no se encontraron.

### **2. CSV TBC (ERP)**
- **Formato:** `.csv`
- **Delimiter:** `;` (punto y coma)
- **Encoding:** `latin1`
- **Columnas a usar:**
  - `Codean` - Código de barras (llave para matching)
  - `Codpro` - SKU del producto
  - `Nompro` - Nombre del producto
  - `Valuni` - Valor unitario (precio)

**Nota:** El CSV puede tener muchas más columnas (us01, us02, etc.), pero solo usaremos estas 4.

---

## 🔄 PROCESAMIENTO DE DATOS

### **Paso 1: Lectura de Archivos**

#### Excel Factura:
```python
import pandas as pd

# Leer Excel
data_factura = pd.read_excel(uploaded_file_factura)

# Validar columnas requeridas
required_cols = ['Codigo de barras', 'Nombre producto', 'Cantidad', 'Precio unitario']
missing_cols = [col for col in required_cols if col not in data_factura.columns]

if missing_cols:
    st.error(f"❌ El archivo no contiene las columnas esperadas.")
    st.error(f"Columnas faltantes: {', '.join(missing_cols)}")
    st.error(f"Columnas esperadas: {', '.join(required_cols)}")
    st.stop()
```

#### CSV TBC:
```python
# Leer CSV con configuración específica
data_tbc = pd.read_csv(uploaded_file_tbc, delimiter=';', encoding='latin1')

# Filtrar productos válidos (eliminar corruptos o vacíos)
data_tbc = data_tbc[
    data_tbc['Codpro'].notna() & 
    ~(data_tbc['Codpro'].isin(['', ' ']) | 
      data_tbc['Codpro'].str.contains('\x1a', na=False))
]

# Seleccionar solo columnas necesarias
data_tbc = data_tbc[['Codean', 'Codpro', 'Nompro', 'Valuni']]
```

### **Paso 2: Limpieza de Datos**

```python
# Limpieza de código de barras en Factura
data_factura['Codigo de barras'] = data_factura['Codigo de barras'].astype(str).str.strip()

# Limpieza de código de barras en TBC
data_tbc['Codean'] = data_tbc['Codean'].astype(str).str.strip()

# Limpieza de SKU en TBC
data_tbc['Codpro'] = data_tbc['Codpro'].astype(str).str.strip()
data_tbc['Codpro'] = data_tbc['Codpro'].replace('nan', pd.NA)
```

### **Paso 3: Merge de Datos**

```python
# Hacer left join: mantener todos los productos de la factura
merged = pd.merge(
    data_factura,
    data_tbc,
    left_on='Codigo de barras',
    right_on='Codean',
    how='left'
)
```

---

## 📊 GENERACIÓN DE REPORTES

El resultado será **1 archivo Excel con 3 hojas**.

### **Hoja 1: "Cambios de Precio"**

**Filtro:** Productos donde `Precio unitario` (factura) ≠ `Valuni` (TBC) Y que existan en TBC.

**Columnas:**
1. `Codigo de barras`
2. `SKU` (Codpro)
3. `Nombre producto` (de la factura)
4. `Precio Factura` (Precio unitario)
5. `Precio TBC` (Valuni)
6. `Diferencia ($)` = Precio Factura - Precio TBC
7. `Diferencia (%)` = ((Precio Factura - Precio TBC) / Precio TBC) * 100

**Criterio de cambio de precio:** Cualquier diferencia, incluso $0.01.

### **Hoja 2: "Productos Nuevos"**

**Filtro:** Productos que NO tienen match en TBC (Codean es NaN después del merge).

**Columnas:**
1. `Codigo de barras`
2. `Nombre producto`
3. `Cantidad`
4. `Precio unitario`

### **Hoja 3: "Resumen Completo"**

**Filtro:** Todos los productos de la factura.

**Columnas:**
1. `Codigo de barras`
2. `SKU` (Codpro - puede ser vacío si es nuevo)
3. `Nombre Factura` (Nombre producto)
4. `Nombre TBC` (Nompro - puede ser vacío si es nuevo)
5. `Cantidad`
6. `Precio Factura` (Precio unitario)
7. `Precio TBC` (Valuni - puede ser vacío si es nuevo)
8. `Status` - Valores posibles:
   - "Nuevo" - No existe en TBC
   - "Sin cambios" - Existe en TBC y precio es igual
   - "Cambio de precio" - Existe en TBC y precio es diferente

---

## 🎨 INTERFAZ DE USUARIO (Streamlit)

### **Layout:**

```python
import streamlit as st

st.title("🔍 Comparador Facturas vs TBC")
st.markdown("---")

# Sección de carga de archivos
st.header("📁 Cargar Archivos")

col1, col2 = st.columns(2)

with col1:
    uploaded_factura = st.file_uploader(
        "Excel Factura Proveedor",
        type=['xlsx', 'xls'],
        help="Debe contener: Codigo de barras, Nombre producto, Cantidad, Precio unitario"
    )

with col2:
    uploaded_tbc = st.file_uploader(
        "CSV TBC (ERP)",
        type=['csv'],
        help="Archivo exportado desde TBC con delimitador ';' y encoding latin1"
    )

# Botón de procesamiento
if uploaded_factura and uploaded_tbc:
    if st.button("⚙️ Procesar Archivos", type="primary"):
        # Aquí va la lógica de procesamiento
        ...

# Sección de resultados
if 'resultados' in st.session_state:
    st.markdown("---")
    st.header("📊 Resultados")
    
    # Métricas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Productos", total_productos)
    
    with col2:
        st.metric("Cambios de Precio", cambios_precio)
    
    with col3:
        st.metric("Productos Nuevos", productos_nuevos)
    
    # Botón de descarga
    st.download_button(
        label="💾 Descargar Reporte Completo",
        data=excel_bytes,
        file_name="Reporte_Factura_vs_TBC.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
```

### **Mensajes de Estado:**

```python
# Mientras procesa
with st.spinner('Procesando archivos...'):
    # procesamiento

# Éxito
st.success("✅ Procesamiento completado!")

# Error
st.error("❌ Error al procesar archivos")
```

---

## 📦 GENERACIÓN DEL EXCEL CON 3 HOJAS

```python
from io import BytesIO
import pandas as pd

# Crear BytesIO para el archivo Excel
output = BytesIO()

# Crear ExcelWriter
with pd.ExcelWriter(output, engine='openpyxl') as writer:
    # Hoja 1: Cambios de Precio
    df_cambios.to_excel(writer, sheet_name='Cambios de Precio', index=False)
    
    # Hoja 2: Productos Nuevos
    df_nuevos.to_excel(writer, sheet_name='Productos Nuevos', index=False)
    
    # Hoja 3: Resumen Completo
    df_resumen.to_excel(writer, sheet_name='Resumen Completo', index=False)

# Obtener bytes
excel_bytes = output.getvalue()
```

---

## 📋 ESTRUCTURA DE ARCHIVOS DEL PROYECTO

```
facturas-tbc/
├── app.py                  # Aplicación principal de Streamlit
├── requirements.txt        # Dependencias
├── README.md              # Documentación del proyecto
└── .gitignore             # Archivos a ignorar en Git
```

---

## 📝 REQUIREMENTS.TXT

```
streamlit
pandas
openpyxl
xlrd
```

---

## 🚀 DEPLOYMENT EN STREAMLIT CLOUD

El proyecto ya está configurado para deployment:
- Repositorio: https://github.com/alejomeek/facturas-tbc
- Archivo principal: `app.py`
- Python version: 3.9+

**Pasos después del desarrollo:**
1. Hacer commit y push al repositorio
2. Conectar Streamlit Cloud al repositorio
3. La app estará disponible en: `https://facturas-tbc.streamlit.app` (o similar)

---

## ⚠️ CONSIDERACIONES IMPORTANTES

1. **NO crear entorno virtual local** - El código debe funcionar directamente en Streamlit Cloud
2. **NO contemplar casos especiales** de duplicados o valores vacíos por ahora
3. **Limpieza de datos** debe seguir el patrón del archivo de referencia `como_lee_archivo_tbc.md`
4. **Matching exacto** entre código de barras (después de strip)
5. **Cualquier diferencia de precio** se considera cambio (incluso $0.01)

---

## 🎯 OBJETIVO FINAL

Una aplicación simple y efectiva que permita a la asistente administrativa:
1. Subir 2 archivos (Excel Factura + CSV TBC)
2. Ver métricas rápidas
3. Descargar un Excel con 3 hojas de análisis

**Sin complejidades innecesarias. Funcional y directo al punto.**

---

## 📚 REFERENCIA

El archivo `como_lee_archivo_tbc.md` muestra cómo se procesa el CSV de TBC en otro proyecto similar. Usar la misma lógica de limpieza y filtrado, pero adaptada a las columnas específicas de este proyecto (Codean, Codpro, Nompro, Valuni).

---

¡Adelante Claude Code! 🚀
