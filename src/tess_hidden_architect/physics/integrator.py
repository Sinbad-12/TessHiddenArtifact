"""Symplectic N-body gravitational integrator.

Implements the time-reversible, 2nd-order Velocity-Verlet algorithm for
deterministic N-body numerical integration under Newtonian mutual gravity.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

from tess_hidden_architect.physics.bodies import Body
from tess_hidden_architect.physics.gravity import compute_gravitational_acceleration
from tess_hidden_architect.physics.system import SystemState


@dataclass
class SimulationTrajectory:
    """Recorded trajectory history from an N-body integration run.

    Attributes:
        timestamps_s: Observation epochs in SI seconds, shape (M,).
        positions: 3D Cartesian positions of all bodies in meters, shape (M, N, 3).
        velocities: 3D Cartesian velocities of all bodies in m/s, shape (M, N, 3).
        masses: Static masses of all bodies in kilograms, shape (N,).
        body_names: Identifiers of all N bodies in order.
    """

    timestamps_s: np.ndarray
    positions: np.ndarray
    velocities: np.ndarray
    masses: np.ndarray
    body_names: list[str]

    def __post_init__(self) -> None:
        m = len(self.timestamps_s)
        n = len(self.masses)
        if self.positions.shape != (m, n, 3):
            raise ValueError(
                f"positions shape {self.positions.shape} inconsistent with "
                f"M={m}, N={n}, 3"
            )
        if self.velocities.shape != (m, n, 3):
            raise ValueError(
                f"velocities shape {self.velocities.shape} inconsistent with "
                f"M={m}, N={n}, 3"
            )
        if len(self.body_names) != n:
            raise ValueError(
                f"body_names length {len(self.body_names)} does not match N={n}"
            )


def shift_to_barycentric_frame(system: SystemState) -> None:
    """Shift a SystemState's positions and velocities in-place to the barycenter.

    Subtracts the center-of-mass position and velocity so that total linear
    momentum is zero and the center of mass is at the origin (0, 0, 0).

    Parameters
    ----------
    system : SystemState
        The gravitational system to shift.
    """
    if len(system.bodies) == 0:
        return

    masses = np.array([b.mass for b in system.bodies], dtype=np.float64)
    total_mass = float(np.sum(masses))
    if total_mass <= 0:
        raise ValueError("Total mass must be strictly positive")

    positions = np.array([b.position for b in system.bodies], dtype=np.float64)
    velocities = np.array([b.velocity for b in system.bodies], dtype=np.float64)

    rcm = np.sum(positions * masses[:, None], axis=0) / total_mass
    vcm = np.sum(velocities * masses[:, None], axis=0) / total_mass

    for b in system.bodies:
        b.position = b.position - rcm
        b.velocity = b.velocity - vcm


class NBodyIntegrator:
    """Deterministic Velocity-Verlet symplectic N-body gravitational integrator.

    The Velocity-Verlet algorithm advances coordinates and velocities as:
        v(t + dt/2) = v(t) + (dt/2) * a(r(t))
        r(t + dt)   = r(t) + dt * v(t + dt/2)
        a(t + dt)   = a(r(t + dt))
        v(t + dt)   = v(t + dt/2) + (dt/2) * a(t + dt)

    This algorithm is:
    - Symplectic: preserves phase-space volume and exhibits no secular energy drift.
    - Time-reversible: stepping forward and backward reproduces initial state.
    - Conserves total linear momentum exactly (within machine precision).
    - Requires exactly 1 acceleration evaluation per full time step.
    """

    def __init__(
        self,
        time_step_s: float = 60.0,
        *,
        softening_m: float | None = None,
    ) -> None:
        if time_step_s <= 0:
            raise ValueError(f"time_step_s must be positive, got {time_step_s}")
        if softening_m is not None and softening_m <= 0:
            raise ValueError(f"softening_m must be positive when set, got {softening_m}")

        self.time_step_s = float(time_step_s)
        self.softening_m = float(softening_m) if softening_m is not None else None

    def step(
        self,
        positions: np.ndarray,
        velocities: np.ndarray,
        masses: np.ndarray,
        dt: float,
        current_accelerations: np.ndarray | None = None,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Perform a single Velocity-Verlet step.

        Parameters
        ----------
        positions : np.ndarray, shape (N, 3)
            Current positions in meters.
        velocities : np.ndarray, shape (N, 3)
            Current velocities in m/s.
        masses : np.ndarray, shape (N,)
            Body masses in kg.
        dt : float
            Time step in seconds.
        current_accelerations : np.ndarray or None, optional
            Precomputed accelerations at current positions. If None,
            computed immediately.

        Returns
        -------
        new_positions : np.ndarray, shape (N, 3)
        new_velocities : np.ndarray, shape (N, 3)
        new_accelerations : np.ndarray, shape (N, 3)
        """
        if current_accelerations is None:
            a_curr = compute_gravitational_acceleration(
                positions, masses, softening=self.softening_m
            )
        else:
            a_curr = current_accelerations

        # Half-step velocity
        v_half = velocities + 0.5 * dt * a_curr

        # Full-step position
        r_next = positions + dt * v_half

        # Acceleration at new position (only 1 force evaluation per step)
        a_next = compute_gravitational_acceleration(
            r_next, masses, softening=self.softening_m
        )

        # Full-step velocity
        v_next = v_half + 0.5 * dt * a_next

        return r_next, v_next, a_next

    def step_system(
        self,
        system: SystemState,
        dt: float | None = None,
    ) -> None:
        """Advance a SystemState by one time step in-place.

        Parameters
        ----------
        system : SystemState
            The gravitational system state.
        dt : float or None, optional
            Time step in seconds (defaults to self.time_step_s).
        """
        step_dt = float(dt) if dt is not None else self.time_step_s
        if len(system.bodies) == 0:
            system.epoch += step_dt
            return

        positions = np.array([b.position for b in system.bodies], dtype=np.float64)
        velocities = np.array([b.velocity for b in system.bodies], dtype=np.float64)
        masses = np.array([b.mass for b in system.bodies], dtype=np.float64)

        r_next, v_next, _ = self.step(positions, velocities, masses, step_dt)

        for idx, b in enumerate(system.bodies):
            b.position = r_next[idx]
            b.velocity = v_next[idx]
        system.epoch += step_dt

    def integrate(
        self,
        system: SystemState,
        duration_s: float,
        *,
        time_step_s: float | None = None,
        record_interval_s: float | None = None,
    ) -> tuple[SystemState, SimulationTrajectory]:
        """Integrate a system forward in time and record its trajectory.

        Parameters
        ----------
        system : SystemState
            Initial system state.
        duration_s : float
            Total integration duration in seconds (> 0).
        time_step_s : float or None, optional
            Integration timestep in seconds. Defaults to self.time_step_s.
        record_interval_s : float or None, optional
            Cadence to record snapshots in seconds. If None, records every
            integration timestep.

        Returns
        -------
        final_system : SystemState
            Updated SystemState at epoch t_final.
        trajectory : SimulationTrajectory
            Recorded history of timestamps, positions, and velocities.
        """
        if duration_s <= 0:
            raise ValueError(f"duration_s must be positive, got {duration_s}")

        dt = float(time_step_s) if time_step_s is not None else self.time_step_s
        if dt <= 0:
            raise ValueError(f"dt must be positive, got {dt}")

        n_bodies = len(system.bodies)
        if n_bodies == 0:
            raise ValueError("Cannot integrate a system with 0 bodies")

        masses = np.array([b.mass for b in system.bodies], dtype=np.float64)
        body_names = [b.name for b in system.bodies]

        positions = np.array([b.position.copy() for b in system.bodies], dtype=np.float64)
        velocities = np.array([b.velocity.copy() for b in system.bodies], dtype=np.float64)

        # Number of integration steps
        n_steps = max(1, int(math.ceil(duration_s / dt)))
        # Adjust dt slightly to span exactly duration_s
        actual_dt = duration_s / n_steps

        # Snapshot recording stride
        if record_interval_s is not None and record_interval_s > actual_dt:
            stride = max(1, int(round(record_interval_s / actual_dt)))
        else:
            stride = 1

        # Preallocate history storage
        recorded_times: list[float] = [float(system.epoch)]
        recorded_positions: list[np.ndarray] = [positions.copy()]
        recorded_velocities: list[np.ndarray] = [velocities.copy()]

        current_time = float(system.epoch)
        current_acc = compute_gravitational_acceleration(
            positions, masses, softening=self.softening_m
        )

        for step_idx in range(1, n_steps + 1):
            positions, velocities, current_acc = self.step(
                positions,
                velocities,
                masses,
                actual_dt,
                current_accelerations=current_acc,
            )
            current_time += actual_dt

            if step_idx % stride == 0 or step_idx == n_steps:
                recorded_times.append(current_time)
                recorded_positions.append(positions.copy())
                recorded_velocities.append(velocities.copy())

        # Update final SystemState in-place
        for idx, b in enumerate(system.bodies):
            b.position = positions[idx].copy()
            b.velocity = velocities[idx].copy()
        system.epoch = current_time

        trajectory = SimulationTrajectory(
            timestamps_s=np.array(recorded_times, dtype=np.float64),
            positions=np.array(recorded_positions, dtype=np.float64),
            velocities=np.array(recorded_velocities, dtype=np.float64),
            masses=masses,
            body_names=body_names,
        )

        return system, trajectory
