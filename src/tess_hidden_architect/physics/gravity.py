"""Newtonian gravitational acceleration in 3D Cartesian coordinates.

The acceleration of body *i* due to all other bodies is:

    a_i = -G * sum_{j != i} m_j * (r_i - r_j) / |r_i - r_j|^3

By default, no gravitational softening is applied.  The physical
inverse-square law is used directly.  An optional softening length
may be provided for specialized numerical experiments; see
:func:`compute_gravitational_acceleration` for details.
"""

from __future__ import annotations

import numpy as np

from tess_hidden_architect.constants import G_SI


def compute_gravitational_acceleration(
    positions: np.ndarray,
    masses: np.ndarray,
    *,
    softening: float | None = None,
) -> np.ndarray:
    """Compute pairwise 3D Newtonian gravitational acceleration.

    Parameters
    ----------
    positions : np.ndarray, shape (N, 3)
        Cartesian positions of all N bodies in meters.
    masses : np.ndarray, shape (N,)
        Masses of all N bodies in kilograms.
    softening : float or None, optional
        Gravitational softening length in meters.  Defaults to ``None``
        (disabled).  When provided, the force denominator becomes
        ``(|r|^2 + softening^2)^(3/2)`` instead of ``|r|^3``.

        .. warning::
            This is a **numerical-experiment feature only**.  Normal
            planetary/stellar dynamics should use ``softening=None``
            (the default) so that the physical inverse-square law is
            applied without artificial modification.

    Returns
    -------
    np.ndarray, shape (N, 3)
        Gravitational acceleration vectors in m/s^2 for each body.

    Raises
    ------
    ValueError
        If input shapes are invalid or softening is not positive.
    """
    positions = np.asarray(positions, dtype=np.float64)
    masses = np.asarray(masses, dtype=np.float64)

    if positions.ndim != 2 or positions.shape[1] != 3:
        raise ValueError(
            f"positions must have shape (N, 3), got {positions.shape}"
        )
    n = positions.shape[0]
    if masses.shape != (n,):
        raise ValueError(
            f"masses must have shape ({n},), got {masses.shape}"
        )

    softening_sq: float = 0.0
    if softening is not None:
        if softening <= 0:
            raise ValueError(
                f"softening must be positive when set, got {softening}"
            )
        softening_sq = softening * softening

    accelerations = np.zeros_like(positions)

    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            r_ij = positions[i] - positions[j]  # vector from j to i
            dist_sq = np.dot(r_ij, r_ij) + softening_sq
            dist = np.sqrt(dist_sq)
            inv_dist_cubed = 1.0 / (dist * dist_sq)
            # a_i += -G * m_j * (r_i - r_j) / |r_i - r_j|^3
            accelerations[i] -= G_SI * masses[j] * r_ij * inv_dist_cubed

    return accelerations
