# services/auth_service.py
# Autenticação via Google OAuth / OIDC usando Authlib

import streamlit as st
from authlib.integrations.requests_client import OAuth2Session
import json
import time
import hashlib
import hmac
import base64
import extra_streamlit_components as stx

_COOKIE_NAME = "be_session_v1"
_COOKIE_MAX_AGE = 7 * 24 * 3600  # 7 dias
_cookie_mgr = None


def init_cookie_manager():
    """Inicializa o CookieManager. Deve ser chamado uma vez no topo do app.py."""
    global _cookie_mgr
    _cookie_mgr = stx.CookieManager(key="be_auth_mgr")
    return _cookie_mgr


def _cookie_manager():
    return _cookie_mgr


def _sign_token(data: dict) -> str:
    secret = st.secrets["auth"]["cookie_secret"]
    payload = base64.b64encode(
        json.dumps({**data, "exp": time.time() + _COOKIE_MAX_AGE}).encode()
    ).decode()
    sig = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{sig}"


def _verify_token(token: str) -> dict | None:
    try:
        secret = st.secrets["auth"]["cookie_secret"]
        payload, sig = token.rsplit(".", 1)
        expected = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return None
        data = json.loads(base64.b64decode(payload).decode())
        if data.get("exp", 0) > time.time():
            return {k: v for k, v in data.items() if k != "exp"}
    except Exception:
        pass
    return None


def save_session_cookie(user_info: dict):
    """Salva sessão autenticada em cookie assinado (7 dias)."""
    cm = _cookie_manager()
    if cm is not None:
        cm.set(_COOKIE_NAME, _sign_token(user_info), max_age=_COOKIE_MAX_AGE)


def restore_session_from_cookie() -> bool:
    """Tenta restaurar sessão a partir do cookie. Retorna True se restaurou."""
    if is_authenticated():
        return True
    cm = _cookie_manager()
    if cm is None:
        return False
    try:
        token = cm.get(_COOKIE_NAME)
        if not token:
            return False
        user_info = _verify_token(token)
        if user_info:
            login_user(user_info)
            return True
    except Exception:
        pass
    return False


def clear_session_cookie():
    """Remove o cookie de sessão."""
    cm = _cookie_manager()
    if cm is not None:
        cm.delete(_COOKIE_NAME)


def get_auth_config():
    """Carrega configuração de autenticação dos secrets."""
    return {
        "client_id": st.secrets["auth"]["client_id"],
        "client_secret": st.secrets["auth"]["client_secret"],
        "redirect_uri": st.secrets["auth"]["redirect_uri"],
        "server_metadata_url": st.secrets["auth"].get(
            "server_metadata_url",
            "https://accounts.google.com/.well-known/openid-configuration"
        ),
    }


def get_allowed_emails():
    """Retorna lista de e-mails autorizados."""
    emails = st.secrets["app"].get("allowed_emails", [])
    if isinstance(emails, str):
        return [e.strip() for e in emails.split(",")]
    return list(emails)


def get_google_auth_url():
    """Gera a URL de autorização do Google."""
    config = get_auth_config()
    session = OAuth2Session(
        client_id=config["client_id"],
        client_secret=config["client_secret"],
        redirect_uri=config["redirect_uri"],
        scope="openid email profile",
    )
    authorization_endpoint = "https://accounts.google.com/o/oauth2/v2/auth"
    uri, state = session.create_authorization_url(authorization_endpoint)
    st.session_state["oauth_state"] = state
    return uri


def handle_callback(code: str):
    """Processa o callback do OAuth e obtém informações do usuário."""
    import requests
    config = get_auth_config()
    
    # Previne processar o mesmo código se o login já foi concluído com sucesso
    if is_authenticated() and st.session_state.get("last_processed_code") == code:
        return st.session_state["user_info"]

    # 1. Trocar código pelo token via POST direto
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": config["client_id"],
        "client_secret": config["client_secret"],
        "redirect_uri": config["redirect_uri"],
        "grant_type": "authorization_code",
    }
    
    response = requests.post(token_url, data=data)
    if not response.ok:
        error_msg = f"HTTP {response.status_code}: {response.text}"
        # Se o erro for invalid_grant, pode ser que o código já foi trocado e já estamos logados
        if "invalid_grant" in response.text and is_authenticated():
            return st.session_state["user_info"]
            
        st.error(f"Erro na troca do token: {error_msg}")
        raise Exception(f"Google Token Error: {error_msg}")
    
    # Só marca como processado se o Google aceitou a troca
    st.session_state["last_processed_code"] = code
    
    tokens = response.json()
    access_token = tokens.get("access_token")

    # 2. Obter informações do usuário
    userinfo_url = "https://openidconnect.googleapis.com/v1/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}
    user_resp = requests.get(userinfo_url, headers=headers)
    
    if not user_resp.ok:
        raise Exception(f"Userinfo Error: {user_resp.text}")
        
    userinfo = user_resp.json()

    return {
        "email": userinfo.get("email", ""),
        "name": userinfo.get("name", ""),
        "picture": userinfo.get("picture", ""),
    }


def is_authenticated() -> bool:
    """Verifica se o usuário está autenticado."""
    return st.session_state.get("authenticated", False)


def get_current_user() -> dict | None:
    """Retorna dados do usuário logado."""
    if is_authenticated():
        return st.session_state.get("user_info", None)
    return None


def is_email_allowed(email: str) -> bool:
    """Verifica se o e-mail está na lista de autorizados."""
    allowed = get_allowed_emails()
    if not allowed:
        return True  # Se não há lista, permite todos
    return email.lower() in [e.lower() for e in allowed]


def login_user(user_info: dict):
    """Registra login do usuário na sessão."""
    st.session_state["authenticated"] = True
    st.session_state["user_info"] = user_info


def logout_user():
    """Remove dados de autenticação da sessão."""
    for key in ["authenticated", "user_info", "oauth_state"]:
        st.session_state.pop(key, None)


def require_auth():
    """
    Decorator/guard para proteger páginas.
    Se não autenticado, exibe mensagem e para a execução.
    """
    if not is_authenticated():
        st.warning("🔒 Você precisa estar autenticado para acessar esta página.")
        st.info("Use o menu lateral para fazer login com Google.")
        st.stop()
