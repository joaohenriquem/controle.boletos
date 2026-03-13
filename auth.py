# auth.py
# Componente de autenticação — renderiza login/logout na sidebar

import streamlit as st
from services.auth_service import (
    is_authenticated, get_current_user, get_google_auth_url,
    handle_callback, is_email_allowed, login_user, logout_user,
    save_session_cookie, clear_session_cookie,
)
from utils.constants import COLORS


def render_auth_sidebar():
    """Renderiza componente de autenticação na sidebar."""
    with st.sidebar:
        # Logo
        st.html(f"""
        <div style="text-align:center; padding:1rem 0;">
            <div style="font-size:1.8rem; font-weight:800; color:{COLORS['primaria']};">
                🌿 Bem Estar
            </div>
            <div style="font-size:0.85rem; color:{COLORS['texto_secundario']};">
                Financeiro
            </div>
        </div>
        """)

        st.markdown("---")

        if is_authenticated():
            user = get_current_user()
            if user:
                # Avatar e info do usuário
                st.html(f"""
                <div style="
                    background: {COLORS['fundo']};
                    border-radius: 12px;
                    padding: 1rem;
                    text-align: center;
                    margin-bottom: 1rem;
                ">
                    <div style="
                        width: 48px; height: 48px;
                        background: {COLORS['primaria']};
                        color: white;
                        border-radius: 50%;
                        display: inline-flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 1.3rem;
                        font-weight: 700;
                        margin-bottom: 0.5rem;
                    ">{user.get('name', 'U')[0].upper()}</div>
                    <div style="font-weight:600; color:{COLORS['texto']};">
                        {user.get('name', 'Usuário')}
                    </div>
                    <div style="font-size:0.8rem; color:{COLORS['texto_secundario']};">
                        {user.get('email', '')}
                    </div>
                </div>
                """)

                if st.button("🚪 Sair", width="stretch"):
                    clear_session_cookie()
                    logout_user()
                    st.rerun()
        else:
            st.html(f"""
            <div style="text-align:center; padding:1rem 0;">
                <p style="color:{COLORS['texto_secundario']}; font-size:0.9rem;">
                    Faça login para acessar o sistema
                </p>
            </div>
            """)

            # Processar callback OAuth
            query_params = st.query_params
            code = query_params.get("code")

            if code and not is_authenticated():
                try:
                    with st.spinner("Autenticando..."):
                        user_info = handle_callback(code)

                    if is_email_allowed(user_info["email"]):
                        login_user(user_info)
                        save_session_cookie(user_info)
                        # Limpa os parâmetros ANTES de qualquer rerun
                        st.query_params.clear()
                        st.rerun()
                    else:
                        st.error(
                            f"⛔ Acesso negado. O e-mail **{user_info['email']}** "
                            "não está autorizado a acessar esta aplicação."
                        )
                        st.query_params.clear()
                except Exception as e:
                    # Se falhar mas já estiver autenticado, apenas limpa
                    if is_authenticated():
                        st.query_params.clear()
                        st.rerun()
                    else:
                        st.error(f"Erro na autenticação: {e}")
                        st.query_params.clear()
            else:
                try:
                    auth_url = get_google_auth_url()
                    st.link_button(
                        "🔐 Entrar com Google",
                        url=auth_url,
                        width="stretch",
                    )
                except Exception as e:
                    st.error(f"Erro ao gerar link de login: {e}")
                    st.info("Verifique as configurações de autenticação em `st.secrets`.")
