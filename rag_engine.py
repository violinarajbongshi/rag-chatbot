import os
import tempfile
from langchain_community.document_loaders import TextLoader, UnstructuredMarkdownLoader, CSVLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_ollama import OllamaEmbeddings
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama

class RAGEngine:
    def __init__(self, api_key=None, provider="openai", model_name="llama3"):
        self.provider = provider
        self.api_key = api_key
        self.model_name = model_name
        
        if provider == "openai":
            if not api_key:
                raise ValueError("API Key required for OpenAI")
            self.embeddings = OpenAIEmbeddings(api_key=api_key)
            # Updated to use gpt-4o-mini
            self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=api_key)
        elif provider == "google":
            if not api_key:
                raise ValueError("API Key required for Google")
            self.embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=api_key)
            self.llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=api_key)
        elif provider == "ollama":
            self.embeddings = OllamaEmbeddings(model=model_name)
            self.llm = ChatOllama(model=model_name)
        else:
            raise ValueError("Unsupported provider")
        
        self.vector_store = None

    def ingest_file(self, file_content, file_name):
        # Handle case-insensitive extensions
        file_name_lower = file_name.lower()
        suffix = f".{file_name.split('.')[-1]}"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, mode='wb') as tmp_file:
            tmp_file.write(file_content)
            tmp_file_path = tmp_file.name
        
        try:
            if file_name_lower.endswith(".txt"):
                loader = TextLoader(tmp_file_path)
            elif file_name_lower.endswith(".md"):
                loader = UnstructuredMarkdownLoader(tmp_file_path)
            elif file_name_lower.endswith(".csv"):
                loader = CSVLoader(tmp_file_path)
            else:
                return f"Unsupported file format: {file_name}"

            documents = loader.load()
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            texts = text_splitter.split_documents(documents)
            
            self.vector_store = Chroma.from_documents(texts, self.embeddings)
            return f"Ingested {len(texts)} chunks from {len(documents)} rows/docs."
        except Exception as e:
            return f"Error ingestion: {e}"
        finally:
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)

    def ask(self, query):
        if not self.vector_store:
            return "Please upload a document first."
        
        qa = RetrievalQA.from_chain_type(llm=self.llm, chain_type="stuff", retriever=self.vector_store.as_retriever())
        return qa.run(query)
