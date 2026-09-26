"""
Test script for Mem0 + Qdrant memory integration.
Run: python test/test_memory.py
"""

import sys
import os
sys.path.insert(0, ".")

from dotenv import load_dotenv
load_dotenv()


def test_memory_manager_init():
    """Test MemoryManager initialization."""
    print("=" * 50)
    print("Test 1: MemoryManager Initialization")
    print("=" * 50)
    
    from src.memory import MemoryManager
    
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    
    print(f"QDRANT_URL: {'Set' if qdrant_url else 'Not set'}")
    print(f"QDRANT_API_KEY: {'Set' if qdrant_api_key else 'Not set'}")
    
    if not qdrant_url or not qdrant_api_key:
        print("\n[SKIP] Qdrant not configured. Set QDRANT_URL and QDRANT_API_KEY in .env")
        return False
    
    mm = MemoryManager()
    print("[PASS] MemoryManager created")
    return mm


def test_memory_operations(mm):
    """Test memory add/search/get operations."""
    print("\n" + "=" * 50)
    print("Test 2: Memory Operations")
    print("=" * 50)
    
    if not mm:
        print("[SKIP] MemoryManager not available")
        return False
    
    # Test adding memory
    print("\n1. Adding test memories...")
    result1 = mm.add(
        "Critical wildfire detected in Amazon Basin, Brazil. Fire spread rate: 500 hectares/day.",
        agent_id="test_agent",
        metadata={"type": "alert", "severity": "high"}
    )
    print(f"   Added memory: {result1 is not None}")
    
    result2 = mm.add(
        "Earthquake magnitude 6.2 detected near Tokyo, Japan. Depth: 35km.",
        agent_id="test_agent",
        metadata={"type": "alert", "severity": "medium"}
    )
    print(f"   Added memory: {result2 is not None}")
    
    result3 = mm.add(
        "Air quality in Delhi reached hazardous levels. PM2.5: 450 ug/m3.",
        agent_id="test_agent",
        metadata={"type": "alert", "severity": "high"}
    )
    print(f"   Added memory: {result3 is not None}")
    
    # Test searching memory
    print("\n2. Searching memories...")
    results = mm.search("fires in South America rainforest", agent_id="test_agent", limit=3)
    print(f"   Found {len(results)} relevant memories for 'fires in South America'")
    for r in results:
        memory_text = r.get("memory", r.get("text", "N/A"))
        print(f"   - {memory_text[:80]}...")
    
    # Test context string
    print("\n3. Getting context string...")
    context = mm.get_context_string("What fires are happening?", agent_id="test_agent")
    print(f"   Context:\n{context[:200]}..." if context else "   No context available")
    
    # Test get all
    print("\n4. Getting all memories...")
    all_memories = mm.get_all(agent_id="test_agent")
    print(f"   Total memories for test_agent: {len(all_memories)}")
    
    print("\n[PASS] Memory operations completed")
    return True


def test_agent_with_memory():
    """Test agent integration with memory."""
    print("\n" + "=" * 50)
    print("Test 3: Agent with Memory Integration")
    print("=" * 50)
    
    from src.memory import MemoryManager
    from src.agents import AirQualityAgent
    
    qdrant_url = os.getenv("QDRANT_URL")
    if not qdrant_url:
        print("[SKIP] Qdrant not configured")
        return False
    
    # Create shared memory manager
    mm = MemoryManager()
    
    # Create agent with memory
    agent = AirQualityAgent(memory_manager=mm)
    print(f"Agent: {agent.name}")
    print(f"Memory enabled: {agent.enable_memory}")
    print(f"Memory manager: {'Connected' if agent.memory else 'Not connected'}")
    
    # Run a query (this will use memory if available)
    print("\nRunning query: 'What is the air quality in Delhi?'")
    result = agent.run("What is the air quality in Delhi?")
    print(f"Result: {result[:200]}...")
    
    # Check if memory was stored
    print("\nChecking stored memories...")
    memories = mm.get_all(agent_id=agent.name)
    print(f"Memories stored for {agent.name}: {len(memories)}")
    
    print("\n[PASS] Agent with memory test completed")
    return True


def cleanup_test_memories():
    """Clean up test memories."""
    print("\n" + "=" * 50)
    print("Cleanup: Removing test memories")
    print("=" * 50)
    
    from src.memory import MemoryManager
    
    qdrant_url = os.getenv("QDRANT_URL")
    if not qdrant_url:
        return
    
    mm = MemoryManager()
    mm.clear_agent_memories("test_agent")
    print("[DONE] Test memories cleared")


if __name__ == "__main__":
    print("\n[Convolve_MAS] Memory Integration Test Suite\n")
    
    # Check env vars
    print(f"GOOGLE_API_KEY: {'Set' if os.getenv('GOOGLE_API_KEY') else 'Not set'}")
    print(f"QDRANT_URL: {'Set' if os.getenv('QDRANT_URL') else 'Not set'}")
    print(f"QDRANT_API_KEY: {'Set' if os.getenv('QDRANT_API_KEY') else 'Not set'}")
    print()
    
    results = []
    
    # Test 1: Initialization
    mm = test_memory_manager_init()
    results.append(("MemoryManager Init", mm is not False))
    
    # Test 2: Memory operations
    if mm:
        results.append(("Memory Operations", test_memory_operations(mm)))
    
    # Test 3: Agent integration
    results.append(("Agent Integration", test_agent_with_memory()))
    
    # Cleanup
    # cleanup_test_memories()  # Uncomment to clean up after tests
    
    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    for name, passed in results:
        status = "[PASS]" if passed else "[SKIP/FAIL]"
        print(f"  {name}: {status}")
    
    print("\nNote: To run full tests, set these in .env:")
    print("  QDRANT_URL=https://your-cluster.qdrant.io")
    print("  QDRANT_API_KEY=your_api_key")
