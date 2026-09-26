import subprocess
import sys
import os
import tempfile
import logging

logger = logging.getLogger(__name__)

class SandboxRunner:
    def run_test(self, test_code: str, timeout: int = 10) -> dict:
        # Create a temporary file for the test
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp_file:
            tmp_file.write(test_code)
            tmp_path = tmp_file.name

        try:
            # Run the test file
            # We use the same python interpreter as the host
            result = subprocess.run(
                [sys.executable, tmp_path],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=os.getcwd() # Ensure it can import src modules if needed
            )
            
            success = (result.returncode == 0)
            return {
                "success": success,
                "output": result.stdout,
                "error": result.stderr if not success else ""
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error": "Execution timed out (possible infinite loop)."
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": f"Sandbox execution error: {str(e)}"
            }
        finally:
            # Clean up
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except:
                    pass
