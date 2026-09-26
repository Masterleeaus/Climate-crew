
import unittest
import sys
import os

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.agents.orchestrator import OrchestratorAgent
from src.agents.tool_builder_agent import ToolBuilderAgent

class TestUniversalIntegration(unittest.TestCase):
    def test_all_agents_have_tool_builder(self):
        # Mock keys to avoid errors
        orch = OrchestratorAgent(google_api_key="dummy_key", firms_api_key="dummy")
        
        tool_builder = orch.agents.get("tool_builder")
        self.assertIsNotNone(tool_builder)
        self.assertIsInstance(tool_builder, ToolBuilderAgent)
        
        # Check specific agents
        agents_to_check = ["air_quality", "wildfire", "climatex_audit"]
        
        for name in agents_to_check:
            agent = orch.agents.get(name)
            self.assertIsNotNone(agent, f"Agent {name} missing")
            
            # Check if tool_builder was injected
            self.assertIsNotNone(agent.tool_builder, f"Agent {name} missing tool_builder instance")
            self.assertEqual(agent.tool_builder, tool_builder, f"Agent {name} has wrong tool_builder instance")

if __name__ == "__main__":
    unittest.main()
