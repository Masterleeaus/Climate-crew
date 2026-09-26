"""Main evaluation runner."""
import os
import time
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from .config import EvaluationConfig
from .dataset import load_dataset, filter_dataset
from .types import (
    EvaluationQuery,
    RunOutput,
    EvaluationResult,
    EvaluationReport,
    RetrievalResult,
    AgentOutput,
    DebateTrace,
    ThoughtTreeTrace,
    ThoughtTreeNode,
    MemoryOperation,
    MetricResult,
)
from .metrics import (
    compute_retrieval,
    compute_synthesis,
    compute_debate,
    compute_memory,
    compute_efficiency,
    compute_coordination,
    compute_thought_tree,
)
from .judges import LLMJudge
from .oracles import OracleRetrieval, OraclePlanner, OracleMemory
from .logging import EventLogger, Tracer
from .reports import create_report, format_report, save_report


class EvaluationRunner:
    """Main evaluation runner."""
    
    def __init__(self, config: EvaluationConfig):
        """
        Initialize evaluation runner.
        
        Args:
            config: Evaluation configuration
        """
        self.config = config
        self.logger = EventLogger(output_dir=config.output_dir)
        self.tracer = self.logger.get_tracer()
        
        # Initialize LLM judge if enabled
        self.llm_judge = None
        if config.use_llm_judge:
            try:
                self.llm_judge = LLMJudge(
                    model_name=config.llm_judge_model,
                    blind_evaluation=config.blind_evaluation
                )
            except Exception as e:
                print(f"Warning: Failed to initialize LLM judge: {e}")
        
        # Initialize oracles if needed
        self.oracle_retrieval = None
        self.oracle_planner = None
        self.oracle_memory = None
    
    def _setup_oracles(self, ground_truth_docs: Optional[Dict[str, str]] = None):
        """Setup oracle components if enabled."""
        if self.config.use_oracle_retrieval and ground_truth_docs:
            self.oracle_retrieval = OracleRetrieval(ground_truth_docs)
        
        if self.config.use_oracle_planner:
            self.oracle_planner = OraclePlanner()
        
        if self.config.use_oracle_memory:
            # For oracle memory, we'd need ground truth memories
            # For now, create empty oracle
            self.oracle_memory = OracleMemory({})
    
    def _run_system(
        self,
        query: EvaluationQuery
    ) -> RunOutput:
        """
        Run the multi-agent system on a query.
        
        This is a placeholder that should be replaced with actual system integration.
        In practice, this would call the orchestrator with the appropriate config.
        
        Args:
            query: Evaluation query
            
        Returns:
            RunOutput with system results
        """
        start_time = time.time()
        errors = []
        
        try:
            # This is a mock implementation - replace with actual system call
            # The actual implementation would:
            # 1. Initialize orchestrator with config
            # 2. Run query through system
            # 3. Capture all outputs, traces, etc.
            
            self.tracer.agent_start("orchestrator", {"query": query.query})
            
            # Mock retrieval results
            retrieval_results = []
            if self.config.enable_rag:
                if self.oracle_retrieval:
                    retrieval_results = self.oracle_retrieval.retrieve(
                        query.query,
                        query.expected_topics,
                        limit=self.config.rag_limit
                    )
                else:
                    # Mock retrieval - replace with actual RAG call
                    for i in range(min(5, len(query.expected_topics))):
                        retrieval_results.append(RetrievalResult(
                            document_id=f"doc_{i}",
                            content=f"Mock document content about {query.expected_topics[i] if i < len(query.expected_topics) else 'topic'}",
                            score=0.9 - i * 0.1,
                            rank=i + 1
                        ))
            
            # Mock agent outputs
            agent_outputs = []
            if self.config.agents_enabled.get("search_agent", False):
                agent_outputs.append(AgentOutput(
                    agent_name="search_agent",
                    output=f"Found information about {', '.join(query.expected_topics[:2])}",
                    tool_calls=[{"tool": "search", "query": query.query}]
                ))
            
            if self.config.agents_enabled.get("synthesizer", False):
                agent_outputs.append(AgentOutput(
                    agent_name="synthesizer",
                    output=query.ground_truth_answer[:200] + "...",  # Mock synthesis
                ))
            
            # Mock debate traces
            debate_traces = []
            if self.config.enable_debate:
                for round_num in range(min(2, self.config.max_debate_rounds)):
                    debate_traces.append(DebateTrace(
                        round=round_num + 1,
                        advocate_claim=f"Claim about {query.expected_topics[0] if query.expected_topics else 'topic'}",
                        critic_response="Counter-argument",
                        judge_decision="Consensus reached",
                        consensus_reached=round_num == 1
                    ))
            
            # Mock thought tree trace
            thought_tree_trace = None
            if self.config.enable_thought_tree:
                nodes = [
                    ThoughtTreeNode(
                        node_id="root",
                        state="Root",
                        visits=5,
                        value=2.5,
                        depth=0
                    ),
                    ThoughtTreeNode(
                        node_id="node1",
                        state="Research finding 1",
                        parent_id="root",
                        visits=3,
                        value=1.8,
                        depth=1
                    )
                ]
                thought_tree_trace = ThoughtTreeTrace(
                    root_node_id="root",
                    nodes=nodes,
                    iterations=self.config.thought_tree_iterations
                )
            
            # Mock memory operations
            memory_operations = []
            if self.config.enable_memory:
                if self.oracle_memory:
                    memory_operations = self.oracle_memory.retrieve(
                        query.query,
                        query.expected_topics
                    )
                else:
                    memory_operations.append(MemoryOperation(
                        operation_type="retrieve",
                        key="context",
                        value=f"Previous context about {query.query[:50]}"
                    ))
            
            # Mock final answer
            final_answer = query.ground_truth_answer[:300] + "..." if len(query.ground_truth_answer) > 300 else query.ground_truth_answer
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Mock token usage and cost
            token_usage = {
                "input_tokens": 500,
                "output_tokens": 300
            }
            cost_usd = 0.01  # Mock cost
            
            self.tracer.agent_end("orchestrator", {"answer": final_answer})
            
            return RunOutput(
                query=query.query,
                final_answer=final_answer,
                retrieval_results=retrieval_results,
                agent_outputs=agent_outputs,
                debate_traces=debate_traces,
                thought_tree_trace=thought_tree_trace,
                memory_operations=memory_operations,
                latency_ms=latency_ms,
                token_usage=token_usage,
                cost_usd=cost_usd,
                errors=errors
            )
            
        except Exception as e:
            errors.append(str(e))
            self.tracer.error("orchestrator", str(e))
            return RunOutput(
                query=query.query,
                final_answer="",
                errors=errors,
                latency_ms=(time.time() - start_time) * 1000
            )
    
    def _compute_metrics(
        self,
        run_output: RunOutput,
        query: EvaluationQuery
    ) -> List[MetricResult]:
        """Compute all metrics for a run."""
        metrics = []
        
        # Convert to dict for metric functions
        run_dict = {
            "query": run_output.query,
            "final_answer": run_output.final_answer,
            "retrieval_results": [
                {
                    "document_id": r.document_id,
                    "content": r.content,
                    "score": r.score,
                    "rank": r.rank,
                    "metadata": r.metadata
                }
                for r in run_output.retrieval_results
            ],
            "agent_outputs": [
                {
                    "agent_name": a.agent_name,
                    "output": a.output,
                    "tool_calls": a.tool_calls,
                    "metadata": a.metadata
                }
                for a in run_output.agent_outputs
            ],
            "debate_traces": [
                {
                    "round": d.round,
                    "advocate_claim": d.advocate_claim,
                    "critic_response": d.critic_response,
                    "judge_decision": d.judge_decision,
                    "consensus_reached": d.consensus_reached,
                    "metadata": d.metadata
                }
                for d in run_output.debate_traces
            ],
            "thought_tree_trace": {
                "root_node_id": run_output.thought_tree_trace.root_node_id if run_output.thought_tree_trace else None,
                "nodes": [
                    {
                        "node_id": n.node_id,
                        "value": n.value,
                        "visits": n.visits,
                        "depth": n.depth
                    }
                    for n in (run_output.thought_tree_trace.nodes if run_output.thought_tree_trace else [])
                ],
                "iterations": run_output.thought_tree_trace.iterations if run_output.thought_tree_trace else 0
            } if run_output.thought_tree_trace else None,
            "memory_operations": [
                {
                    "operation_type": m.operation_type,
                    "key": m.key,
                    "value": m.value,
                    "timestamp": m.timestamp.isoformat(),
                    "metadata": m.metadata
                }
                for m in run_output.memory_operations
            ],
            "latency_ms": run_output.latency_ms,
            "token_usage": run_output.token_usage,
            "cost_usd": run_output.cost_usd,
            "errors": run_output.errors
        }
        
        ground_truth_dict = {
            "expected_topics": query.expected_topics,
            "ground_truth_answer": query.ground_truth_answer
        }
        
        # LLM judge function for synthesis metrics
        llm_judge_fn = None
        if self.llm_judge:
            def judge_fn(answer, query, ground_truth):
                score, _ = self.llm_judge.absolute_scoring(answer, query, ground_truth)
                return score
            llm_judge_fn = judge_fn
        
        # Compute all metrics
        if self.config.enable_rag:
            metrics.extend(compute_retrieval(run_dict, ground_truth_dict).values())
        
        metrics.extend(compute_synthesis(run_dict, ground_truth_dict, llm_judge_fn).values())
        
        if self.config.enable_debate:
            metrics.extend(compute_debate(run_dict, ground_truth_dict).values())
        
        if self.config.enable_memory:
            metrics.extend(compute_memory(run_dict, ground_truth_dict).values())
        
        if self.config.enable_thought_tree:
            metrics.extend(compute_thought_tree(run_dict, ground_truth_dict).values())
        
        metrics.extend(compute_efficiency(run_dict, ground_truth_dict).values())
        metrics.extend(compute_coordination(run_dict, ground_truth_dict).values())
        
        return metrics
    
    def run_single(
        self,
        query: EvaluationQuery,
        ground_truth_docs: Optional[Dict[str, str]] = None
    ) -> EvaluationResult:
        """
        Run evaluation on a single query.
        
        Args:
            query: Evaluation query
            ground_truth_docs: Optional ground truth documents for oracle retrieval
            
        Returns:
            EvaluationResult
        """
        self._setup_oracles(ground_truth_docs)
        self.tracer.clear()
        
        # Run system
        run_output = self._run_system(query)
        
        # Compute metrics
        metrics = self._compute_metrics(run_output, query)
        
        # Create result
        result = EvaluationResult(
            query=query,
            run_output=run_output,
            metrics=metrics,
            config_name=self.config.config_name
        )
        
        # Log run
        if self.config.save_traces:
            run_dict = {
                "query": run_output.query,
                "final_answer": run_output.final_answer,
                "retrieval_results": [r.__dict__ for r in run_output.retrieval_results],
                "agent_outputs": [a.__dict__ for a in run_output.agent_outputs],
                "debate_traces": [d.__dict__ for d in run_output.debate_traces],
                "thought_tree_trace": run_output.thought_tree_trace.__dict__ if run_output.thought_tree_trace else None,
                "memory_operations": [m.__dict__ for m in run_output.memory_operations],
                "latency_ms": run_output.latency_ms,
                "token_usage": run_output.token_usage,
                "cost_usd": run_output.cost_usd,
                "errors": run_output.errors
            }
            self.logger.log_run(query.query, run_dict, self.config.config_name)
        
        return result
    
    def run_batch(
        self,
        queries: List[EvaluationQuery],
        ground_truth_docs: Optional[Dict[str, str]] = None
    ) -> List[EvaluationResult]:
        """
        Run evaluation on multiple queries.
        
        Args:
            queries: List of evaluation queries
            ground_truth_docs: Optional ground truth documents
            
        Returns:
            List of EvaluationResult
        """
        results = []
        
        for i, query in enumerate(queries):
            print(f"Running query {i+1}/{len(queries)}: {query.query[:50]}...")
            try:
                result = self.run_single(query, ground_truth_docs)
                results.append(result)
            except Exception as e:
                print(f"Error running query: {e}")
                # Create error result
                error_result = EvaluationResult(
                    query=query,
                    run_output=RunOutput(
                        query=query.query,
                        final_answer="",
                        errors=[str(e)]
                    ),
                    metrics=[],
                    config_name=self.config.config_name
                )
                results.append(error_result)
        
        return results


def run_evaluation(
    config: str = "full",
    dataset: str = "eval/data/benchmark.json",
    output_dir: Optional[str] = None,
    ground_truth_docs: Optional[Dict[str, str]] = None,
    **kwargs
) -> EvaluationReport:
    """
    Main entry point for evaluation.
    
    Args:
        config: Configuration preset name or path to config file
        dataset: Path to evaluation dataset JSON file
        output_dir: Optional output directory override
        ground_truth_docs: Optional ground truth documents for oracle retrieval
        **kwargs: Additional config overrides
        
    Returns:
        EvaluationReport
    """
    # Load config
    if isinstance(config, str) and config.endswith('.json'):
        # Load from file
        with open(config, 'r') as f:
            config_dict = json.load(f)
        eval_config = EvaluationConfig(**config_dict)
    else:
        # Use preset
        eval_config = EvaluationConfig.from_preset(config)
    
    # Apply overrides
    for key, value in kwargs.items():
        if hasattr(eval_config, key):
            setattr(eval_config, key, value)
    
    if output_dir:
        eval_config.output_dir = output_dir
    
    # Load dataset
    queries = load_dataset(dataset)
    
    # Create runner
    runner = EvaluationRunner(eval_config)
    
    # Run evaluation
    results = runner.run_batch(queries, ground_truth_docs)
    
    # Create report
    report = create_report(results, eval_config.config_name)
    
    # Save report
    if eval_config.save_metrics:
        report_path = Path(eval_config.output_dir) / f"report_{eval_config.config_name}.json"
        save_report(report, str(report_path), format="json")
        
        # Also save as markdown
        md_path = Path(eval_config.output_dir) / f"report_{eval_config.config_name}.md"
        save_report(report, str(md_path), format="markdown")
    
    return report
