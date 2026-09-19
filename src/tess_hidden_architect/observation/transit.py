"""Forward synthetic transit observation generator.

Generates normalized stellar light curves for a single-star, single-planet
system using Keplerian orbital propagation and exact geometric disk-overlap
area calculation.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

from tess_hidden_architect.config.observation import ObservationConfig
from tess_hidden_architect.constants import G_SI
from tess_hidden_architect.data.provenance import ProvenanceRecord
from tess_hidden_architect.observation.observation import Observation
from tess_hidden_architect.physics.bodies import Body, Star
from tess_hidden_architect.physics.coordinates import keplerian_to_cartesian
from tess_hidden_architect.types import ProvenanceOrigin, QualityFlag


@dataclass
class KeplerianOrbit:
    """Keplerian orbital parameters for a companion body.

    Attributes:
        semi_major_axis_m: Semi-major axis in meters (> 0).
        eccentricity: Orbital eccentricity [0, 1).
        inclination_rad: Orbital inclination in radians (0 = face-on, pi/2 = edge-on).
        longitude_of_ascending_node_rad: Longitude of ascending node in radians.
        argument_of_periapsis_rad: Argument of periapsis in radians.
        initial_mean_anomaly_rad: Mean anomaly at t = 0 in radians.
    """

    semi_major_axis_m: float
    eccentricity: float = 0.0
    inclination_rad: float = math.pi / 2
    longitude_of_ascending_node_rad: float = 0.0
    argument_of_periapsis_rad: float = 0.0
    initial_mean_anomaly_rad: float = 0.0

    def __post_init__(self) -> None:
        if self.semi_major_axis_m <= 0:
            raise ValueError(
                f"semi_major_axis_m must be positive, got {self.semi_major_axis_m}"
            )
        if not (0.0 <= self.eccentricity < 1.0):
            raise ValueError(
                f"eccentricity must be in [0, 1), got {self.eccentricity}"
            )


def solve_kepler(
    mean_anomaly: np.ndarray,
    eccentricity: float,
    tol: float = 1e-12,
    max_iter: int = 50,
) -> np.ndarray:
    """Solve Kepler's equation M = E - e * sin(E) for eccentric anomaly E.

    Parameters
    ----------
    mean_anomaly : np.ndarray
        Mean anomaly values in radians.
    eccentricity : float
        Orbital eccentricity (0 <= e < 1).
    tol : float, optional
        Convergence tolerance for Newton-Raphson iteration.
    max_iter : int, optional
        Maximum Newton-Raphson iterations.

    Returns
    -------
    np.ndarray
        Eccentric anomaly E in radians with the same shape as mean_anomaly.
    """
    m_arr = np.asarray(mean_anomaly, dtype=np.float64)
    e = float(eccentricity)
    if e == 0.0:
        return m_arr

    # Initial guess
    e_arr = m_arr.copy()
    for _ in range(max_iter):
        f = e_arr - e * np.sin(e_arr) - m_arr
        f_prime = 1.0 - e * np.cos(e_arr)
        delta = f / f_prime
        e_arr -= delta
        if np.max(np.abs(delta)) < tol:
            break

    return e_arr


def eccentric_to_true_anomaly(
    eccentric_anomaly: np.ndarray,
    eccentricity: float,
) -> np.ndarray:
    """Convert eccentric anomaly E to true anomaly nu.

    Parameters
    ----------
    eccentric_anomaly : np.ndarray
        Eccentric anomaly in radians.
    eccentricity : float
        Orbital eccentricity (0 <= e < 1).

    Returns
    -------
    np.ndarray
        True anomaly nu in radians in [-pi, pi].
    """
    e_arr = np.asarray(eccentric_anomaly, dtype=np.float64)
    e = float(eccentricity)
    if e == 0.0:
        return e_arr

    sin_nu = np.sqrt(1.0 - e * e) * np.sin(e_arr) / (1.0 - e * np.cos(e_arr))
    cos_nu = (np.cos(e_arr) - e) / (1.0 - e * np.cos(e_arr))
    return np.arctan2(sin_nu, cos_nu)


def compute_disk_overlap_area(
    r_star: float,
    r_planet: float,
    separation: np.ndarray,
) -> np.ndarray:
    """Compute geometric overlap area between stellar and planetary circular disks.

    Parameters
    ----------
    r_star : float
        Stellar radius in meters (> 0).
    r_planet : float
        Planetary radius in meters (> 0).
    separation : np.ndarray
        Projected center-to-center distance on sky plane in meters.

    Returns
    -------
    np.ndarray
        Geometric intersection area in square meters.
    """
    d = np.asarray(separation, dtype=np.float64)
    r1 = float(r_star)
    r2 = float(r_planet)
    area = np.zeros_like(d)

    # Complete overlap: d <= |r1 - r2|
    full_mask = d <= abs(r1 - r2)
    area[full_mask] = math.pi * (min(r1, r2) ** 2)

    # Partial overlap: |r1 - r2| < d < r1 + r2
    partial_mask = (d > abs(r1 - r2)) & (d < (r1 + r2))
    if np.any(partial_mask):
        d_p = d[partial_mask]
        d_sq = d_p * d_p
        r1_sq = r1 * r1
        r2_sq = r2 * r2

        cos_t1 = np.clip((d_sq + r1_sq - r2_sq) / (2.0 * d_p * r1), -1.0, 1.0)
        cos_t2 = np.clip((d_sq + r2_sq - r1_sq) / (2.0 * d_p * r2), -1.0, 1.0)

        t1 = np.arccos(cos_t1)
        t2 = np.arccos(cos_t2)

        triangle_arg = np.maximum(
            0.0,
            (-d_p + r1 + r2) * (d_p + r1 - r2) * (d_p - r1 + r2) * (d_p + r1 + r2),
        )
        triangle = 0.5 * np.sqrt(triangle_arg)
        area[partial_mask] = r1_sq * t1 + r2_sq * t2 - triangle

    return area


def generate_synthetic_transit_observation(
    star: Star,
    planet: Body | None = None,
    *,
    orbit: KeplerianOrbit | None = None,
    planet_radius_m: float | None = None,
    planet_mass_kg: float = 0.0,
    semi_major_axis_m: float | None = None,
    eccentricity: float = 0.0,
    inclination_rad: float = math.pi / 2,
    longitude_of_ascending_node_rad: float = 0.0,
    argument_of_periapsis_rad: float = 0.0,
    initial_mean_anomaly_rad: float = 0.0,
    cadence_s: float = 120.0,
    duration_s: float | None = None,
    num_periods: float = 3.0,
    noise_std: float = 0.0,
    seed: int | None = None,
    observation_config: ObservationConfig | None = None,
    scenario_name: str | None = None,
) -> Observation:
    """Generate a synthetic transit observation for a single-star single-planet system.

    Parameters
    ----------
    star : Star
        The host star.
    planet : Body or None, optional
        Companion planet body. If provided, overrides planet_radius_m and
        planet_mass_kg.
    orbit : KeplerianOrbit or None, optional
        Orbital configuration. If provided, overrides individual orbital element arguments.
    planet_radius_m : float or None, optional
        Planet radius in meters. Required if planet is not provided.
    planet_mass_kg : float, optional
        Planet mass in kg (default 0.0).
    semi_major_axis_m : float or None, optional
        Semi-major axis in meters. Required if orbit is not provided.
    eccentricity : float, optional
        Orbital eccentricity [0, 1). Default is 0.0.
    inclination_rad : float, optional
        Orbital inclination in radians (0 = face-on, pi/2 = edge-on). Default is pi/2.
    longitude_of_ascending_node_rad : float, optional
        Longitude of ascending node in radians. Default is 0.0.
    argument_of_periapsis_rad : float, optional
        Argument of periapsis in radians. Default is 0.0.
    initial_mean_anomaly_rad : float, optional
        Mean anomaly at t = 0 in radians. Default is 0.0.
    cadence_s : float, optional
        Cadence (time between observations) in seconds. Default is 120.0 s.
    duration_s : float or None, optional
        Total observation duration in seconds. If None, computed as num_periods * period.
    num_periods : float, optional
        Number of orbital periods to observe when duration_s is None. Default is 3.0.
    noise_std : float, optional
        Standard deviation of Gaussian measurement noise added to normalized flux.
    seed : int or None, optional
        Random seed for deterministic Gaussian noise.
    observation_config : ObservationConfig or None, optional
        If provided, overrides cadence_s, duration_s, seed, and noise_std (if configured).
    scenario_name : str or None, optional
        Name of the simulated scenario for provenance tracking.

    Returns
    -------
    Observation
        Observation product containing timestamps, flux, uncertainties, quality flags,
        and simulated provenance metadata, WITHOUT exposing hidden planet parameters.
    """
    # 1. Resolve planetary physical parameters
    if planet is not None:
        rp = float(planet.radius)
        mp = float(planet.mass)
    else:
        if planet_radius_m is None or planet_radius_m <= 0:
            raise ValueError(
                f"planet_radius_m must be positive, got {planet_radius_m}"
            )
        rp = float(planet_radius_m)
        mp = float(planet_mass_kg)

    # 2. Resolve orbital parameters
    if orbit is not None:
        sma = orbit.semi_major_axis_m
        ecc = orbit.eccentricity
        inc = orbit.inclination_rad
        omega_node = orbit.longitude_of_ascending_node_rad
        arg_peri = orbit.argument_of_periapsis_rad
        m0 = orbit.initial_mean_anomaly_rad
    else:
        if semi_major_axis_m is None or semi_major_axis_m <= 0:
            raise ValueError(
                f"semi_major_axis_m must be positive, got {semi_major_axis_m}"
            )
        sma = float(semi_major_axis_m)
        ecc = float(eccentricity)
        inc = float(inclination_rad)
        omega_node = float(longitude_of_ascending_node_rad)
        arg_peri = float(argument_of_periapsis_rad)
        m0 = float(initial_mean_anomaly_rad)

    # 3. Resolve observation configuration
    if observation_config is not None:
        cadence = float(observation_config.cadence_s)
        duration = float(observation_config.duration_s)
        if seed is None:
            seed = observation_config.seed
        if observation_config.noise_parameters and noise_std == 0.0:
            noise_std = float(
                observation_config.noise_parameters.get(
                    "std",
                    observation_config.noise_parameters.get(
                        "noise_std",
                        observation_config.noise_parameters.get("sigma", 0.0),
                    ),
                )
            )
    else:
        cadence = float(cadence_s)
        duration = float(duration_s) if duration_s is not None else None

    # 4. Compute orbital dynamics
    mu = G_SI * (star.mass + mp)
    period_s = 2.0 * math.pi * math.sqrt((sma**3) / mu)

    if duration is None:
        duration = float(num_periods) * period_s

    # Chronological timestamps array spanning multiple periods
    timestamps = np.arange(0.0, duration, cadence, dtype=np.float64)
    if len(timestamps) == 0:
        raise ValueError(f"duration ({duration}) must be greater than cadence ({cadence})")

    # 5. Propagate orbit using Keplerian mechanics
    mean_motion = 2.0 * math.pi / period_s
    mean_anomalies = (m0 + mean_motion * timestamps) % (2.0 * math.pi)

    eccentric_anomalies = solve_kepler(mean_anomalies, ecc)
    true_anomalies = eccentric_to_true_anomaly(eccentric_anomalies, ecc)

    # Compute 3D positions for each time step using existing keplerian_to_cartesian model
    n_points = len(timestamps)
    positions = np.empty((n_points, 3), dtype=np.float64)
    for idx, nu in enumerate(true_anomalies):
        pos, _ = keplerian_to_cartesian(
            semi_major_axis=sma,
            eccentricity=ecc,
            inclination=inc,
            longitude_of_ascending_node=omega_node,
            argument_of_periapsis=arg_peri,
            true_anomaly=float(nu),
            mu=mu,
        )
        positions[idx] = pos

    # 6. Projected separation and line-of-sight check
    # Observer looks along +z toward the system.
    # The planet is in front of the host star if z < 0.
    # Projected separation on sky plane: d = sqrt(x^2 + y^2).
    x = positions[:, 0]
    y = positions[:, 1]
    z = positions[:, 2]
    d_sky = np.sqrt(x * x + y * y)

    # 7. Compute normalized flux using geometric disk-overlap
    star_disk_area = math.pi * (star.radius**2)
    flux = np.ones(n_points, dtype=np.float64)

    # Transit can only occur when planet is in front of the star (z < 0)
    in_front_mask = z < 0.0
    if np.any(in_front_mask):
        overlap_areas = compute_disk_overlap_area(
            r_star=star.radius,
            r_planet=rp,
            separation=d_sky[in_front_mask],
        )
        obscured_fraction = overlap_areas / star_disk_area
        flux[in_front_mask] = 1.0 - obscured_fraction

    # 8. Deterministic Gaussian measurement noise
    if noise_std > 0.0:
        rng = np.random.default_rng(seed)
        noise = rng.normal(0.0, noise_std, size=n_points)
        flux_observed = flux + noise
        uncertainties = np.full(n_points, noise_std, dtype=np.float64)
    else:
        flux_observed = flux.copy()
        uncertainties = np.zeros(n_points, dtype=np.float64)

    # 9. Quality flags (all GOOD)
    quality_flags = np.full(n_points, QualityFlag.GOOD.value, dtype=np.int32)

    # 10. Build provenance without exposing hidden ground truth
    provenance = ProvenanceRecord(
        origin=ProvenanceOrigin.SIMULATED,
        simulation_seed=seed,
        scenario_name=scenario_name or "synthetic_transit",
    )

    return Observation(
        timestamps_s=timestamps,
        flux=flux_observed,
        uncertainties=uncertainties,
        quality_flags=quality_flags,
        provenance=provenance,
    )
