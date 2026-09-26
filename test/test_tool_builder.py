
import unittest
import shutil
import os
import sys
from io import StringIO
from contextlib import redirect_stdout

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.agents.tool_builder_agent import ToolBuilderAgent
from src.agents.orchestrator import OrchestratorAgent

class TestToolBuilder(unittest.TestCase):
    def setUp(self):
        # Ensure we have a clean slate for dynamic tools
        self.test_tool_path = "src/tools/dynamic/test_math_tool.py"
        if os.path.exists(self.test_tool_path):
            os.remove(self.test_tool_path)

    def test_tool_creation_safety(self):
        """Test that dangerous imports are blocked."""
        agent = ToolBuilderAgent()
        
        # Try to make a dangerous tool
        dangerous_code = """
import os
import subprocess

def hack_system():
    subprocess.run("echo hacked")
"""
        result = agent.create_tool.invoke({
            "tool_name": "hack_tool", 
            "python_code": dangerous_code, 
            "description": "A bad tool"
        })
        
        self.assertIn("SECURITY ERROR", result)

    def test_orchestrator_integration(self):
        """Test that Orchestrator initializes ToolBuilder."""
        orch = OrchestratorAgent(google_api_key="dummy")
        self.assertIn("tool_builder", orch.agents)
        self.assertIsInstance(orch.agents["tool_builder"], ToolBuilderAgent)

    def tearDown(self):
        if os.path.exists(self.test_tool_path):
            os.remove(self.test_tool_path)

if __name__ == "__main__":
    unittest.main()
