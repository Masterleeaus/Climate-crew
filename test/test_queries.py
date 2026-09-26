"""
Test agents with natural language queries (requires GOOGLE_API_KEY)
"""
import sys
import os
sys.path.insert(0, ".")

# Check for API key
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("⚠️  GOOGLE_API_KEY not set in environment")
    print("Set it with: $env:GOOGLE_API_KEY='your-key'")
    print("\nRunning in fallback mode (tools only, no LLM)...")
    print()

print("=" * 60)
print("ClimateX.ai - Agent Query Tests")
print("=" * 60)

# Test via Orchestrator with natural language queries
from src.agents.orchestrator import OrchestratorAgent

orchestrator = OrchestratorAgent()

queries = [
    ("🌊 Ocean", "What are the ocean conditions near the Florida Keys?"),
    ("🦋 Biodiversity", "Search for Bengal Tiger species"),
    ("🌡️ Climate Anomaly", "Is there a heat wave in Delhi right now?"),
    ("🏭 Carbon Emissions", "What sectors produce carbon emissions?"),
]

for emoji_name, query in queries:
    print(f"\n{emoji_name}")
    print("-" * 40)
    print(f"Query: {query}\n")
    try:
        response = orchestrator.run(query)
        # Limit output length for readability
        if len(response) > 600:
            print(response[:600] + "...")
        else:
            print(response)
    except Exception as e:
        print(f"Error: {e}")

print("\n" + "=" * 60)
print("Query Tests Complete!")
print("=" * 60)
