"""Dynamical body and stellar data models.

All quantities are stored in SI units (meters, kilograms, seconds, watts, kelvin).
Positions and velocities are 3D Cartesian vectors.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from tess_hidden_architect.constants import SOLAR_LUMINOSITY_W


def _validate_positive(value: float, name: str) -> None:
    """Raise ValueError if *value* is not finite and positive."""
    if not np.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be finite and positive, got {value}")


def _validate_3d_vector(arr: np.ndarray, name: str) -> np.ndarray:
    """Ensure *arr* is a finite float64 array with shape (3,)."""
    arr = np.asarray(arr, dtype=np.float64)
    if arr.shape != (3,):
        raise ValueError(f"{name} must have shape (3,), got {arr.shape}")
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} must contain only finite values")
    return arr


@dataclass
class Body:
    """A dynamical body participating in gravitational interactions.

    All bodies — including stars — share this base representation so
    that they can be stored in a single collection and participate
    uniformly in mutual Newtonian gravity.

    Attributes:
        name: Human-readable identifier.
        mass: Mass in kilograms (must be > 0).
        radius: Physical radius in meters (must be > 0).
        position: 3D Cartesian position in meters, shape (3,).
        velocity: 3D Cartesian velocity in m/s, shape (3,).
    """

    name: str
    mass: float
    radius: float
    position: np.ndarray = field(default_factory=lambda: np.zeros(3))
    velocity: np.ndarray = field(default_factory=lambda: np.zeros(3))

    def __post_init__(self) -> None:
        _validate_positive(self.mass, "mass")
        _validate_positive(self.radius, "radius")
        self.position = _validate_3d_vector(self.position, "position")
        self.velocity = _validate_3d_vector(self.velocity, "velocity")


@dataclass
class Star(Body):
    """A stellar body with additional astrophysical properties.

    Inherits all dynamical fields from :class:`Body` and adds stellar
    parameters needed for transit and light-curve modelling.

    A ``Star`` is stored alongside planets in the same ``bodies`` list
    within a :class:`~tess_hidden_architect.physics.system.SystemState`.
    It participates in gravitational dynamics identically to any other body.

    Attributes:
        luminosity: Bolometric luminosity in watts (must be > 0).
        effective_temperature: Effective surface temperature in kelvin
            (must be > 0).
        limb_darkening_coefficients: Tuple of coefficients for the
            limb-darkening law. The interpretation (linear, quadratic,
            power-2, etc.) depends on the transit model used. Empty tuple
            means no limb-darkening coefficients are specified.
        variability_parameters: Optional dictionary describing intrinsic
            stellar variability (e.g., spot modulation, oscillations).
            Reserved for future use.
    """

    luminosity: float = SOLAR_LUMINOSITY_W
    effective_temperature: float = 5778.0
    limb_darkening_coefficients: tuple[float, ...] = ()
    variability_parameters: dict | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        _validate_positive(self.luminosity, "luminosity")
        _validate_positive(self.effective_temperature, "effective_temperature")
