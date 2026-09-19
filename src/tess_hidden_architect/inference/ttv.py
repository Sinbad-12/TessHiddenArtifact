"""Transit-timing variation analysis.

This module derives O-C timing residuals from observed transit centers.
It does not use hidden orbital periods or hidden transit labels.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from tess_hidden_architect.observation.transit_events import TransitEvent


@dataclass(frozen=True)
class TTVResult:
    """Result of fitting a constant-period transit ephemeris."""

    reference_time_s: float
    fitted_period_s: float
    transit_numbers: np.ndarray
    observed_times_s: np.ndarray
    calculated_times_s: np.ndarray
    oc_residuals_s: np.ndarray

    @property
    def rms_s(self) -> float:
        """Root-mean-square O-C timing residual."""

        return float(np.sqrt(np.mean(self.oc_residuals_s**2)))

    @property
    def peak_to_peak_s(self) -> float:
        """Peak-to-peak range of O-C timing residuals."""

        return float(
            np.max(self.oc_residuals_s)
            - np.min(self.oc_residuals_s)
        )


def fit_constant_period_ephemeris(
    events: list[TransitEvent],
) -> TTVResult:
    """Fit a linear transit ephemeris to detected transit centers.

    The transit number is assigned chronologically starting at zero.
    The fitted ephemeris is:

        t_calculated = t_reference + n * period

    where both reference time and period are fitted from the observed
    transit centers.

    Parameters
    ----------
    events:
        Chronologically ordered transit events.

    Returns
    -------
    TTVResult
        Fitted ephemeris and O-C residuals.

    Raises
    ------
    ValueError
        If fewer than three transit events are supplied.
    """

    if len(events) < 3:
        raise ValueError(
            "At least three transit events are required for TTV analysis"
        )

    observed_times_s = np.asarray(
        [event.center_time_s for event in events],
        dtype=np.float64,
    )

    if not np.all(np.isfinite(observed_times_s)):
        raise ValueError("Transit center times must be finite")

    transit_numbers = np.arange(
        len(observed_times_s),
        dtype=np.float64,
    )

    design_matrix = np.column_stack(
        (
            np.ones(len(transit_numbers)),
            transit_numbers,
        )
    )

    coefficients, *_ = np.linalg.lstsq(
        design_matrix,
        observed_times_s,
        rcond=None,
    )

    reference_time_s = float(coefficients[0])
    fitted_period_s = float(coefficients[1])

    if fitted_period_s <= 0.0:
        raise ValueError("Fitted period must be positive")

    calculated_times_s = (
        reference_time_s
        + transit_numbers * fitted_period_s
    )

    oc_residuals_s = (
        observed_times_s
        - calculated_times_s
    )

    return TTVResult(
        reference_time_s=reference_time_s,
        fitted_period_s=fitted_period_s,
        transit_numbers=transit_numbers,
        observed_times_s=observed_times_s,
        calculated_times_s=calculated_times_s,
        oc_residuals_s=oc_residuals_s,
    )