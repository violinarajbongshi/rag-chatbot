import streamlit as st
import os
from dotenv import load_dotenv
from rag_engine import RAGEngine

# Load environment variables
load_dotenv()

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

st.set_page_config(page_title="Shiprocket KB Checker", layout="wide")

st.title("📚 Shiprocket KB Checker")

# Sidebar
with st.sidebar:
    st.header("Configuration")
    provider = st.selectbox("LLM Provider", ["openai", "google", "ollama"])
    
    api_key = None
    model_name = "llama3"
    
    if provider == "ollama":
        model_name = st.text_input("Model Name", value="llama3", help="Make sure you have pulled this model using 'ollama pull <model>'")
    elif provider == "openai":
        # Check environment variable first
        api_key = os.getenv("OPENAI_API_KEY")
        
        # If not found, try st.secrets
        if not api_key:
            try:
                if "OPENAI_API_KEY" in st.secrets:
                    api_key = st.secrets["OPENAI_API_KEY"]
            except FileNotFoundError:
                pass
            except Exception:
                pass
            
        if not api_key:
            st.error("OPENAI_API_KEY not found in .env or secrets.")
            
    elif provider == "google":
        api_key = os.getenv("GOOGLE_API_KEY")
        
        if not api_key:
            try:
                if "GOOGLE_API_KEY" in st.secrets:
                    api_key = st.secrets["GOOGLE_API_KEY"]
            except FileNotFoundError:
                pass
            except Exception:
                pass
            
        if not api_key:
            st.error("GOOGLE_API_KEY not found in .env or secrets.")
    
    st.divider()
    st.header("Knowledge Base")
    if st.button("Reload Knowledge Base"):
        st.session_state.kb_loaded = False

    if st.button("Sync SOP Knowledge"):
        with st.spinner("Fetching latest SOPs from the site..."):
            try:
                import sys
                if BASE_DIR not in sys.path:
                    sys.path.append(BASE_DIR)
                
                from sop_crawler import crawl_sop_site
                count = crawl_sop_site("https://sites.google.com/shiprocket.com/sop-shiprocket/home")
                st.success(f"Successfully synced {count} SOP pages!")
                st.session_state.kb_loaded = False # Force reload
            except Exception as e:
                st.error(f"Sync failed: {e}")

# Initialize Session State
if "rag_engine" not in st.session_state:
    st.session_state.rag_engine = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "kb_loaded" not in st.session_state:
    st.session_state.kb_loaded = False

# Automatic or Triggered Ingestion
is_ready = (provider == "ollama") or (api_key)

if is_ready and not st.session_state.kb_loaded:
    with st.spinner("Scanning and Ingesting KB folder..."):
        try:
            kb_path = os.path.join(BASE_DIR, "KB")
            engine = RAGEngine(api_key, provider, model_name)
            msg = engine.ingest_directory(kb_path)
            st.session_state.rag_engine = engine
            st.session_state.kb_loaded = True
            st.success(msg)
        except Exception as e:
            st.error(f"Error loading KB: {e}")

# Chat Interface
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask a question about Shiprocket"):
    if not st.session_state.rag_engine or not st.session_state.kb_loaded:
        st.warning("Please configure the provider and ensure KB is loaded.")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = st.session_state.rag_engine.ask(prompt)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
