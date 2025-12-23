import os
from langchain_community.document_loaders import CSVLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

load_dotenv()

def debug_ingest():
    # Pick one file that definitely exists
    file_path = "KB/Mobile App KB - faq_orders.csv"
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        # Try listing KB
        print("KB content:", os.listdir("KB"))
        return

    print(f"Loading {file_path}...")
    try:
        loader = CSVLoader(file_path)
        docs = loader.load()
        print(f"Loaded {len(docs)} documents (rows).")
        
        if docs:
            print("\n--- SAMPLE DOCUMENT (First Row) ---")
            print(docs[0].page_content)
            print("-----------------------------------\n")
            
        # Test Splitting
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        texts = text_splitter.split_documents(docs)
        print(f"Split into {len(texts)} chunks.")

        # Test Embedding (Dry run if key exists)
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            print("OPENAI_API_KEY found. Testing vector store creation (in-memory)...")
            embeddings = OpenAIEmbeddings(api_key=api_key)
            vector_store = Chroma.from_documents(texts, embeddings)
            
            # Simple retrieval test
            query = "How to create an order?"
            print(f"\nQuerying: '{query}'")
            retriever = vector_store.as_retriever()
            results = retriever.invoke(query)
            
            print(f"Retrieved {len(results)} results.")
            for i, res in enumerate(results):
                print(f"[Result {i+1}] {res.page_content[:200]}...")
        else:
             print("OPENAI_API_KEY not found. Skipping vector store test.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_ingest()
