import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from eval import run_evaluation
from eval.config import EvaluationConfig


def test_offline_baseline_evaluation(tmp_path):
    """Exercise the committed benchmark through the no-provider baseline path."""
    dataset_path = Path(__file__).resolve().parent.parent / "eval" / "data" / "benchmark.json"
    output_dir = tmp_path / "offline-baseline"

    report = run_evaluation(
        config="baseline",
        dataset=str(dataset_path),
        output_dir=str(output_dir),
        use_llm_judge=False,
    )

    assert report.total_queries == 3
    assert report.successful_runs == 3
    assert report.failed_runs == 0
    assert report.aggregate_metrics

def test_basic_evaluation():
    """Test basic evaluation with mock system."""
    print("=" * 80)
    print("Testing Evaluation System")
    print("=" * 80)
    
    # Test with baseline config (no LLM judge to avoid API key requirement)
    print("\n1. Testing with baseline config (no LLM judge)...")
    try:
        config = EvaluationConfig.from_preset("baseline")
        config.use_llm_judge = False  # Disable LLM judge for testing
        config.output_dir = "eval/outputs/test"
        config.config_name = "test_baseline"
        
        dataset_path = "eval/data/benchmark.json"
        if not Path(dataset_path).exists():
            print(f"ERROR: Dataset file not found: {dataset_path}")
            return False
        
        print(f"   - Config: {config.config_name}")
        print(f"   - Dataset: {dataset_path}")
        print(f"   - Output dir: {config.output_dir}")
        print(f"   - LLM Judge: {config.use_llm_judge}")
        
        report = run_evaluation(
            config="baseline",
            dataset=dataset_path,
            output_dir=config.output_dir,
            use_llm_judge=False
        )
        
        print(f"\n   ✓ Evaluation completed successfully!")
        print(f"   - Total queries: {report.total_queries}")
        print(f"   - Successful runs: {report.successful_runs}")
        print(f"   - Failed runs: {report.failed_runs}")
        print(f"   - Aggregate metrics: {len(report.aggregate_metrics)}")
        
        if report.aggregate_metrics:
            print(f"\n   Sample metrics:")
            for metric in report.aggregate_metrics[:5]:  # Show first 5
                print(f"     - {metric.metric_name}: {metric.mean:.4f} (std: {metric.std:.4f})")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_presets():
    """Test different config presets."""
    print("\n2. Testing config presets...")
    
    presets = ["baseline", "full", "no_debate", "no_memory", "single_agent"]
    
    for preset in presets:
        try:
            config = EvaluationConfig.from_preset(preset)
            print(f"   ✓ {preset}: {config.config_name}")
        except Exception as e:
            print(f"   ✗ {preset}: {e}")
            return False
    
    return True


def test_single_query():
    """Test evaluation on a single query."""
    print("\n3. Testing single query evaluation...")
    
    try:
        from eval.runner import EvaluationRunner
        from eval.types import EvaluationQuery, Difficulty
        from eval.config import EvaluationConfig
        
        config = EvaluationConfig.from_preset("baseline")
        config.use_llm_judge = False
        config.output_dir = "eval/outputs/test"
        
        runner = EvaluationRunner(config)
        
        query = EvaluationQuery(
            query="What is climate change?",
            expected_topics=["climate", "global warming", "temperature"],
            ground_truth_answer="Climate change refers to long-term changes in global temperatures and weather patterns.",
            difficulty=Difficulty.SIMPLE,
            requires_multihop=False,
            requires_debate=False,
            requires_memory=False
        )
        
        result = runner.run_single(query)
        
        print(f"   ✓ Single query evaluation completed")
        print(f"   - Query: {query.query[:50]}...")
        print(f"   - Metrics computed: {len(result.metrics)}")
        print(f"   - Answer length: {len(result.run_output.final_answer)} chars")
        print(f"   - Latency: {result.run_output.latency_ms:.2f} ms")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_metrics_computation():
    """Test individual metric computations."""
    print("\n4. Testing metric computations...")
    
    try:
        from eval.types import RunOutput, RetrievalResult, AgentOutput
        from eval.metrics import (
            compute_retrieval,
            compute_synthesis,
            compute_efficiency,
            compute_coordination
        )
        
        # Create mock run output
        run_output = {
            "query": "Test query",
            "final_answer": "This is a test answer about climate change and renewable energy.",
            "retrieval_results": [
                {
                    "document_id": "doc1",
                    "content": "Climate change is caused by greenhouse gases.",
                    "score": 0.9,
                    "rank": 1
                },
                {
                    "document_id": "doc2",
                    "content": "Renewable energy sources include solar and wind.",
                    "score": 0.8,
                    "rank": 2
                }
            ],
            "agent_outputs": [
                {
                    "agent_name": "search_agent",
                    "output": "Found information about climate change",
                    "tool_calls": []
                }
            ],
            "latency_ms": 150.5,
            "token_usage": {"input_tokens": 100, "output_tokens": 50},
            "cost_usd": 0.001,
            "errors": []
        }
        
        ground_truth = {
            "expected_topics": ["climate change", "renewable energy"],
            "ground_truth_answer": "Climate change and renewable energy are important topics."
        }
        
        # Test retrieval metrics
        retrieval_metrics = compute_retrieval(run_output, ground_truth)
        print(f"   ✓ Retrieval metrics: {len(retrieval_metrics)} metrics")
        
        # Test synthesis metrics
        synthesis_metrics = compute_synthesis(run_output, ground_truth, llm_judge_fn=None)
        print(f"   ✓ Synthesis metrics: {len(synthesis_metrics)} metrics")
        
        # Test efficiency metrics
        efficiency_metrics = compute_efficiency(run_output, ground_truth)
        print(f"   ✓ Efficiency metrics: {len(efficiency_metrics)} metrics")
        
        # Test coordination metrics
        coordination_metrics = compute_coordination(run_output, ground_truth)
        print(f"   ✓ Coordination metrics: {len(coordination_metrics)} metrics")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("EVALUATION SYSTEM TEST SUITE")
    print("=" * 80)
    
    results = []
    
    # Test 1: Config presets
    results.append(("Config Presets", test_config_presets()))
    
    # Test 2: Metrics computation
    results.append(("Metrics Computation", test_metrics_computation()))
    
    # Test 3: Single query
    results.append(("Single Query Evaluation", test_single_query()))
    
    # Test 4: Full evaluation (may take longer)
    results.append(("Full Evaluation", test_basic_evaluation()))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
