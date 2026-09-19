"""Data provenance and traceability.

Every data product in the system carries a :class:`ProvenanceRecord`
that classifies its origin and, where applicable, traces it back to
specific real or simulated sources.

Access control policy
---------------------
Data with ``origin == ProvenanceOrigin.HIDDEN_GROUND_TRUTH`` must
never be passed to player-facing observation or inference interfaces.
This invariant is enforced by convention in Phase 0 and will be
enforced at runtime in later phases.

Real TESS data traceability
---------------------------
When ``origin`` is ``REAL`` or ``DERIVED_FROM_REAL``, the optional
fields (``target_id``, ``sector``, ``cadence``, ``source_id``,
``archive``, ``product_id``, ``processing_version``) should be
populated to trace the data back to its MAST archive source.

No TESS data is downloaded in Phase 0.  These fields document the
future provenance schema.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tess_hidden_architect.types import ProvenanceOrigin


@dataclass
class ProvenanceRecord:
    """Extensible provenance metadata for any data product.

    Attributes:
        origin: Classification of the data's origin.
        target_id: TIC identifier (for real TESS data).
        sector: TESS sector number.
        cadence: Cadence label, e.g. ``"short"``, ``"fast"``, ``"long"``.
        source_id: Observation or source identifier.
        archive: Archive name, e.g. ``"MAST"``, ``"ExoFOP"``.
        product_id: Data product or file identifier.
        processing_version: Pipeline or processing version string.
        simulation_seed: Random seed (for simulated data).
        scenario_name: Scenario name (for simulated data).
        metadata: Arbitrary additional metadata.
    """

    origin: ProvenanceOrigin

    # -- Real TESS traceability -----------------------------------------------
    target_id: str | None = None
    sector: int | None = None
    cadence: str | None = None
    source_id: str | None = None
    archive: str | None = None
    product_id: str | None = None
    processing_version: str | None = None

    # -- Simulation traceability ----------------------------------------------
    simulation_seed: int | None = None
    scenario_name: str | None = None

    # -- Extensible -----------------------------------------------------------
    metadata: dict | None = None

    @property
    def is_hidden_ground_truth(self) -> bool:
        """Return True if this data must not be exposed to the player."""
        return self.origin is ProvenanceOrigin.HIDDEN_GROUND_TRUTH
