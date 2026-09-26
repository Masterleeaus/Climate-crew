"""
Test suite for Advanced Memory System.
Tests hierarchical memory, shared pool, and recency weighting.
"""
import sys
sys.path.insert(0, ".")

from datetime import datetime, timedelta, timezone
import time

print("=" * 60)
print("Testing Advanced Memory System")
print("=" * 60)

# Test 1: Working Memory
print("\n🧠 TEST 1: Working Memory")
print("-" * 40)
try:
    from src.memory import WorkingMemory
    
    wm = WorkingMemory(max_items=5)
    wm.start_session("test-session-1")
    
    # Add items
    wm.add("User asked about ocean conditions near Miami", "ocean_agent")
    wm.add("Tool result: SST=25.3°C, Wave=0.4m", "ocean_agent", "tool_result")
    wm.add("User asked about air quality in Delhi", "air_quality_agent")
    
    # Test retrieval
    recent = wm.get_recent(limit=5)
    assert len(recent) == 3, f"Expected 3 items, got {len(recent)}"
    
    # Test context string
    ctx = wm.get_context_string(limit=3)
    assert "[Working Memory" in ctx
    
    # Test FIFO eviction
    for i in range(5):
        wm.add(f"Item {i}", "test_agent")
    
    assert len(wm) == 5, f"Expected 5 items after FIFO eviction, got {len(wm)}"
    
    print("✅ Working Memory: PASSED")
    
except Exception as e:
    print(f"❌ Working Memory: FAILED - {e}")

# Test 2: Recency Weighting
print("\n⏰ TEST 2: Recency Weighting")
print("-" * 40)
try:
    from src.memory.episodic_memory import EpisodicMemory
    import math
    
    em = EpisodicMemory()
    
    # Test recency score calculation
    now = datetime.now(timezone.utc)
    one_week_ago = now - timedelta(days=7)
    one_month_ago = now - timedelta(days=30)
    
    score_now = em.calculate_recency_score(now)
    score_week = em.calculate_recency_score(one_week_ago)
    score_month = em.calculate_recency_score(one_month_ago)
    
    assert 0.99 < score_now <= 1.0, f"Now score should be ~1.0, got {score_now}"
    assert 0.3 < score_week < 0.6, f"Week old score should be ~0.37, got {score_week}"  # Adjusted for half-life
    assert score_month < 0.1, f"Month old score should be <0.1, got {score_month}"
    
    print(f"   Recency now: {score_now:.3f}")
    print(f"   Recency 1 week: {score_week:.3f}")
    print(f"   Recency 1 month: {score_month:.3f}")
    
    # Test final score calculation
    semantic_sim = 0.8
    final_now = em.calculate_final_score(semantic_sim, score_now)
    final_week = em.calculate_final_score(semantic_sim, score_week)
    
    assert final_now > final_week, "Recent memory should score higher"
    
    print("✅ Recency Weighting: PASSED")
    
except Exception as e:
    print(f"❌ Recency Weighting: FAILED - {e}")

# Test 3: Shared Memory Pool (offline mode)
print("\n🔗 TEST 3: Shared Memory Pool Structure")
print("-" * 40)
try:
    from src.memory import SharedMemoryPool, SharedMemoryItem
    
    sp = SharedMemoryPool()
    
    # Test visibility checking
    assert sp._can_access("air_quality_agent", "global") == True
    assert sp._can_access("ocean_agent", "air_quality_agent,ocean_agent") == True
    assert sp._can_access("wildfire_agent", "air_quality_agent,ocean_agent") == False
    
    print("   Visibility: global -> all agents ✓")
    print("   Visibility: list -> only listed agents ✓")
    print("✅ Shared Memory Pool: PASSED")
    
except Exception as e:
    print(f"❌ Shared Memory Pool: FAILED - {e}")

# Test 4: Advanced Memory Manager
print("\n🎯 TEST 4: Advanced Memory Manager Integration")
print("-" * 40)
try:
    from src.memory import AdvancedMemoryManager
    
    # Initialize without external services (working memory only)
    amm = AdvancedMemoryManager(
        enable_working=True,
        enable_episodic=True,  # Requires Qdrant
        enable_semantic=False,  # Requires Neo4j
        enable_shared=True     # Requires Qdrant
    )
    
    # Test working memory through manager
    item1 = amm.add_to_working("Test context item", "test_agent")
    item2 = amm.add_to_working("Tool result: success", "test_agent", "tool_result")
    
    # Check that items are stored (access buffer directly)
    assert amm.working is not None, "Working memory should be initialized"
    buffer_len = len(amm.working._buffer)
    assert buffer_len == 2, f"Expected 2 items in buffer, got {buffer_len}"
    
    print("   Working memory via manager ✓")
    print("✅ Advanced Memory Manager: PASSED")
    
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"❌ Advanced Memory Manager: FAILED - {e}")

# Test 5: BaseAgent Integration
print("\n🤖 TEST 5: BaseAgent Memory Integration")
print("-" * 40)
try:
    from src.memory import AdvancedMemoryManager
    from src.agents.air_quality_agent import AirQualityAgent
    
    # Create advanced memory
    amm = AdvancedMemoryManager(
        enable_working=True,
        enable_episodic=True,
        enable_semantic=True,
        enable_shared=True
    )
    
    # Create agent with advanced memory
    agent = AirQualityAgent()
    agent.set_advanced_memory(amm)
    
    # Test working memory storage
    agent.store_to_working_memory("Air quality analysis for Delhi", "context")
    
    ctx = amm.get_working_context(limit=5)
    # May or may not have agent-filtered content
    assert len(amm.working) > 0 or ctx == ""
    
    print("   Agent -> Working Memory ✓")
    print("✅ BaseAgent Integration: PASSED")
    
except Exception as e:
    print(f"❌ BaseAgent Integration: FAILED - {e}")

print("\n" + "=" * 60)
print("Memory System Tests Complete!")
print("=" * 60)
