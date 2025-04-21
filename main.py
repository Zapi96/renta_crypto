# main.py

import streamlit as st
from data_loader import load_multiple_csvs, preprocess_df
from processor import calcular_plusvalias_fifo
from visualizer import mostrar_resumen
from tax_utils import calcular_impuestos, resumen_fiscal, filtrar_plusvalias_sobre_retiradas
from datetime import datetime
import os
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder
import pandas as pd



st.set_page_config(page_title="🪙 Crypto Tax Analyzer - España", layout="wide")
st.title("🪙 Crypto Tax Analyzer - Declaración de la Renta (España)")

uploaded_files = st.file_uploader(
    "Sube tus CSVs de Bitpanda",
    type="csv",
    accept_multiple_files=True
)

if uploaded_files:
    # Crear carpeta 'data' y subcarpeta con la fecha actual
    today = datetime.now().strftime("%Y-%m-%d")
    data_dir = os.path.join("data", today)
    os.makedirs(data_dir, exist_ok=True)

    # Guardar archivos en la carpeta correspondiente
    temp_paths = []
    for file in uploaded_files:
        file_path = os.path.join(data_dir, file.name)
        with open(file_path, "wb") as f:
            f.write(file.getbuffer())
            temp_paths.append(file_path)

    # Procesar datos
    df_raw = load_multiple_csvs(temp_paths)
    df = preprocess_df(df_raw)
    df = resumen_fiscal(df)
    
    # Selección del año fiscal
    st.subheader("📆 Año Fiscal")
    año_fiscal = st.selectbox("Selecciona el año fiscal a declarar", [2022, 2023, 2024, 2025], index=2)
    fecha_corte = datetime(año_fiscal, 12, 31).date()

    # Asegurar que la columna Date es tipo datetime
    df = df[df["Date"] <= fecha_corte]

    st.success(f"{len(df)} transacciones cargadas.")
    st.subheader("📋 Vista preliminar de tus transacciones")
    # Agregar filtros para cada columna utilizando Ag-Grid

    # Configurar opciones de la tabla interactiva
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(editable=True, filter=True, sortable=True, resizable=True)
    gb.configure_side_bar()  # Barra lateral para filtros avanzados

    grid_options = gb.build()

    # Mostrar tabla interactiva
    grid_response = AgGrid(
        df,
        gridOptions=grid_options,
        enable_enterprise_modules=True,
        theme="streamlit",  # Cambiar tema si es necesario
        height=400,
        fit_columns_on_grid_load=True
    )
    
    # Obtener datos filtrados desde la tabla interactiva
    filtered_df = pd.DataFrame(grid_response["data"])

    # Calcular totales para las columnas numéricas después de aplicar el filtro
    totals = filtered_df.select_dtypes(include='number').sum()
    totals_row = pd.DataFrame([totals], columns=totals.index)
    totals_row = totals_row.reindex(columns=filtered_df.columns, fill_value="-")  # Asegurar que coincidan las columnas

    # Agregar la fila de totales al DataFrame filtrado
    filtered_df_with_totals = pd.concat([totals_row], ignore_index=True)

    # Extraer y mostrar los totales de "Outgoing amount" e "Incoming amount"
    outgoing_total = filtered_df["Outgoing Amount"].sum() if "Outgoing Amount" in filtered_df else 0
    incoming_total = filtered_df["Incoming Amount"].sum() if "Incoming Amount" in filtered_df else 0

    # Mostrar los totales en un formato más visual
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Filtered Outgoing amount", value=f"{outgoing_total:,.2f} €")
    with col2:
        st.metric(label="Filtered Incoming amount", value=f"{incoming_total:,.2f} €")

    # Obtener datos filtrados desde la tabla interactiva
    filtered_df = grid_response["data"]

    # Calcular plusvalías
    st.divider()
    st.subheader("💹 Cálculo de Ganancias y Pérdidas (FIFO)")
    resultados = calcular_plusvalias_fifo(df)
    
    
    mostrar_resumen(resultados)

    # Calcular plusvalías asociadas a retiradas (Non-taxable Outgoing EUR)
    st.subheader("Plusvalías relacionadas con retiradas a cuenta bancaria")

    retiradas_df, total_retiradas, cantidad_total_retiradas = filtrar_plusvalias_sobre_retiradas(df, resultados)

    if not retiradas_df.empty:

        # Resumen por moneda
        resumen_moneda = resultados.groupby("Cripto").agg({
            "Cantidad vendida": "sum",
            "Ingreso EUR": "sum",
            "Coste EUR (FIFO)": "sum",
            "Ganancia/pérdida EUR": "sum",
            "Comisión": "sum"
        }).reset_index()

        resumen_moneda["Precio medio venta"] = resumen_moneda["Ingreso EUR"] / resumen_moneda["Cantidad vendida"]
        resumen_moneda["Precio medio compra"] = resumen_moneda["Coste EUR (FIFO)"] / resumen_moneda["Cantidad vendida"]

        col1, col2, col3 = st.columns([5, 0.2, 2])
        with col1:
            # Configurar opciones de la tabla interactiva
            gb = GridOptionsBuilder.from_dataframe(resumen_moneda.round(2))
            gb.configure_default_column(editable=True, filter=True, sortable=True, resizable=True)
            gb.configure_side_bar()  # Barra lateral para filtros avanzados

            grid_options = gb.build()

            # Mostrar tabla interactiva
            grid_response = AgGrid(
                resumen_moneda.round(2),
                gridOptions=grid_options,
                enable_enterprise_modules=True,
                theme="streamlit",  # Cambiar tema si es necesario
                height=400,
                fit_columns_on_grid_load=True
            )
        with col3:
            ganancia_retirada = retiradas_df["Ganancia/pérdida EUR"].sum()
            st.metric(label="Ganancia por retiradas a declarar", value=f"{ganancia_retirada:,.2f} €")
            st.metric(label="Número total de retiradas", value=f"{total_retiradas}")         
            st.metric(label="Cantidad total retirada", value=f"{cantidad_total_retiradas:,.2f} €")
    else:
        st.info("No se han detectado retiradas a cuenta bancaria asociadas a ventas previas.")
    
    # Calcular lo que se debe declarar y pagar
    st.divider()
    st.subheader("📄 Declaración y Pago de Impuestos")

    # Supongamos que `resultados` contiene una columna "Ganancia Neta"
    ganancia_neta = retiradas_df["Ganancia/pérdida EUR"].sum()

    impuestos_a_pagar = calcular_impuestos(ganancia_neta)

    # Mostrar resultados
    st.metric(label="Ganancia Neta a Declarar", value=f"{ganancia_neta:,.2f} €")
    st.metric(label="Impuestos a Pagar", value=f"{impuestos_a_pagar:,.2f} €")
    
    # Footer
    st.markdown("---")
    st.caption("🛠️ Desarrollado para ayudarte con tu declaración de la renta 🇪🇸")

else:
    st.info("👈 Sube uno o más archivos CSV exportados desde Bitpanda.")
