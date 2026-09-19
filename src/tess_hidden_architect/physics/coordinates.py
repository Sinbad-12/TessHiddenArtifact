"""Keplerian orbital elements to 3D Cartesian state-vector conversion.

Coordinate convention
---------------------
- The reference plane is the x-y plane.
- The observer looks along the +z axis toward the system.
- **Inclination i = 0** : face-on (orbital plane coincides with x-y).
- **Inclination i = pi/2** : edge-on (orbital plane contains the z-axis;
  transits are geometrically possible).

This convention is consistent with the standard IAU definition.

The conversion follows the classical procedure:

1. Compute position and velocity in the perifocal (orbital-plane) frame.
2. Rotate by argument of periapsis (omega), inclination (i), and
   longitude of ascending node (Omega) to obtain the 3D inertial frame.
"""

from __future__ import annotations

import math

import numpy as np


def keplerian_to_cartesian(
    semi_major_axis: float,
    eccentricity: float,
    inclination: float,
    longitude_of_ascending_node: float,
    argument_of_periapsis: float,
    true_anomaly: float,
    mu: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Convert Keplerian orbital elements to 3D Cartesian state vectors.

    Parameters
    ----------
    semi_major_axis : float
        Semi-major axis in meters (must be > 0).
    eccentricity : float
        Orbital eccentricity, dimensionless.  Must satisfy 0 <= e < 1
        for bound elliptical orbits.
    inclination : float
        Orbital inclination in radians.
        0 = face-on, pi/2 = edge-on.
    longitude_of_ascending_node : float
        Longitude of the ascending node (Omega) in radians.
    argument_of_periapsis : float
        Argument of periapsis (omega) in radians.
    true_anomaly : float
        True anomaly (nu) in radians.
    mu : float
        Gravitational parameter G * (M_1 + M_2) in m^3 s^-2.

    Returns
    -------
    position : np.ndarray, shape (3,)
        3D Cartesian position in meters.
    velocity : np.ndarray, shape (3,)
        3D Cartesian velocity in m/s.

    Raises
    ------
    ValueError
        If parameters are physically invalid.
    """
    if semi_major_axis <= 0:
        raise ValueError(
            f"semi_major_axis must be positive, got {semi_major_axis}"
        )
    if not (0.0 <= eccentricity < 1.0):
        raise ValueError(
            f"eccentricity must be in [0, 1), got {eccentricity}"
        )
    if mu <= 0:
        raise ValueError(f"mu must be positive, got {mu}")

    # Shorthand
    a = semi_major_axis
    e = eccentricity
    i = inclination
    Omega = longitude_of_ascending_node
    omega = argument_of_periapsis
    nu = true_anomaly

    # Semi-latus rectum
    p = a * (1.0 - e * e)

    # Distance from focus
    r_mag = p / (1.0 + e * math.cos(nu))

    # Position in perifocal frame (orbital plane)
    r_peri = np.array([
        r_mag * math.cos(nu),
        r_mag * math.sin(nu),
        0.0,
    ])

    # Velocity in perifocal frame
    h = math.sqrt(mu * p)  # specific angular momentum magnitude
    v_peri = np.array([
        -(mu / h) * math.sin(nu),
        (mu / h) * (e + math.cos(nu)),
        0.0,
    ])

    # Rotation matrix: perifocal -> inertial
    # R = R_z(-Omega) . R_x(-i) . R_z(-omega)
    cos_omega = math.cos(omega)
    sin_omega = math.sin(omega)
    cos_Omega = math.cos(Omega)
    sin_Omega = math.sin(Omega)
    cos_i = math.cos(i)
    sin_i = math.sin(i)

    # Combined rotation matrix elements
    r11 = cos_Omega * cos_omega - sin_Omega * sin_omega * cos_i
    r12 = -(cos_Omega * sin_omega + sin_Omega * cos_omega * cos_i)
    r13 = sin_Omega * sin_i

    r21 = sin_Omega * cos_omega + cos_Omega * sin_omega * cos_i
    r22 = -(sin_Omega * sin_omega - cos_Omega * cos_omega * cos_i)
    r23 = -cos_Omega * sin_i

    r31 = sin_omega * sin_i
    r32 = cos_omega * sin_i
    r33 = cos_i

    rotation = np.array([
        [r11, r12, r13],
        [r21, r22, r23],
        [r31, r32, r33],
    ])

    position = rotation @ r_peri
    velocity = rotation @ v_peri

    return position, velocity
