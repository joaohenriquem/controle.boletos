# pages/5_Parametros.py
# Configurações e parametrizações do sistema

import streamlit as st
import uuid
from services.auth_service import require_auth
from services.google_sheets_service import (
    get_parametros, update_parametro,
    get_fornecedores, get_categorias,
    insert_record, update_record, delete_record,
    get_fornecedores_ativos, get_categorias_ativas,
)
from utils.constants import SHEET_FORNECEDORES, SHEET_CATEGORIAS, COLORS
from utils.formatters import format_currency

st.set_page_config(page_title="Parâmetros — Bem Estar Financeiro", page_icon="⚙️", layout="wide")

try:
    with open("assets/styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass

require_auth()

st.html("""
<div class="page-header">
    <h1>⚙️ Parâmetros</h1>
    <p>Configure limites, fornecedores e categorias</p>
</div>
""")

tab_geral, tab_forn, tab_cat = st.tabs(["📊 Geral", "🏢 Fornecedores", "🏷️ Categorias"])

# ---- TAB GERAL ----
with tab_geral:
    st.markdown("### Configurações Gerais")

    params = get_parametros()

    with st.form("form_parametros"):
        limite = st.number_input(
            "Limite máximo diário (R$)",
            min_value=0.0,
            value=float(params.get("limite_maximo_diario", 15000)),
            step=500.0,
            format="%.2f",
        )
        dias_alerta = st.number_input(
            "Dias de alerta antecipado",
            min_value=1,
            max_value=30,
            value=int(params.get("dias_alerta", 3)),
        )

        st.markdown("#### Faixas de Risco")
        col1, col2 = st.columns(2)
        with col1:
            faixa_verde = st.number_input(
                "Faixa verde — até (% do limite)",
                min_value=10,
                max_value=100,
                value=int(params.get("faixa_verde_percentual", 70)),
                help="Abaixo deste percentual = situação normal (verde)",
            )
        with col2:
            faixa_amarela = st.number_input(
                "Faixa amarela — até (% do limite)",
                min_value=10,
                max_value=200,
                value=int(params.get("faixa_amarela_percentual", 100)),
                help="Entre faixa verde e este valor = atenção (amarelo). Acima = vermelho",
            )

        # Preview visual
        st.markdown("**Visualização das faixas:**")
        st.html(f"""
        <div style="display:flex; height:30px; border-radius:8px; overflow:hidden; margin:0.5rem 0;">
            <div style="width:{faixa_verde}%; background:{COLORS['primaria']}; display:flex;
                        align-items:center; justify-content:center; color:white; font-size:0.8rem;">
                Verde (0-{faixa_verde}%)
            </div>
            <div style="width:{faixa_amarela - faixa_verde}%; background:{COLORS['alerta']}; display:flex;
                        align-items:center; justify-content:center; font-size:0.8rem;">
                Amarelo ({faixa_verde}-{faixa_amarela}%)
            </div>
            <div style="flex:1; background:{COLORS['erro']}; display:flex;
                        align-items:center; justify-content:center; color:white; font-size:0.8rem;">
                Vermelho (&gt;{faixa_amarela}%)
            </div>
        </div>
        """)

        if st.form_submit_button("💾 Salvar Parâmetros", type="primary", width="stretch"):
            update_parametro("limite_maximo_diario", str(limite))
            update_parametro("dias_alerta", str(dias_alerta))
            update_parametro("faixa_verde_percentual", str(faixa_verde))
            update_parametro("faixa_amarela_percentual", str(faixa_amarela))
            st.success("✅ Parâmetros salvos com sucesso!")

# ---- TAB FORNECEDORES ----
with tab_forn:
    st.markdown("### Gerenciar Fornecedores")

    df_forn = get_fornecedores()

    # Adicionar novo
    with st.form("form_novo_fornecedor"):
        col1, col2 = st.columns([3, 1])
        with col1:
            novo_forn = st.text_input("Nome do fornecedor")
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            btn_add = st.form_submit_button("➕ Adicionar")

        if btn_add and novo_forn.strip():
            record = {
                "id": f"forn-{uuid.uuid4().hex[:8]}",
                "nome": novo_forn.strip(),
                "ativo": "TRUE",
            }
            if insert_record(SHEET_FORNECEDORES, record):
                st.success(f"✅ Fornecedor '{novo_forn}' adicionado!")
                st.rerun()

    # Lista existente
    if not df_forn.empty:
        st.markdown("#### Fornecedores cadastrados")
        for _, row in df_forn.iterrows():
            col1, col2, col3 = st.columns([4, 1, 1])
            with col1:
                status_icon = "🟢" if str(row.get("ativo", "TRUE")).upper() == "TRUE" else "🔴"
                st.markdown(f"{status_icon} **{row['nome']}**")
            with col2:
                ativo = str(row.get("ativo", "TRUE")).upper() == "TRUE"
                if st.button(
                    "Desativar" if ativo else "Ativar",
                    key=f"toggle_forn_{row['id']}",
                    width="stretch",
                ):
                    updated = {"id": row["id"], "nome": row["nome"], "ativo": "FALSE" if ativo else "TRUE"}
                    update_record(SHEET_FORNECEDORES, row["id"], updated)
                    st.rerun()
            with col3:
                if st.button("🗑️", key=f"del_forn_{row['id']}"):
                    delete_record(SHEET_FORNECEDORES, row["id"])
                    st.rerun()

# ---- TAB CATEGORIAS ----
with tab_cat:
    st.markdown("### Gerenciar Categorias")

    df_cat = get_categorias()

    with st.form("form_nova_categoria"):
        col1, col2 = st.columns([3, 1])
        with col1:
            nova_cat = st.text_input("Nome da categoria")
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            btn_add_cat = st.form_submit_button("➕ Adicionar")

        if btn_add_cat and nova_cat.strip():
            record = {
                "id": f"cat-{uuid.uuid4().hex[:8]}",
                "nome": nova_cat.strip(),
                "ativo": "TRUE",
            }
            if insert_record(SHEET_CATEGORIAS, record):
                st.success(f"✅ Categoria '{nova_cat}' adicionada!")
                st.rerun()

    if not df_cat.empty:
        st.markdown("#### Categorias cadastradas")
        for _, row in df_cat.iterrows():
            col1, col2, col3 = st.columns([4, 1, 1])
            with col1:
                status_icon = "🟢" if str(row.get("ativo", "TRUE")).upper() == "TRUE" else "🔴"
                st.markdown(f"{status_icon} **{row['nome']}**")
            with col2:
                ativo = str(row.get("ativo", "TRUE")).upper() == "TRUE"
                if st.button(
                    "Desativar" if ativo else "Ativar",
                    key=f"toggle_cat_{row['id']}",
                    width="stretch",
                ):
                    updated = {"id": row["id"], "nome": row["nome"], "ativo": "FALSE" if ativo else "TRUE"}
                    update_record(SHEET_CATEGORIAS, row["id"], updated)
                    st.rerun()
            with col3:
                if st.button("🗑️", key=f"del_cat_{row['id']}"):
                    delete_record(SHEET_CATEGORIAS, row["id"])
                    st.rerun()
