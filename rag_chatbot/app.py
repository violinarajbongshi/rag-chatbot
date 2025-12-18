import streamlit as st
from rag_engine import RAGEngine

st.set_page_config(page_title="RAG Chatbot", layout="wide")

st.title("📚 RAG Chatbot")

# Sidebar
with st.sidebar:
    st.header("Configuration")
    provider = st.selectbox("LLM Provider", ["openai", "google", "ollama"])
    
    api_key = None
    model_name = "llama3"
    
    if provider == "ollama":
        model_name = st.text_input("Model Name", value="llama3", help="Make sure you have pulled this model using 'ollama pull <model>'")
    else:
        api_key = st.text_input("API Key", type="password")
    
    st.divider()
    st.header("Upload KB")
    uploaded_file = st.file_uploader("Upload a document", type=["txt", "md", "csv"])

# Initialize Session State
if "rag_engine" not in st.session_state:
    st.session_state.rag_engine = None

if "messages" not in st.session_state:
    st.session_state.messages = []

# Handle Upload
is_ready = (provider == "ollama") or (api_key)

if uploaded_file and is_ready:
    if st.button("Process Document"):
        with st.spinner("Processing..."):
            try:
                # Initialize engine if needed or updated
                engine = RAGEngine(api_key, provider, model_name)
                msg = engine.ingest_file(uploaded_file.getvalue(), uploaded_file.name)
                st.session_state.rag_engine = engine
                st.success(msg)
            except Exception as e:
                st.error(f"Error: {e}")

# Chat Interface
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask a question about your documents"):
    if not st.session_state.rag_engine:
        st.warning("Please configure the provider and upload a document first.")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = st.session_state.rag_engine.ask(prompt)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
