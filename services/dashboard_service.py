# services/dashboard_service.py
# Lógica de negócio para o dashboard e KPIs

import pandas as pd
import unicodedata
from datetime import date, timedelta
from utils.dates import today, date_range_this_month, next_n_days, parse_date_safe
from utils.formatters import parse_currency, normalize_column_name
from utils.constants import STATUS_PAGO, STATUS_CANCELADO
import streamlit as st
import json
from google.oauth2 import service_account

def _get_credentials():
    """Obtém credenciais da service account a partir dos secrets."""
    try:
        secret = dict(st.secrets["google_service_account"])
        secret["private_key"] = secret["private_key"].replace("\\n", "\n")
        return service_account.Credentials.from_service_account_info(secret)
    except Exception:
        return None


    # Remove a definição local para usar a importada


def prepare_boletos_df(df: pd.DataFrame) -> pd.DataFrame:
    """Prepara DataFrame de boletos com tipos corretos."""
    if df is None or df.empty:
        return pd.DataFrame(columns=["id", "data_vencimento", "data_emissao", "valor", "status", "categoria", "fornecedor"])

    # Normalizar nomes de colunas para evitar KeyError em caso de cabeçalhos alterados
    normalized = { normalize_column_name(c): c for c in df.columns }
    column_mappings = {}
    expected_cols = ("id", "data_vencimento", "data_emissao", "valor", "status", "categoria", "fornecedor")
    for expected in expected_cols:
        if expected not in df.columns and expected in normalized:
            column_mappings[normalized[expected]] = expected
    if column_mappings:
        df = df.rename(columns=column_mappings)

    df = df.copy()
    
    # Garantir que colunas existem antes de aplicar transformações
    for col in expected_cols:
        if col not in df.columns:
            df[col] = "" if col != "valor" else 0.0

    df["data_vencimento"] = df["data_vencimento"].apply(parse_date_safe)
    df["data_emissao"] = df["data_emissao"].apply(parse_date_safe)
    df["valor"] = df["valor"].apply(parse_currency)

    # Atualizar status de vencidos automaticamente
    t = today()
    mask = (
        df["data_vencimento"].notna() &
        (df["data_vencimento"] < t) &
        (~df["status"].astype(str).str.lower().isin([STATUS_PAGO, STATUS_CANCELADO]))
    )
    df.loc[mask, "status"] = "vencido"

    return df


def get_kpis(df: pd.DataFrame, limite_diario: float) -> dict:
    """Calcula os KPIs do dashboard."""
    # Retorno padrão para evitar erros se o DF estiver vazio ou incompleto
    default_vals = {
        "qtd_hoje": 0, "valor_hoje": 0.0, "qtd_vencidos": 0,
        "valor_vencidos": 0.0, "valor_prox_7dias": 0.0,
        "valor_mes": 0.0, "limite_diario": limite_diario,
        "percentual_limite": 0.0, "excedeu_limite": False,
    }

    if df is None or df.empty or "data_vencimento" not in df.columns:
        return default_vals

    t = today()
    first_month, last_month = date_range_this_month()
    _, next_7 = next_n_days(7)

    # Filtros
    try:
        status_filter = ~df["status"].astype(str).str.lower().isin([STATUS_PAGO, STATUS_CANCELADO])
        
        hoje_mask = (df["data_vencimento"] == t)
        vencidos_mask = (df["data_vencimento"] < t) & status_filter
        prox7_mask = (df["data_vencimento"] >= t) & (df["data_vencimento"] <= next_7) & status_filter
        mes_mask = (df["data_vencimento"] >= first_month) & (df["data_vencimento"] <= last_month) & status_filter
        hoje_pendente = hoje_mask & status_filter

        total_hoje = df.loc[hoje_pendente, "valor"].sum() if not df.empty else 0
        percentual_limite = (total_hoje / limite_diario * 100) if limite_diario > 0 else 0

        return {
            "qtd_hoje": int(hoje_pendente.sum()),
            "valor_hoje": total_hoje,
            "qtd_vencidos": int(vencidos_mask.sum()),
            "valor_vencidos": df.loc[vencidos_mask, "valor"].sum(),
            "valor_prox_7dias": df.loc[prox7_mask, "valor"].sum(),
            "valor_mes": df.loc[mes_mask, "valor"].sum(),
            "limite_diario": limite_diario,
            "percentual_limite": percentual_limite,
            "excedeu_limite": total_hoje > limite_diario,
        }
    except Exception as e:
        st.error(f"Erro ao calcular KPIs: {e}")
        return default_vals


def get_daily_totals(df: pd.DataFrame, year: int, month: int) -> dict:
    """Retorna dicionário {dia: valor_total} para um mês específico."""
    if df is None or df.empty or "data_vencimento" not in df.columns:
        return {}

    mask = (
        df["data_vencimento"].notna() &
        (df["data_vencimento"].apply(lambda d: d.year if d else None) == year) &
        (df["data_vencimento"].apply(lambda d: d.month if d else None) == month) &
        (~df["status"].astype(str).str.lower().isin([STATUS_PAGO, STATUS_CANCELADO]))
    )

    filtered = df[mask].copy()
    if filtered.empty:
        return {}

    filtered["dia"] = filtered["data_vencimento"].apply(lambda d: d.day)
    return filtered.groupby("dia")["valor"].sum().to_dict()


def get_boletos_by_date(df: pd.DataFrame, target_date: date) -> pd.DataFrame:
    """Retorna boletos de uma data específica."""
    if df is None or df.empty or "data_vencimento" not in df.columns:
        return df
    mask = df["data_vencimento"] == target_date
    return df[mask].sort_values("valor", ascending=False)
