"""Transit-event extraction from numerically integrated trajectories.

Transit centers are derived from the actual N-body trajectory and the
observer's projected geometry. No orbital period or hidden transit times
are supplied to the extractor.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from tess_hidden_architect.physics.integrator import SimulationTrajectory


@dataclass(frozen=True)
class TransitEvent:
    """One geometrically detected transit event."""

    body_name: str
    center_time_s: float
    minimum_projected_separation_m: float
    ingress_time_s: float
    egress_time_s: float


def _quadratic_minimum_time(
    times_s: np.ndarray,
    separations_m: np.ndarray,
    index: int,
) -> float:
    """Refine a local minimum using a quadratic through three samples."""

    if index <= 0 or index >= len(times_s) - 1:
        return float(times_s[index])

    x = times_s[index - 1:index + 2]
    y = separations_m[index - 1:index + 2]

    # Shift time coordinates for numerical conditioning.
    x0 = x[1]
    u = x - x0

    coefficients = np.polyfit(u, y, 2)
    a, b, _ = coefficients

    if a <= 0.0 or not np.isfinite(a) or not np.isfinite(b):
        return float(x0)

    vertex = -b / (2.0 * a)

    # Never extrapolate beyond the three samples used for interpolation.
    half_width = max(abs(u[0]), abs(u[2]))
    vertex = float(np.clip(vertex, -half_width, half_width))

    return float(x0 + vertex)


def _interpolate_crossing_time(
    t0: float,
    t1: float,
    d0: float,
    d1: float,
    threshold: float,
) -> float:
    """Linearly interpolate the time at which separation crosses threshold."""

    if d1 == d0:
        return float(0.5 * (t0 + t1))

    fraction = (threshold - d0) / (d1 - d0)
    fraction = float(np.clip(fraction, 0.0, 1.0))
    return float(t0 + fraction * (t1 - t0))


def extract_transit_events(
    trajectory: SimulationTrajectory,
    *,
    star_name: str,
    planet_name: str,
    star_radius_m: float,
    planet_radius_m: float,
) -> list[TransitEvent]:
    """Extract transit centers from a numerical trajectory.

    The observer looks along the +z axis. Therefore the projected
    star-planet separation is measured in the x-y plane.

    A transit is detected whenever the planet center enters the
    projected stellar disk expanded by the planet radius:

        projected_separation <= R_star + R_planet

    The center time is refined from the local minimum projected
    separation.

    Parameters
    ----------
    trajectory:
        N-body trajectory containing star and planet positions.
    star_name:
        Name of the host star.
    planet_name:
        Name of the candidate transiting planet.
    star_radius_m:
        Physical stellar radius.
    planet_radius_m:
        Physical planetary radius.

    Returns
    -------
    list[TransitEvent]
        Transit events in chronological order.
    """

    if star_radius_m <= 0:
        raise ValueError("star_radius_m must be positive")
    if planet_radius_m <= 0:
        raise ValueError("planet_radius_m must be positive")

    try:
        star_index = trajectory.body_names.index(star_name)
        planet_index = trajectory.body_names.index(planet_name)
    except ValueError as exc:
        raise ValueError(
            f"Unknown body name: {exc.args[0]}"
        ) from exc

    times = np.asarray(trajectory.timestamps_s, dtype=np.float64)

    if times.ndim != 1 or len(times) < 3:
        raise ValueError("Trajectory must contain at least three timestamps")

    star_positions = trajectory.positions[:, star_index, :]
    planet_positions = trajectory.positions[:, planet_index, :]

    relative = planet_positions - star_positions

    # Observer looks along +z; x-y is the sky plane.
    projected_separation = np.sqrt(
        relative[:, 0] ** 2 + relative[:, 1] ** 2
    )

    threshold = float(star_radius_m + planet_radius_m)
    inside = projected_separation <= threshold

    events: list[TransitEvent] = []

    start: int | None = None

    for i, is_inside in enumerate(inside):
        if is_inside and start is None:
            start = i

        leaving = start is not None and (not is_inside or i == len(inside) - 1)

        if not leaving:
            continue

        end = i if is_inside and i == len(inside) - 1 else i - 1

        if end >= start:
            segment = projected_separation[start:end + 1]
            local_index = int(np.argmin(segment))
            minimum_index = start + local_index

            center_time = _quadratic_minimum_time(
                times,
                projected_separation,
                minimum_index,
            )

            if start > 0:
                ingress_time = _interpolate_crossing_time(
                    times[start - 1],
                    times[start],
                    projected_separation[start - 1],
                    projected_separation[start],
                    threshold,
                )
            else:
                ingress_time = float(times[start])

            if end < len(times) - 1:
                egress_time = _interpolate_crossing_time(
                    times[end],
                    times[end + 1],
                    projected_separation[end],
                    projected_separation[end + 1],
                    threshold,
                )
            else:
                egress_time = float(times[end])

            events.append(
                TransitEvent(
                    body_name=planet_name,
                    center_time_s=center_time,
                    minimum_projected_separation_m=float(
                        projected_separation[minimum_index]
                    ),
                    ingress_time_s=ingress_time,
                    egress_time_s=egress_time,
                )
            )

        start = None

    return events