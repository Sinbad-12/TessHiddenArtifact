from __future__ import annotations

import numpy as np

from tess_hidden_architect.observation.transit_events import (
    extract_transit_events,
)
from tess_hidden_architect.physics.integrator import NBodyIntegrator
from tess_hidden_architect.scenarios.hidden_system import make_hidden_system


def _generate_hidden_trajectory():
    system = make_hidden_system()
    system, trajectory = NBodyIntegrator(
        time_step_s=60.0
    ).integrate(
        system,
        duration_s=15 * 86400.0,
        record_interval_s=300.0,
    )
    return system, trajectory


def _extract_planet_a_events(system, trajectory):
    star = next(body for body in system.bodies if body.name == "Host Star")
    planet = next(body for body in system.bodies if body.name == "Planet A")

    return extract_transit_events(
        trajectory,
        star_name="Host Star",
        planet_name="Planet A",
        star_radius_m=star.radius,
        planet_radius_m=planet.radius,
    )


def test_hidden_system_has_repeated_planet_a_transits():
    system, trajectory = _generate_hidden_trajectory()

    events = _extract_planet_a_events(system, trajectory)

    assert len(events) >= 10


def test_transit_events_are_chronological():
    system, trajectory = _generate_hidden_trajectory()

    events = _extract_planet_a_events(system, trajectory)

    centers = [event.center_time_s for event in events]

    assert centers == sorted(centers)
    assert all(
        later > earlier
        for earlier, later in zip(centers, centers[1:])
    )


def test_transit_events_have_valid_geometry_and_duration():
    system, trajectory = _generate_hidden_trajectory()

    star = next(body for body in system.bodies if body.name == "Host Star")

    events = _extract_planet_a_events(system, trajectory)

    for event in events:
        assert event.minimum_projected_separation_m < star.radius
        assert event.ingress_time_s < event.center_time_s
        assert event.center_time_s < event.egress_time_s

        duration_s = event.egress_time_s - event.ingress_time_s

        assert 60.0 * 60.0 < duration_s < 4.0 * 60.0 * 60.0


def test_planet_b_is_not_detected_as_a_transiting_body():
    system, trajectory = _generate_hidden_trajectory()

    star = next(body for body in system.bodies if body.name == "Host Star")
    planet_b = next(body for body in system.bodies if body.name == "Planet B")

    events = extract_transit_events(
        trajectory,
        star_name="Host Star",
        planet_name="Planet B",
        star_radius_m=star.radius,
        planet_radius_m=planet_b.radius,
    )

    assert events == []


def test_transit_event_extraction_is_deterministic():
    system_a, trajectory_a = _generate_hidden_trajectory()
    system_b, trajectory_b = _generate_hidden_trajectory()

    events_a = _extract_planet_a_events(system_a, trajectory_a)
    events_b = _extract_planet_a_events(system_b, trajectory_b)

    assert events_a == events_b


def test_transit_centers_are_separated_by_about_one_planet_a_period():
    system, trajectory = _generate_hidden_trajectory()

    events = _extract_planet_a_events(system, trajectory)

    centers_days = np.array(
        [event.center_time_s / 86400.0 for event in events]
    )

    periods_days = np.diff(centers_days)

    # Planet A's nominal period is about 1.195 days.
    # The N-body perturbation should produce small deviations,
    # rather than destroying the repeated-transit structure.
    assert np.all(periods_days > 1.0)
    assert np.all(periods_days < 1.4)
