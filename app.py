# app.py
# Ponto de entrada da aplicação Bem Estar Financeiro
# Farmácia Bem Estar — Controle inteligente de vencimentos e previsões

import streamlit as st
from auth import render_auth_sidebar
from services.auth_service import is_authenticated
from services.google_sheets_service import initialize_sheets
from utils.constants import COLORS

# Configuração da página principal
st.set_page_config(
    page_title="Bem Estar Financeiro",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "**Bem Estar Financeiro** — Controle inteligente de vencimentos e previsões. "
                 "Desenvolvido para Farmácia Bem Estar."
    },
)

# Carregar CSS customizado
try:
    with open("assets/styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass

# Renderizar sidebar de autenticação (processa callback OAuth e atualiza sessão)
render_auth_sidebar()


def _home_page():
    st.html(f"""
    <div style="
        text-align: center;
        padding: 2rem 1rem;
        max-width: 800px;
        margin: 0 auto;
    ">
        <div style="font-size: 6rem; margin-bottom: 0.5rem;">🌿</div>
        <h1 style="
            color: {COLORS['primaria']};
            font-size: 2.6rem;
            font-weight: 800;
            margin-bottom: 0.2rem;
        ">Bem Estar Financeiro</h1>
        <p style="
            color: {COLORS['texto_secundario']};
            font-size: 1.1rem;
            margin-bottom: 3rem;
        ">Controle inteligente de vencimentos e previsões</p>
    </div>
    """)

    st.html("<div style='height: 2rem;'></div>")

    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<div class="home-card-container">', unsafe_allow_html=True)
        if st.button("📅\n\n**CALENDÁRIO**\n\nVisão mensal", key="btn_cal", use_container_width=True):
            st.switch_page("pages/4_Calendario.py")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="home-card-container">', unsafe_allow_html=True)
        if st.button("📊\n\n**DASHBOARD**\n\nKPIs e visão geral", key="btn_dash", use_container_width=True):
            st.switch_page("pages/1_Dashboard.py")
        st.markdown('</div>', unsafe_allow_html=True)

    with col3:
        st.markdown('<div class="home-card-container">', unsafe_allow_html=True)
        if st.button("📝\n\n**CADASTRO**\n\nGerencie boletos", key="btn_cad", use_container_width=True):
            st.switch_page("pages/2_Cadastro_de_Boletos.py")
        st.markdown('</div>', unsafe_allow_html=True)

   

    st.html("""
    <div style="text-align: center; margin-top: 4rem;">
        <p style="color: #6B7280; font-size: 1rem; font-weight: 500;">
            Clique nos painéis acima para gerenciar suas finanças.
        </p>
    </div>
    """)


def _login_page():
    st.html(f"""
    <div style="
        text-align: center;
        padding: 4rem 2rem;
        max-width: 600px;
        margin: 0 auto;
    ">
        <div style="font-size: 5rem; margin-bottom: 1rem;">🌿</div>
        <h1 style="
            color: {COLORS['primaria']};
            font-size: 2.6rem;
            font-weight: 800;
            margin-bottom: 0.5rem;
        ">Bem Estar Financeiro</h1>
        <p style="
            color: {COLORS['texto_secundario']};
            font-size: 1.15rem;
            margin-bottom: 2rem;
        ">Controle inteligente de vencimentos e previsões</p>
        <div style="
            background: white;
            border: 1px solid {COLORS['borda']};
            border-radius: 16px;
            padding: 2rem;
            box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        ">
            <p style="color: {COLORS['texto']}; font-size: 1rem; margin-bottom: 1rem;">
                🔒 Faça login com sua conta Google para acessar o sistema.
            </p>
            <p style="color: {COLORS['texto_secundario']}; font-size: 0.85rem;">
                Use o botão <strong>"Entrar com Google"</strong> no menu lateral.
            </p>
        </div>
    </div>
    """)


# Navegação dinâmica baseada no estado de autenticação
if is_authenticated():
    if not st.session_state.get("sheets_initialized"):
        with st.spinner("Verificando estrutura da planilha..."):
            initialize_sheets()
        st.session_state["sheets_initialized"] = True
    pages = [
        st.Page(_home_page, title="Início", icon="🏠"),
        st.Page("pages/1_Dashboard.py", title="Dashboard", icon="📊"),
        st.Page("pages/2_Cadastro_de_Boletos.py", title="Cadastro de Boletos", icon="📝"),
        st.Page("pages/3_Consulta.py", title="Consulta", icon="🔍"),
        st.Page("pages/4_Calendario.py", title="Calendário", icon="📅"),
        st.Page("pages/5_Parametros.py", title="Parâmetros", icon="⚙️"),
        st.Page("pages/6_Relatorios.py", title="Relatórios", icon="📈"),
    ]
else:
    pages = [
        st.Page(_login_page, title="Entrar", icon="🔐"),
    ]

pg = st.navigation(pages)
pg.run()
