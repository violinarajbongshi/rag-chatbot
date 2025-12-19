import os
import glob
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

    def ingest_directory(self, directory_path):
        if not os.path.exists(directory_path):
            return f"Directory not found: {directory_path}"
        
        all_documents = []
        files_processed = 0
        
        # Support recursive search for txt, md, csv
        patterns = ["*.txt", "*.md", "*.csv"]
        for pattern in patterns:
            # Case insensitive search logic could be complex with glob, 
            # assuming extensions are lowercase or properly matched.
            # We will iterate all files and check extensions to be robust.
            pass
            
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                file_name_lower = file.lower()
                
                try:
                    loader = None
                    if file_name_lower.endswith(".txt"):
                        loader = TextLoader(file_path)
                    elif file_name_lower.endswith(".md"):
                        loader = UnstructuredMarkdownLoader(file_path)
                    elif file_name_lower.endswith(".csv"):
                        loader = CSVLoader(file_path)
                    
                    if loader:
                        docs = loader.load()
                        all_documents.extend(docs)
                        files_processed += 1
                except Exception as e:
                    print(f"Error loading {file}: {e}")

        if not all_documents:
            return "No valid documents found in KB directory."

        try:
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            texts = text_splitter.split_documents(all_documents)
            
            self.vector_store = Chroma.from_documents(texts, self.embeddings)
            return f"Successfully ingested {len(texts)} chunks from {files_processed} files."
        except Exception as e:
            return f"Error creating vector store: {e}"

    def ask(self, query):
        if not self.vector_store:
            return "Knowledge Base is empty. Please load documents."
        
        qa = RetrievalQA.from_chain_type(llm=self.llm, chain_type="stuff", retriever=self.vector_store.as_retriever())
        return qa.run(query)
