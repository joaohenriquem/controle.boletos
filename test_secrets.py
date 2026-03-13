import streamlit as st
import json

def test_secrets():
    print("Iniciando teste de secrets...")
    
    # Teste Auth
    try:
        auth = st.secrets["auth"]
        print("✅ Segredo [auth] encontrado.")
        print(f"   Redirect URI: {auth['redirect_uri']}")
    except Exception as e:
        print(f"❌ Erro ao acessar [auth]: {e}")

    # Teste Google Service Account
    try:
        gsa = st.secrets["google_service_account"]
        print("✅ Segredo [google_service_account] encontrado.")
        pk = gsa["private_key"]
        if "\\n" in pk:
            print("❗ Chave contém '\\n' escapado. O tratamento no código é necessário.")
            pk_fixed = pk.replace("\\n", "\n")
            if "\n" in pk_fixed:
                 print("✅ Tratamento de '\\n' para '\\n' (newline) funciona.")
        elif "\n" in pk:
            print("✅ Chave contém newlines reais.")
    except Exception as e:
        print(f"❌ Erro ao acessar [google_service_account]: {e}")

    # Teste App
    try:
        app = st.secrets["app"]
        print("✅ Segredo [app] encontrado.")
        print(f"   Spreadsheet: {app['spreadsheet_name']}")
    except Exception as e:
        print(f"❌ Erro ao acessar [app]: {e}")

if __name__ == "__main__":
    # Simular ambiente streamlit se necessário ou apenas rodar se st.secrets estiver disponível
    try:
        test_secrets()
    except Exception as e:
        print(f"Não foi possível rodar o teste diretamente fora do Streamlit context: {e}")
        print("Isso é esperado se não estiver em um processo Streamlit.")
