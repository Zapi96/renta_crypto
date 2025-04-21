# visualizer.py

import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
import plotly.express as px

def mostrar_resumen(resultados_df: pd.DataFrame):
    if resultados_df.empty:
        st.warning("No se han encontrado operaciones con plusvalías.")
        return
    col1, _, col3 = st.columns((5,0.2,2))

    with col1:
        gb = GridOptionsBuilder.from_dataframe(resultados_df)
        gb.configure_default_column(editable=True, filter=True, sortable=True, resizable=True)
        gb.configure_side_bar()  # Barra lateral para filtros avanzados

        grid_options = gb.build()

        # Mostrar tabla interactiva
        grid_response = AgGrid(
            resultados_df,
            gridOptions=grid_options,
            enable_enterprise_modules=True,
            theme="streamlit",  # Cambiar tema si es necesario
            height=650,
            fit_columns_on_grid_load=True
        )

    with col3:
        total_ganancia = resultados_df["Ganancia/pérdida EUR"].sum()
        total_operaciones = len(resultados_df)
        ganancia_promedio = total_ganancia / total_operaciones if total_operaciones > 0 else 0

        st.metric("🧾 Ganancia/Pérdida Total", f"{total_ganancia:,.2f} €")
        st.metric("📊 Total Operaciones", total_operaciones)
        st.metric("📈 Ganancia Promedio", f"{ganancia_promedio:,.2f} €")

    # Filtros para monedas y rango de fechas
    monedas = resultados_df["Cripto"].unique()
    moneda_seleccionada = st.multiselect("Filtrar por moneda", monedas, default=monedas)

    fechas = pd.to_datetime(resultados_df["Fecha"])
    fecha_min, fecha_max = fechas.min(), fechas.max()
    rango_fechas = st.date_input("Filtrar por rango de fechas", [fecha_min, fecha_max])

    # Filtrar el DataFrame
    resultados_filtrados = resultados_df[
        (resultados_df["Cripto"].isin(moneda_seleccionada)) &
        (fechas.between(pd.to_datetime(rango_fechas[0]), pd.to_datetime(rango_fechas[1])))
    ]

    # Gráfico
    fig = px.bar(
        resultados_filtrados,
        x="Fecha",
        y="Ganancia/pérdida EUR",
        color="Cripto",
        title="Ganancia/Pérdida por operación",
        labels={"Ganancia/pérdida EUR": "€"}
    )
    st.plotly_chart(fig, use_container_width=True)

    # Resumen de ganancias por moneda
    resumen_ganancias = resultados_df[resultados_df["Ganancia/pérdida EUR"] > 0].groupby("Cripto")["Ganancia/pérdida EUR"].sum().reset_index()
    resumen_ganancias["Porcentaje"] = (resumen_ganancias["Ganancia/pérdida EUR"] / resumen_ganancias["Ganancia/pérdida EUR"].sum()) * 100

    # Resumen de pérdidas por moneda
    resumen_perdidas = resultados_df[resultados_df["Ganancia/pérdida EUR"] < 0].groupby("Cripto")["Ganancia/pérdida EUR"].sum().reset_index()
    resumen_perdidas["Porcentaje"] = (resumen_perdidas["Ganancia/pérdida EUR"].abs() / resumen_perdidas["Ganancia/pérdida EUR"].abs().sum()) * 100

    # Resumen por moneda
    st.subheader("📊 Resumen por Moneda")
    st.subheader("Distribución de Ganancias y Pérdidas por Moneda")
    col1,_, col3 = st.columns((3,0.2, 2))

    with col1:
        
        resumen_por_moneda = resultados_df.groupby("Cripto")["Ganancia/pérdida EUR"].sum().reset_index()

        # Añadir columna de porcentaje de ganancias
        resumen_por_moneda = resumen_por_moneda.merge(
            resumen_ganancias[["Cripto", "Porcentaje"]].rename(columns={"Porcentaje": "Porcentaje Ganancias"}),
            on="Cripto",
            how="left"
        )

        # Añadir columna de porcentaje de pérdidas
        resumen_por_moneda = resumen_por_moneda.merge(
            resumen_perdidas[["Cripto", "Porcentaje"]].rename(columns={"Porcentaje": "Porcentaje Pérdidas"}),
            on="Cripto",
            how="left"
        )

        # Rellenar NaN con 0 para porcentajes
        resumen_por_moneda["Porcentaje Ganancias"] = resumen_por_moneda["Porcentaje Ganancias"].fillna(0)
        resumen_por_moneda["Porcentaje Pérdidas"] = resumen_por_moneda["Porcentaje Pérdidas"].fillna(0)
        
        gb = GridOptionsBuilder.from_dataframe(resumen_por_moneda)
        gb.configure_default_column(editable=True, filter=True, sortable=True, resizable=True)
        gb.configure_side_bar()  # Barra lateral para filtros avanzados

        grid_options = gb.build()

        # Mostrar tabla interactiva
        grid_response = AgGrid(
            resumen_por_moneda,
            gridOptions=grid_options,
            enable_enterprise_modules=True,
            theme="streamlit",  # Cambiar tema si es necesario
            height=650,
            fit_columns_on_grid_load=True
        )

    with col3:
        # Subcolumnas para los gráficos
        subcol1, subcol2 = st.columns(2)

        with subcol1:
            # Gráfico de pastel para ganancias
            fig_ganancias = px.pie(
            resumen_ganancias,
            names="Cripto",
            values="Porcentaje",
            title="Distribución de Ganancias por Moneda",
            labels={"Porcentaje": "%"}
            )
            fig_ganancias.update_traces(textinfo='none')  # Quitar valores porcentuales del gráfico
            st.plotly_chart(fig_ganancias, use_container_width=True)

        with subcol2:
            # Gráfico de pastel para pérdidas
            fig_perdidas = px.pie(
            resumen_perdidas,
            names="Cripto",
            values="Porcentaje",
            title="Distribución de Pérdidas por Moneda",
            labels={"Porcentaje": "%"}
            )
            fig_perdidas.update_traces(textinfo='none')  # Quitar valores porcentuales del gráfico
            st.plotly_chart(fig_perdidas, use_container_width=True)

        col1, col2 = st.columns(2)

        with col1:
            max_ganancia = resultados_df["Ganancia/pérdida EUR"].max()
            st.metric("📈 Máxima Ganancia", f"{max_ganancia:,.2f} €")

            min_ganancia = resultados_df["Ganancia/pérdida EUR"].min()
            st.metric("📉 Mínima Ganancia", f"{min_ganancia:,.2f} €")

        with col2:
            operaciones_positivas = (resultados_df["Ganancia/pérdida EUR"] > 0).sum()
            operaciones_negativas = (resultados_df["Ganancia/pérdida EUR"] < 0).sum()
            st.metric("✅ Operaciones Positivas", operaciones_positivas)
            st.metric("❌ Operaciones Negativas", operaciones_negativas)
