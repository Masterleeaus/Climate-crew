import sys
import traceback

sys.path.insert(0, ".")

print("Testing new data sources and agents...")
print("")

# Test data sources
print("=== DATA SOURCES ===")
try:
    from src.data_sources.noaa_ocean import NOAAOceanClient
    print("[OK] NOAAOceanClient imported")
except Exception as e:
    print(f"[FAIL] NOAAOceanClient: {e}")

try:
    from src.data_sources.gbif import GBIFClient
    print("[OK] GBIFClient imported")
except Exception as e:
    print(f"[FAIL] GBIFClient: {e}")

try:
    from src.data_sources.climate_trace import ClimateTraceClient
    print("[OK] ClimateTraceClient imported")
except Exception as e:
    print(f"[FAIL] ClimateTraceClient: {e}")

print("")
print("=== AGENTS ===")

# Test agents one by one
print("Testing OceanAgent...")
try:
    from src.agents.ocean_agent import OceanAgent
    agent = OceanAgent()
    tools = agent.get_tools()
    print(f"[OK] OceanAgent imported - tools: {[t.name for t in tools]}")
except Exception as e:
    print(f"[FAIL] OceanAgent: {e}")
    traceback.print_exc()

print("")
print("Testing BiodiversityAgent...")
try:
    from src.agents.biodiversity_agent import BiodiversityAgent
    agent = BiodiversityAgent()
    tools = agent.get_tools()
    print(f"[OK] BiodiversityAgent imported - tools: {[t.name for t in tools]}")
except Exception as e:
    print(f"[FAIL] BiodiversityAgent: {e}")
    traceback.print_exc()

print("")
print("Testing ClimateAnomalyAgent...")
try:
    from src.agents.climate_anomaly_agent import ClimateAnomalyAgent
    agent = ClimateAnomalyAgent()
    tools = agent.get_tools()
    print(f"[OK] ClimateAnomalyAgent imported - tools: {[t.name for t in tools]}")
except Exception as e:
    print(f"[FAIL] ClimateAnomalyAgent: {e}")
    traceback.print_exc()

print("")
print("Testing CarbonEmissionsAgent...")
try:
    from src.agents.carbon_emissions_agent import CarbonEmissionsAgent
    agent = CarbonEmissionsAgent()
    tools = agent.get_tools()
    print(f"[OK] CarbonEmissionsAgent imported - tools: {[t.name for t in tools]}")
except Exception as e:
    print(f"[FAIL] CarbonEmissionsAgent: {e}")
    traceback.print_exc()

print("")
print("=== ORCHESTRATOR ===")
try:
    from src.agents.orchestrator import OrchestratorAgent
    agent = OrchestratorAgent()
    print(f"[OK] OrchestratorAgent imported with agents: {list(agent.agents.keys())}")
except Exception as e:
    print(f"[FAIL] OrchestratorAgent: {e}")
    traceback.print_exc()

print("")
print("Done.")

