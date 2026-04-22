"""Organism builder — constructs organisms from metrics and adapter data."""

from typing import Dict, List, Optional

from ..metrics.models import ModuleMetrics, ProjectMetrics
from ..metrics.stability import classify_stability, classify_age
from .model import Organism, OrganismHealthState, Ecosystem
from .organisms import (
    OrganismType,
    ROLE_TO_ORGANISM,
)
from .health_scoring import compute_health_score


def _extract_adapter_state(
    health_state: Optional[OrganismHealthState],
) -> tuple:
    """Extract values from health_state, returning defaults if None."""
    if health_state is None:
        return (0.0, "S", False, 0.0, None, "seral")
    return (
        health_state.crack_intensity,
        health_state.infection_state,
        health_state.anomaly_active,
        health_state.complexity_score,
        health_state.territory_id,
        health_state.succession_stage,
    )


def _apply_health_modifiers(
    health: float,
    crack_intensity: float,
    infection_state: str,
    anomaly_active: bool,
) -> float:
    """Apply external health state modifiers to health score."""
    health -= crack_intensity * 30

    if infection_state == "I":
        health -= 20
    elif infection_state == "E":
        health -= 10
    elif infection_state == "R":
        health -= 5

    if anomaly_active:
        health -= 15

    return max(0.0, min(100.0, health))


def _collect_symptoms(
    metrics: ModuleMetrics,
    crack_intensity: float,
    infection_state: str,
    anomaly_active: bool,
    complexity_score: float,
    succession_stage: str,
) -> List[str]:
    """Gather symptom strings from metrics and adapter state."""
    from .health_scoring import (
        CHURN_THRESHOLD,
        COMPLEXITY_THRESHOLD,
        COVERAGE_THRESHOLD,
    )

    symptoms = []

    if metrics.churn_rate > CHURN_THRESHOLD:
        symptoms.append(
            f"Churn rate {metrics.churn_rate:.1f}x above threshold (>{CHURN_THRESHOLD}/month)"
        )

    if metrics.complexity > COMPLEXITY_THRESHOLD:
        symptoms.append(
            f"Cyclomatic complexity: {metrics.complexity} (threshold: {COMPLEXITY_THRESHOLD})"
        )

    if metrics.test_coverage < COVERAGE_THRESHOLD and not metrics.is_test:
        symptoms.append(
            f"Test coverage: {metrics.test_coverage:.0%} (threshold: {COVERAGE_THRESHOLD:.0%})"
        )

    if metrics.bug_count > 0:
        symptoms.append(f"{metrics.bug_count} open bug(s) assigned")

    if metrics.is_dead:
        symptoms.append("Module appears to be dead code")

    if metrics.is_deprecated:
        symptoms.append("Module is deprecated")

    if crack_intensity > 0.0:
        symptoms.append(
            f"Crack intensity: {crack_intensity:.2f} — cracked bark, wilting"
        )

    if infection_state == "I":
        symptoms.append("Infection active — contagion glow detected")
    elif infection_state == "E":
        symptoms.append("Exposed to infection — incubating")

    if anomaly_active:
        symptoms.append("Anomaly detected — immune response active")

    if complexity_score > 0.0:
        symptoms.append(
            f"High Kolmogorov complexity: {complexity_score:.2f} — dense, unpredictable structure"
        )

    return symptoms


def _collect_strengths(
    metrics: ModuleMetrics,
    churn_rate: float,
    complexity: int,
    coverage: float,
    succession_stage: str,
) -> List[str]:
    """Gather strength strings from metrics."""
    from .health_scoring import (
        CHURN_THRESHOLD,
        COMPLEXITY_THRESHOLD,
        COVERAGE_THRESHOLD,
    )

    strengths = []

    if churn_rate < 1.0 and metrics.commit_count > 0:
        strengths.append("Low churn — stable and predictable")

    if complexity <= 5 and complexity > 0:
        strengths.append("Low complexity — easy to understand")

    if coverage >= COVERAGE_THRESHOLD:
        strengths.append(f"Good test coverage: {coverage:.0%}")

    if succession_stage == "pioneer":
        strengths.append("Pioneer stage — young, adaptable code")
    elif succession_stage == "climax":
        strengths.append("Climax stage — mature, stable ecosystem")

    return strengths


def build_organism(
    metrics: ModuleMetrics,
    avg_churn: float = 5.0,
    health_state: Optional[OrganismHealthState] = None,
) -> Organism:
    """Build an Organism from module metrics.

    Args:
        metrics: Module metrics to convert.
        avg_churn: Average churn for the project.
        health_state: Optional merged health state from external adapters.

    Returns:
        An Organism with computed health and type.
    """
    # Determine organism type
    if metrics.age_days < 30 and not metrics.is_deprecated:
        organism_type = OrganismType.SEEDLING
    else:
        organism_type = ROLE_TO_ORGANISM.get(metrics.module_role, OrganismType.BUSH)

    # Compute health
    health = compute_health_score(metrics, avg_churn)

    # Apply external health state modifiers
    (
        crack_intensity,
        infection_state,
        anomaly_active,
        complexity_score,
        territory_id,
        succession_stage,
    ) = _extract_adapter_state(health_state)

    health = _apply_health_modifiers(
        health, crack_intensity, infection_state, anomaly_active
    )

    # Collect symptoms and strengths
    symptoms = _collect_symptoms(
        metrics,
        crack_intensity,
        infection_state,
        anomaly_active,
        complexity_score,
        succession_stage,
    )
    strengths = _collect_strengths(
        metrics,
        metrics.churn_rate,
        metrics.complexity,
        metrics.test_coverage,
        succession_stage,
    )

    # Handle recovered infection as strength
    if infection_state == "R":
        strengths.append("Recovered from infection — scarred but stable")

    stability_tier = classify_stability(metrics.days_since_last_change)
    age_tier = classify_age(metrics.age_days)

    return Organism(
        path=metrics.path,
        organism_type=organism_type,
        health=health,
        stability_tier=stability_tier,
        age_tier=age_tier,
        symptoms=symptoms,
        strengths=strengths,
        crack_intensity=crack_intensity,
        infection_state=infection_state,
        anomaly_active=anomaly_active,
        complexity_score=complexity_score,
        territory_id=territory_id,
        succession_stage=succession_stage,
    )


def build_ecosystem(
    project: ProjectMetrics,
    health_states: Optional[Dict[str, OrganismHealthState]] = None,
) -> Ecosystem:
    """Build a full Ecosystem from project metrics.

    Args:
        project: ProjectMetrics from the metrics engine.
        health_states: Optional mapping of file path to merged health state
            from external adapters.

    Returns:
        An Ecosystem with all organisms and aggregate stats.
    """
    ecosystem = Ecosystem(root_path=project.root_path)

    avg_churn = project.avg_churn if project.avg_churn > 0 else 5.0
    health_states = health_states or {}

    for path, metrics in project.modules.items():
        health_state = health_states.get(path)
        organism = build_organism(metrics, avg_churn, health_state)
        ecosystem.organisms[path] = organism

    ecosystem.compute_stats()
    return ecosystem
