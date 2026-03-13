# pages/3_Consulta.py
# Consulta e filtros avançados de boletos

import streamlit as st
from services.auth_service import require_auth
from services.google_sheets_service import get_boletos, get_fornecedores_ativos, get_categorias_ativas
from services.dashboard_service import prepare_boletos_df
from components.filters import render_quick_filters, render_advanced_filters, apply_filters
from components.tables import render_boletos_table

st.set_page_config(page_title="Consulta — Bem Estar Financeiro", page_icon="🔍", layout="wide")

try:
    with open("assets/styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass

require_auth()

st.html("""
<div class="page-header">
    <h1>🔍 Consulta de Boletos</h1>
    <p>Pesquise, filtre e analise seus compromissos</p>
</div>
""")

# Carregar dados
with st.spinner("Carregando boletos..."):
    df_raw = get_boletos()
    df = prepare_boletos_df(df_raw)
    fornecedores = get_fornecedores_ativos()
    categorias = get_categorias_ativas()

# Filtros rápidos
render_quick_filters()

st.markdown("<br>", unsafe_allow_html=True)

# Filtros avançados
filters = render_advanced_filters(fornecedores, categorias)

# Aplicar filtros
filtered = apply_filters(df, filters)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown(f"### Resultados ({len(filtered)} boleto{'s' if len(filtered) != 1 else ''})")

# Tabela
render_boletos_table(filtered)
