import pandas as pd
from collections import defaultdict

def safe_float(x):
    try:
        return float(x)
    except:
        return 0.0

def calcular_plusvalias_fifo(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df_trades = df[df["Transaction Type"] == "Trade"].sort_values("Date")

    wallets = defaultdict(list)
    resultados = []

    for _, row in df_trades.iterrows():
        out_asset = row["Outgoing Asset"]
        in_asset = row["Incoming Asset"]
        out_amt = safe_float(row["Outgoing Amount"])
        in_amt = safe_float(row["Incoming Amount"])
        fee = safe_float(row.get("Fee Amount (optional)", 0.0))
        date = row["Date"]

        # COMPRA → EUR -> Cripto
        if out_asset == "EUR" and pd.notna(in_asset):
            price_per_unit = out_amt / in_amt if in_amt else 0
            wallets[in_asset].append({
                "cantidad": in_amt,
                "precio_unitario": price_per_unit,
                "fecha": date
            })

        # VENTA → Cripto -> EUR
        elif in_asset == "EUR" and pd.notna(out_asset):
            cantidad_a_vender = out_amt
            ingreso_total = in_amt - fee
            cantidad_vendida = 0.0
            coste_total = 0.0

            while cantidad_a_vender > 0 and wallets[out_asset]:
                entrada = wallets[out_asset][0]
                cantidad_disponible = entrada["cantidad"]

                if cantidad_disponible <= cantidad_a_vender:
                    cantidad_vendida += cantidad_disponible
                    coste_total += cantidad_disponible * entrada["precio_unitario"]
                    cantidad_a_vender -= cantidad_disponible
                    wallets[out_asset].pop(0)
                else:
                    cantidad_vendida += cantidad_a_vender
                    coste_total += cantidad_a_vender * entrada["precio_unitario"]
                    entrada["cantidad"] -= cantidad_a_vender
                    cantidad_a_vender = 0

            ganancia = ingreso_total - coste_total

            resultados.append({
                "Fecha": date,
                "Cripto": out_asset,
                "Cantidad vendida": cantidad_vendida,
                "Ingreso EUR": ingreso_total,
                "Coste EUR (FIFO)": coste_total,
                "Ganancia/pérdida EUR": ganancia,
                "Comisión": fee
            })

        # PERMUTA → Cripto A -> Cripto B (también se considera venta)
        elif pd.notna(out_asset) and pd.notna(in_asset) and out_asset != "EUR" and in_asset != "EUR":
            cantidad_a_vender = out_amt
            valor_adquisicion = 0.0
            cantidad_vendida = 0.0

            while cantidad_a_vender > 0 and wallets[out_asset]:
                entrada = wallets[out_asset][0]
                cantidad_disponible = entrada["cantidad"]

                if cantidad_disponible <= cantidad_a_vender:
                    cantidad_vendida += cantidad_disponible
                    valor_adquisicion += cantidad_disponible * entrada["precio_unitario"]
                    cantidad_a_vender -= cantidad_disponible
                    wallets[out_asset].pop(0)
                else:
                    cantidad_vendida += cantidad_a_vender
                    valor_adquisicion += cantidad_a_vender * entrada["precio_unitario"]
                    entrada["cantidad"] -= cantidad_a_vender
                    cantidad_a_vender = 0

            # Precio de compra estimado de la cripto recibida
            precio_unitario_compra = valor_adquisicion / in_amt if in_amt else 0

            # Registrar la nueva cripto como comprada
            wallets[in_asset].append({
                "cantidad": in_amt,
                "precio_unitario": precio_unitario_compra,
                "fecha": date
            })

            resultados.append({
                "Fecha": date,
                "Cripto": out_asset,
                "Cantidad vendida": cantidad_vendida,
                "Ingreso EUR": valor_adquisicion,
                "Coste EUR (FIFO)": valor_adquisicion,
                "Ganancia/pérdida EUR": 0.0,  # neutra fiscalmente, pero se refleja la venta
                "Comisión": fee
            })

    return pd.DataFrame(resultados)


