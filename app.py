import streamlit as st
import os
from dotenv import load_dotenv
from rag_engine import RAGEngine

# Load environment variables
load_dotenv()

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

st.set_page_config(page_title="SOP AI ASSISTANT", layout="wide")

st.title("🤖 SOP AI ASSISTANT")

# Initialize Session State
if "rag_engine" not in st.session_state:
    st.session_state.rag_engine = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "kb_loaded" not in st.session_state:
    st.session_state.kb_loaded = False

# Configuration and Ingestion (Auto-load)
api_key = os.getenv("OPENAI_API_KEY")
provider = "openai" 
model_name = "gpt-4o-mini"

if not api_key:
    st.error("OPENAI_API_KEY not found in environment variables. Please check your .env file.")
    st.stop()

if not st.session_state.kb_loaded:
    with st.spinner("Initializing SOP Knowledge Base..."):
        try:
            kb_path = os.path.join(BASE_DIR, "KB")
            engine = RAGEngine(api_key, provider, model_name)
            
            # Try loading existing index first (Fast)
            if engine.load_existing_index(kb_path):
                st.session_state.rag_engine = engine
                st.session_state.kb_loaded = True
            else:
                # If no index, ingest (Slow)
                success, msg = engine.ingest_directory(kb_path)
                if success:
                    st.session_state.rag_engine = engine
                    st.session_state.kb_loaded = True
                else:
                    st.error(f"Failed to load Knowledge Base: {msg}")
                    # Keep kb_loaded = False to retry on next rerun
        except Exception as e:
            st.error(f"Error during initialization: {e}")

# Chat Interface
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask a question about Shiprocket SOPs"):
    if not st.session_state.rag_engine or not st.session_state.kb_loaded:
        st.warning("Knowledge Base is not ready. Please check for errors or wait for synchronization.")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Searching SOPs..."):
                response = st.session_state.rag_engine.ask(prompt)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
