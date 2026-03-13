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
provider = "openai" # Default to OpenAI as per current setup, can be made dynamic from .env
model_name = "gpt-4o-mini"

if not api_key:
    st.error("OPENAI_API_KEY not found in environment variables. Please check your .env file.")
    st.stop()

if not st.session_state.kb_loaded:
    with st.spinner("Initializing Knowledge Base..."):
        try:
            kb_path = os.path.join(BASE_DIR, "KB")
            engine = RAGEngine(api_key, provider, model_name)
            msg = engine.ingest_directory(kb_path)
            st.session_state.rag_engine = engine
            st.session_state.kb_loaded = True
            # st.toast(msg) # Subtle notification
        except Exception as e:
            st.error(f"Error loading KB: {e}")

# Chat Interface
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask a question about Shiprocket SOPs"):
    if not st.session_state.rag_engine or not st.session_state.kb_loaded:
        st.warning("Knowledge Base is still loading. Please wait a moment.")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Searching SOPs..."):
                response = st.session_state.rag_engine.ask(prompt)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
