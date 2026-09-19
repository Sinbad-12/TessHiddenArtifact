"""Scenario construction helpers.

Provides convenience functions for building common system configurations
from astronomical parameters.  These helpers convert user-friendly
astronomical units to the internal SI representation.

Phase 0 note:
    Only basic construction helpers are provided.  Preset scenarios
    (e.g., Sun-Earth, hot Jupiter) are deferred to later phases.
"""

from __future__ import annotations

import numpy as np

from tess_hidden_architect.constants import (
    G_SI,
    SOLAR_LUMINOSITY_W,
    SOLAR_MASS_KG,
    SOLAR_RADIUS_M,
    au_to_m,
    solar_mass_to_kg,
)
from tess_hidden_architect.physics.bodies import Body, Star
from tess_hidden_architect.physics.coordinates import keplerian_to_cartesian
from tess_hidden_architect.physics.system import SystemState


def make_star(
    name: str,
    mass_kg: float = SOLAR_MASS_KG,
    radius_m: float = SOLAR_RADIUS_M,
    luminosity_w: float = SOLAR_LUMINOSITY_W,
    effective_temperature_k: float = 5778.0,
    position: np.ndarray | None = None,
    velocity: np.ndarray | None = None,
    limb_darkening_coefficients: tuple[float, ...] = (),
) -> Star:
    """Create a Star with sensible solar defaults.

    Parameters
    ----------
    name : str
        Human-readable name.
    mass_kg : float
        Stellar mass in kg.
    radius_m : float
        Stellar radius in meters.
    luminosity_w : float
        Bolometric luminosity in watts.
    effective_temperature_k : float
        Effective temperature in kelvin.
    position : np.ndarray or None
        3D position in meters. Defaults to origin.
    velocity : np.ndarray or None
        3D velocity in m/s. Defaults to zero.
    limb_darkening_coefficients : tuple of float
        Limb-darkening coefficients.

    Returns
    -------
    Star
    """
    return Star(
        name=name,
        mass=mass_kg,
        radius=radius_m,
        position=position if position is not None else np.zeros(3),
        velocity=velocity if velocity is not None else np.zeros(3),
        luminosity=luminosity_w,
        effective_temperature=effective_temperature_k,
        limb_darkening_coefficients=limb_darkening_coefficients,
    )


def make_body_from_keplerian(
    name: str,
    mass_kg: float,
    radius_m: float,
    semi_major_axis_m: float,
    eccentricity: float,
    inclination_rad: float,
    longitude_of_ascending_node_rad: float,
    argument_of_periapsis_rad: float,
    true_anomaly_rad: float,
    central_mass_kg: float,
) -> Body:
    """Create a Body from Keplerian orbital elements.

    The orbital elements are converted to 3D Cartesian position and
    velocity using the standard Keplerian-to-Cartesian transformation.

    Parameters
    ----------
    name : str
        Human-readable name.
    mass_kg : float
        Body mass in kg.
    radius_m : float
        Physical radius in meters.
    semi_major_axis_m : float
        Semi-major axis in meters.
    eccentricity : float
        Orbital eccentricity [0, 1).
    inclination_rad : float
        Inclination in radians (0 = face-on, pi/2 = edge-on).
    longitude_of_ascending_node_rad : float
        Longitude of ascending node in radians.
    argument_of_periapsis_rad : float
        Argument of periapsis in radians.
    true_anomaly_rad : float
        True anomaly in radians.
    central_mass_kg : float
        Mass of the central body for computing mu.

    Returns
    -------
    Body
    """
    mu = G_SI * (central_mass_kg + mass_kg)
    position, velocity = keplerian_to_cartesian(
        semi_major_axis=semi_major_axis_m,
        eccentricity=eccentricity,
        inclination=inclination_rad,
        longitude_of_ascending_node=longitude_of_ascending_node_rad,
        argument_of_periapsis=argument_of_periapsis_rad,
        true_anomaly=true_anomaly_rad,
        mu=mu,
    )
    return Body(
        name=name,
        mass=mass_kg,
        radius=radius_m,
        position=position,
        velocity=velocity,
    )
