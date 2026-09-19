"""Control system for validating hidden-companion TTVs.

The control contains the same host star and transiting Planet A as the
hidden-companion scenario, but removes Planet B entirely.

This provides a physically integrated baseline against which the
interacting three-body system can be compared.
"""

from __future__ import annotations

from tess_hidden_architect.physics.integrator import shift_to_barycentric_frame
from tess_hidden_architect.physics.system import SystemState
from tess_hidden_architect.scenarios.builder import (
    make_body_from_keplerian,
    make_star,
)
from tess_hidden_architect.constants import (
    SOLAR_MASS_KG,
    SOLAR_RADIUS_M,
    au_to_m,
)


JUPITER_MASS_KG = 1.89813e27
JUPITER_RADIUS_M = 7.1492e7


def make_control_system() -> SystemState:
    """Construct the Planet-A-only control system."""

    star = make_star(
        name="Host Star",
        mass_kg=SOLAR_MASS_KG,
        radius_m=SOLAR_RADIUS_M,
        effective_temperature_k=5778.0,
    )

    planet_a = make_body_from_keplerian(
        name="Planet A",
        mass_kg=JUPITER_MASS_KG,
        radius_m=JUPITER_RADIUS_M,
        semi_major_axis_m=au_to_m(0.035),
        eccentricity=0.01,
        inclination_rad=__import__("math").radians(89.7),
        longitude_of_ascending_node_rad=0.0,
        argument_of_periapsis_rad=__import__("math").radians(90.0),
        true_anomaly_rad=__import__("math").radians(270.0),
        central_mass_kg=SOLAR_MASS_KG,
    )

    system = SystemState(
        bodies=[star, planet_a],
        epoch=0.0,
        metadata={
            "scenario": "control_no_companion",
            "description": (
                "Control system containing the host star and transiting "
                "Planet A without a gravitational companion."
            ),
            "observer_axis": "+z",
            "planet_a_role": "transiting_target",
            "synthetic": True,
        },
    )

    shift_to_barycentric_frame(system)
    return system