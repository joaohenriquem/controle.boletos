# pages/2_Cadastro_de_Boletos.py
# Cadastro, edição e exclusão de boletos + leitura automática

import streamlit as st
import uuid
from datetime import datetime, date
from services.auth_service import require_auth
from services.google_sheets_service import (
    get_boletos, insert_record, update_record, delete_record,
    get_fornecedores_ativos, get_categorias_ativas,
)
from services.dashboard_service import prepare_boletos_df
from services.boleto_reader_service import read_boleto
from utils.validators import validate_boleto_form
from utils.formatters import format_currency, format_date_br, parse_currency
from utils.constants import SHEET_BOLETOS, STATUS_OPTIONS
from components.cards import render_alert_card

st.set_page_config(page_title="Cadastro de Boletos — Bem Estar Financeiro", page_icon="📝", layout="wide")

try:
    with open("assets/styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass

require_auth()

st.html("""
<div class="page-header">
    <h1>📝 Cadastro de Boletos</h1>
    <p>Cadastre, edite e gerencie seus compromissos financeiros</p>
</div>
""")

# Carregar dados auxiliares
fornecedores = get_fornecedores_ativos()
categorias = get_categorias_ativas()

# ----- Leitura automática de boleto -----
st.markdown("### 📄 Leitura Automática de Boleto")
with st.expander("Enviar boleto para leitura automática", expanded=False):
    uploaded = st.file_uploader(
        "Envie o boleto em PDF ou imagem",
        type=["pdf", "png", "jpg", "jpeg"],
        key="boleto_upload",
    )

    if uploaded:
        st.markdown(f"**Arquivo:** {uploaded.name} ({uploaded.size / 1024:.1f} KB)")

        if st.button("🔍 Ler Boleto", type="primary"):
            with st.spinner("Processando boleto..."):
                ext = uploaded.name.rsplit(".", 1)[-1].lower()
                result = read_boleto(uploaded.read(), ext)

            if result["success"]:
                st.success(result["message"])
                # Preencher sessão com dados extraídos
                if result["cobrador"]:
                    st.session_state["auto_cobrador"] = result["cobrador"]
                if result["data_vencimento"]:
                    st.session_state["auto_data_vencimento"] = result["data_vencimento"]
                if result["valor"]:
                    st.session_state["auto_valor"] = result["valor"]

                st.markdown("**Campos encontrados:**")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"**Cobrador:** {result['cobrador'] or '❌ Não encontrado'}")
                with col2:
                    st.markdown(f"**Vencimento:** {format_date_br(result['data_vencimento']) if result['data_vencimento'] else '❌ Não encontrado'}")
                with col3:
                    st.markdown(f"**Valor:** {format_currency(float(result['valor'])) if result['valor'] else '❌ Não encontrado'}")
            else:
                st.warning(result["message"])

            if result["raw_text"]:
                with st.expander("Ver texto extraído"):
                    st.text(result["raw_text"][:2000])

# ----- Tabs: Novo / Editar / Excluir -----
tab_novo, tab_editar, tab_excluir = st.tabs(["➕ Novo Boleto", "✏️ Editar Boleto", "🗑️ Excluir Boleto"])

# ---- TAB NOVO ----
with tab_novo:
    st.markdown("### Cadastrar Novo Boleto")

    with st.form("form_novo_boleto", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            descricao = st.text_input("Descrição *")
            fornecedor = st.selectbox("Fornecedor *", options=[""] + fornecedores)
            cobrador = st.text_input(
                "Cobrador / Beneficiário",
                value=st.session_state.pop("auto_cobrador", ""),
            )
            categoria = st.selectbox("Categoria *", options=[""] + categorias)
            numero_doc = st.text_input("Nº Documento")

        with col2:
            data_emissao = st.date_input("Data de Emissão *", value=date.today())

            # Data de vencimento com auto-preenchimento
            auto_venc = st.session_state.pop("auto_data_vencimento", None)
            if auto_venc:
                try:
                    default_venc = datetime.strptime(auto_venc, "%Y-%m-%d").date()
                except ValueError:
                    default_venc = date.today()
            else:
                default_venc = date.today()
            data_vencimento = st.date_input("Data de Vencimento *", value=default_venc)

            auto_val = st.session_state.pop("auto_valor", "")
            valor = st.text_input("Valor (R$) *", value=auto_val, placeholder="1.500,00")

            recorrente = st.checkbox("Boleto recorrente")
            competencia = st.text_input("Competência", placeholder="2025-03")

        observacoes = st.text_area("Observações", height=80)

        submitted = st.form_submit_button("💾 Salvar Boleto", type="primary", width="stretch")

        if submitted:
            data = {
                "descricao": descricao,
                "fornecedor": fornecedor,
                "cobrador": cobrador or fornecedor,
                "categoria": categoria,
                "numero_documento": numero_doc,
                "data_emissao": str(data_emissao),
                "data_vencimento": str(data_vencimento),
                "valor": valor,
                "status": "pendente",
                "recorrente": "TRUE" if recorrente else "FALSE",
                "observacoes": observacoes,
                "competencia": competencia or str(data_vencimento)[:7],
                "data_pagamento": "",
                "criado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "atualizado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "id": f"bol-{uuid.uuid4().hex[:8]}",
            }

            errors = validate_boleto_form(data)
            if errors:
                for err in errors:
                    st.error(err)
            else:
                if insert_record(SHEET_BOLETOS, data):
                    st.success("✅ Boleto cadastrado com sucesso!")
                    st.balloons()
                else:
                    st.error("Erro ao salvar o boleto. Tente novamente.")

# ---- TAB EDITAR ----
with tab_editar:
    st.markdown("### Editar Boleto Existente")

    df_raw = get_boletos()
    df = prepare_boletos_df(df_raw)

    if df.empty:
        st.info("Nenhum boleto cadastrado.")
    else:
        # Seletor de boleto
        boleto_options = {
            f"{row['descricao']} — {format_currency(row['valor'])} — {format_date_br(row['data_vencimento'])}": row["id"]
            for _, row in df.iterrows()
        }
        selected_label = st.selectbox("Selecione o boleto", options=list(boleto_options.keys()))
        selected_id = boleto_options[selected_label]
        boleto = df[df["id"] == selected_id].iloc[0]

        with st.form("form_editar_boleto"):
            col1, col2 = st.columns(2)

            with col1:
                ed_descricao = st.text_input("Descrição", value=boleto["descricao"])
                ed_fornecedor = st.selectbox(
                    "Fornecedor",
                    options=fornecedores,
                    index=fornecedores.index(boleto["fornecedor"]) if boleto["fornecedor"] in fornecedores else 0,
                )
                ed_cobrador = st.text_input("Cobrador", value=boleto.get("cobrador", ""))
                ed_categoria = st.selectbox(
                    "Categoria",
                    options=categorias,
                    index=categorias.index(boleto["categoria"]) if boleto["categoria"] in categorias else 0,
                )
                ed_numero = st.text_input("Nº Documento", value=boleto.get("numero_documento", ""))

            with col2:
                ed_emissao = st.date_input("Data de Emissão", value=boleto["data_emissao"])
                ed_vencimento = st.date_input("Data de Vencimento", value=boleto["data_vencimento"])
                ed_valor = st.text_input("Valor (R$)", value=f"{boleto['valor']:.2f}")
                ed_status = st.selectbox(
                    "Status",
                    options=STATUS_OPTIONS,
                    index=STATUS_OPTIONS.index(boleto["status"]) if boleto["status"] in STATUS_OPTIONS else 0,
                )
                ed_recorrente = st.checkbox("Recorrente", value=str(boleto.get("recorrente", "FALSE")).upper() == "TRUE")
                ed_competencia = st.text_input("Competência", value=boleto.get("competencia", ""))

            ed_obs = st.text_area("Observações", value=boleto.get("observacoes", ""))

            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                btn_salvar = st.form_submit_button("💾 Salvar Alterações", type="primary", width="stretch")
            with col_btn2:
                btn_pagar = st.form_submit_button("✅ Marcar como Pago", width="stretch")

            if btn_salvar:
                updated = {
                    "id": selected_id,
                    "descricao": ed_descricao,
                    "fornecedor": ed_fornecedor,
                    "cobrador": ed_cobrador or ed_fornecedor,
                    "categoria": ed_categoria,
                    "numero_documento": ed_numero,
                    "data_emissao": str(ed_emissao),
                    "data_vencimento": str(ed_vencimento),
                    "valor": str(parse_currency(ed_valor)),
                    "status": ed_status,
                    "recorrente": "TRUE" if ed_recorrente else "FALSE",
                    "observacoes": ed_obs,
                    "competencia": ed_competencia,
                    "data_pagamento": boleto.get("data_pagamento", ""),
                    "criado_em": boleto.get("criado_em", ""),
                    "atualizado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
                if update_record(SHEET_BOLETOS, selected_id, updated):
                    st.success("✅ Boleto atualizado com sucesso!")
                    st.rerun()
                else:
                    st.error("Erro ao atualizar o boleto.")

            if btn_pagar:
                updated = {
                    "id": selected_id,
                    "descricao": boleto["descricao"],
                    "fornecedor": boleto["fornecedor"],
                    "cobrador": boleto.get("cobrador", ""),
                    "categoria": boleto["categoria"],
                    "numero_documento": boleto.get("numero_documento", ""),
                    "data_emissao": str(boleto["data_emissao"]),
                    "data_vencimento": str(boleto["data_vencimento"]),
                    "valor": str(boleto["valor"]),
                    "status": "pago",
                    "recorrente": str(boleto.get("recorrente", "FALSE")),
                    "observacoes": boleto.get("observacoes", ""),
                    "competencia": boleto.get("competencia", ""),
                    "data_pagamento": datetime.now().strftime("%Y-%m-%d"),
                    "criado_em": boleto.get("criado_em", ""),
                    "atualizado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
                if update_record(SHEET_BOLETOS, selected_id, updated):
                    st.success("✅ Boleto marcado como pago!")
                    st.rerun()
                else:
                    st.error("Erro ao atualizar o boleto.")

# ---- TAB EXCLUIR ----
with tab_excluir:
    st.markdown("### Excluir Boleto")
    st.warning("⚠️ Esta ação é irreversível.")

    df_raw2 = get_boletos()
    df2 = prepare_boletos_df(df_raw2)

    if df2.empty:
        st.info("Nenhum boleto cadastrado.")
    else:
        del_options = {
            f"{row['descricao']} — {format_currency(row['valor'])} — {format_date_br(row['data_vencimento'])}": row["id"]
            for _, row in df2.iterrows()
        }
        del_label = st.selectbox("Selecione o boleto para excluir", options=list(del_options.keys()), key="del_select")
        del_id = del_options[del_label]

        confirm = st.checkbox("Confirmo que desejo excluir este boleto permanentemente")

        if st.button("🗑️ Excluir Boleto", type="primary", disabled=not confirm):
            if delete_record(SHEET_BOLETOS, del_id):
                st.success("✅ Boleto excluído com sucesso.")
                st.rerun()
            else:
                st.error("Erro ao excluir o boleto.")
