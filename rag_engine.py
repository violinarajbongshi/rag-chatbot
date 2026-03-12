import os
import shutil
from langchain_community.document_loaders import TextLoader, CSVLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_ollama import OllamaEmbeddings
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain.prompts import PromptTemplate

class RAGEngine:
    def __init__(self, api_key=None, provider="openai", model_name="llama3"):
        self.provider = provider
        self.api_key = api_key
        self.model_name = model_name
        
        if provider == "openai":
            self.embeddings = OpenAIEmbeddings(api_key=api_key)
            self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=api_key)
        elif provider == "google":
            self.embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=api_key)
            self.llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=api_key)
        elif provider == "ollama":
            self.embeddings = OllamaEmbeddings(model=model_name)
            self.llm = ChatOllama(model=model_name)
        
        self.vector_store = None

    def ingest_directory(self, directory_path):
        if not os.path.exists(directory_path):
            return f"Directory not found: {directory_path}"
        
        all_documents = []
        files_processed = 0
        
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                file_name_lower = file.lower()
                
                try:
                    loader = None
                    if file_name_lower.endswith(".txt"):
                        loader = TextLoader(file_path)
                    elif file_name_lower.endswith(".md"):
                        loader = TextLoader(file_path)
                    elif file_name_lower.endswith(".csv"):
                        loader = CSVLoader(file_path)
                    
                    if loader:
                        docs = loader.load()
                        rel_path = os.path.relpath(file_path, directory_path)
                        for doc in docs:
                            doc.metadata["source"] = rel_path
                        all_documents.extend(docs)
                        files_processed += 1
                except Exception as e:
                    print(f"Error loading {file}: {e}")

        if not all_documents:
            return "No valid documents found in KB directory."

        try:
            persist_dir = os.path.join(directory_path, "../chroma_db")
            # Clear existing vector store to avoid duplicates
            if os.path.exists(persist_dir):
                shutil.rmtree(persist_dir)
            
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=300)
            texts = text_splitter.split_documents(all_documents)
            
            self.vector_store = Chroma.from_documents(
                texts, 
                self.embeddings,
                persist_directory=persist_dir
            )
            return f"Successfully ingested {len(texts)} chunks from {files_processed} files."
        except Exception as e:
            return f"Error creating vector store: {e}"

    def ask(self, query):
        if not self.vector_store:
            return "Knowledge Base is empty. Please load documents."
        
        prompt_template = """You are an internal Shiprocket SOP assistant.

Your role:
Help users quickly find instructions and processes from the Shiprocket SOP knowledge base.

Rules:
- Answer ONLY using the knowledge base provided. Be thorough when checking.
- Do not generate information outside the SOP.
- If the answer is not found, say:
  "This information is not available in the SOP knowledge base."

Response style:
- Keep answers concise and structured.
- Prefer step-by-step instructions.
- Use numbered steps when explaining processes.
- Provide the SOP reference link at the end.

Audience:
Assume the user is a Shiprocket support agent.
Provide clear troubleshooting steps they can follow while assisting sellers.
Avoid long explanations.
Focus on actionable instructions.

Context:
{context}

Question: {question}
Answer:"""
        
        PROMPT = PromptTemplate(
            template=prompt_template, input_variables=["context", "question"]
        )
        
        qa = RetrievalQA.from_chain_type(
            llm=self.llm, 
            chain_type="stuff", 
            retriever=self.vector_store.as_retriever(search_kwargs={"k": 5}), # Increased to 5 for better coverage
            chain_type_kwargs={"prompt": PROMPT}
        )
        
        result = qa.invoke(query)
        return result['result']
