"""Observation data model.

The :class:`Observation` dataclass holds a time-series observation with
provenance tracking.  This is the primary data product that flows from
the observation pipeline to the inference layer.

Phase 0 note:
    The forward observation pipeline (transit geometry, noise injection,
    etc.) is intentionally deferred.  This module defines the data model
    only.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from tess_hidden_architect.data.provenance import ProvenanceRecord
from tess_hidden_architect.types import ProvenanceOrigin


@dataclass
class Observation:
    """A time-series observation with provenance tracking.

    Attributes:
        timestamps_s: Observation times in SI seconds, shape ``(N,)``.
        flux: Measured flux values (relative or absolute), shape ``(N,)``.
        uncertainties: Flux uncertainty estimates, shape ``(N,)``.
        quality_flags: Integer quality flags per data point, shape ``(N,)``.
            See :class:`~tess_hidden_architect.types.QualityFlag`.
        provenance: Origin and traceability metadata.

    Raises:
        ValueError: If array shapes are inconsistent or provenance
            indicates hidden ground truth.
    """

    timestamps_s: np.ndarray
    flux: np.ndarray
    uncertainties: np.ndarray
    quality_flags: np.ndarray
    provenance: ProvenanceRecord

    def __post_init__(self) -> None:
        n = len(self.timestamps_s)
        if self.flux.shape != (n,):
            raise ValueError(
                f"flux shape {self.flux.shape} does not match "
                f"timestamps length {n}"
            )
        if self.uncertainties.shape != (n,):
            raise ValueError(
                f"uncertainties shape {self.uncertainties.shape} does not "
                f"match timestamps length {n}"
            )
        if self.quality_flags.shape != (n,):
            raise ValueError(
                f"quality_flags shape {self.quality_flags.shape} does not "
                f"match timestamps length {n}"
            )
        if self.provenance.origin is ProvenanceOrigin.HIDDEN_GROUND_TRUTH:
            raise ValueError(
                "Observation must not carry HIDDEN_GROUND_TRUTH provenance. "
                "Ground truth must never flow into the observation layer."
            )
