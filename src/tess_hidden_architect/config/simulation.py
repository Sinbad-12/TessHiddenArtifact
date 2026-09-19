"""Simulation configuration.

Phase 0 note:
    This configuration describes the *parameters* for a future numerical
    integration. Phase 0 does NOT implement a numerical integrator.
    The ``integrator`` field documents the intended future integration
    method but no integrator is operational in Phase 0.
"""

from dataclasses import dataclass


@dataclass
class SimulationConfig:
    """Configuration for a deterministic gravitational simulation.

    All time values are in SI seconds.

    Attributes:
        time_step_s: Integration timestep in seconds.
        total_time_s: Total simulation duration in seconds.
        seed: Deterministic random seed for reproducibility.
        integrator: Name of the integration method to use.
            Phase 0 records this for future use but does NOT implement
            any integrator. Valid future values include
            ``"velocity_verlet"``, ``"leapfrog"``, ``"rk4"``.
        softening_m: Optional gravitational softening length in meters.
            Defaults to ``None`` (disabled). This is a numerical-experiment
            feature ONLY. Normal Newtonian gravity uses the physical
            inverse-square law without artificial softening. When enabled,
            the gravitational force denominator becomes
            ``(|r|^2 + softening_m^2)^(3/2)`` instead of ``|r|^3``.
            This should never be silently applied to ordinary simulations.

    Raises:
        ValueError: If any parameter is physically invalid.
    """

    time_step_s: float
    total_time_s: float
    seed: int
    integrator: str = "velocity_verlet"
    softening_m: float | None = None

    def __post_init__(self) -> None:
        if self.time_step_s <= 0:
            raise ValueError(
                f"time_step_s must be positive, got {self.time_step_s}"
            )
        if self.total_time_s <= 0:
            raise ValueError(
                f"total_time_s must be positive, got {self.total_time_s}"
            )
        if not isinstance(self.seed, int):
            raise TypeError(
                f"seed must be an integer, got {type(self.seed).__name__}"
            )
        if self.softening_m is not None and self.softening_m <= 0:
            raise ValueError(
                f"softening_m must be positive when set, got {self.softening_m}"
            )
