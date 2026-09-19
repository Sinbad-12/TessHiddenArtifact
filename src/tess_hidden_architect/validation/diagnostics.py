"""Diagnostic hooks for conservation-law testing.

These functions compute instantaneous conserved quantities (total
mechanical energy and total angular momentum) for a given system
snapshot.  They are diagnostic tools, **not** integrators.

In later phases, these diagnostics will be used to monitor numerical
integrator accuracy over time.
"""

from __future__ import annotations

import numpy as np

from tess_hidden_architect.constants import G_SI


def compute_total_kinetic_energy(
    velocities: np.ndarray,
    masses: np.ndarray,
) -> float:
    """Compute total kinetic energy of all bodies.

    Parameters
    ----------
    velocities : np.ndarray, shape (N, 3)
        Velocity vectors in m/s.
    masses : np.ndarray, shape (N,)
        Masses in kg.

    Returns
    -------
    float
        Total kinetic energy in joules.
    """
    # KE = sum_i 0.5 * m_i * |v_i|^2
    v_sq = np.sum(velocities * velocities, axis=1)  # shape (N,)
    return float(0.5 * np.sum(masses * v_sq))


def compute_total_potential_energy(
    positions: np.ndarray,
    masses: np.ndarray,
) -> float:
    """Compute total gravitational potential energy.

    Parameters
    ----------
    positions : np.ndarray, shape (N, 3)
        Position vectors in meters.
    masses : np.ndarray, shape (N,)
        Masses in kg.

    Returns
    -------
    float
        Total potential energy in joules (negative for bound systems).
    """
    n = len(masses)
    pe = 0.0
    for i in range(n):
        for j in range(i + 1, n):
            r_ij = positions[j] - positions[i]
            dist = np.sqrt(np.dot(r_ij, r_ij))
            pe -= G_SI * masses[i] * masses[j] / dist
    return float(pe)


def compute_total_energy(
    positions: np.ndarray,
    velocities: np.ndarray,
    masses: np.ndarray,
) -> tuple[float, float, float]:
    """Compute total mechanical energy of the system.

    Parameters
    ----------
    positions : np.ndarray, shape (N, 3)
        Position vectors in meters.
    velocities : np.ndarray, shape (N, 3)
        Velocity vectors in m/s.
    masses : np.ndarray, shape (N,)
        Masses in kg.

    Returns
    -------
    kinetic_energy : float
        Total kinetic energy in joules.
    potential_energy : float
        Total gravitational potential energy in joules.
    total_energy : float
        Sum of kinetic and potential energy in joules.
    """
    ke = compute_total_kinetic_energy(velocities, masses)
    pe = compute_total_potential_energy(positions, masses)
    return ke, pe, ke + pe


def compute_total_angular_momentum(
    positions: np.ndarray,
    velocities: np.ndarray,
    masses: np.ndarray,
) -> np.ndarray:
    """Compute total angular momentum vector of the system.

    Parameters
    ----------
    positions : np.ndarray, shape (N, 3)
        Position vectors in meters.
    velocities : np.ndarray, shape (N, 3)
        Velocity vectors in m/s.
    masses : np.ndarray, shape (N,)
        Masses in kg.

    Returns
    -------
    np.ndarray, shape (3,)
        Total angular momentum vector in kg m^2 / s.
    """
    # L = sum_i m_i * (r_i x v_i)
    L = np.zeros(3)
    for idx in range(len(masses)):
        L += masses[idx] * np.cross(positions[idx], velocities[idx])
    return L
