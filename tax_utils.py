# tax_utils.py
import pandas as pd

def es_transaccion_sujeta_a_irpf(row):
    """
    Determina si la transacción debería ser incluida en la declaración de la renta.
    """
    if row["Transaction Type"] == "Trade":
        return "Yes"
    return "No"  # Deposits, Withdrawals y Internal Transfers no generan IRPF

def resumen_fiscal(df):
    """
    Muestra un resumen de qué transacciones están sujetas a IRPF.
    """
    df["Sujeta a IRPF"] = df.apply(es_transaccion_sujeta_a_irpf, axis=1)
    return df

 # Calcular impuestos según los tramos
def calcular_impuestos(ganancia):
    if ganancia <= 6000:
        return ganancia * 0.19
    elif ganancia <= 50000:
        return 6000 * 0.19 + (ganancia - 6000) * 0.21
    elif ganancia <= 200000:
        return 6000 * 0.19 + (50000 - 6000) * 0.21 + (ganancia - 50000) * 0.23
    else:
        return 6000 * 0.19 + (50000 - 6000) * 0.21 + (200000 - 50000) * 0.23 + (ganancia - 200000) * 0.27
    
def filtrar_plusvalias_sobre_retiradas(transacciones_df: pd.DataFrame, plusvalias_df: pd.DataFrame) -> (pd.DataFrame, int, float):
    """
    Filtra las plusvalías relacionadas con retiradas y calcula el total de retiradas y la cantidad retirada.
    """
    # Asegurar que las fechas estén en formato datetime
    transacciones_df["Date"] = pd.to_datetime(transacciones_df["Date"])
    plusvalias_df["Fecha"] = pd.to_datetime(plusvalias_df["Fecha"])

    # Filtrar transacciones que son retiradas de EUR (Non-taxable + Outgoing EUR)
    retiradas = transacciones_df[
        (transacciones_df["Transaction Type"] == "Non-taxable") &
        (transacciones_df["Outgoing Asset"] == "EUR")
    ].copy()

    if retiradas.empty:
        return pd.DataFrame(columns=plusvalias_df.columns), 0, 0.0  # No hay retiradas

    # Calcular el total de retiradas y la cantidad retirada
    total_retiradas = len(retiradas)
    cantidad_total_retiradas = retiradas["Outgoing Amount"].sum()

    # Tomamos la fecha máxima de retirada como tope para las ventas
    fecha_limite = retiradas["Date"].max()

    # Filtrar plusvalías (ventas de cripto por EUR) que ocurrieron hasta esa fecha
    plusvalias_filtradas = plusvalias_df[plusvalias_df["Fecha"] <= fecha_limite].copy()

    return plusvalias_filtradas, total_retiradas, cantidad_total_retiradas

