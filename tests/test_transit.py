"""Focused tests for the synthetic transit observation generator."""

import math
import numpy as np
import pytest

from tess_hidden_architect.constants import (
    AU_IN_METERS,
    DAY_IN_SECONDS,
    SOLAR_MASS_KG,
    SOLAR_RADIUS_M,
)
from tess_hidden_architect.observation import (
    KeplerianOrbit,
    Observation,
    compute_disk_overlap_area,
    generate_synthetic_transit_observation,
)
from tess_hidden_architect.physics.bodies import Body, Star
from tess_hidden_architect.types import ProvenanceOrigin


@pytest.fixture
def standard_system() -> tuple[Star, Body, KeplerianOrbit]:
    """Provide a standard Sun-like star and a Jupiter-sized planet in a 3-day orbit."""
    star = Star(
        name="HostStar",
        mass=SOLAR_MASS_KG,
        radius=SOLAR_RADIUS_M,
    )
    # Jupiter-sized planet: radius ~ 7.0e7 m (ratio Rp/Rs ~ 0.1, depth ~ 0.01)
    planet_radius = 0.1 * SOLAR_RADIUS_M
    planet_mass = 1.898e27
    planet = Body(
        name="PlanetB",
        mass=planet_mass,
        radius=planet_radius,
    )
    # 3-day circular orbit
    # a ~ (mu * (P / 2pi)^2)^(1/3)
    orbit = KeplerianOrbit(
        semi_major_axis_m=0.04 * AU_IN_METERS,
        eccentricity=0.0,
        inclination_rad=math.pi / 2,  # edge-on
    )
    return star, planet, orbit


def test_no_transit_face_on(standard_system: tuple[Star, Body, KeplerianOrbit]) -> None:
    """When the orbit is face-on (i = 0), no transit occurs across multiple periods."""
    star, planet, orbit = standard_system
    face_on_orbit = KeplerianOrbit(
        semi_major_axis_m=orbit.semi_major_axis_m,
        eccentricity=0.0,
        inclination_rad=0.0,  # face-on
    )

    obs = generate_synthetic_transit_observation(
        star=star,
        planet=planet,
        orbit=face_on_orbit,
        cadence_s=300.0,
        num_periods=2.5,
        noise_std=0.0,
    )

    # Flux must remain identically 1.0 at all observation timestamps
    assert isinstance(obs, Observation)
    assert len(obs.flux) > 100
    assert np.all(obs.flux == 1.0)
    assert np.min(obs.flux) == 1.0


def test_transit_occurs_edge_on(standard_system: tuple[Star, Body, KeplerianOrbit]) -> None:
    """When the orbit is edge-on (i = pi/2), periodic transit dips occur."""
    star, planet, orbit = standard_system

    obs = generate_synthetic_transit_observation(
        star=star,
        planet=planet,
        orbit=orbit,
        cadence_s=120.0,
        num_periods=3.0,
        noise_std=0.0,
    )

    assert isinstance(obs, Observation)
    # Flux should drop below 1.0 during transits
    assert np.min(obs.flux) < 1.0

    # There should be in-transit points (< 1.0) and out-of-transit points (== 1.0)
    in_transit = obs.flux < 1.0
    out_of_transit = obs.flux == 1.0
    assert np.any(in_transit)
    assert np.any(out_of_transit)

    # Timestamps span multiple periods
    mu = star.mass * 6.67430e-11
    period = 2.0 * math.pi * math.sqrt(orbit.semi_major_axis_m**3 / mu)
    total_span = obs.timestamps_s[-1] - obs.timestamps_s[0]
    assert total_span >= 2.5 * period


def test_central_full_transit_depth_approaches_radius_ratio_squared(
    standard_system: tuple[Star, Body, KeplerianOrbit],
) -> None:
    """Central full transit depth should equal (Rp / Rs)^2 for uniform stellar disk."""
    star, planet, orbit = standard_system
    expected_depth = (planet.radius / star.radius) ** 2

    # High-cadence sampling to cleanly capture the central full transit bottom
    obs = generate_synthetic_transit_observation(
        star=star,
        planet=planet,
        orbit=orbit,
        cadence_s=60.0,
        num_periods=1.5,
        noise_std=0.0,
    )

    min_flux = np.min(obs.flux)
    actual_depth = 1.0 - min_flux

    # The minimum observed depth should match (Rp/Rs)^2 to high precision
    assert actual_depth == pytest.approx(expected_depth, rel=1e-5)


def test_geometric_overlap_non_constant_during_ingress_egress(
    standard_system: tuple[Star, Body, KeplerianOrbit],
) -> None:
    """Flux must not simply jump as a step function; partial transit points exist."""
    star, planet, orbit = standard_system
    expected_full_depth = (planet.radius / star.radius) ** 2
    full_transit_flux = 1.0 - expected_full_depth

    obs = generate_synthetic_transit_observation(
        star=star,
        planet=planet,
        orbit=orbit,
        cadence_s=30.0,
        num_periods=1.5,
        noise_std=0.0,
    )

    # Points during ingress / egress have flux strictly between (1 - depth) and 1.0
    partial_transit_mask = (obs.flux > full_transit_flux + 1e-7) & (obs.flux < 1.0 - 1e-7)
    assert np.sum(partial_transit_mask) > 0, "Ingress/egress must have intermediate flux values"


def test_deterministic_noise_with_same_seed(
    standard_system: tuple[Star, Body, KeplerianOrbit],
) -> None:
    """Identical seed produces identical noise; different seed produces different noise."""
    star, planet, orbit = standard_system
    noise_sigma = 1e-4

    obs1 = generate_synthetic_transit_observation(
        star=star,
        planet=planet,
        orbit=orbit,
        cadence_s=300.0,
        num_periods=1.0,
        noise_std=noise_sigma,
        seed=42,
    )

    obs2 = generate_synthetic_transit_observation(
        star=star,
        planet=planet,
        orbit=orbit,
        cadence_s=300.0,
        num_periods=1.0,
        noise_std=noise_sigma,
        seed=42,
    )

    obs3 = generate_synthetic_transit_observation(
        star=star,
        planet=planet,
        orbit=orbit,
        cadence_s=300.0,
        num_periods=1.0,
        noise_std=noise_sigma,
        seed=999,
    )

    # obs1 and obs2 must match bit-for-bit
    assert np.array_equal(obs1.flux, obs2.flux)
    assert np.array_equal(obs1.uncertainties, obs2.uncertainties)
    assert np.all(obs1.uncertainties == noise_sigma)

    # obs3 must differ due to different seed
    assert not np.array_equal(obs1.flux, obs3.flux)


def test_observation_data_contains_no_hidden_ground_truth(
    standard_system: tuple[Star, Body, KeplerianOrbit],
) -> None:
    """Observation object must NOT expose hidden true planetary parameters."""
    star, planet, orbit = standard_system

    obs = generate_synthetic_transit_observation(
        star=star,
        planet=planet,
        orbit=orbit,
        cadence_s=300.0,
        num_periods=1.0,
        seed=123,
    )

    # Check provenance origin
    assert obs.provenance.origin == ProvenanceOrigin.SIMULATED
    assert obs.provenance.is_hidden_ground_truth is False

    # Check observation attributes do not leak ground-truth parameters
    for forbidden_attr in [
        "planet",
        "star",
        "orbit",
        "semi_major_axis",
        "semi_major_axis_m",
        "eccentricity",
        "inclination",
        "inclination_rad",
        "planet_radius",
        "planet_mass",
        "true_parameters",
    ]:
        assert not hasattr(obs, forbidden_attr), f"Observation leaked attribute: {forbidden_attr}"

    # Check provenance metadata dictionary does not carry ground truth objects
    if obs.provenance.metadata:
        for forbidden_key in ["planet", "orbit", "ground_truth", "true_system"]:
            assert forbidden_key not in obs.provenance.metadata
