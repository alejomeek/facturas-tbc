import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Comparador Facturas vs TBC", layout="wide")

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
        with st.spinner('Procesando archivos...'):
            try:
                # ===== PASO 1: LECTURA DE ARCHIVOS =====

                # Leer Excel Factura
                data_factura = pd.read_excel(uploaded_factura)

                # Validar columnas requeridas
                required_cols = ['Codigo de barras', 'Nombre producto', 'Cantidad', 'Precio unitario']
                missing_cols = [col for col in required_cols if col not in data_factura.columns]

                if missing_cols:
                    st.error(f"❌ El archivo no contiene las columnas esperadas.")
                    st.error(f"Columnas faltantes: {', '.join(missing_cols)}")
                    st.error(f"Columnas esperadas: {', '.join(required_cols)}")
                    st.stop()

                # Leer CSV TBC con configuración específica
                data_tbc = pd.read_csv(uploaded_tbc, delimiter=';', encoding='latin1')

                # ===== VALIDACIÓN: DETECTAR NOTACIÓN CIENTÍFICA EN EAN =====
                # Convertir a string para detectar formato científico
                codean_str = data_tbc['Codean'].astype(str)

                # Detectar si hay códigos con notación científica (E+ o e+)
                tiene_notacion_cientifica = codean_str.str.contains(r'[Ee][+-]', na=False, regex=True).any()

                if tiene_notacion_cientifica:
                    st.error("⚠️ **ALERTA: Formato Científico Detectado en Códigos de Barras**")
                    st.error("El archivo TBC contiene códigos EAN en notación científica (ej. 9,42022E+12).")
                    st.error("**Esto causará cruces incorrectos entre productos.**")
                    st.warning("**Solución:** Abrir el archivo CSV en Excel, seleccionar la columna 'Codean', cambiar formato a 'Número' (sin decimales), y guardar nuevamente.")

                    # Mostrar ejemplos de códigos problemáticos
                    ejemplos_cientificos = codean_str[codean_str.str.contains(r'[Ee][+-]', na=False, regex=True)].head(5).tolist()
                    st.error(f"Ejemplos detectados: {', '.join(ejemplos_cientificos)}")
                    st.stop()

                # Filtrar productos válidos (eliminar corruptos o vacíos)
                data_tbc = data_tbc[
                    data_tbc['Codpro'].notna() &
                    ~(data_tbc['Codpro'].isin(['', ' ']) |
                      data_tbc['Codpro'].str.contains('\x1a', na=False))
                ]

                # Seleccionar solo columnas necesarias
                data_tbc = data_tbc[['Codean', 'Codpro', 'Nompro', 'Valuni']]

                # ===== PASO 2: LIMPIEZA DE DATOS =====

                # Limpieza de código de barras en Factura
                data_factura['Codigo de barras'] = data_factura['Codigo de barras'].astype(str).str.strip()

                # Limpieza de código de barras en TBC
                data_tbc['Codean'] = data_tbc['Codean'].astype(str).str.strip()

                # Limpieza de SKU en TBC
                data_tbc['Codpro'] = data_tbc['Codpro'].astype(str).str.strip()
                data_tbc['Codpro'] = data_tbc['Codpro'].replace('nan', pd.NA)

                # ===== PASO 3: MERGE DE DATOS =====

                # Hacer left join: mantener todos los productos de la factura
                merged = pd.merge(
                    data_factura,
                    data_tbc,
                    left_on='Codigo de barras',
                    right_on='Codean',
                    how='left'
                )

                # ===== GENERACIÓN DE REPORTES =====

                # Hoja 1: Cambios de Precio
                df_cambios = merged[
                    (merged['Codean'].notna()) &  # Existe en TBC
                    (merged['Precio unitario'] != merged['Valuni'])  # Precio diferente
                ].copy()

                df_cambios = df_cambios[[
                    'Codigo de barras',
                    'Codpro',
                    'Nombre producto',
                    'Precio unitario',
                    'Valuni'
                ]].rename(columns={
                    'Codpro': 'SKU',
                    'Precio unitario': 'Precio Factura',
                    'Valuni': 'Precio TBC'
                })

                # Calcular diferencias
                df_cambios['Diferencia ($)'] = df_cambios['Precio Factura'] - df_cambios['Precio TBC']
                df_cambios['Diferencia (%)'] = ((df_cambios['Precio Factura'] - df_cambios['Precio TBC']) / df_cambios['Precio TBC']) * 100

                # Hoja 2: Productos Nuevos
                df_nuevos = merged[merged['Codean'].isna()].copy()

                df_nuevos = df_nuevos[[
                    'Codigo de barras',
                    'Nombre producto',
                    'Cantidad',
                    'Precio unitario'
                ]]

                # Hoja 3: Resumen Completo
                df_resumen = merged.copy()

                # Determinar status
                def get_status(row):
                    if pd.isna(row['Codean']):
                        return 'Nuevo'
                    elif row['Precio unitario'] != row['Valuni']:
                        return 'Cambio de precio'
                    else:
                        return 'Sin cambios'

                df_resumen['Status'] = df_resumen.apply(get_status, axis=1)

                df_resumen = df_resumen[[
                    'Codigo de barras',
                    'Codpro',
                    'Nombre producto',
                    'Nompro',
                    'Cantidad',
                    'Precio unitario',
                    'Valuni',
                    'Status'
                ]].rename(columns={
                    'Codpro': 'SKU',
                    'Nombre producto': 'Nombre Factura',
                    'Nompro': 'Nombre TBC',
                    'Precio unitario': 'Precio Factura',
                    'Valuni': 'Precio TBC'
                })

                # ===== GENERACIÓN DEL EXCEL CON 3 HOJAS =====

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

                # Guardar en session_state
                st.session_state['resultados'] = {
                    'excel_bytes': excel_bytes,
                    'total_productos': len(data_factura),
                    'cambios_precio': len(df_cambios),
                    'productos_nuevos': len(df_nuevos)
                }

                st.success("✅ Procesamiento completado!")

            except Exception as e:
                st.error("❌ Error al procesar archivos")
                st.error(f"Detalle del error: {str(e)}")

# Sección de resultados
if 'resultados' in st.session_state:
    st.markdown("---")
    st.header("📊 Resultados")

    # Métricas
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Productos", st.session_state['resultados']['total_productos'])

    with col2:
        st.metric("Cambios de Precio", st.session_state['resultados']['cambios_precio'])

    with col3:
        st.metric("Productos Nuevos", st.session_state['resultados']['productos_nuevos'])

    # Botón de descarga
    st.download_button(
        label="💾 Descargar Reporte Completo",
        data=st.session_state['resultados']['excel_bytes'],
        file_name="Reporte_Factura_vs_TBC.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
