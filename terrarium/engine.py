"""TerrariumEngine — collects, scores, and serializes ecosystem health."""

import json
from typing import Dict, List, Optional

from .health import HealthScore
from .adapters.base import BaseAdapter
from .scoring import (
    compute_fatigue,
    compute_epidemic,
    compute_anomaly,
    compute_drift,
    compute_complexity,
    compute_churn,
    extract_territory_and_succession,
)


class TerrariumEngine:
    """Central engine that orchestrates adapter collection and health scoring.

    Args:
        adapters: List of initialized adapter instances.
    """

    def __init__(self, adapters: List[BaseAdapter]) -> None:
        self.adapters = adapters
        self._last_collected: Optional[Dict[str, Dict]] = None

    def collect(self) -> Dict[str, Dict]:
        """Call each adapter's ``get_metrics()`` and merge into a unified dict.

        Returns:
            Mapping of adapter name ->; loaded metrics dict.
        """
        collected: Dict[str, Dict] = {}
        for adapter in self.adapters:
            if not adapter.is_available():
                collected[adapter.name] = {
                    "error": "adapter not available",
                    "stub": True,
                }
                continue
            try:
                states = adapter.load()
                collected[adapter.name] = {
                    "count": len(states),
                    "states": {
                        path: self._state_to_dict(state)
                        for path, state in states.items()
                    },
                    "stub": getattr(adapter, "STUB_MODE", False),
                }
            except Exception as exc:
                collected[adapter.name] = {"error": str(exc), "stub": True}
        self._last_collected = collected
        return collected

    @staticmethod
    def _state_to_dict(state) -> Dict:
        """Convert an OrganismHealthState to a plain dict."""
        return {
            "vitality": state.vitality,
            "crack_intensity": state.crack_intensity,
            "infection_state": state.infection_state,
            "anomaly_active": state.anomaly_active,
            "complexity_score": state.complexity_score,
            "territory_id": state.territory_id,
            "succession_stage": state.succession_stage,
        }

    def score(self) -> HealthScore:
        """Compute a 0.0–1.0 overall ecosystem health score from merged metrics.

        The algorithm averages the inverse of each damage signal:
        - fatigue: 1.0 - mean(crack_intensity)
        - epidemic: ratio of non-infected files
        - anomaly: ratio of non-anomalous files
        - drift: 1.0 - mean(1.0 - vitality where vitality < 1.0)
        - complexity: 1.0 - mean(complexity_score)
        """
        if self._last_collected is None:
            self.collect()

        collected = self._last_collected or {}
        health = HealthScore()
        health.raw = collected

        health.fatigue = compute_fatigue(collected.get("fatigue", {}))
        health.epidemic = compute_epidemic(collected.get("endemic", {}))
        health.anomaly = compute_anomaly(collected.get("sentinel", {}))
        health.drift = compute_drift(collected)
        health.complexity = compute_complexity(collected.get("kompressi", {}))
        health.churn = compute_churn(collected.get("churnmap", {}))

        health.territory, health.succession = extract_territory_and_succession(
            collected
        )

        # Overall: weighted average of sub-scores
        weights = {
            "fatigue": 0.20,
            "epidemic": 0.20,
            "anomaly": 0.20,
            "drift": 0.15,
            "complexity": 0.15,
            "churn": 0.10,
        }
        overall = 0.0
        total_weight = 0.0
        for key, weight in weights.items():
            overall += getattr(health, key) * weight
            total_weight += weight

        health.overall = overall / total_weight if total_weight > 0 else 1.0
        return health

    def to_json(self) -> str:
        """Serialize the current collected state and score to JSON."""
        score = self.score()
        payload = {
            "health": score.to_dict(),
            "adapters": self._last_collected or {},
        }
        return json.dumps(payload, indent=2)
