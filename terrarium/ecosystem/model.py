"""Ecosystem model — data classes for organisms and ecosystems."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .organisms import (
    OrganismType,
    Vitality,
    ROLE_TO_ORGANISM,
    health_to_vitality,
    get_emoji,
    VITALITY_COLORS,
    ANSI_RESET,
    ANSI_BOLD,
)


@dataclass
class OrganismHealthState:
    """Merged health state from external ussyverse data sources."""

    path: str
    vitality: float = 1.0
    crack_intensity: float = 0.0
    infection_state: str = "S"
    anomaly_active: bool = False
    complexity_score: float = 0.0
    territory_id: Optional[str] = None
    succession_stage: str = "seral"


@dataclass
class Organism:
    """A living organism representing a code module."""

    path: str
    organism_type: OrganismType = OrganismType.BUSH
    health: float = 0.0
    vitality: Vitality = Vitality.HEALTHY
    stability_tier: str = ""
    age_tier: str = ""
    emoji: str = ""
    symptoms: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    crack_intensity: float = 0.0
    infection_state: str = "S"
    anomaly_active: bool = False
    complexity_score: float = 0.0
    territory_id: Optional[str] = None
    succession_stage: str = "seral"

    def __post_init__(self) -> None:
        """Compute derived fields."""
        self.vitality = health_to_vitality(self.health)
        self.emoji = get_emoji(self.organism_type, self.vitality)

    def colored_name(self) -> str:
        """Return the organism's path with ANSI color based on vitality."""
        color = VITALITY_COLORS.get(self.vitality, "")
        return f"{color}{self.emoji} {self.path}{ANSI_RESET}"


@dataclass
class Ecosystem:
    """The full ecosystem representing a project."""

    root_path: str
    organisms: Dict[str, Organism] = field(default_factory=dict)
    overall_health: float = 0.0
    thriving_count: int = 0
    healthy_count: int = 0
    stressed_count: int = 0
    critical_count: int = 0
    dead_count: int = 0

    def compute_stats(self) -> None:
        """Compute aggregate ecosystem statistics."""
        if not self.organisms:
            return

        self.overall_health = sum(o.health for o in self.organisms.values()) / len(
            self.organisms
        )

        self.thriving_count = sum(
            1 for o in self.organisms.values() if o.vitality == Vitality.THRIVING
        )
        self.healthy_count = sum(
            1 for o in self.organisms.values() if o.vitality == Vitality.HEALTHY
        )
        self.stressed_count = sum(
            1 for o in self.organisms.values() if o.vitality == Vitality.STRESSED
        )
        self.critical_count = sum(
            1
            for o in self.organisms.values()
            if o.vitality in (Vitality.WILTING, Vitality.DYING)
        )
        self.dead_count = sum(
            1 for o in self.organisms.values() if o.vitality == Vitality.DEAD
        )

    @property
    def health_tier(self) -> str:
        """Human-readable health tier."""
        if self.overall_health >= 80:
            return "EXCELLENT"
        elif self.overall_health >= 60:
            return "GOOD"
        elif self.overall_health >= 40:
            return "FAIR"
        elif self.overall_health >= 20:
            return "POOR"
        else:
            return "CRITICAL"

    def most_critical(self) -> Optional[Organism]:
        """Return the organism with the lowest health."""
        if not self.organisms:
            return None
        return min(self.organisms.values(), key=lambda o: o.health)

    def healthiest(self) -> Optional[Organism]:
        """Return the organism with the highest health."""
        if not self.organisms:
            return None
        return max(self.organisms.values(), key=lambda o: o.health)
