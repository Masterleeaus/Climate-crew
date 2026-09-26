"""Debug script to fully trace the error"""
import sys
sys.path.insert(0, ".")
import traceback

# Skip the __init__.py chain - import directly
print("Importing base...")
from src.agents.base import BaseAgent
print("BaseAgent imported OK")

print("\nImporting noaa_ocean data sources...")
from src.data_sources.noaa_ocean import NOAAOceanClient, CoralReefWatchClient, OpenMeteoMarineClient
print("Data sources imported OK")

print("\nNow executing ocean_agent.py...")
# Read and exec the ocean_agent.py file directly
with open("src/agents/ocean_agent.py", encoding="utf-8") as f:
    code = f.read()

# Create namespace with necessary imports
namespace = {
    "__name__": "__main__",
    "BaseAgent": BaseAgent,
    "NOAAOceanClient": NOAAOceanClient,
    "CoralReefWatchClient": CoralReefWatchClient,
    "OpenMeteoMarineClient": OpenMeteoMarineClient,
}

# Add the standard imports to namespace
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
from langchain_core.tools import tool
namespace.update({
    "Any": Any, "Dict": Dict, "List": List, "Optional": Optional, "Callable": Callable,
    "datetime": datetime, "tool": tool
})

try:
    # Compile and exec with detailed traceback
    compiled = compile(code, "ocean_agent.py", "exec")
    exec(compiled, namespace)
    print("SUCCESS: ocean_agent.py executed without errors")
except Exception as e:
    print(f"FAILED: {e}")
    traceback.print_exc()
