# data_loader.py

import pandas as pd
import os

COLUMNS = [
    "Date (UTC)", "Integration Name", "Label", "Outgoing Asset", "Outgoing Amount",
    "Incoming Asset", "Incoming Amount", "Fee Asset (optional)", "Fee Amount (optional)",
    "Comment (optional)", "Trx. ID (optional)", "Source Type", "Source Name"
]

def load_bitpanda_csv(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path, sep=";", parse_dates=["Date (UTC)"], dayfirst=True)
    df.columns = [col.strip() for col in df.columns]
    df = df[COLUMNS]  # Ordenamos y seleccionamos columnas relevantes
    return df

def load_multiple_csvs(file_paths: list[str]) -> pd.DataFrame:
    dfs = [load_bitpanda_csv(path) for path in file_paths]
    combined_df = pd.concat(dfs, ignore_index=True)
    combined_df.sort_values(by="Date (UTC)", inplace=True)
    
    # Eliminar duplicados basados en columnas clave
    if "Trx. ID (optional)" in combined_df.columns:
        combined_df.drop_duplicates(subset=["Trx. ID (optional)"], inplace=True)
    else:
        combined_df.drop_duplicates(inplace=True)
    
    return combined_df

def classify_transaction(row):
    label = row["Label"].lower()
    if "trade" in label:
        return "Trade"
    elif "deposit" in label:
        return "Deposit"
    elif "withdrawal" in label:
        return "Withdrawal"
    elif "staking" in label:
        return "Staking"
    elif "auto balance" in label:
        return "Internal Transfer"
    elif "non-taxable" in label:
        return "Non-taxable"
    else:
        return "Other"

def preprocess_df(df: pd.DataFrame) -> pd.DataFrame:
    df["Transaction Type"] = df.apply(classify_transaction, axis=1)
    df["Date (UTC)"] = pd.to_datetime(df["Date (UTC)"]).dt.date
    
    # Reemplazar NaN en las columnas de Fee con 0
    df["Fee Asset (optional)"].fillna("", inplace=True)
    df["Fee Amount (optional)"].fillna(0, inplace=True)
    
    df.drop(columns=["Label"], inplace=True)
    df.rename(columns={"Date (UTC)": "Date"}, inplace=True)
    
    df["EsRetirada"] = (df["Transaction Type"] == "Non-taxable") & (df["Outgoing Asset"] == "EUR")
    return df
