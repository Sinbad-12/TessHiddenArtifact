"""Focused tests for the N-body gravitational integrator."""

import math
import numpy as np
import pytest

from tess_hidden_architect.constants import AU_IN_METERS, G_SI, SOLAR_MASS_KG, SOLAR_RADIUS_M
from tess_hidden_architect.physics import (
    Body,
    NBodyIntegrator,
    Star,
    SystemState,
    compute_gravitational_acceleration,
    shift_to_barycentric_frame,
)
from tess_hidden_architect.validation import (
    compute_center_of_mass,
    compute_total_angular_momentum,
    compute_total_energy,
    compute_total_linear_momentum,
)


@pytest.fixture
def standard_two_body_system() -> tuple[SystemState, float, float]:
    """Create a standard Star + Jupiter-mass planet system in circular orbit.

    Returns:
        system: SystemState shifted to barycenter.
        semi_major_axis_m: Orbit radius.
        period_s: Orbital period.
    """
    m_star = SOLAR_MASS_KG
    m_planet = 1.898e27  # Jupiter mass
    a = 0.05 * AU_IN_METERS  # ~0.05 AU
    mu = G_SI * (m_star + m_planet)
    period = 2.0 * math.pi * math.sqrt(a**3 / mu)
    v_orb = math.sqrt(mu / a)

    # Place star and planet relative to origin, then shift to barycenter
    star = Star(
        name="HostStar",
        mass=m_star,
        radius=SOLAR_RADIUS_M,
        position=np.zeros(3),
        velocity=np.zeros(3),
    )
    planet = Body(
        name="PlanetB",
        mass=m_planet,
        radius=7.0e7,
        position=np.array([a, 0.0, 0.0]),
        velocity=np.array([0.0, v_orb, 0.0]),
    )

    system = SystemState(bodies=[star, planet])
    shift_to_barycentric_frame(system)
    return system, a, period


def test_two_body_gravitational_acceleration() -> None:
    """Verify pairwise Newtonian acceleration and Newton's third law."""
    m1 = SOLAR_MASS_KG
    m2 = 1.898e27
    r = 1.5e11  # 1 AU

    positions = np.array([
        [0.0, 0.0, 0.0],
        [r, 0.0, 0.0],
    ])
    masses = np.array([m1, m2])

    acc = compute_gravitational_acceleration(positions, masses)

    # Force on body 0 is towards body 1 (+x direction)
    expected_a0_x = G_SI * m2 / (r**2)
    # Force on body 1 is towards body 0 (-x direction)
    expected_a1_x = -G_SI * m1 / (r**2)

    assert acc[0, 0] == pytest.approx(expected_a0_x, rel=1e-12)
    assert acc[1, 0] == pytest.approx(expected_a1_x, rel=1e-12)
    assert np.all(acc[:, 1:] == 0.0)

    # Newton's third law: m1 * a1 + m2 * a2 == 0
    net_force = m1 * acc[0] + m2 * acc[1]
    assert np.linalg.norm(net_force) == pytest.approx(0.0, abs=1e-15)


def test_deterministic_integration() -> None:
    """Verify integration is strictly deterministic and bit-for-bit reproducible."""
    # Star + 2 planets system
    star = Star(name="Star", mass=SOLAR_MASS_KG, radius=SOLAR_RADIUS_M)
    p1 = Body(name="Planet1", mass=1.0e27, radius=5e7, position=np.array([0.04 * AU_IN_METERS, 0.0, 0.0]), velocity=np.array([0.0, 45000.0, 0.0]))
    p2 = Body(name="Planet2", mass=2.0e27, radius=6e7, position=np.array([0.08 * AU_IN_METERS, 0.0, 0.0]), velocity=np.array([0.0, 32000.0, 0.0]))

    sys1 = SystemState(bodies=[star, p1, p2])
    shift_to_barycentric_frame(sys1)

    sys2 = SystemState(bodies=[
        Star(name="Star", mass=star.mass, radius=star.radius, position=star.position.copy(), velocity=star.velocity.copy()),
        Body(name="Planet1", mass=p1.mass, radius=p1.radius, position=p1.position.copy(), velocity=p1.velocity.copy()),
        Body(name="Planet2", mass=p2.mass, radius=p2.radius, position=p2.position.copy(), velocity=p2.velocity.copy()),
    ])

    integrator = NBodyIntegrator(time_step_s=100.0)
    _, traj1 = integrator.integrate(sys1, duration_s=86400.0)
    _, traj2 = integrator.integrate(sys2, duration_s=86400.0)

    assert np.array_equal(traj1.positions, traj2.positions)
    assert np.array_equal(traj1.velocities, traj2.velocities)
    assert np.array_equal(traj1.timestamps_s, traj2.timestamps_s)


def test_approximate_energy_conservation(standard_two_body_system: tuple[SystemState, float, float]) -> None:
    """Verify that mechanical energy is conserved with symplectic accuracy over multiple orbits."""
    system, _, period = standard_two_body_system
    integrator = NBodyIntegrator(time_step_s=60.0)

    # Integrate for 5 complete orbits
    duration = 5.0 * period
    _, traj = integrator.integrate(system, duration_s=duration, record_interval_s=600.0)

    masses = traj.masses
    energies = []
    for step in range(len(traj.timestamps_s)):
        pos = traj.positions[step]
        vel = traj.velocities[step]
        _, _, e_tot = compute_total_energy(pos, vel, masses)
        energies.append(e_tot)

    e0 = energies[0]
    e_max_diff = max(abs(e - e0) for e in energies)
    rel_energy_error = e_max_diff / abs(e0)

    # Velocity-Verlet energy conservation over 5 orbits
    assert rel_energy_error < 1e-6, f"Relative energy error {rel_energy_error:.3e} exceeds 1e-6"


def test_approximate_angular_momentum_conservation(standard_two_body_system: tuple[SystemState, float, float]) -> None:
    """Verify that angular momentum vector is conserved over multiple orbits."""
    system, _, period = standard_two_body_system
    integrator = NBodyIntegrator(time_step_s=60.0)

    duration = 5.0 * period
    _, traj = integrator.integrate(system, duration_s=duration, record_interval_s=600.0)

    masses = traj.masses
    l_vectors = []
    for step in range(len(traj.timestamps_s)):
        pos = traj.positions[step]
        vel = traj.velocities[step]
        l_vec = compute_total_angular_momentum(pos, vel, masses)
        l_vectors.append(l_vec)

    l0 = l_vectors[0]
    l0_norm = np.linalg.norm(l0)
    l_max_diff = max(np.linalg.norm(l - l0) for l in l_vectors)
    rel_l_error = l_max_diff / l0_norm

    assert rel_l_error < 1e-10, f"Relative angular momentum error {rel_l_error:.3e} exceeds 1e-10"


def test_linear_momentum_and_center_of_mass_sanity(standard_two_body_system: tuple[SystemState, float, float]) -> None:
    """Verify linear momentum conservation and stationary center of mass."""
    system, _, period = standard_two_body_system
    integrator = NBodyIntegrator(time_step_s=60.0)

    duration = 3.0 * period
    _, traj = integrator.integrate(system, duration_s=duration, record_interval_s=600.0)

    masses = traj.masses
    max_rcm_drift = 0.0
    for step in range(len(traj.timestamps_s)):
        pos = traj.positions[step]
        vel = traj.velocities[step]
        rcm = compute_center_of_mass(pos, masses)
        p_lin = compute_total_linear_momentum(vel, masses)

        rcm_drift = float(np.linalg.norm(rcm))
        if rcm_drift > max_rcm_drift:
            max_rcm_drift = rcm_drift

        # Total linear momentum should remain virtually 0 (< 1e18 kg m/s vs total momentum scale > 1e35)
        assert np.linalg.norm(p_lin) < 1e19

    # Center-of-mass position drift must be sub-micron (< 1e-4 m) over 3 AU-scale orbits
    assert max_rcm_drift < 1e-4, f"Center of mass drifted by {max_rcm_drift:.3e} m"


def test_stable_star_planet_orbit(standard_two_body_system: tuple[SystemState, float, float]) -> None:
    """Verify that a circular orbit remains stable and circular over 10 full orbits."""
    system, semimajor_axis, period = standard_two_body_system
    integrator = NBodyIntegrator(time_step_s=60.0)

    # 10 full orbits
    duration = 10.0 * period
    _, traj = integrator.integrate(system, duration_s=duration, record_interval_s=1200.0)

    # Measure star-planet distance at all snapshots
    r_star = traj.positions[:, 0, :]
    r_planet = traj.positions[:, 1, :]
    separations = np.linalg.norm(r_planet - r_star, axis=1)

    max_rel_radius_deviation = float(np.max(np.abs(separations - semimajor_axis) / semimajor_axis))

    # For circular orbit with dt=60s, radial variation is tiny (< 0.05%)
    assert max_rel_radius_deviation < 5e-4, f"Max radial deviation {max_rel_radius_deviation:.3e} exceeds 5e-4"
