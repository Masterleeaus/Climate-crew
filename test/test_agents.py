import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

print("=" * 60)
print(" CLIMATE FINANCE AGENT TEST")
print("=" * 60)

from src.agents import ClimateFinanceOrchestrator

orchestrator = ClimateFinanceOrchestrator()
print(" Orchestrator initialized\n")

queries = [
    "What is the climate risk for investing in Exxon Mobil (XOM)?",
    "What is the carbon price in the EU?",
    "Compare regulatory risk between USA, Germany, and China"
]

for query in queries:
    print(f"\n Query: {query}")
    print("-" * 50)
    try:
        response = orchestrator.run(query)
        print(response)
    except Exception as e:
        print(f"Error: {e}")
    print()
