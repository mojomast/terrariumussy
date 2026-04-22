"""Health scoring logic for organisms."""

from ..metrics.models import ModuleMetrics

# Health score weights
CHURN_PENALTY_WEIGHT = 0.25
COMPLEXITY_PENALTY_WEIGHT = 0.20
COVERAGE_BONUS_WEIGHT = 0.20
BUG_PENALTY_WEIGHT = 0.15
STABILITY_BONUS_WEIGHT = 0.10
DEAD_PENALTY_WEIGHT = 0.10

# Thresholds
COMPLEXITY_THRESHOLD = 15
CHURN_THRESHOLD = 5.0  # commits per month
COVERAGE_THRESHOLD = 0.80


def compute_health_score(metrics: ModuleMetrics, avg_churn: float = 5.0) -> float:
    """Compute a health score (0-100) from module metrics.

    Args:
        metrics: Module metrics to evaluate.
        avg_churn: Average churn rate for the project (for relative scoring).

    Returns:
        Health score from 0 to 100.
    """
    score = 100.0

    # Churn penalty: high churn = stressed
    if metrics.churn_rate > CHURN_THRESHOLD:
        churn_penalty = min(
            (metrics.churn_rate - CHURN_THRESHOLD) / CHURN_THRESHOLD, 1.0
        )
        score -= churn_penalty * 25 * CHURN_PENALTY_WEIGHT / 0.25

    # Complexity penalty
    if metrics.complexity > COMPLEXITY_THRESHOLD:
        complexity_penalty = min(
            (metrics.complexity - COMPLEXITY_THRESHOLD) / COMPLEXITY_THRESHOLD, 1.0
        )
        score -= complexity_penalty * 25 * COMPLEXITY_PENALTY_WEIGHT / 0.20
    elif metrics.complexity <= 5:
        # Bonus for low complexity
        score += 5

    # Coverage bonus/penalty
    if metrics.test_coverage >= COVERAGE_THRESHOLD:
        coverage_bonus = (metrics.test_coverage - COVERAGE_THRESHOLD) / (
            1.0 - COVERAGE_THRESHOLD
        )
        score += coverage_bonus * 10
    else:
        coverage_penalty = (
            COVERAGE_THRESHOLD - metrics.test_coverage
        ) / COVERAGE_THRESHOLD
        score -= coverage_penalty * 20

    # Bug penalty
    score -= min(metrics.bug_count * 5, 25)

    # Stability bonus: old-growth is good
    if metrics.days_since_last_change > 180 and not metrics.is_dead:
        # Stable and maintained
        score += 5
    elif metrics.days_since_last_change == 0 and metrics.age_days < 30:
        # Very new, might be unstable
        score -= 5

    # Dead code penalty
    if metrics.is_dead:
        score -= 30

    # Deprecated penalty
    if metrics.is_deprecated:
        score -= 15

    return max(0.0, min(100.0, score))
