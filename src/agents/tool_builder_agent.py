import os
import ast
import logging
from typing import List, Callable, Optional, Dict, Any, Tuple
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage

from .base import BaseAgent
from ..utils.dynamic_tool_loader import DynamicToolLoader
from ..utils.sandbox_runner import SandboxRunner

logger = logging.getLogger(__name__)

class ToolBuilderAgent(BaseAgent):
    def __init__(self, google_api_key: Optional[str] = None, memory_manager: Any = None):
        super().__init__("ToolBuilderAgent", google_api_key, memory_manager)
        self.tool_loader = DynamicToolLoader()
        self.sandbox = SandboxRunner()
        self.tools_dir = "src/tools/dynamic"
        os.makedirs(self.tools_dir, exist_ok=True)

    def get_system_prompt(self) -> str:
        return """You are an Autonomous AI Engineer.
You build Python tools to solve problems that existing tools cannot handling.
You follow a Test-Driven Development (TDD) approach:
1. Write a standalone Python function with type hints.
2. Write a `unittest` test case to verify it.

AVAILABLE DATA SOURCES (You can import these):
- Weather: `from src.data_sources.open_meteo import OpenMeteoClient`
- Earthquakes: `from src.data_sources.usgs_earthquake import USGSEarthquakeClient`
- Air Quality: `from src.data_sources.openaq import OpenAQClient`
- Ocean Data: `from src.data_sources.noaa_ocean import NOAAOceanClient`
- Emissions: `from src.data_sources.climate_trace import ClimateTraceClient`
- NASA Fires: `from src.data_sources.nasa_firms import NASAFirmsClient`

EXAMPLE USAGE:
```python
from src.data_sources.open_meteo import OpenMeteoClient
client = OpenMeteoClient()
data = client.get_weather(lat, lon)
```
"""

    def get_tools(self) -> List[Callable]:
        return [] # No external tools, it operates via internal loop

    def _generate_code(self, query: str, error_context: str = "") -> Tuple[str, str]:
        """Generates tool code and test code components."""
        
        prompt = f"""
        TASK: {query}
        
        {f"PREVIOUS ERROR TO FIX: {error_context}" if error_context else ""}
        
        Generate TWO code blocks:
        1. The implementation code (function).
        2. A complete `unittest` script that imports the function (assume it's in the same file or importable) and tests it.
        
        Format your response EXACTLY like this:
        
        ```python
        # IMPLEMENTATION
        def my_tool(...):
           ...
        ```
        
        ```python
        # TEST
        import unittest
        class TestTool(unittest.TestCase):
            ...
        if __name__ == '__main__':
            unittest.main()
        ```
        """
        
        response = self.llm.invoke([
             SystemMessage(content=self.get_system_prompt()),
             HumanMessage(content=prompt)
        ])
        content = response.content
        
        # Naive parsing of code blocks
        blocks = []
        lines = content.split('\n')
        in_block = False
        current_block = []
        
        for line in lines:
            if "```python" in line:
                in_block = True
                current_block = []
                continue
            if "```" in line and in_block:
                in_block = False
                blocks.append("\n".join(current_block))
                continue
            if in_block:
                current_block.append(line)
                
        if len(blocks) >= 2:
            return blocks[0], blocks[1]
        elif len(blocks) == 1:
            return blocks[0], "" # Fallback
        return "", ""

    def _combine_for_test(self, tool_code: str, test_code: str) -> str:
        """Combines tool and test into one script for the sandbox."""
        # Remove any main block from tool_code to avoid conflicts
        return f"{tool_code}\n\n{test_code}"

    def build_and_execute(self, query: str, context_data: Optional[Dict] = None) -> str:
        """
        TDD Execution Loop:
        1. Generate Code & Test.
        2. Run Test in Sandbox.
        3. Fails? -> Loop with error feedback.
        4. Success? -> Save tool -> Load -> Execute.
        """
        attempts = 0
        max_retries = 3
        error_log = ""
        
        while attempts < max_retries:
            tool_code, test_code = self._generate_code(query, error_log)
            
            if not tool_code or not test_code:
                error_log = "Failed to parse code blocks."
                attempts += 1
                continue
                
            # Verify in Sandbox
            combined_script = self._combine_for_test(tool_code, test_code)
            result = self.sandbox.run_test(combined_script)
            
            if result["success"]:
                # EPHEMERAL MODE: Do not save to disk.
                # Instead, immediately run the tool to answer the query.
                
                runner_script = self._generate_runner(tool_code, query)
                run_result = self.sandbox.run_test(runner_script)
                
                if run_result["success"]:
                    return f"✅ **Solved (Ephemeral Mode)**\n\n**Answer**:\n{run_result['output']}\n\n**Generated Tool Code**:\n```python\n{tool_code}\n```"
                else:
                    return f"Tool verified, but runtime execution failed for this specific query.\nError: {run_result['error']}"
            
            else:
                error_log = f"Test Failed:\n{result['error']}\nOutput:\n{result['output']}"
                attempts += 1
        
        return f"Failed to build tool after {max_retries} attempts. Last error: {error_log}"

    def _generate_runner(self, tool_code: str, query: str) -> str:
        """Generates a script that defines the tool and calls it to answer the query."""
        prompt = f"""
        We have a verified python tool:
        ```python
        {tool_code}
        ```
        
        The user asked: "{query}"
        
        Generate a python script that:
        1. Includes the tool definition above.
        2. Calls the tool with the appropriate arguments derived from the user's query.
        3. Prints the FINAL ANSWER to stdout.
        
        Output ONLY the python code.
        """
        
        response = self.llm.invoke([{"role": "user", "content": prompt}])
        content = response.content
        
        # Clean markdown
        if "```python" in content:
            content = content.split("```python")[1].split("```")[0]
            
        return content

    def _extract_function_name(self, code: str) -> str:
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    return node.name
        except:
            return ""
        return ""
