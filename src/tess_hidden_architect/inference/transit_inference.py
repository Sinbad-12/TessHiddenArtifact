"""Inference layer for transit period recovery, timing, and prediction.

This module provides deterministic, non-ML algorithms to:
1. Construct a baseline-aware period/frequency search grid.
2. Search and recover the dominant transit period from observed light curves.
3. Measure observed transit times and fit a linear ephemeris.
4. Predict the next unseen transit center.
5. Evaluate prediction timing error against separate withheld observations.

Ground-truth parameters, probabilities, and fabricated uncertainties are never
used or generated in this module.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

from tess_hidden_architect.observation.observation import Observation


@dataclass
class TransitInferenceResult:
    """Inferred transit parameters and future transit prediction.

    Attributes:
        inferred_period_s: Dominant recovered transit period in SI seconds.
        reference_epoch_s: Reference transit center time T0 in SI seconds.
        predicted_next_transit_s: Predicted center time of the next unseen transit in SI seconds.
        observed_transit_times_s: List of measured transit center times in the training data.
        period_grid_s: Candidate periods evaluated during search in SI seconds.
        scores: Objective transit dip scores corresponding to period_grid_s.
    """

    inferred_period_s: float
    reference_epoch_s: float
    predicted_next_transit_s: float
    observed_transit_times_s: list[float]
    period_grid_s: np.ndarray
    scores: np.ndarray


@dataclass
class PredictionEvaluation:
    """Evaluation of a predicted transit time against withheld observation data.

    Attributes:
        predicted_transit_s: The predicted transit center time in SI seconds.
        actual_transit_s: The measured actual transit center time in the withheld data in SI seconds.
        timing_error_s: Absolute difference |predicted - actual| in SI seconds.
    """

    predicted_transit_s: float
    actual_transit_s: float
    timing_error_s: float


def build_baseline_aware_period_grid(
    timestamps_s: np.ndarray,
    *,
    min_period_s: float | None = None,
    max_period_s: float | None = None,
    oversampling_factor: float = 5.0,
    min_transits_required: float = 1.8,
) -> np.ndarray:
    """Construct a baseline-aware period grid from observation timestamps.

    The frequency spacing is chosen such that the phase shift across the
    observation baseline T_base does not exceed 1 / oversampling_factor.

    Parameters
    ----------
    timestamps_s : np.ndarray
        Array of observation times in SI seconds.
    min_period_s : float or None, optional
        Minimum trial period in seconds. If None, derived from cadence.
    max_period_s : float or None, optional
        Maximum trial period in seconds. If None, derived from T_base / min_transits_required.
    oversampling_factor : float, optional
        Frequency oversampling factor relative to natural resolution 1 / T_base.
    min_transits_required : float, optional
        Minimum number of transits required within the baseline to bound max_period.

    Returns
    -------
    np.ndarray
        Sorted 1D array of candidate periods in SI seconds.
    """
    t = np.asarray(timestamps_s, dtype=np.float64)
    if len(t) < 2:
        raise ValueError("Need at least 2 timestamps to construct period grid")

    t_base = float(t[-1] - t[0])
    if t_base <= 0:
        raise ValueError("Observation baseline must be strictly positive")

    diffs = np.diff(t)
    median_cadence = float(np.median(diffs[diffs > 0])) if np.any(diffs > 0) else 120.0

    # Upper period bound: must observe multiple transits in the baseline
    p_max = float(max_period_s) if max_period_s is not None else t_base / min_transits_required
    if p_max <= 0:
        raise ValueError("max_period_s must be positive")

    # Lower period bound: cadence-aware limit
    p_min = float(min_period_s) if min_period_s is not None else max(3.0 * median_cadence, 0.05 * p_max)
    if p_min <= 0 or p_min >= p_max:
        raise ValueError(f"Invalid period bounds: min={p_min}, max={p_max}")

    f_min = 1.0 / p_max
    f_max = 1.0 / p_min

    # Natural frequency step: df = 1 / (oversampling_factor * T_base)
    df = 1.0 / (float(oversampling_factor) * t_base)
    n_freq = max(10, int(math.ceil((f_max - f_min) / df)) + 1)

    freqs = np.linspace(f_min, f_max, n_freq)
    # Return periods sorted in ascending order
    return 1.0 / freqs[::-1]


def search_transit_period(
    timestamps_s: np.ndarray,
    flux: np.ndarray,
    *,
    period_grid_s: np.ndarray | None = None,
    oversampling_factor: float = 5.0,
    n_bins: int = 100,
) -> tuple[np.ndarray, np.ndarray, float, float]:
    """Search for the dominant transit period using phase-folding dip scoring.

    Parameters
    ----------
    timestamps_s : np.ndarray
        Observation timestamps in SI seconds.
    flux : np.ndarray
        Observed normalized flux.
    period_grid_s : np.ndarray or None, optional
        Precomputed period grid. If None, built dynamically from timestamps.
    oversampling_factor : float, optional
        Grid oversampling factor if period_grid_s is None.
    n_bins : int, optional
        Number of phase bins for folded light curve evaluation.

    Returns
    -------
    periods : np.ndarray
        Evaluated period grid in SI seconds.
    scores : np.ndarray
        Objective transit dip depth scores for each period.
    best_period_s : float
        Period that maximizes the transit dip score.
    best_score : float
        Maximum transit dip score.
    """
    t = np.asarray(timestamps_s, dtype=np.float64)
    f = np.asarray(flux, dtype=np.float64)

    if period_grid_s is None:
        period_grid_s = build_baseline_aware_period_grid(
            t,
            oversampling_factor=oversampling_factor,
        )

    baseline_flux = float(np.median(f))
    t0 = t[0]
    n_periods = len(period_grid_s)
    scores = np.zeros(n_periods, dtype=np.float64)

    for i, p in enumerate(period_grid_s):
        phase = ((t - t0) / p) % 1.0
        bin_idx = np.clip((phase * n_bins).astype(np.int64), 0, n_bins - 1)
        counts = np.bincount(bin_idx, minlength=n_bins)
        valid = counts > 0
        if np.any(valid):
            sums = np.bincount(bin_idx, weights=f, minlength=n_bins)
            means = np.full(n_bins, baseline_flux)
            means[valid] = sums[valid] / counts[valid]
            scores[i] = max(0.0, baseline_flux - float(np.min(means)))

    best_idx = int(np.argmax(scores))
    best_p = float(period_grid_s[best_idx])
    best_score = float(scores[best_idx])

    # Refine around best candidate with a localized fine sub-grid
    p_low = period_grid_s[max(0, best_idx - 1)]
    p_high = period_grid_s[min(n_periods - 1, best_idx + 1)]
    if p_high > p_low:
        fine_grid = np.linspace(p_low, p_high, 50)
        fine_scores = np.zeros(len(fine_grid), dtype=np.float64)
        for j, pf in enumerate(fine_grid):
            phase = ((t - t0) / pf) % 1.0
            bin_idx = np.clip((phase * n_bins).astype(np.int64), 0, n_bins - 1)
            counts = np.bincount(bin_idx, minlength=n_bins)
            valid = counts > 0
            if np.any(valid):
                sums = np.bincount(bin_idx, weights=f, minlength=n_bins)
                means = np.full(n_bins, baseline_flux)
                means[valid] = sums[valid] / counts[valid]
                fine_scores[j] = max(0.0, baseline_flux - float(np.min(means)))
        fine_best_idx = int(np.argmax(fine_scores))
        if fine_scores[fine_best_idx] >= best_score:
            best_p = float(fine_grid[fine_best_idx])
            best_score = float(fine_scores[fine_best_idx])

    return period_grid_s, scores, best_p, best_score


def detect_transit_centroids(
    timestamps_s: np.ndarray,
    flux: np.ndarray,
    *,
    min_points_per_dip: int = 3,
    depth_fraction_threshold: float = 0.35,
) -> list[float]:
    """Detect distinct transit dip events and compute their flux-weighted centroid times.

    Parameters
    ----------
    timestamps_s : np.ndarray
        Observation timestamps in SI seconds.
    flux : np.ndarray
        Observed flux.
    min_points_per_dip : int, optional
        Minimum number of consecutive dip points to qualify as a valid transit event.
    depth_fraction_threshold : float, optional
        Fraction of maximum dip depth below median baseline to trigger detection.

    Returns
    -------
    list of float
        Measured transit center times in chronological order.
    """
    t = np.asarray(timestamps_s, dtype=np.float64)
    f = np.asarray(flux, dtype=np.float64)

    baseline = float(np.median(f))
    min_val = float(np.min(f))
    total_depth = baseline - min_val

    # No detectable transit dip
    if total_depth <= 0.0:
        return []

    threshold = baseline - depth_fraction_threshold * total_depth
    dip_indices = np.where(f < threshold)[0]

    if len(dip_indices) == 0:
        return []

    # Cluster contiguous dip points
    clusters: list[list[int]] = []
    cur_cluster = [dip_indices[0]]
    for idx in dip_indices[1:]:
        if idx == cur_cluster[-1] + 1:
            cur_cluster.append(idx)
        else:
            if len(cur_cluster) >= min_points_per_dip:
                clusters.append(cur_cluster)
            cur_cluster = [idx]
    if len(cur_cluster) >= min_points_per_dip:
        clusters.append(cur_cluster)

    centroids: list[float] = []
    for cluster in clusters:
        weights = baseline - f[cluster]
        if np.sum(weights) > 0:
            tc = float(np.average(t[cluster], weights=weights))
            centroids.append(tc)

    return centroids


def infer_transit_ephemeris_and_predict(
    timestamps_s: np.ndarray | None = None,
    flux: np.ndarray | None = None,
    *,
    observation: Observation | None = None,
    oversampling_factor: float = 5.0,
) -> TransitInferenceResult:
    """Infer orbital period and transit ephemeris, and predict the next unseen transit.

    Parameters
    ----------
    timestamps_s : np.ndarray or None, optional
        Observation timestamps in SI seconds (if observation is not supplied).
    flux : np.ndarray or None, optional
        Observed flux (if observation is not supplied).
    observation : Observation or None, optional
        Observation object. Only .timestamps_s and .flux are accessed.
    oversampling_factor : float, optional
        Frequency oversampling factor for period search grid.

    Returns
    -------
    TransitInferenceResult
        Inferred period, reference epoch, predicted next transit time,
        measured transit timings, period grid, and objective dip scores.
    """
    if observation is not None:
        t = np.asarray(observation.timestamps_s, dtype=np.float64)
        f = np.asarray(observation.flux, dtype=np.float64)
    else:
        if timestamps_s is None or flux is None:
            raise ValueError("Must provide either observation or both timestamps_s and flux")
        t = np.asarray(timestamps_s, dtype=np.float64)
        f = np.asarray(flux, dtype=np.float64)

    # 1. Run baseline-aware period search
    period_grid, scores, best_search_period, _ = search_transit_period(
        t,
        f,
        oversampling_factor=oversampling_factor,
    )

    # 2. Detect individual observed transits in the training light curve
    measured_transits = detect_transit_centroids(t, f)

    if len(measured_transits) >= 2:
        # Fit linear ephemeris T(k) = T0 + k * P
        # Determine transit indices relative to the first observed transit
        transit_diffs = np.array(measured_transits) - measured_transits[0]
        transit_indices = np.round(transit_diffs / best_search_period).astype(int)

        if len(set(transit_indices)) >= 2:
            poly = np.polyfit(transit_indices, measured_transits, deg=1)
            inferred_period = float(poly[0])
            reference_epoch = float(poly[1])
        else:
            inferred_period = float(measured_transits[1] - measured_transits[0])
            reference_epoch = float(measured_transits[0])

        last_transit = measured_transits[-1]
        predicted_next = last_transit + inferred_period

    elif len(measured_transits) == 1:
        inferred_period = best_search_period
        reference_epoch = measured_transits[0]
        predicted_next = reference_epoch + inferred_period
    else:
        raise ValueError("No distinct transit events detected in training light curve")

    return TransitInferenceResult(
        inferred_period_s=inferred_period,
        reference_epoch_s=reference_epoch,
        predicted_next_transit_s=predicted_next,
        observed_transit_times_s=measured_transits,
        period_grid_s=period_grid,
        scores=scores,
    )


def split_observation(
    observation: Observation,
    *,
    split_time_s: float | None = None,
    train_fraction: float = 0.7,
) -> tuple[Observation, Observation]:
    """Chronologically split an Observation into training and withheld portions.

    Parameters
    ----------
    observation : Observation
        Full observation to split.
    split_time_s : float or None, optional
        Timestamp dividing training from withheld data.
    train_fraction : float, optional
        Fraction of data in training portion if split_time_s is None.

    Returns
    -------
    train_observation : Observation
        Training portion.
    withheld_observation : Observation
        Withheld future portion.
    """
    n = len(observation.timestamps_s)
    if n < 2:
        raise ValueError("Observation is too short to split")

    if split_time_s is not None:
        train_mask = observation.timestamps_s <= float(split_time_s)
    else:
        split_idx = int(n * float(train_fraction))
        train_mask = np.zeros(n, dtype=bool)
        train_mask[:split_idx] = True

    test_mask = ~train_mask
    if not np.any(train_mask) or not np.any(test_mask):
        raise ValueError("Split produced an empty training or withheld dataset")

    train_obs = Observation(
        timestamps_s=observation.timestamps_s[train_mask],
        flux=observation.flux[train_mask],
        uncertainties=observation.uncertainties[train_mask],
        quality_flags=observation.quality_flags[train_mask],
        provenance=observation.provenance,
    )

    withheld_obs = Observation(
        timestamps_s=observation.timestamps_s[test_mask],
        flux=observation.flux[test_mask],
        uncertainties=observation.uncertainties[test_mask],
        quality_flags=observation.quality_flags[test_mask],
        provenance=observation.provenance,
    )

    return train_obs, withheld_obs


def evaluate_transit_prediction(
    predicted_transit_s: float,
    *,
    withheld_observation: Observation | None = None,
    withheld_timestamps_s: np.ndarray | None = None,
    withheld_flux: np.ndarray | None = None,
) -> PredictionEvaluation:
    """Evaluate prediction timing error against withheld future observations.

    Parameters
    ----------
    predicted_transit_s : float
        Predicted transit center time in SI seconds.
    withheld_observation : Observation or None, optional
        Withheld observation containing the unseen transit.
    withheld_timestamps_s : np.ndarray or None, optional
        Withheld timestamps if observation is not supplied.
    withheld_flux : np.ndarray or None, optional
        Withheld flux if observation is not supplied.

    Returns
    -------
    PredictionEvaluation
        Predicted time, measured actual time in withheld data, and absolute timing error.
    """
    if withheld_observation is not None:
        t = np.asarray(withheld_observation.timestamps_s, dtype=np.float64)
        f = np.asarray(withheld_observation.flux, dtype=np.float64)
    else:
        if withheld_timestamps_s is None or withheld_flux is None:
            raise ValueError("Must provide either withheld_observation or both timestamps and flux")
        t = np.asarray(withheld_timestamps_s, dtype=np.float64)
        f = np.asarray(withheld_flux, dtype=np.float64)

    # Detect transits present in the withheld dataset
    withheld_transits = detect_transit_centroids(t, f)
    if len(withheld_transits) == 0:
        raise ValueError("No transit events found in withheld observation")

    # Match the withheld transit closest to the predicted time
    actual_transit = min(withheld_transits, key=lambda tc: abs(tc - predicted_transit_s))
    timing_error = abs(predicted_transit_s - actual_transit)

    return PredictionEvaluation(
        predicted_transit_s=float(predicted_transit_s),
        actual_transit_s=float(actual_transit),
        timing_error_s=float(timing_error),
    )
