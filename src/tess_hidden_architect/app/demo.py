"""Mission state manager for TESS Hidden Architect.

Coordinates:
OBSERVE -> INFER -> PREDICT -> REVEAL

The existing transit-prediction demo remains intact while the validated
N-body/TTV science layer is exposed as mission telemetry.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any

import numpy as np

from tess_hidden_architect.constants import (
    AU_IN_METERS,
    DAY_IN_SECONDS,
    SOLAR_MASS_KG,
    SOLAR_RADIUS_M,
)
from tess_hidden_architect.inference import (
    PredictionEvaluation,
    TransitInferenceResult,
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
from tess_hidden_architect.app.ttv_demo import build_ttv_science_result


class DemoSession:
    """Stateful coordinator for the reconstruction mission."""

    def __init__(
        self,
        seed: int = 42,
        noise_std: float = 1.5e-4,
        cadence_s: float = 120.0,
    ) -> None:
        self.seed = seed
        self.noise_std = noise_std
        self.cadence_s = cadence_s

        # ------------------------------------------------------------------
        # Existing deterministic transit-reconstruction demo
        # ------------------------------------------------------------------

        self._star = Star(
            name="Host Star (G-type)",
            mass=SOLAR_MASS_KG,
            radius=SOLAR_RADIUS_M,
        )

        self._planet_radius_m = 0.1 * SOLAR_RADIUS_M
        self._planet_mass_kg = 1.898e27

        self._planet = Body(
            name="Hidden Planet B",
            mass=self._planet_mass_kg,
            radius=self._planet_radius_m,
        )

        self._orbit = KeplerianOrbit(
            semi_major_axis_m=0.035 * AU_IN_METERS,
            eccentricity=0.0,
            inclination_rad=math.pi / 2,
        )

        mu = 6.67430e-11 * (
            self._star.mass + self._planet.mass
        )

        self._true_period_s = (
            2.0
            * math.pi
            * math.sqrt(
                self._orbit.semi_major_axis_m**3 / mu
            )
        )

        self._full_observation = (
            generate_synthetic_transit_observation(
                star=self._star,
                planet=self._planet,
                orbit=self._orbit,
                cadence_s=self.cadence_s,
                num_periods=4.0,
                noise_std=self.noise_std,
                seed=self.seed,
                scenario_name="deterministic_demo_mvp",
            )
        )

        self._split_time_s = (
            2.6 * self._true_period_s
        )

        (
            self._train_obs,
            self._withheld_obs,
        ) = split_observation(
            self._full_observation,
            split_time_s=self._split_time_s,
        )

        # ------------------------------------------------------------------
        # Validated N-body / TTV science layer
        # ------------------------------------------------------------------

        self._ttv_result = build_ttv_science_result()

        # ------------------------------------------------------------------
        # Mission lifecycle
        # ------------------------------------------------------------------

        self.inferred: bool = False
        self.revealed: bool = False

        self.inference_result: (
            TransitInferenceResult | None
        ) = None

        self.evaluation: (
            PredictionEvaluation | None
        ) = None

    def run_inference(self) -> dict[str, Any]:
        """Infer the next transit using observed data only."""

        self.inference_result = (
            infer_transit_ephemeris_and_predict(
                observation=self._train_obs,
                oversampling_factor=8.0,
            )
        )

        self.inferred = True

        return self.get_state()

    def reveal_withheld(self) -> dict[str, Any]:
        """Reveal withheld observation and scientific TTV evidence."""

        if (
            not self.inferred
            or self.inference_result is None
        ):
            raise RuntimeError(
                "Must run inference before revealing withheld data"
            )

        self.evaluation = evaluate_transit_prediction(
            self.inference_result.predicted_next_transit_s,
            withheld_observation=self._withheld_obs,
        )

        self.revealed = True

        return self.get_state()

    def reset(self) -> dict[str, Any]:
        """Reset mission state."""

        self.inferred = False
        self.revealed = False
        self.inference_result = None
        self.evaluation = None

        return self.get_state()

    def get_state(self) -> dict[str, Any]:
        """Return the public mission telemetry."""

        train_t_days = (
            self._train_obs.timestamps_s
            / DAY_IN_SECONDS
        ).tolist()

        train_f = self._train_obs.flux.tolist()

        ttv = self._ttv_result.ttv

        payload: dict[str, Any] = {
            "stage": (
                "REVEALED"
                if self.revealed
                else (
                    "INFERRED"
                    if self.inferred
                    else "OBSERVED"
                )
            ),
            "split_time_days": (
                self._split_time_s
                / DAY_IN_SECONDS
            ),
            "total_duration_days": float(
                self._full_observation.timestamps_s[-1]
                / DAY_IN_SECONDS
            ),
            "observed_data": {
                "time_days": train_t_days,
                "flux": train_f,
                "count": len(train_t_days),
            },
            "inferred": self.inferred,
            "revealed": self.revealed,
            "ttv": {
                "transit_count": len(
                    self._ttv_result.events
                ),
                "fitted_period_days": (
                    ttv.fitted_period_s
                    / DAY_IN_SECONDS
                ),
                "observed_transit_times_days": [
                    t / DAY_IN_SECONDS
                    for t in ttv.observed_times_s
                ],
                "oc_residuals_seconds": (
                    ttv.oc_residuals_s.tolist()
                ),
                "rms_seconds": ttv.rms_s,
                "peak_to_peak_seconds": (
                    ttv.peak_to_peak_s
                ),
                "control_rms_seconds": (
                    self._ttv_result.control_ttv_rms_s
                ),
                "control_peak_to_peak_seconds": (
                    self._ttv_result
                    .control_ttv_peak_to_peak_s
                ),
                "rms_amplification": (
                    self._ttv_result
                    .timing_amplification
                ),
                "peak_to_peak_amplification": (
                    self._ttv_result
                    .peak_to_peak_amplification
                ),
            },
        }

        if (
            self.inferred
            and self.inference_result is not None
        ):
            p_inf_s = (
                self.inference_result.inferred_period_s
            )

            pred_t_s = (
                self.inference_result
                .predicted_next_transit_s
            )

            payload["inference"] = {
                "inferred_period_days": (
                    p_inf_s / DAY_IN_SECONDS
                ),
                "inferred_period_hours": (
                    p_inf_s / 3600.0
                ),
                "inferred_period_seconds": p_inf_s,
                "predicted_next_transit_days": (
                    pred_t_s / DAY_IN_SECONDS
                ),
                "predicted_next_transit_hours": (
                    pred_t_s / 3600.0
                ),
                "predicted_next_transit_seconds": pred_t_s,
                "observed_transits_days": [
                    t / DAY_IN_SECONDS
                    for t in (
                        self.inference_result
                        .observed_transit_times_s
                    )
                ],
                "status": (
                    "Target locked - awaiting "
                    "withheld verification"
                    if not self.revealed
                    else "Verified against withheld data"
                ),
            }

        if (
            self.revealed
            and self.evaluation is not None
        ):
            withheld_t_days = (
                self._withheld_obs.timestamps_s
                / DAY_IN_SECONDS
            ).tolist()

            withheld_f = (
                self._withheld_obs.flux.tolist()
            )

            payload["withheld_data"] = {
                "time_days": withheld_t_days,
                "flux": withheld_f,
                "count": len(withheld_t_days),
            }

            payload["evaluation"] = {
                "predicted_transit_days": (
                    self.evaluation
                    .predicted_transit_s
                    / DAY_IN_SECONDS
                ),
                "actual_transit_days": (
                    self.evaluation
                    .actual_transit_s
                    / DAY_IN_SECONDS
                ),
                "timing_error_seconds": (
                    self.evaluation
                    .timing_error_s
                ),
                "timing_error_minutes": (
                    self.evaluation
                    .timing_error_s / 60.0
                ),
            }

            # Hidden truth is released only after REVEAL.
            payload["hidden_ground_truth"] = {
                "star_name": self._star.name,
                "star_radius_solar": (
                    self._star.radius
                    / SOLAR_RADIUS_M
                ),
                "planet_name": self._planet.name,
                "true_period_days": (
                    self._true_period_s
                    / DAY_IN_SECONDS
                ),
                "true_period_seconds": (
                    self._true_period_s
                ),
                "true_semi_major_axis_au": (
                    self._orbit.semi_major_axis_m
                    / AU_IN_METERS
                ),
                "true_radius_ratio": (
                    self._planet_radius_m
                    / self._star.radius
                ),
                "hidden_companion": {
                    "revealed": True,
                    "role": (
                        "gravitational companion "
                        "responsible for additional "
                        "transit-timing structure"
                    ),
                },
            }

        return payload