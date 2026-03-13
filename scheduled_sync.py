import os
import sys
from dotenv import load_dotenv
from sop_crawler import crawl_sop_site
from rag_engine import RAGEngine

# Load environment variables
load_dotenv()

def run_sync():
    print("Starting background SOP sync...")
    
    # Get BASE_DIR
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # 1. Crawl
    base_url = "https://sites.google.com/shiprocket.com/sop-shiprocket/home"
    count = crawl_sop_site(base_url)
    print(f"Crawler finished. Updated {count} files.")
    
    # 2. Re-ingest
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not found.")
        return
        
    engine = RAGEngine(api_key=api_key, provider="openai")
    kb_path = os.path.join(BASE_DIR, "KB")
    
    print("Re-ingesting Knowledge Base...")
    result = engine.ingest_directory(kb_path)
    print(result)
    print("Sync complete.")

if __name__ == "__main__":
    run_sync()
