"""Format evaluation reports."""
import json
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime
from ..types import EvaluationReport, AggregateMetrics


def format_report(report: EvaluationReport, format: str = "json") -> str:
    """
    Format evaluation report as string.
    
    Args:
        report: EvaluationReport to format
        format: Output format ("json", "text", "markdown")
        
    Returns:
        Formatted report string
    """
    if format == "json":
        return _format_json(report)
    elif format == "text":
        return _format_text(report)
    elif format == "markdown":
        return _format_markdown(report)
    else:
        raise ValueError(f"Unknown format: {format}")


def _format_json(report: EvaluationReport) -> str:
    """Format as JSON."""
    def serialize(obj):
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        elif isinstance(obj, datetime):
            return obj.isoformat()
        return str(obj)
    
    return json.dumps(report, indent=2, default=serialize)


def _format_text(report: EvaluationReport) -> str:
    """Format as plain text."""
    lines = []
    lines.append("=" * 80)
    lines.append(f"Evaluation Report: {report.config_name}")
    lines.append("=" * 80)
    lines.append(f"Timestamp: {report.timestamp}")
    lines.append(f"Total Queries: {report.total_queries}")
    lines.append(f"Successful Runs: {report.successful_runs}")
    lines.append(f"Failed Runs: {report.failed_runs}")
    lines.append("")
    
    # Aggregate metrics
    lines.append("Aggregate Metrics:")
    lines.append("-" * 80)
    for metric in report.aggregate_metrics:
        lines.append(f"  {metric.metric_name}:")
        lines.append(f"    Mean: {metric.mean:.4f}")
        lines.append(f"    Std:  {metric.std:.4f}")
        lines.append(f"    Min:  {metric.min:.4f}")
        lines.append(f"    Max:  {metric.max:.4f}")
        lines.append(f"    Median: {metric.median:.4f}")
        if metric.per_difficulty:
            lines.append(f"    Per Difficulty:")
            for diff, value in metric.per_difficulty.items():
                lines.append(f"      {diff}: {value:.4f}")
        lines.append("")
    
    # Cost summary
    lines.append("Cost Summary:")
    lines.append("-" * 80)
    for key, value in report.cost_summary.items():
        lines.append(f"  {key}: {value}")
    lines.append("")
    
    # Failure modes
    if report.failure_modes:
        lines.append("Failure Modes:")
        lines.append("-" * 80)
        for mode in report.failure_modes:
            lines.append(f"  {mode['error_type']}: {mode['count']} ({mode['percentage']:.1f}%)")
        lines.append("")
    
    return "\n".join(lines)


def _format_markdown(report: EvaluationReport) -> str:
    """Format as Markdown."""
    lines = []
    lines.append(f"# Evaluation Report: {report.config_name}")
    lines.append("")
    lines.append(f"**Timestamp:** {report.timestamp}")
    lines.append(f"**Total Queries:** {report.total_queries}")
    lines.append(f"**Successful Runs:** {report.successful_runs}")
    lines.append(f"**Failed Runs:** {report.failed_runs}")
    lines.append("")
    
    # Aggregate metrics table
    lines.append("## Aggregate Metrics")
    lines.append("")
    lines.append("| Metric | Mean | Std | Min | Max | Median |")
    lines.append("|--------|------|-----|-----|-----|--------|")
    for metric in report.aggregate_metrics:
        lines.append(f"| {metric.metric_name} | {metric.mean:.4f} | {metric.std:.4f} | "
                    f"{metric.min:.4f} | {metric.max:.4f} | {metric.median:.4f} |")
    lines.append("")
    
    # Cost summary
    lines.append("## Cost Summary")
    lines.append("")
    for key, value in report.cost_summary.items():
        lines.append(f"- **{key}**: {value}")
    lines.append("")
    
    # Failure modes
    if report.failure_modes:
        lines.append("## Failure Modes")
        lines.append("")
        for mode in report.failure_modes:
            lines.append(f"- **{mode['error_type']}**: {mode['count']} ({mode['percentage']:.1f}%)")
        lines.append("")
    
    return "\n".join(lines)


def save_report(report: EvaluationReport, output_path: str, format: str = "json"):
    """
    Save evaluation report to file.
    
    Args:
        report: EvaluationReport to save
        output_path: Path to save report
        format: Output format ("json", "text", "markdown")
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    content = format_report(report, format)
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
