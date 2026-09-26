
import sys
import os
import shutil
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.agents.orchestrator import OrchestratorAgent
from src.agents.base import BaseAgent
from src.agents.tool_builder_agent import ToolBuilderAgent

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')

def clean_dynamic_tools():
    dynamic_dir = "src/tools/dynamic"
    if os.path.exists(dynamic_dir):
        for f in os.listdir(dynamic_dir):
            if f.endswith(".py") and f != "__init__.py":
                os.remove(os.path.join(dynamic_dir, f))
    print(" Dynamic tools cleaned.")

def run_demo():
    
    clean_dynamic_tools()
    
    # 2. Initialize Orchestrator
    # We use a dummy API key if env not set, just for structure initialization
    api_key = os.getenv("GOOGLE_API_KEY")
    orchestrator = OrchestratorAgent(google_api_key=api_key)
    
    # 3. Define a query for a tool that DOES NOT exist
    # New Metric: "Atmospheric Density Index" = (Temperature * Pressure) / Humidity
    # This assumes we have access to variables, or the tool will take them as args.
    query = "Calculate the Atmospheric Density Index (ADI) given temperature=25, pressure=1013, and humidity=60. Formula is (temp * pressure) / humidity."
    
    print(f" User Query: {query}")
    print("   (Note: No tool exists for 'Atmospheric Density Index'.)\n")
    
    # 4. Run Orchestrator
    # This should trigger route -> ToolBuilder -> Create Tool -> Run Tool
    print("  Orchestrator Running...\n")
    response = orchestrator.run(query)
    
    print("\n Final Response:\n")
    print(response)
    
    # 5. Verify Tool Execution (Ephemeral)
    print("\n Verifying Ephemeral Execution...\n")
    
    if "Solved (Ephemeral Mode)" in str(response) and "Answer" in str(response):
        print("\n SUCCESS: Tool was generated, verified, and executed ephemerally!")
        print("   (No file was left on disk, as requested).")
    else:
        print("\n FAILURE: Response did not indicate successful ephemeral execution.")
        
    # Verify no file exists
    found_tool = False
    dynamic_dir = "src/tools/dynamic"
    if os.path.exists(dynamic_dir):
        for f in os.listdir(dynamic_dir):
            if f.endswith(".py") and "adi" in f.lower():
                found_tool = True
    
    if found_tool:
        print("   WARNING: A tool file WAS found on disk. Cleanup required.")
    else:
        print("   Verified: No tool file remaining on disk.")

if __name__ == "__main__":
    run_demo()
