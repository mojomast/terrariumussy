"""Scoring module — computes health dimensions from collected adapter data."""

from typing import Dict


def compute_fatigue(fatigue_data: Dict) -> float:
    if "states" in fatigue_data:
        intensities = [s["crack_intensity"] for s in fatigue_data["states"].values()]
        return 1.0 - (sum(intensities) / len(intensities)) if intensities else 1.0
    return 1.0


def compute_epidemic(endemic_data: Dict) -> float:
    if "states" in endemic_data:
        states_list = list(endemic_data["states"].values())
        infected = sum(1 for s in states_list if s["infection_state"] == "I")
        return 1.0 - (infected / len(states_list)) if states_list else 1.0
    return 1.0


def compute_anomaly(sentinel_data: Dict) -> float:
    if "states" in sentinel_data:
        states_list = list(sentinel_data["states"].values())
        anomalous = sum(1 for s in states_list if s["anomaly_active"])
        return 1.0 - (anomalous / len(states_list)) if states_list else 1.0
    return 1.0


def compute_drift(collected: Dict) -> float:
    drift_values = []
    for adapter_name, data in collected.items():
        if "states" in data:
            for state in data["states"].values():
                if state["vitality"] < 1.0:
                    drift_values.append(1.0 - state["vitality"])
    return 1.0 - (sum(drift_values) / len(drift_values)) if drift_values else 1.0


def compute_complexity(kompressi_data: Dict) -> float:
    if "states" in kompressi_data:
        scores = [s["complexity_score"] for s in kompressi_data["states"].values()]
        return 1.0 - (sum(scores) / len(scores)) if scores else 1.0
    return 1.0


def compute_churn(churnmap_data: Dict) -> float:
    if "states" in churnmap_data:
        states_list = list(churnmap_data["states"].values())
        churning = sum(1 for s in states_list if s.get("territory_id"))
        return 1.0 - (churning / len(states_list)) if states_list else 1.0
    return 1.0


def extract_territory_and_succession(collected: Dict) -> tuple:
    """Extract territory and succession from first available adapter."""
    territory = ""
    succession = "seral"
    for adapter_name in ("churnmap", "seral"):
        data = collected.get(adapter_name, {})
        if "states" in data and data["states"]:
            first = next(iter(data["states"].values()))
            if adapter_name == "churnmap":
                territory = first.get("territory_id", "")
            elif adapter_name == "seral":
                succession = first.get("succession_stage", "seral")
    return territory, succession
