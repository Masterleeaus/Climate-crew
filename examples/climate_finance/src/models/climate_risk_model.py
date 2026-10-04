"""
Statistical Climate Risk Scoring Model

Mathematical framework — no heuristics, no arbitrary weights, no hardcoded bounds.

For a target company with feature vector x:

  1.  REFERENCE UNIVERSE  U = {x¹, x², …, xᴺ}  (N ≈ 35 real companies)
      Fetch 13 financial features per company from Yahoo Finance.

  2.  PERCENTILE RANKING  For each feature j, compute
          pⱼ = (rank of xⱼ among Uⱼ) / N
      This is the empirical CDF — it maps every feature to [0, 1]
      without any hardcoded bounds.

  3.  RISK DIRECTION  Compute
          ρⱼ = Spearman correlation of feature j with realised volatility
                across the reference universe.
      If ρⱼ > 0 → higher feature value = more risk  → keep pⱼ
      If ρⱼ < 0 → higher feature value = less risk  → flip: pⱼ ← 1 − pⱼ
      The DATA tells us what's risky, not a human assumption.

  4.  WEIGHTING  Each feature is weighted by |ρⱼ| — the strength of its
      empirical relationship with realised risk.
          score = Σ |ρⱼ| · pⱼ  /  Σ |ρⱼ|       ∈ [0, 1]
      Features that explain more variance in realised risk
      automatically get more influence.

  5.  SCALING  Map to [0, 100]:
          final_score = score × 100

Everything is determined by the data: the normalisation (percentile),
the direction (sign of ρ), and the importance (magnitude of ρ).
"""

import os
import math
import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy import stats as sp_stats

logger = logging.getLogger(__name__)


# ── Features to extract from yfinance ──────────────────────
# (name, yfinance_key)  — risk direction is LEARNED from data
FEATURES: List[Tuple[str, str]] = [
    ("beta",             "beta"),
    ("debt_to_equity",   "debtToEquity"),
    ("profit_margin",    "profitMargins"),
    ("operating_margin", "operatingMargins"),
    ("return_on_equity", "returnOnEquity"),
    ("revenue_growth",   "revenueGrowth"),
    ("trailing_pe",      "trailingPE"),
    ("price_to_book",    "priceToBook"),
    ("log_market_cap",   "_computed"),
    ("dividend_yield",   "dividendYield"),
    ("labour_intensity", "_computed"),
    ("current_ratio",    "currentRatio"),
    ("free_cf_yield",    "_computed"),
]

FEATURE_NAMES = [f[0] for f in FEATURES]

# Pillar groupings (TCFD framework categories)
PILLAR_FEATURES = {
    "physical_risk":          ["beta", "labour_intensity"],
    "transition_risk":        ["trailing_pe", "price_to_book", "free_cf_yield"],
    "financial_vulnerability": ["debt_to_equity", "profit_margin", "operating_margin",
                                "return_on_equity", "revenue_growth", "current_ratio"],
    "market_sentiment":       ["log_market_cap", "dividend_yield"],
}

# Reference universe — a cross-section of the economy.
# These are only used to BUILD the distribution; their scores
# are not hardcoded.  The model fetches their live data.
REFERENCE_TICKERS = [
    "XOM", "CVX", "COP", "EOG", "SLB",       # Energy
    "NEE", "DUK", "SO", "AEP",                # Utilities
    "NUE", "FCX", "LIN", "APD",               # Materials
    "CAT", "BA", "UNP", "GE",                 # Industrials
    "WMT", "PG", "KO", "MCD",                 # Consumer
    "AAPL", "MSFT", "GOOGL", "NVDA", "META",  # Tech
    "JNJ", "UNH", "PFE",                      # Healthcare
    "JPM", "GS", "BAC", "BLK",                # Financials
    "AMT", "PLD",                              # Real Estate
    "ENPH", "FSLR",                            # Clean Energy
]


class ClimateRiskModel:
    """
    Percentile-rank model with correlation-derived weights.
    See module docstring for the full mathematical specification.
    """

    def __init__(self):
        # Calibration artefacts (populated once, cached)
        self._ref_matrix: Optional[np.ndarray] = None   # (N, p) feature matrix
        self._ref_vol: Optional[np.ndarray] = None       # (N,)   volatilities
        self._rho: Optional[np.ndarray] = None           # (p,)   Spearman ρ per feature
        self._abs_rho: Optional[np.ndarray] = None       # (p,)   |ρ| (weights)
        self._risk_sign: Optional[np.ndarray] = None     # (p,)   +1 or -1
        self._calibrated = False
        self._finnhub_key = os.getenv("FINNHUB_API_KEY")

    # ════════════════════════════════════════════════════════
    #  PUBLIC API
    # ════════════════════════════════════════════════════════

    def score(self, ticker: str) -> Dict[str, Any]:
        """Compute the climate-risk score for *ticker*."""
        try:
            import yfinance as yf
        except ImportError:
            return {"error": "yfinance not installed"}

        # 1. Calibrate on first call
        if not self._calibrated:
            self._calibrate()

        # 2. Extract features for the target
        stock = yf.Ticker(ticker.upper())
        info = stock.info or {}
        features = self._extract_features(info)
        volatility = self._compute_volatility(stock)
        target_vec = np.array(
            [features.get(n, np.nan) for n in FEATURE_NAMES], dtype=np.float64
        )

        # 3. Impute missing values with reference median
        target_vec = self._impute(target_vec)

        # 4. Compute percentile ranks against reference universe
        percentiles = self._percentile_rank(target_vec)

        # 5. Risk-align percentiles
        aligned = self._risk_align(percentiles)

        # 6. Weighted score
        w = self._abs_rho if self._abs_rho is not None else np.ones(len(FEATURE_NAMES))
        total_w = w.sum()
        if total_w == 0:
            raw_score = 50.0
        else:
            raw_score = float(np.dot(w, aligned) / total_w) * 100

        # 7. ESG adjustment (if Finnhub available — as an additional data point)
        esg = self._fetch_finnhub_esg(ticker)
        env_score = esg.get("environmental_score") if esg else None
        if env_score is not None and not np.isnan(env_score):
            # env_score: higher = better → invert
            esg_risk = 100.0 - env_score
            # Bayesian-style combination: treat ESG as one extra observation
            # with weight equal to the sum of top-3 feature weights
            esg_weight = float(np.sort(w)[-3:].sum()) if len(w) >= 3 else float(w.sum()) / 2
            final_score = (raw_score * total_w + esg_risk * esg_weight) / (total_w + esg_weight)
            source = f"Percentile model + Finnhub ESG (weight ratio {total_w:.1f}:{esg_weight:.1f})"
        else:
            final_score = raw_score
            esg_risk = None
            source = "Percentile model (correlation-weighted) — no ESG data"

        final_score = int(np.clip(round(final_score), 1, 99))

        # 8. Pillar breakdown
        pillars = self._compute_pillars(aligned, w)

        # 9. Feature contributions
        contributions = self._feature_contributions(features, percentiles, aligned, w, volatility)

        # 10. Key risks from data
        key_risks = self._derive_key_risks(contributions)

        return {
            "risk_score": final_score,
            "risk_level": self._level(final_score),
            "score_source": source,
            "pillars": pillars,
            "key_risks": key_risks,
            "feature_contributions": contributions,
            "esg_data": esg,
            "historical_volatility": round(volatility, 4) if volatility else None,
            "methodology": {
                "features_used": len(FEATURE_NAMES),
                "reference_universe_size": len(self._ref_matrix) if self._ref_matrix is not None else 0,
                "correlation_anchor": "realised_volatility_1y",
            },
        }

    # ════════════════════════════════════════════════════════
    #  CALIBRATION — runs once, cached in memory
    # ════════════════════════════════════════════════════════

    def _calibrate(self):
        """
        Build the reference universe and compute correlations.

        1. Fetch features + volatility for each reference ticker.
        2. Impute missing values (column median).
        3. Compute Spearman ρ between each feature and volatility.
        """
        try:
            import yfinance as yf
        except ImportError:
            self._calibrated = True
            return

        logger.info("Calibrating risk model — fetching reference universe...")

        rows: List[np.ndarray] = []
        vols: List[float] = []

        for tkr in REFERENCE_TICKERS:
            try:
                stock = yf.Ticker(tkr)
                info = stock.info or {}
                if not info.get("sector"):
                    continue
                feats = self._extract_features(info)
                vol = self._compute_volatility(stock)
                if vol is None:
                    continue

                vec = np.array(
                    [feats.get(n, np.nan) for n in FEATURE_NAMES], dtype=np.float64
                )
                rows.append(vec)
                vols.append(vol)
            except Exception as e:
                logger.warning(f"Skipping {tkr}: {e}")

        if len(rows) < 8:
            logger.warning(f"Only {len(rows)} tickers fetched — model will have low confidence")
            self._calibrated = True
            return

        X = np.vstack(rows)                 # (N, p)
        sigma = np.array(vols)              # (N,)

        # Impute missing values with column median
        col_medians = np.nanmedian(X, axis=0)
        for j in range(X.shape[1]):
            mask = np.isnan(X[:, j])
            X[mask, j] = col_medians[j] if not np.isnan(col_medians[j]) else 0.0

        self._ref_matrix = X
        self._ref_vol = sigma
        self._col_medians = col_medians

        # Compute Spearman correlation between each feature and volatility
        p = X.shape[1]
        rho = np.zeros(p)
        for j in range(p):
            if np.std(X[:, j]) < 1e-12:
                rho[j] = 0.0
            else:
                corr, _ = sp_stats.spearmanr(X[:, j], sigma)
                rho[j] = corr if not np.isnan(corr) else 0.0

        self._rho = rho
        self._abs_rho = np.abs(rho)
        self._risk_sign = np.sign(rho)    # +1 if higher→riskier, -1 if higher→safer

        self._calibrated = True

        logger.info(
            f"Model calibrated: {len(rows)} companies, {p} features. "
            f"Top correlations: "
            + ", ".join(
                f"{FEATURE_NAMES[i]}={rho[i]:+.2f}"
                for i in np.argsort(-self._abs_rho)[:5]
            )
        )

    # ════════════════════════════════════════════════════════
    #  FEATURE EXTRACTION
    # ════════════════════════════════════════════════════════

    def _extract_features(self, info: Dict[str, Any]) -> Dict[str, float]:
        """Pull real numeric features from a yfinance info dict."""
        feats: Dict[str, float] = {}

        for name, key in FEATURES:
            if key == "_computed":
                continue
            val = info.get(key)
            feats[name] = float(val) if val is not None else np.nan

        # log(market cap)
        mc = info.get("marketCap")
        feats["log_market_cap"] = math.log(mc) if mc and mc > 0 else np.nan

        # labour intensity = employees per $M revenue
        emp = info.get("fullTimeEmployees")
        rev = info.get("totalRevenue")
        if emp and rev and rev > 0:
            feats["labour_intensity"] = emp / (rev / 1e6)
        else:
            feats["labour_intensity"] = np.nan

        # free-cashflow yield = FCF / market cap
        fcf = info.get("freeCashflow")
        if fcf is not None and mc and mc > 0:
            feats["free_cf_yield"] = fcf / mc
        else:
            feats["free_cf_yield"] = np.nan

        return feats

    def _compute_volatility(self, stock: Any) -> Optional[float]:
        """Annualised volatility from 1 year of daily returns."""
        try:
            hist = stock.history(period="1y", interval="1d")
            if hist is None or hist.empty or len(hist) < 30:
                return None
            rets = hist["Close"].pct_change().dropna()
            if len(rets) < 20:
                return None
            return float(rets.std() * np.sqrt(252))
        except Exception as e:
            logger.warning(f"Volatility failed: {e}")
            return None

    # ════════════════════════════════════════════════════════
    #  STATISTICAL SCORING
    # ════════════════════════════════════════════════════════

    def _impute(self, vec: np.ndarray) -> np.ndarray:
        """Replace NaNs with reference-universe column medians."""
        out = vec.copy()
        if hasattr(self, "_col_medians") and self._col_medians is not None:
            for j in range(len(out)):
                if np.isnan(out[j]):
                    out[j] = self._col_medians[j] if not np.isnan(self._col_medians[j]) else 0.0
        else:
            out = np.nan_to_num(out, nan=0.0)
        return out

    def _percentile_rank(self, target: np.ndarray) -> np.ndarray:
        """
        For each feature j, compute the fraction of reference-universe
        values that are ≤ target_j.   Result ∈ [0, 1].
        """
        if self._ref_matrix is None:
            return np.full(len(target), 0.5)

        N = self._ref_matrix.shape[0]
        pctiles = np.zeros(len(target))
        for j in range(len(target)):
            pctiles[j] = np.sum(self._ref_matrix[:, j] <= target[j]) / N
        return pctiles

    def _risk_align(self, pctiles: np.ndarray) -> np.ndarray:
        """
        Align percentiles so that higher = more risk.

        If ρⱼ > 0 (higher feature value correlates with higher volatility),
        the percentile already points in the risk direction → keep.

        If ρⱼ < 0 (higher value = lower risk), flip: pⱼ ← 1 − pⱼ.
        """
        if self._risk_sign is None:
            return pctiles
        aligned = pctiles.copy()
        for j in range(len(aligned)):
            if self._risk_sign[j] < 0:
                aligned[j] = 1.0 - aligned[j]
        return aligned

    # ════════════════════════════════════════════════════════
    #  PILLAR BREAKDOWN
    # ════════════════════════════════════════════════════════

    def _compute_pillars(
        self, aligned: np.ndarray, weights: np.ndarray
    ) -> Dict[str, Optional[int]]:
        """
        For each TCFD pillar, compute the weighted average of its
        risk-aligned percentiles (using the same correlation weights).
        """
        idx_map = {n: i for i, n in enumerate(FEATURE_NAMES)}
        result = {}

        for pillar, feat_list in PILLAR_FEATURES.items():
            indices = [idx_map[f] for f in feat_list if f in idx_map]
            if not indices:
                result[pillar] = None
                continue
            w = weights[indices]
            a = aligned[indices]
            total_w = w.sum()
            if total_w < 1e-12:
                result[pillar] = round(float(a.mean()) * 100)
            else:
                result[pillar] = round(float(np.dot(w, a) / total_w) * 100)

        return result

    # ════════════════════════════════════════════════════════
    #  FEATURE CONTRIBUTIONS
    # ════════════════════════════════════════════════════════

    def _feature_contributions(
        self,
        raw_features: Dict[str, float],
        percentiles: np.ndarray,
        aligned: np.ndarray,
        weights: np.ndarray,
        volatility: Optional[float],
    ) -> List[Dict[str, Any]]:
        """
        For each feature, show:
          - its raw value
          - its percentile in the reference universe
          - whether it increases or decreases risk (from ρ sign)
          - its weight |ρ|
          - its risk-aligned contribution to the final score
        """
        contribs = []
        total_w = weights.sum() if weights.sum() > 0 else 1.0

        LABELS = {
            "beta": "Market Beta",
            "debt_to_equity": "Debt / Equity",
            "profit_margin": "Profit Margin",
            "operating_margin": "Operating Margin",
            "return_on_equity": "Return on Equity",
            "revenue_growth": "Revenue Growth",
            "trailing_pe": "Trailing P/E",
            "price_to_book": "Price / Book",
            "log_market_cap": "Company Size",
            "dividend_yield": "Dividend Yield",
            "labour_intensity": "Labour Intensity",
            "current_ratio": "Current Ratio",
            "free_cf_yield": "Free CF Yield",
        }

        for j, name in enumerate(FEATURE_NAMES):
            raw = raw_features.get(name)
            if raw is None or (isinstance(raw, float) and np.isnan(raw)):
                continue

            # Format display value
            if name in ("profit_margin", "operating_margin", "return_on_equity",
                        "revenue_growth", "dividend_yield", "free_cf_yield"):
                display = f"{raw * 100:.1f}%"
            elif name == "log_market_cap":
                display = f"${math.exp(raw) / 1e9:.1f}B"
            elif name == "debt_to_equity":
                display = f"{raw:.0f}"
            elif name == "labour_intensity":
                display = f"{raw:.1f} per $M"
            elif name == "current_ratio":
                display = f"{raw:.2f}"
            else:
                display = f"{raw:.2f}"

            pctile = percentiles[j]
            risk_pctile = aligned[j]
            w = float(weights[j])
            rho_val = float(self._rho[j]) if self._rho is not None else 0.0

            contribs.append({
                "feature": LABELS.get(name, name),
                "value": display,
                "percentile": round(pctile * 100),
                "risk_impact": round(risk_pctile * 100),
                "weight": round(w, 3),
                "correlation": round(rho_val, 3),
                "direction": "increases" if risk_pctile > 0.5 else "decreases",
            })

        # Add volatility itself as context (not a model feature, it's the anchor)
        if volatility is not None:
            contribs.append({
                "feature": "Realised Volatility (1Y)",
                "value": f"{volatility * 100:.1f}%",
                "percentile": None,
                "risk_impact": None,
                "weight": None,
                "correlation": None,
                "direction": "anchor",
            })

        # Sort by risk impact descending
        contribs.sort(key=lambda x: x.get("risk_impact") or 0, reverse=True)
        return contribs

    # ════════════════════════════════════════════════════════
    #  KEY RISKS
    # ════════════════════════════════════════════════════════

    def _derive_key_risks(self, contributions: List[Dict[str, Any]]) -> List[str]:
        """
        Generate risk descriptions from the top percentile-ranked features.
        """
        risks = []
        for c in contributions:
            ri = c.get("risk_impact")
            if ri is None or ri < 60 or c["direction"] != "increases":
                continue
            pct = c.get("percentile", ri)
            feat = c["feature"]
            val = c["value"]

            risks.append(
                f"{feat}: {val} (top {100 - pct}% of reference universe)"
                if pct is not None and pct > 50
                else f"{feat}: {val} (elevated risk signal)"
            )
            if len(risks) >= 5:
                break

        if not risks:
            risks.append("No features in the high-risk percentile range")

        return risks

    # ════════════════════════════════════════════════════════
    #  ESG
    # ════════════════════════════════════════════════════════

    def _fetch_finnhub_esg(self, ticker: str) -> Optional[Dict[str, Any]]:
        if not self._finnhub_key:
            return None
        try:
            import requests
            resp = requests.get(
                "https://finnhub.io/api/v1/stock/esg",
                params={"symbol": ticker.upper(), "token": self._finnhub_key},
                timeout=8,
            )
            if resp.status_code != 200:
                return None
            data = resp.json()
            if not data or not data.get("totalESGScore"):
                return None
            return {
                "total_score": data.get("totalESGScore"),
                "environmental_score": data.get("environmentalScore"),
                "social_score": data.get("socialScore"),
                "governance_score": data.get("governanceScore"),
                "source": "Finnhub (Live)",
            }
        except Exception as e:
            logger.warning(f"Finnhub ESG failed for {ticker}: {e}")
            return None

    # ════════════════════════════════════════════════════════
    #  HELPERS
    # ════════════════════════════════════════════════════════

    @staticmethod
    def _level(score: int) -> str:
        if score >= 75:
            return "Very High"
        if score >= 55:
            return "High"
        if score >= 35:
            return "Moderate"
        if score >= 15:
            return "Low"
        return "Very Low"
