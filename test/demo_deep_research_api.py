
import sys
import os
import logging
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Load env vars
load_dotenv()
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.agents.deep_research.router import router

# Create APP with real router (which uses real dependencies)
app = FastAPI()
app.include_router(router)

client = TestClient(app)

def run_real_test():
    print("="*60)
    print("🚀 STARTING REAL DEEP RESEARCH API TEST")
    print("="*60)
    
    query = "What are the latest advancements in solid-state batteries for EVs?"
    print(f"📝 Query: {query}")
    print("⏳ Sending request... (this may take 30-60 seconds)")
    
    try:
        response = client.post(
            "/deep-research/", 
            json={"query": query},
            timeout=120 # Allow time for deep research
        )
        
        print(f"📥 Response Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n📊 REPORT SUMMARY:")
            print("-" * 40)
            print(data["report"][:1000] + "..." if len(data["report"]) > 1000 else data["report"])
            print("-" * 40)
            
            print(f"\n🔗 SOURCES ({len(data['sources'])}):")
            for source in data["sources"]:
                print(f" - {source['title']}: {source['url']}")
                
            print("\n✅ Deep Research test PASSED")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_real_test()
