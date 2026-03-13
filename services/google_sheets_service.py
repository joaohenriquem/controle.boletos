# services/google_sheets_service.py [v1.0.1]
# Camada de persistência com Google Sheets via gspread + service account

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import json
from utils.formatters import format_currency, parse_currency, normalize_column_name
from utils.dates import today
from utils.constants import (
    BOLETOS_COLUMNS, PARAMETROS_COLUMNS, FORNECEDORES_COLUMNS,
    CATEGORIAS_COLUMNS, SHEET_BOLETOS, SHEET_PARAMETROS,
    SHEET_FORNECEDORES, SHEET_CATEGORIAS, DEFAULT_PARAMS,
    SEED_CATEGORIAS, SEED_FORNECEDORES, SEED_BOLETOS,
)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Mapeamento de abas com suas colunas esperadas
SHEET_SCHEMA = {
    SHEET_BOLETOS: BOLETOS_COLUMNS,
    SHEET_PARAMETROS: PARAMETROS_COLUMNS,
    SHEET_FORNECEDORES: FORNECEDORES_COLUMNS,
    SHEET_CATEGORIAS: CATEGORIAS_COLUMNS,
}


@st.cache_resource(ttl=300)
def _get_gspread_client():
    """Cria e retorna o cliente gspread autenticado via service account."""
    try:
        creds_dict = dict(st.secrets["google_service_account"])
        # Tratar quebras de linha na chave privada
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Erro na autenticação do Google Sheets: {e}")
        raise e


def _get_spreadsheet():
    """Abre a planilha pelo nome configurado nos secrets."""
    try:
        client = _get_gspread_client()
        name = st.secrets["app"]["spreadsheet_name"]
        return client.open(name)
    except Exception as e:
        st.error(f"❌ Não foi possível abrir a planilha '{st.secrets['app'].get('spreadsheet_name')}'. Verifique se ela foi compartilhada com o e-mail da Service Account.")
        raise e


def _ensure_sheet(spreadsheet, sheet_name: str, columns: list):
    """Verifica se a aba existe; cria com cabeçalho se necessário."""
    try:
        existing = [ws.title for ws in spreadsheet.worksheets()]
        if sheet_name not in existing:
            ws = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=len(columns))
            ws.append_row(columns)
            return ws
        else:
            ws = spreadsheet.worksheet(sheet_name)
            # Verificar se o cabeçalho existe
            header = ws.row_values(1)
            if not header:
                ws.append_row(columns)
            return ws
    except Exception:
        return None


def initialize_sheets():
    """Garante que todas as abas e colunas existem na planilha."""
    try:
        spreadsheet = _get_spreadsheet()
        for sheet_name, columns in SHEET_SCHEMA.items():
            _ensure_sheet(spreadsheet, sheet_name, columns)

        # Seed de dados iniciais se as abas estiverem vazias
        _seed_if_empty(spreadsheet)
        return True
    except Exception as e:
        st.error(f"Erro ao inicializar planilha: {e}")
        return False


def _seed_if_empty(spreadsheet):
    """Insere dados iniciais se as abas estiverem vazias."""
    try:
        # Seed parâmetros
        ws_params = spreadsheet.worksheet(SHEET_PARAMETROS)
        data = ws_params.get_all_records()
        if not data:
            for chave, valor in DEFAULT_PARAMS.items():
                ws_params.append_row([chave, valor])

        # Seed categorias
        ws_cat = spreadsheet.worksheet(SHEET_CATEGORIAS)
        data = ws_cat.get_all_records()
        if not data:
            for cat in SEED_CATEGORIAS:
                ws_cat.append_row([cat["id"], cat["nome"], cat["ativo"]])

        # Seed fornecedores
        ws_forn = spreadsheet.worksheet(SHEET_FORNECEDORES)
        data = ws_forn.get_all_records()
        if not data:
            for forn in SEED_FORNECEDORES:
                ws_forn.append_row([forn["id"], forn["nome"], forn["ativo"]])

        # Seed boletos
        ws_bol = spreadsheet.worksheet(SHEET_BOLETOS)
        data = ws_bol.get_all_records()
        if not data:
            for bol in SEED_BOLETOS:
                row = [bol.get(col, "") for col in BOLETOS_COLUMNS]
                ws_bol.append_row(row)
    except Exception:
        pass


# --- Operações genéricas de leitura ---

@st.cache_data(ttl=60)
def read_sheet(sheet_name: str) -> pd.DataFrame:
    """Lê uma aba e retorna como DataFrame."""
    columns = SHEET_SCHEMA.get(sheet_name, [])
    try:
        spreadsheet = _get_spreadsheet()
        ws = spreadsheet.worksheet(sheet_name)
        records = ws.get_all_records()
        if not records:
            return pd.DataFrame(columns=columns)
        return pd.DataFrame(records)
    except Exception as e:
        error_msg = str(e)
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            except:
                pass
        
        st.error(f"Erro ao ler aba '{sheet_name}': {error_msg}")
        return pd.DataFrame(columns=columns)


def _invalidate_cache(sheet_name: str):
    """Invalida o cache de leitura após uma escrita."""
    # Somente read_sheet tem o decorador @st.cache_data, então só ela tem .clear()
    read_sheet.clear()
    # Para garantir 100% de sincronia, podemos limpar todos os dados em cache
    st.cache_data.clear()


# --- Operações de escrita ---

def insert_record(sheet_name: str, record: dict):
    """Insere um novo registro na aba especificada."""
    try:
        spreadsheet = _get_spreadsheet()
        ws = spreadsheet.worksheet(sheet_name)
        columns = SHEET_SCHEMA.get(sheet_name, [])
        row = [str(record.get(col, "")) for col in columns]
        ws.append_row(row, value_input_option="USER_ENTERED")
        _invalidate_cache(sheet_name)
        return True
    except Exception as e:
        st.error(f"Erro ao inserir registro: {e}")
        return False


def update_record(sheet_name: str, record_id: str, updated_data: dict):
    """Atualiza um registro existente pelo campo 'id'."""
    try:
        spreadsheet = _get_spreadsheet()
        ws = spreadsheet.worksheet(sheet_name)
        records = ws.get_all_values()
        if not records:
            return False

        header = records[0]
        id_col = header.index("id") if "id" in header else 0

        for row_idx, row in enumerate(records[1:], start=2):
            if row[id_col] == record_id:
                columns = SHEET_SCHEMA.get(sheet_name, [])
                new_row = []
                for col in columns:
                    if col in updated_data:
                        new_row.append(str(updated_data[col]))
                    else:
                        col_idx = header.index(col) if col in header else -1
                        new_row.append(row[col_idx] if col_idx >= 0 else "")
                # Atualizar a linha inteira
                cell_range = f"A{row_idx}:{chr(64 + len(columns))}{row_idx}"
                ws.update(cell_range, [new_row], value_input_option="USER_ENTERED")
                _invalidate_cache(sheet_name)
                return True
        return False
    except Exception as e:
        st.error(f"Erro ao atualizar registro: {e}")
        return False


def delete_record(sheet_name: str, record_id: str):
    """Exclui um registro pelo campo 'id'."""
    try:
        spreadsheet = _get_spreadsheet()
        ws = spreadsheet.worksheet(sheet_name)
        records = ws.get_all_values()
        if not records:
            return False

        header = records[0]
        id_col = header.index("id") if "id" in header else 0

        for row_idx, row in enumerate(records[1:], start=2):
            if row[id_col] == record_id:
                ws.delete_rows(row_idx)
                _invalidate_cache(sheet_name)
                return True
        return False
    except Exception as e:
        st.error(f"Erro ao excluir registro: {e}")
        return False


# --- Operações específicas ---

def get_boletos() -> pd.DataFrame:
    """Retorna todos os boletos como DataFrame."""
    return read_sheet(SHEET_BOLETOS)


def get_parametros() -> dict:
    """Retorna parâmetros como dicionário {chave: valor}."""
    df = read_sheet(SHEET_PARAMETROS)
    if df.empty:
        return DEFAULT_PARAMS.copy()
    
    try:
        # Normaliza colunas para evitar case-sensitivity
        mapping = { normalize_column_name(c): c for c in df.columns }
        chave_col = mapping.get("chave", "chave")
        valor_col = mapping.get("valor", "valor")
        
        res = {}
        for _, row in df.iterrows():
            k = str(row[chave_col]).strip().lower()
            v = str(row[valor_col]).strip()
            res[k] = v
        return res
    except Exception:
        return DEFAULT_PARAMS.copy()


def update_parametros_batch(params_dict: dict):
    """Atualiza múltiplos parâmetros de uma vez para otimizar performance e evitar erros de API."""
    try:
        spreadsheet = _get_spreadsheet()
        ws = spreadsheet.worksheet(SHEET_PARAMETROS)
        all_vals = ws.get_all_values()
        
        if not all_vals:
            # Se vazio, inicializa com cabeçalho e dados
            rows = [["chave", "valor"]]
            for k, v in params_dict.items():
                rows.append([k, str(v)])
            ws.append_rows(rows, value_input_option="USER_ENTERED")
            _invalidate_cache(SHEET_PARAMETROS)
            return True
            
        header = all_vals[0]
        mapping = { normalize_column_name(c): i for i, c in enumerate(header) }
        idx_chave = mapping.get("chave", 0)
        idx_valor = mapping.get("valor", 1)
        
        updates = []
        found_keys = set()
        
        # Procura chaves existentes
        for row_idx, row in enumerate(all_vals[1:], start=2):
            curr_k = str(row[idx_chave]).strip().lower() if len(row) > idx_chave else ""
            if curr_k in [k.strip().lower() for k in params_dict.keys()]:
                # Encontra a chave original do dict para pegar o valor
                actual_k = [k for k in params_dict.keys() if k.strip().lower() == curr_k][0]
                val = str(params_dict[actual_k])
                
                col_letter = chr(64 + idx_valor + 1)
                updates.append({
                    'range': f"{col_letter}{row_idx}",
                    'values': [[val]]
                })
                found_keys.add(actual_k)
        
        # Executa atualizações em lote via range
        if updates:
            ws.batch_update(updates, value_input_option="USER_ENTERED")
            
        # Adiciona chaves não encontradas
        for k, v in params_dict.items():
            if k not in found_keys:
                new_row = [""] * max(idx_chave + 1, idx_valor + 1, len(header))
                new_row[idx_chave] = k
                new_row[idx_valor] = str(v)
                ws.append_row(new_row, value_input_option="USER_ENTERED")
                
        _invalidate_cache(SHEET_PARAMETROS)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar parâmetros em lote: {e}")
        return False


def update_parametro(chave: str, valor: str):
    """Atualiza um único parâmetro (wrapper para batch)."""
    return update_parametros_batch({chave: valor})


def get_fornecedores() -> pd.DataFrame:
    """Retorna fornecedores como DataFrame."""
    return read_sheet(SHEET_FORNECEDORES)


def get_categorias() -> pd.DataFrame:
    """Retorna categorias como DataFrame."""
    return read_sheet(SHEET_CATEGORIAS)


def get_fornecedores_ativos() -> list:
    """Retorna lista de nomes de fornecedores ativos."""
    df = get_fornecedores()
    if df.empty or "ativo" not in df.columns or "nome" not in df.columns:
        return []
    ativos = df[df["ativo"].astype(str).str.upper() == "TRUE"]
    return sorted(ativos["nome"].tolist())


def get_categorias_ativas() -> list:
    """Retorna lista de nomes de categorias ativas."""
    df = get_categorias()
    if df.empty or "ativo" not in df.columns or "nome" not in df.columns:
        return []
    ativas = df[df["ativo"].astype(str).str.upper() == "TRUE"]
    return sorted(ativas["nome"].tolist())
