"""Calibrated judge using gold anchor examples."""
from typing import Dict, List, Optional, Tuple, Any
from .llm_judge import LLMJudge


class CalibratedJudge:
    """LLM judge calibrated with gold anchor examples."""
    
    def __init__(
        self,
        anchor_examples: List[Dict[str, Any]],
        model_name: str = "gemini-1.5-pro",
        **kwargs
    ):
        """
        Initialize calibrated judge.
        
        Args:
            anchor_examples: List of dicts with keys:
                - query: str
                - answer: str
                - ground_truth: str
                - gold_score: float (0-1)
            model_name: LLM model name
            **kwargs: Additional args for LLMJudge
        """
        self.anchor_examples = anchor_examples
        self.judge = LLMJudge(model_name=model_name, **kwargs)
        self.calibration_offset = 0.0  # Will be computed from anchors
    
    def calibrate(self):
        """Calibrate judge using anchor examples."""
        if not self.anchor_examples:
            return
        
        predicted_scores = []
        gold_scores = []
        
        for example in self.anchor_examples:
            query = example["query"]
            answer = example["answer"]
            ground_truth = example.get("ground_truth", "")
            gold_score = example["gold_score"]
            
            predicted_score, _ = self.judge.absolute_scoring(
                answer, query, ground_truth
            )
            
            predicted_scores.append(predicted_score)
            gold_scores.append(gold_score)
        
        # Compute calibration offset (mean difference)
        if predicted_scores and gold_scores:
            mean_predicted = sum(predicted_scores) / len(predicted_scores)
            mean_gold = sum(gold_scores) / len(gold_scores)
            self.calibration_offset = mean_gold - mean_predicted
    
    def absolute_scoring(
        self,
        answer: str,
        query: str,
        ground_truth: Optional[str] = None
    ) -> Tuple[float, str]:
        """
        Score answer with calibration applied.
        
        Returns:
            Tuple of (calibrated_score: float, reasoning: str)
        """
        score, reasoning = self.judge.absolute_scoring(answer, query, ground_truth)
        calibrated_score = score + self.calibration_offset
        calibrated_score = max(0.0, min(1.0, calibrated_score))  # Clamp to [0, 1]
        
        return (calibrated_score, reasoning)
