"""
Demo script for testing advanced multi-agent features with real queries.
"""
import sys
sys.path.insert(0, ".")

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from src.agents.orchestrator import OrchestratorAgent

print("=" * 60)
print("🚀 Testing Advanced Multi-Agent System with Queries")
print("=" * 60)

# Create orchestrator with dynamic routing enabled
print("\n⏳ Initializing Orchestrator with advanced features...")
orch = OrchestratorAgent(
    enable_dynamic_routing=True,
    enable_meta_learning=True,
    enable_collaboration=True
)
print("✅ Orchestrator initialized!")

# Test queries
test_queries = [
    "What is the air quality in Delhi today?",
    "Are there any active wildfires in California?",
    "What's the earthquake activity near Tokyo?",
]

print("\n" + "=" * 60)
print("🔍 Testing Query Routing")
print("=" * 60)

for query in test_queries:
    print(f"\n📝 Query: {query}")
    print("-" * 40)
    
    # Test routing decision (without executing full agent)
    if orch.dynamic_router:
        decision = orch.dynamic_router.route(query)
        print(f"   🎯 Primary Agent: {decision.primary_agent}")
        print(f"   📊 Confidence: {decision.confidence:.2f}")
        print(f"   🔀 Complexity: {decision.complexity.value}")
        print(f"   🤝 Secondary Agents: {decision.secondary_agents or 'None'}")
        print(f"   💬 Reasoning: {decision.reasoning[:100]}..." if len(decision.reasoning) > 100 else f"   💬 Reasoning: {decision.reasoning}")
        print(f"   📌 Source: {decision.source}")
    else:
        # Fallback keyword routing
        agent = orch._keyword_route(query)
        print(f"   🎯 Keyword Route: {agent}")

print("\n" + "=" * 60)
print("🧪 Testing Full Query Execution (1 sample)")  
print("=" * 60)

# Run a single query to test the full pipeline
sample_query = "What is the current air quality index?"
print(f"\n📝 Executing: {sample_query}")
print("-" * 40)

try:
    response = orch.run(sample_query)
    print(f"✅ Response received ({len(response)} chars):")
    print(response[:500] + "..." if len(response) > 500 else response)
except Exception as e:
    print(f"⚠️ Execution error (expected if no API key): {e}")

print("\n" + "=" * 60)
print("📈 Agent Performance Stats")
print("=" * 60)

stats = orch.get_agent_performance()
if stats:
    for agent, perf in stats.items():
        print(f"   {agent}: {perf}")
else:
    print("   No performance data yet (meta-learning will populate over time)")

print("\n✅ Demo complete!")
