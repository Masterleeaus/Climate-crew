# Pinned NASA GISTEMP input

`GLB.Ts+dSST.csv` is a fixed snapshot of NASA GISS GISTEMP v4 global land-ocean anomaly data. Its retrieval date, SHA-256, baseline, source URLs, and analysis period are in `gistemp_manifest.json`.

The analysis reads the annual `J-D` column in degrees Celsius anomaly relative to 1951–1980. It uses complete years 1880–2025 and excludes the incomplete 2026 row. NASA may revise the live source; do not overwrite this snapshot silently.
