
import unittest
import sys
import os
from unittest.mock import MagicMock

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.agents.tool_builder_agent import ToolBuilderAgent

class TestToolBuilderIntegration(unittest.TestCase):
    def test_prompt_includes_datasources(self):
        agent = ToolBuilderAgent()
        prompt = agent.get_system_prompt()
        self.assertIn("AVAILABLE DATA SOURCES", prompt)
        self.assertIn("src.data_sources.open_meteo", prompt)

if __name__ == "__main__":
    unittest.main()
