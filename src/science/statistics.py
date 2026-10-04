"""Dependency-light trend tests used by the reproducible GISTEMP example."""

from __future__ import annotations

import csv
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class AnnualSeries:
    years: tuple[int, ...]
    anomalies_c: tuple[float, ...]


def load_gistemp_annual(path: str | Path, start: int = 1880, end: int = 2025) -> AnnualSeries:
    """Read complete-year J-D anomalies from NASA's published GISTEMP CSV."""
    with Path(path).open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream)
        next(reader)  # descriptive title row
        header = next(reader)
        year_index = header.index("Year")
        annual_index = header.index("J-D")
        values: list[tuple[int, float]] = []
        for row in reader:
            if len(row) <= annual_index or not row[year_index].strip().isdigit():
                continue
            year = int(row[year_index])
            raw = row[annual_index].strip()
            if start <= year <= end and raw not in {"", "***"}:
                values.append((year, float(raw)))
    if len(values) < 8:
        raise ValueError(f"Need at least 8 annual observations, found {len(values)}")
    years = tuple(year for year, _ in values)
    if years != tuple(range(years[0], years[-1] + 1)):
        raise ValueError("Annual series has missing or duplicated years")
    return AnnualSeries(years, tuple(value for _, value in values))


def ols_slope(years: Iterable[int], values: Iterable[float]) -> float:
    """Return the ordinary least-squares slope in units per calendar year."""
    x = tuple(float(value) for value in years)
    y = tuple(float(value) for value in values)
    if len(x) != len(y) or len(x) < 2:
        raise ValueError("years and values must have equal length >= 2")
    x_bar = sum(x) / len(x)
    y_bar = sum(y) / len(y)
    denominator = sum((value - x_bar) ** 2 for value in x)
    if denominator == 0:
        raise ValueError("years must contain at least two distinct values")
    return sum((xv - x_bar) * (yv - y_bar) for xv, yv in zip(x, y)) / denominator


def sen_slope(years: Iterable[int], values: Iterable[float]) -> float:
    """Return the median of all pairwise slopes (Theil-Sen estimator)."""
    x = tuple(years)
    y = tuple(values)
    slopes = [
        (y[j] - y[i]) / (x[j] - x[i])
        for i in range(len(x) - 1)
        for j in range(i + 1, len(x))
    ]
    if not slopes:
        raise ValueError("at least two observations are required")
    slopes.sort()
    middle = len(slopes) // 2
    if len(slopes) % 2:
        return slopes[middle]
    return (slopes[middle - 1] + slopes[middle]) / 2


def mann_kendall(years: Iterable[int], values: Iterable[float]) -> dict[str, float | int]:
    """Two-sided normal-approximation Mann-Kendall monotonic trend test."""
    x = tuple(years)
    y = tuple(values)
    if len(x) != len(y) or len(y) < 8:
        raise ValueError("years and values must have equal length >= 8")
    n = len(y)
    score = sum(
        1 if y[j] > y[i] else -1 if y[j] < y[i] else 0
        for i in range(n - 1)
        for j in range(i + 1, n)
    )
    tied = 0
    counts: dict[float, int] = {}
    for value in y:
        counts[value] = counts.get(value, 0) + 1
    for count in counts.values():
        tied += count * (count - 1) * (2 * count + 5)
    variance = (n * (n - 1) * (2 * n + 5) - tied) / 18
    if variance <= 0:
        z = 0.0
        p_value = 1.0
    else:
        z = (score - 1) / math.sqrt(variance) if score > 0 else (
            (score + 1) / math.sqrt(variance) if score < 0 else 0.0
        )
        p_value = math.erfc(abs(z) / math.sqrt(2.0))
    pair_count = n * (n - 1) / 2
    tied_pairs = sum(count * (count - 1) / 2 for count in counts.values())
    tau_b = score / math.sqrt(pair_count * (pair_count - tied_pairs)) if pair_count > tied_pairs else 0.0
    return {"n": n, "s": score, "tau_b": tau_b, "z": z, "p_value": p_value}


def _percentile(sorted_values: list[float], probability: float) -> float:
    position = (len(sorted_values) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return sorted_values[lower]
    weight = position - lower
    return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight


def moving_block_bootstrap_ci(
    years: Iterable[int],
    values: Iterable[float],
    *,
    block_length: int = 5,
    replicates: int = 2000,
    seed: int = 1042026,
    alpha: float = 0.05,
) -> tuple[float, float]:
    """Bootstrap OLS slope CI by resampling circular blocks of detrended residuals."""
    x = tuple(float(value) for value in years)
    y = tuple(float(value) for value in values)
    if len(x) != len(y) or len(y) < 12:
        raise ValueError("years and values must have equal length >= 12")
    if not 1 <= block_length <= len(y):
        raise ValueError("block_length must be between 1 and the series length")
    slope = ols_slope(x, y)
    x_bar = sum(x) / len(x)
    y_bar = sum(y) / len(y)
    intercept = y_bar - slope * x_bar
    residuals = [value - (intercept + slope * year) for year, value in zip(x, y)]
    rng = random.Random(seed)
    estimates: list[float] = []
    n = len(y)
    for _ in range(replicates):
        sample: list[float] = []
        while len(sample) < n:
            first = rng.randrange(n)
            sample.extend(residuals[(first + offset) % n] for offset in range(block_length))
        boot_y = [intercept + slope * year + residual for year, residual in zip(x, sample[:n])]
        estimates.append(ols_slope(x, boot_y))
    estimates.sort()
    return _percentile(estimates, alpha / 2), _percentile(estimates, 1 - alpha / 2)


def trend_summary(series: AnnualSeries, *, bootstrap_replicates: int = 2000) -> dict[str, object]:
    """Compute the primary trend and endpoint sensitivity checks."""
    years, values = series.years, series.anomalies_c
    if len(years) < 20:
        raise ValueError("at least 20 consecutive annual observations are required for sensitivity checks")
    slope = ols_slope(years, values)
    lower, upper = moving_block_bootstrap_ci(
        years, values, block_length=5, replicates=bootstrap_replicates, seed=1042026
    )
    mk = mann_kendall(years, values)
    cut_year = years[-1] - 10
    older = AnnualSeries(
        tuple(year for year in years if year <= cut_year),
        tuple(value for year, value in zip(years, values) if year <= cut_year),
    )
    recent_start = max(years[0], 1970)
    recent = AnnualSeries(
        tuple(year for year in years if year >= recent_start),
        tuple(value for year, value in zip(years, values) if year >= recent_start),
    )
    older_test = mann_kendall(older.years, older.anomalies_c)
    recent_test = mann_kendall(recent.years, recent.anomalies_c)
    return {
        "period": [years[0], years[-1]],
        "n": len(years),
        "ols_slope_c_per_decade": slope * 10,
        "ols_slope_95_ci_c_per_decade": [lower * 10, upper * 10],
        "sen_slope_c_per_decade": sen_slope(years, values) * 10,
        "mann_kendall": mk,
        "endpoint_falsification": {
            "question": f"Does the positive trend persist after excluding {cut_year + 1}-{years[-1]}?",
            "period": [years[0], cut_year],
            "sen_slope_c_per_decade": sen_slope(older.years, older.anomalies_c) * 10,
            "mann_kendall": older_test,
            "outcome": "not_falsified" if older_test["tau_b"] > 0 and older_test["p_value"] < 0.05 else "inconclusive_or_falsified",
        },
        "recent_window_check": {
            "period": [recent_start, years[-1]],
            "sen_slope_c_per_decade": sen_slope(recent.years, recent.anomalies_c) * 10,
            "mann_kendall": recent_test,
        },
        "methods": {
            "trend_test": "two-sided Mann-Kendall normal approximation with tie correction",
            "robust_slope": "Theil-Sen median of all pairwise slopes",
            "interval": "95% circular moving-block bootstrap of detrended OLS residuals; 5-year blocks; seed 1042026; 2000 replicates",
        },
    }
