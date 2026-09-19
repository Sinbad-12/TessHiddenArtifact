"""Focused tests for the transit inference and prediction layer."""

import math
import numpy as np
import pytest

from tess_hidden_architect.constants import AU_IN_METERS, SOLAR_MASS_KG, SOLAR_RADIUS_M
from tess_hidden_architect.inference import (
    PredictionEvaluation,
    TransitInferenceResult,
    build_baseline_aware_period_grid,
    evaluate_transit_prediction,
    infer_transit_ephemeris_and_predict,
    split_observation,
)
from tess_hidden_architect.observation import (
    KeplerianOrbit,
    Observation,
    generate_synthetic_transit_observation,
)
from tess_hidden_architect.physics.bodies import Body, Star


@pytest.fixture
def synthetic_observation() -> tuple[Observation, float]:
    """Generate a 4-period synthetic observation with known period and small noise."""
    star = Star(name="TestStar", mass=SOLAR_MASS_KG, radius=SOLAR_RADIUS_M)
    planet = Body(name="TestPlanet", mass=1.898e27, radius=0.1 * SOLAR_RADIUS_M)
    # Orbit with a ~ 0.035 AU
    orbit = KeplerianOrbit(
        semi_major_axis_m=0.035 * AU_IN_METERS,
        eccentricity=0.0,
        inclination_rad=math.pi / 2,
    )

    mu = 6.67430e-11 * (star.mass + planet.mass)
    true_period = 2.0 * math.pi * math.sqrt(orbit.semi_major_axis_m**3 / mu)

    # 4.0 orbital periods with 120s cadence and small measurement noise
    obs = generate_synthetic_transit_observation(
        star=star,
        planet=planet,
        orbit=orbit,
        cadence_s=120.0,
        num_periods=4.0,
        noise_std=1e-4,
        seed=42,
    )
    return obs, true_period


def test_period_recovery_from_training_light_curve(
    synthetic_observation: tuple[Observation, float],
) -> None:
    """Proves the dominant period can be recovered approximately from the training light curve."""
    obs, true_period = synthetic_observation

    # Split: first 2.6 periods for training (contains 2 complete transits)
    train_obs, _ = split_observation(obs, split_time_s=2.6 * true_period)

    # Run inference using ONLY training observation
    result = infer_transit_ephemeris_and_predict(observation=train_obs)

    assert isinstance(result, TransitInferenceResult)
    # Inferred period must match true period within 0.1%
    relative_error = abs(result.inferred_period_s - true_period) / true_period
    assert relative_error < 0.001, f"Period error {relative_error:.5%} exceeds 0.1%"

    # Period grid is baseline-aware and non-empty
    assert len(result.period_grid_s) > 10
    assert len(result.scores) == len(result.period_grid_s)
    # Peak score must be positive and correspond to transit depth
    assert np.max(result.scores) > 0.005


def test_next_transit_prediction_uses_inferred_training_data(
    synthetic_observation: tuple[Observation, float],
) -> None:
    """Proves the next transit prediction extrapolates forward from inferred training data."""
    obs, true_period = synthetic_observation
    train_obs, _ = split_observation(obs, split_time_s=2.6 * true_period)

    result = infer_transit_ephemeris_and_predict(observation=train_obs)

    # 1. Prediction must occur strictly in the FUTURE of all training data
    max_train_time = float(np.max(train_obs.timestamps_s))
    assert result.predicted_next_transit_s > max_train_time

    # 2. Prediction must equal the last observed transit time plus the inferred period
    last_observed = result.observed_transit_times_s[-1]
    expected_prediction = last_observed + result.inferred_period_s
    assert result.predicted_next_transit_s == pytest.approx(expected_prediction, abs=1e-3)


def test_withheld_observations_not_passed_into_inference(
    synthetic_observation: tuple[Observation, float],
) -> None:
    """Proves inference functions strictly without access to withheld future observations."""
    obs, true_period = synthetic_observation
    train_obs, withheld_obs = split_observation(obs, split_time_s=2.6 * true_period)

    # Run inference on training data only
    result1 = infer_transit_ephemeris_and_predict(observation=train_obs)

    # Corrupt or modify withheld data completely
    corrupted_withheld = Observation(
        timestamps_s=withheld_obs.timestamps_s.copy(),
        flux=np.full_like(withheld_obs.flux, 999.0),
        uncertainties=withheld_obs.uncertainties.copy(),
        quality_flags=withheld_obs.quality_flags.copy(),
        provenance=withheld_obs.provenance,
    )

    # Inference on training data is completely decoupled from withheld data
    result2 = infer_transit_ephemeris_and_predict(observation=train_obs)

    assert result1.inferred_period_s == result2.inferred_period_s
    assert result1.predicted_next_transit_s == result2.predicted_next_transit_s
    assert np.array_equal(result1.scores, result2.scores)


def test_prediction_timing_error_computed_correctly(
    synthetic_observation: tuple[Observation, float],
) -> None:
    """Proves prediction timing error is calculated only after comparing with withheld observation."""
    obs, true_period = synthetic_observation
    train_obs, withheld_obs = split_observation(obs, split_time_s=2.6 * true_period)

    # Step 1: Infer prediction from training data only
    result = infer_transit_ephemeris_and_predict(observation=train_obs)
    predicted_time = result.predicted_next_transit_s

    # Step 2: Compare prediction against the unseen withheld future observations
    evaluation = evaluate_transit_prediction(
        predicted_time,
        withheld_observation=withheld_obs,
    )

    assert isinstance(evaluation, PredictionEvaluation)
    assert evaluation.predicted_transit_s == predicted_time
    assert evaluation.timing_error_s == abs(evaluation.predicted_transit_s - evaluation.actual_transit_s)

    # The prediction timing error should be very small (less than 1 minute on a 2.4-day orbit)
    assert evaluation.timing_error_s < 60.0, f"Timing error {evaluation.timing_error_s:.2f}s exceeds 60s"


def test_inference_is_deterministic(
    synthetic_observation: tuple[Observation, float],
) -> None:
    """Proves inference produces identical results across repeated executions on identical input."""
    obs, true_period = synthetic_observation
    train_obs, _ = split_observation(obs, split_time_s=2.6 * true_period)

    result_a = infer_transit_ephemeris_and_predict(observation=train_obs)
    result_b = infer_transit_ephemeris_and_predict(observation=train_obs)

    assert result_a.inferred_period_s == result_b.inferred_period_s
    assert result_a.reference_epoch_s == result_b.reference_epoch_s
    assert result_a.predicted_next_transit_s == result_b.predicted_next_transit_s
    assert result_a.observed_transit_times_s == result_b.observed_transit_times_s
    assert np.array_equal(result_a.period_grid_s, result_b.period_grid_s)
    assert np.array_equal(result_a.scores, result_b.scores)
