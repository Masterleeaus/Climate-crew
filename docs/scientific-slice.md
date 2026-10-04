# Reproducible GISTEMP trend slice

## Question and hypotheses

Question: did NASA GISTEMP v4 annual global land-ocean anomalies increase over 1880–2025?

- H1: the annual series has a positive monotonic trend over the stated period.
- H2: the apparent rise is solely a recent-endpoint effect and disappears when 2016–2025 is omitted.

## Evidence and methods

The input is NASA's global GISTEMP v4 CSV snapshot. The analysis uses complete annual `J-D` anomalies, relative to 1951–1980. It reports the SHA-256 of the input and separates source data from derived statistics in a Pydantic-validated evidence graph.

- Primary trend: two-sided Mann–Kendall normal approximation with tie correction.
- Robust slope: Theil–Sen median of pairwise slopes.
- Interval: 95% circular moving-block bootstrap of detrended OLS residuals, block length 5, 2,000 replicates, seed 1042026.
- Exploratory falsification attempt: rerun trend tests after omitting the final ten complete years. This sensitivity check was not preregistered, so it should not be read as confirmatory evidence.

## Result for the pinned snapshot

Across 146 years, OLS slope is 0.0834 °C/decade (95% block-bootstrap interval 0.0676–0.0980); Theil–Sen slope is 0.0812 °C/decade; Mann–Kendall tau-b is 0.7347 with p=3.44×10⁻³⁹. After excluding 2016–2025, the 1880–2015 Sen slope is 0.0711 °C/decade and the Mann–Kendall p-value is 4.37×10⁻³³. This endpoint check does not overturn H1 in this dataset; H2 is challenged by the pre-2016 result.

## Interpretation limits

This is one descriptive global time series. It is not an independent replication across datasets and it does not attribute causes. The Mann–Kendall p-value does not adjust its variance for serial autocorrelation. The bootstrap interval depends on the chosen 5-year block scheme and does not capture every measurement or structural uncertainty. These limits are included in the machine-readable report.
