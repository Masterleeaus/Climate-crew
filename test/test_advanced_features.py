"""
Test suite for Advanced Multi-Agent Features.
Tests meta-learning, dynamic routing, and collaboration protocols.
"""
import sys
sys.path.insert(0, ".")

print("=" * 60)
print("Testing Advanced Multi-Agent Features")
print("=" * 60)

# Test 1: Performance Store
print("\n📊 TEST 1: Performance Store")
print("-" * 40)
try:
    from src.memory.performance_store import PerformanceStore, RoutingRecord, AgentStats
    
    # Test AgentStats
    stats = AgentStats(agent_name="test_agent")
    stats.update(quality=0.9, latency_ms=100, success=True)
    stats.update(quality=0.8, latency_ms=150, success=True)
    stats.update(quality=0.7, latency_ms=200, success=False)
    
    assert stats.total_queries == 3
    assert abs(stats.avg_quality - 0.8) < 0.01
    assert abs(stats.success_rate - 0.667) < 0.01
    
    print(f"   AgentStats: {stats.total_queries} queries, avg quality {stats.avg_quality:.2f}")
    print("✅ Performance Store: PASSED")
    
except Exception as e:
    print(f"❌ Performance Store: FAILED - {e}")

# Test 2: Meta-Learner Structure
print("\n🧠 TEST 2: Meta-Learner Structure")
print("-" * 40)
try:
    from src.agents.meta_learning import MetaLearner, RoutingSuggestion
    
    # Create without Qdrant (offline mode)
    ml = MetaLearner(performance_store=None)
    
    # Test suggestion for empty history
    suggestion = ml.suggest_agent("What is the air quality in Delhi?")
    
    assert isinstance(suggestion, RoutingSuggestion)
    assert suggestion.confidence == 0.0  # No history yet
    
    print(f"   Suggestion: agent={suggestion.agent_name}, conf={suggestion.confidence:.2f}")
    print("✅ Meta-Learner Structure: PASSED")
    
except Exception as e:
    print(f"❌ Meta-Learner Structure: FAILED - {e}")

# Test 3: Dynamic Router Capabilities
print("\n🔀 TEST 3: Dynamic Router Capabilities")
print("-" * 40)
try:
    from src.agents.dynamic_router import DynamicRouter, AGENT_CAPABILITIES, QueryComplexity
    
    # Check capability registry
    assert "air_quality" in AGENT_CAPABILITIES
    assert "wildfire" in AGENT_CAPABILITIES
    assert "disaster_management" in AGENT_CAPABILITIES
    
    air_cap = AGENT_CAPABILITIES["air_quality"]
    assert "PM2.5" in air_cap.domains or "pollution" in air_cap.domains
    
    print(f"   Registered agents: {len(AGENT_CAPABILITIES)}")
    print(f"   Air quality domains: {air_cap.domains[:3]}...")
    print("✅ Dynamic Router Capabilities: PASSED")
    
except Exception as e:
    print(f"❌ Dynamic Router Capabilities: FAILED - {e}")

# Test 4: Negotiation Protocol
print("\n🤝 TEST 4: Negotiation Protocol")
print("-" * 40)
try:
    from src.agents.protocols.negotiation import NegotiationProtocol, InfoRequest, InfoResponse, RequestPriority
    
    # Test InfoRequest creation
    request = InfoRequest(
        from_agent="agent_a",
        to_agent="agent_b",
        query="What is the current situation?",
        priority=RequestPriority.HIGH
    )
    
    assert request.from_agent == "agent_a"
    assert request.to_agent == "agent_b"
    assert request.priority == RequestPriority.HIGH
    assert request.id is not None
    
    print(f"   Request ID: {request.id[:8]}...")
    print(f"   Priority: {request.priority.name}")
    print("✅ Negotiation Protocol: PASSED")
    
except Exception as e:
    print(f"❌ Negotiation Protocol: FAILED - {e}")

# Test 5: Message Bus
print("\n📨 TEST 5: Message Bus")
print("-" * 40)
try:
    from src.agents.protocols.message_bus import MessageBus, AgentMessage, MessageType
    
    bus = MessageBus(shared_memory=None, persist_messages=False)
    
    # Test subscription
    received_messages = []
    def message_handler(msg):
        received_messages.append(msg)
    
    bus.subscribe("test_agent", message_handler)
    
    # Test broadcast
    msg_id = bus.broadcast(
        content="Important climate update",
        source_agent="orchestrator",
        message_type=MessageType.KNOWLEDGE_SHARE
    )
    
    assert msg_id is not None
    assert len(received_messages) == 1
    assert received_messages[0].content == "Important climate update"
    
    print(f"   Message ID: {msg_id[:8]}...")
    print(f"   Received: {len(received_messages)} message(s)")
    print("✅ Message Bus: PASSED")
    
except Exception as e:
    print(f"❌ Message Bus: FAILED - {e}")

# Test 6: BaseAgent Collaboration Hooks
print("\n🤖 TEST 6: BaseAgent Collaboration Hooks")
print("-" * 40)
try:
    from src.agents.base import BaseAgent
    
    # Check new attributes exist
    class TestAgent(BaseAgent):
        def get_tools(self):
            return []
        def get_system_prompt(self):
            return "Test agent for climate queries"
    
    agent = TestAgent(name="test_agent")
    
    # Check collaboration attributes
    assert hasattr(agent, 'message_bus')
    assert hasattr(agent, 'negotiation_protocol')
    assert hasattr(agent, 'last_performance')
    assert hasattr(agent, 'can_help_with')
    assert hasattr(agent, 'request_from_peer')
    assert hasattr(agent, 'broadcast_knowledge')
    
    # Test can_help_with
    can_help, conf = agent.can_help_with("climate")
    assert isinstance(can_help, bool)
    assert isinstance(conf, float)
    
    print(f"   Agent has collaboration hooks ✓")
    print(f"   can_help_with('climate'): {can_help}, conf={conf:.2f}")
    print("✅ BaseAgent Collaboration: PASSED")
    
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"❌ BaseAgent Collaboration: FAILED - {e}")

# Test 7: Orchestrator Advanced Features
print("\n🎭 TEST 7: Orchestrator Advanced Features")
print("-" * 40)
try:
    from src.agents.orchestrator import OrchestratorAgent
    
    # Create orchestrator with advanced features disabled for speed
    orch = OrchestratorAgent(
        enable_dynamic_routing=False,
        enable_meta_learning=False,
        enable_collaboration=False
    )
    
    # Check keyword routing still works
    agent = orch._keyword_route("What is the air quality in Delhi?")
    assert agent == "air_quality"
    
    agent = orch._keyword_route("Earthquake in Tokyo")
    assert agent == "earthquake"
    
    agent = orch._keyword_route("How do I evacuate during a disaster?")
    assert agent == "disaster_management"
    
    print(f"   Keyword routing works ✓")
    print(f"   Agents available: {len(orch.agents)}")
    print("✅ Orchestrator Features: PASSED")
    
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"❌ Orchestrator Features: FAILED - {e}")

# Test 8: Full Import Check
print("\n📦 TEST 8: Full Import Check")
print("-" * 40)
try:
    from src.agents import (
        MetaLearner, RoutingSuggestion,
        DynamicRouter, QueryComplexity, RoutingDecision, AGENT_CAPABILITIES,
        NegotiationProtocol, InfoRequest, InfoResponse,
        MessageBus, AgentMessage
    )
    
    from src.memory import PerformanceStore, RoutingRecord, AgentStats
    
    print("   All imports successful ✓")
    print("✅ Import Check: PASSED")
    
except Exception as e:
    print(f"❌ Import Check: FAILED - {e}")

print("\n" + "=" * 60)
print("Advanced Multi-Agent Features Tests Complete!")
print("=" * 60)
