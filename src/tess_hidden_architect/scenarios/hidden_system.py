"""Deterministic hidden multi-planet system scenario.

The scenario contains:
    - one solar-type host star,
    - Planet A: the observable transiting planet,
    - Planet B: a non-transiting gravitational companion.

The bodies are initialized from Keplerian orbital elements and then
shifted into the barycentric frame before N-body integration.

The scenario is synthetic and is intended for scientific validation and
the TESS Hidden Architect reconstruction experience.
"""

from __future__ import annotations

import math

from tess_hidden_architect.constants import (
    G_SI,
    SOLAR_MASS_KG,
    SOLAR_RADIUS_M,
    au_to_m,
)
from tess_hidden_architect.physics.bodies import Body, Star
from tess_hidden_architect.physics.system import SystemState
from tess_hidden_architect.scenarios.builder import (
    make_body_from_keplerian,
    make_star,
)
from tess_hidden_architect.physics.integrator import shift_to_barycentric_frame


# Physical constants for the scenario.
JUPITER_MASS_KG = 1.89813e27
JUPITER_RADIUS_M = 7.1492e7


def make_hidden_system() -> SystemState:
    """Construct the deterministic Star + Planet A + Planet B system.

    Planet A is the transiting body seen by the observer.

    Planet B is deliberately placed on a different orbital plane so that
    it does not transit the star from the observer's line of sight, while
    remaining massive enough to gravitationally perturb Planet A.

    Returns
    -------
    SystemState
        Barycentrically initialized three-body system.
    """

    star = make_star(
        name="Host Star",
        mass_kg=SOLAR_MASS_KG,
        radius_m=SOLAR_RADIUS_M,
        effective_temperature_k=5778.0,
    )

    # ------------------------------------------------------------------
    # Planet A: observable transiting planet
    #
    # Nearly edge-on orbit.  With the chosen orientation, the planet
    # passes close to the observer-star line of sight.
    # ------------------------------------------------------------------
    planet_a = make_body_from_keplerian(
        name="Planet A",
        mass_kg=JUPITER_MASS_KG,
        radius_m=JUPITER_RADIUS_M,
        semi_major_axis_m=au_to_m(0.035),
        eccentricity=0.01,
        inclination_rad=math.radians(89.7),
        longitude_of_ascending_node_rad=0.0,
        argument_of_periapsis_rad=math.radians(90.0),
        true_anomaly_rad=math.radians(270.0),
        central_mass_kg=SOLAR_MASS_KG,
    )

    # ------------------------------------------------------------------
    # Planet B: hidden gravitational companion
    #
    # This body is intentionally NOT coplanar with Planet A.  Its
    # inclination and node place it away from the stellar disk in
    # projection, so it does not create an obvious transit signal.
    #
    # Its mass is still dynamically significant and can perturb
    # Planet A's transit times.
    # ------------------------------------------------------------------
    planet_b = make_body_from_keplerian(
        name="Planet B",
        mass_kg=0.30 * JUPITER_MASS_KG,
        radius_m=0.60 * JUPITER_RADIUS_M,
        semi_major_axis_m=au_to_m(0.055),
        eccentricity=0.04,
        inclination_rad=math.radians(82.0),
        longitude_of_ascending_node_rad=math.radians(55.0),
        argument_of_periapsis_rad=math.radians(35.0),
        true_anomaly_rad=math.radians(145.0),
        central_mass_kg=SOLAR_MASS_KG,
    )

    system = SystemState(
        bodies=[star, planet_a, planet_b],
        epoch=0.0,
        metadata={
            "scenario": "hidden_companion",
            "description": (
                "A transiting planet gravitationally perturbed by a "
                "non-transiting companion."
            ),
            "observer_axis": "+z",
            "planet_a_role": "transiting_target",
            "planet_b_role": "hidden_gravitational_companion",
            "synthetic": True,
        },
    )

    # Convert the initially star-centered orbital states into a
    # barycentric state before N-body integration.
    shift_to_barycentric_frame(system)

    return system