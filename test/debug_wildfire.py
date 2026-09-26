import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# Load env before imports if needed
load_dotenv()

try:
    print("Importing WildfireAgent...")
    from src.agents.wildfire_agent import WildfireAgent
    print("Import successful.")

    print("Initializing WildfireAgent...")
    api_key = os.getenv("GOOGLE_API_KEY")
    firms_key = os.getenv("NASA_FIRMS_API_KEY")
    agent = WildfireAgent(google_api_key=api_key, firms_api_key=firms_key)
    print("Initialization successful.")

    print("Binding tools...")
    tools = agent.get_tools()
    print(f"Tools found: {[t.name for t in tools]}")
    
    # Try binding manually to see if Pydantic crashes
    if agent.llm:
        print("Binding to LLM...")
        agent.llm.bind_tools(tools)
        print("Bind successful.")

    print("Running Agent with query...")
    response = agent.run("Check fire risk in California.")
    print(f"Response: {response}")

except Exception as e:
    print(f"CRITICAL EXCEPTION: {e}")
    import traceback
    traceback.print_exc()
