"""Core enumeration types used throughout the package."""

from enum import Enum


class ProvenanceOrigin(Enum):
    """Classification of a data product's origin.

    Every data product in the system must be labeled with one of these
    categories to prevent accidental mixing of ground truth, simulated
    data, real observations, and inferred quantities.

    Access control rule:
        Data products with origin HIDDEN_GROUND_TRUTH must never flow
        into player-facing observation or inference interfaces.
    """

    REAL = "real"
    """Data obtained directly from a real instrument (e.g., TESS)."""

    DERIVED_FROM_REAL = "derived_from_real"
    """Data derived from real observations (e.g., detrended light curve)."""

    SIMULATED = "simulated"
    """Data produced by the forward simulation model."""

    INFERRED = "inferred"
    """Quantities reconstructed by the inference/analysis pipeline."""

    HIDDEN_GROUND_TRUTH = "hidden_ground_truth"
    """The true physical state of the hidden system.

    This must NEVER be exposed through observation or inference interfaces.
    It exists solely for internal simulation and final reveal/comparison.
    """


class QualityFlag(Enum):
    """Quality flags for individual observation data points."""

    GOOD = 0
    """Data point passed all quality checks."""

    SUSPECT = 1
    """Data point may be unreliable."""

    BAD = 2
    """Data point is known to be bad (e.g., cosmic ray, saturation)."""

    GAP = 3
    """No data collected at this cadence (data gap)."""

    OUTLIER = 4
    """Data point flagged as a statistical outlier."""
