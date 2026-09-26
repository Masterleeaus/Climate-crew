"""
Test agent responses with LangSmith tracing enabled.
This tests the full agent.run() method to verify tracing captures tool calls.
"""
import sys
sys.path.insert(0, ".")

import os
from dotenv import load_dotenv
load_dotenv()

print("=" * 60)
print("ClimateX.ai - Testing Agent Responses with Tracing")
print("=" * 60)

# Check if LangSmith is configured
langsmith_key = os.getenv("LANGCHAIN_API_KEY") or os.getenv("LANGSMITH_API_KEY")
project = os.getenv("LANGCHAIN_PROJECT") or os.getenv("LANGSMITH_PROJECT") or "default"
if langsmith_key and langsmith_key != "your_langsmith_api_key_here":
    print(f"✅ LangSmith tracing ENABLED")
    print(f"   Project: {project}")
else:
    print("⚠️  LangSmith API key not configured - traces will not be sent to dashboard")
print()

# Test 1: Air Quality Agent
print("\n🌬️ AIR QUALITY AGENT - Full Response Test")
print("-" * 50)
try:
    from src.agents.air_quality_agent import AirQualityAgent
    
    agent = AirQualityAgent()
    print("Query: 'What is the air quality in Delhi?'")
    print("Running agent...")
    response = agent.run("What is the air quality in Delhi?")
    print(f"\nResponse:\n{response[:500]}..." if len(response) > 500 else f"\nResponse:\n{response}")
    print("\n[OK] AirQualityAgent response received!")
except Exception as e:
    print(f"[FAIL] AirQualityAgent: {e}")

# Test 2: Ocean Agent  
print("\n\n🌊 OCEAN AGENT - Full Response Test")
print("-" * 50)
try:
    from src.agents.ocean_agent import OceanAgent
    
    agent = OceanAgent()
    print("Query: 'What are ocean conditions near Miami?'")
    print("Running agent...")
    response = agent.run("What are ocean conditions near Miami?")
    print(f"\nResponse:\n{response[:500]}..." if len(response) > 500 else f"\nResponse:\n{response}")
    print("\n[OK] OceanAgent response received!")
except Exception as e:
    print(f"[FAIL] OceanAgent: {e}")

# Test 3: Orchestrator routing
print("\n\n🎯 ORCHESTRATOR - Routing + Response Test")
print("-" * 50)
try:
    from src.agents.orchestrator import OrchestratorAgent
    
    orchestrator = OrchestratorAgent()
    print("Query: 'Is there any earthquake activity in Japan?'")
    print("Running orchestrator (will route to EarthquakeAgent)...")
    response = orchestrator.run("Is there any earthquake activity in Japan?")
    print(f"\nResponse:\n{response[:500]}..." if len(response) > 500 else f"\nResponse:\n{response}")
    print("\n[OK] Orchestrator routing + response worked!")
except Exception as e:
    print(f"[FAIL] Orchestrator: {e}")

print("\n" + "=" * 60)
print("Testing Complete!")
print("=" * 60)