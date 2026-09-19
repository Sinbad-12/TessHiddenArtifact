from __future__ import annotations

from tess_hidden_architect.inference.ttv import (
    fit_constant_period_ephemeris,
)
from tess_hidden_architect.observation.transit_events import (
    extract_transit_events,
)
from tess_hidden_architect.physics.integrator import NBodyIntegrator
from tess_hidden_architect.scenarios.control_system import (
    make_control_system,
)
from tess_hidden_architect.scenarios.hidden_system import (
    make_hidden_system,
)


def _extract_events(system):
    system, trajectory = NBodyIntegrator(
        time_step_s=60.0
    ).integrate(
        system,
        duration_s=15 * 86400.0,
        record_interval_s=300.0,
    )

    star = next(
        body for body in system.bodies
        if body.name == "Host Star"
    )
    planet = next(
        body for body in system.bodies
        if body.name == "Planet A"
    )

    return extract_transit_events(
        trajectory,
        star_name="Host Star",
        planet_name="Planet A",
        star_radius_m=star.radius,
        planet_radius_m=planet.radius,
    )


def test_hidden_system_produces_measurable_ttv():
    events = _extract_events(make_hidden_system())

    result = fit_constant_period_ephemeris(events)

    assert len(events) >= 10
    assert result.rms_s > 20.0
    assert result.peak_to_peak_s > 60.0


def test_control_has_smaller_ttv_than_hidden_companion_system():
    hidden_events = _extract_events(make_hidden_system())
    control_events = _extract_events(make_control_system())

    hidden = fit_constant_period_ephemeris(hidden_events)
    control = fit_constant_period_ephemeris(control_events)

    assert hidden.rms_s > control.rms_s * 2.0
    assert hidden.peak_to_peak_s > control.peak_to_peak_s * 2.0


def test_ttv_result_has_one_residual_per_transit():
    events = _extract_events(make_hidden_system())

    result = fit_constant_period_ephemeris(events)

    assert len(result.observed_times_s) == len(events)
    assert len(result.calculated_times_s) == len(events)
    assert len(result.oc_residuals_s) == len(events)


def test_fitted_ephemeris_period_is_physically_reasonable():
    events = _extract_events(make_hidden_system())

    result = fit_constant_period_ephemeris(events)

    period_days = result.fitted_period_s / 86400.0

    assert 1.1 < period_days < 1.3


def test_ttv_analysis_is_deterministic():
    result_a = fit_constant_period_ephemeris(
        _extract_events(make_hidden_system())
    )
    result_b = fit_constant_period_ephemeris(
        _extract_events(make_hidden_system())
    )

    assert result_a.fitted_period_s == result_b.fitted_period_s
    assert result_a.rms_s == result_b.rms_s
    assert result_a.peak_to_peak_s == result_b.peak_to_peak_s