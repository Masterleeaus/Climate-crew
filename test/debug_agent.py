import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.agents.biodiversity_agent import BiodiversityAgent

load_dotenv()

def debug_biodiversity():
    print("Initializing BiodiversityAgent...")
    api_key = os.getenv("GOOGLE_API_KEY")
    agent = BiodiversityAgent(google_api_key=api_key)
    
    print("Running Agent...")
    try:
        response = agent.run("Hello, just check basic status.")
        print(f"Response: {response}")
    except Exception as e:
        print(f"CRITICAL EXCEPTION: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_biodiversity()
