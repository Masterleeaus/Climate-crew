import importlib
import inspect
import os
import sys
import logging
from typing import List, Callable, Dict

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

logger = logging.getLogger(__name__)

class DynamicToolLoader:
    def __init__(self, tools_dir: str = "src/tools/dynamic"):
        self.tools_dir = tools_dir
        self.loaded_tools: Dict[str, Callable] = {}
        
        # Ensure directory exists
        if not os.path.exists(tools_dir):
            os.makedirs(tools_dir)

    def load_tools(self) -> List[Callable]:
        """Scans the tools directory and loads all valid functions."""
        self.loaded_tools = {}
        tool_functions = []

        # Get absolute path
        abs_tools_dir = os.path.abspath(self.tools_dir)
        
        if not os.path.exists(abs_tools_dir):
            logger.warning(f"Tools directory {abs_tools_dir} does not exist.")
            return []

        for filename in os.listdir(abs_tools_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                module_name = filename[:-3]
                try:
                    # Import module
                    # We use relative import path assuming running from root
                    import_path = self.tools_dir.replace("/", ".").replace("\\", ".") + "." + module_name
                    
                    if import_path in sys.modules:
                        module = importlib.reload(sys.modules[import_path])
                    else:
                        module = importlib.import_module(import_path)

                    # Inspect for functions
                    for name, obj in inspect.getmembers(module):
                        if inspect.isfunction(obj):
                            # Basic check: functions should have docstrings to be used as tools
                            if obj.__doc__:
                                self.loaded_tools[name] = obj
                                tool_functions.append(obj)
                                logger.info(f"Loaded dynamic tool: {name}")
                
                except Exception as e:
                    logger.error(f"Failed to load tool {filename}: {e}")

        return tool_functions

    def get_tool(self, name: str) -> Callable:
        return self.loaded_tools.get(name)
