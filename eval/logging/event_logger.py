"""Event logger for evaluation runs."""
import json
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from .tracer import Tracer


class EventLogger:
    """Logger for evaluation events."""
    
    def __init__(self, output_dir: str = "eval/outputs"):
        """
        Initialize event logger.
        
        Args:
            output_dir: Directory to save logs
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.tracer = Tracer()
    
    def log_run(
        self,
        query: str,
        run_output: Dict[str, Any],
        config_name: str,
        run_id: Optional[str] = None
    ):
        """
        Log a complete evaluation run.
        
        Args:
            query: Evaluation query
            run_output: RunOutput as dict
            config_name: Configuration name
            run_id: Optional run ID (generated if not provided)
        """
        if run_id is None:
            run_id = f"{config_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        log_data = {
            "run_id": run_id,
            "query": query,
            "config_name": config_name,
            "timestamp": datetime.now().isoformat(),
            "run_output": run_output,
            "trace": self.tracer.get_trace(),
        }
        
        # Save to file
        log_file = self.output_dir / f"{run_id}.json"
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, default=str)
        
        return log_file
    
    def get_tracer(self) -> Tracer:
        """Get the tracer instance."""
        return self.tracer
