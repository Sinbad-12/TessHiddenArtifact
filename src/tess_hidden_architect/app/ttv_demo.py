"""TTV science layer for the TESS Hidden Architect mission.

Builds the physically integrated hidden-companion scenario and derives
observable transit-timing information from the numerical trajectory.

This module contains no UI code and does not expose hidden Planet B
parameters through the public result.
"""

from __future__ import annotations

from dataclasses import dataclass

from tess_hidden_architect.constants import DAY_IN_SECONDS
from tess_hidden_architect.inference.ttv import (
    TTVResult,
    fit_constant_period_ephemeris,
)
from tess_hidden_architect.observation.transit_events import (
    TransitEvent,
    extract_transit_events,
)
from tess_hidden_architect.physics.integrator import NBodyIntegrator
from tess_hidden_architect.scenarios.control_system import make_control_system
from tess_hidden_architect.scenarios.hidden_system import make_hidden_system


@dataclass(frozen=True)
class TTVScienceResult:
    """Publicly presentable TTV measurements."""

    events: tuple[TransitEvent, ...]
    ttv: TTVResult
    control_ttv_rms_s: float
    control_ttv_peak_to_peak_s: float

    @property
    def timing_amplification(self) -> float:
        """Ratio of interacting RMS timing variation to control RMS."""

        if self.control_ttv_rms_s <= 0.0:
            return float("inf")

        return self.ttv.rms_s / self.control_ttv_rms_s

    @property
    def peak_to_peak_amplification(self) -> float:
        """Ratio of interacting to control peak-to-peak variation."""

        if self.control_ttv_peak_to_peak_s <= 0.0:
            return float("inf")

        return (
            self.ttv.peak_to_peak_s
            / self.control_ttv_peak_to_peak_s
        )


def _extract_planet_a_events(
    system,
) -> list[TransitEvent]:
    """Integrate a system and extract Planet A transit events."""

    system, trajectory = NBodyIntegrator(
        time_step_s=60.0
    ).integrate(
        system,
        duration_s=15.0 * DAY_IN_SECONDS,
        record_interval_s=300.0,
    )

    star = next(
        body for body in system.bodies
        if body.name == "Host Star"
    )

    planet_a = next(
        body for body in system.bodies
        if body.name == "Planet A"
    )

    return extract_transit_events(
        trajectory,
        star_name="Host Star",
        planet_name="Planet A",
        star_radius_m=star.radius,
        planet_radius_m=planet_a.radius,
    )


def build_ttv_science_result() -> TTVScienceResult:
    """Build the deterministic interacting-vs-control TTV comparison."""

    hidden_events = _extract_planet_a_events(
        make_hidden_system()
    )

    control_events = _extract_planet_a_events(
        make_control_system()
    )

    hidden_ttv = fit_constant_period_ephemeris(
        hidden_events
    )

    control_ttv = fit_constant_period_ephemeris(
        control_events
    )

    return TTVScienceResult(
        events=tuple(hidden_events),
        ttv=hidden_ttv,
        control_ttv_rms_s=control_ttv.rms_s,
        control_ttv_peak_to_peak_s=control_ttv.peak_to_peak_s,
    )