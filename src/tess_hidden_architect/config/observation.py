"""Observation configuration for simulated or real observation sequences."""

from dataclasses import dataclass


@dataclass
class ObservationConfig:
    """Configuration describing an observation sequence.

    All time values are in SI seconds.

    Attributes:
        cadence_s: Time between consecutive samples in seconds.
        exposure_time_s: Integration/exposure time per sample in seconds.
            Must not exceed cadence_s.
        duration_s: Total observation span in seconds.
        noise_parameters: Future noise model configuration. Deferred.
        gap_parameters: Future data-gap configuration. Deferred.
        outlier_parameters: Future outlier configuration. Deferred.
        seed: Deterministic seed for stochastic observation generation.

    Raises:
        ValueError: If any parameter is physically invalid.
    """

    cadence_s: float
    exposure_time_s: float
    duration_s: float
    noise_parameters: dict | None = None
    gap_parameters: dict | None = None
    outlier_parameters: dict | None = None
    seed: int | None = None

    def __post_init__(self) -> None:
        if self.cadence_s <= 0:
            raise ValueError(
                f"cadence_s must be positive, got {self.cadence_s}"
            )
        if self.exposure_time_s <= 0:
            raise ValueError(
                f"exposure_time_s must be positive, got {self.exposure_time_s}"
            )
        if self.duration_s <= 0:
            raise ValueError(
                f"duration_s must be positive, got {self.duration_s}"
            )
        if self.exposure_time_s > self.cadence_s:
            raise ValueError(
                f"exposure_time_s ({self.exposure_time_s}) must not exceed "
                f"cadence_s ({self.cadence_s})"
            )
