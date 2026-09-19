"""System state container for a gravitational system."""

from __future__ import annotations

from dataclasses import dataclass, field

from tess_hidden_architect.physics.bodies import Body, Star


@dataclass
class SystemState:
    """Complete dynamical state of a gravitational N-body system.

    All bodies — including stars — are stored in the ``bodies`` list
    and participate uniformly in mutual Newtonian gravity.  There is
    no separate ``star`` field; stars are identified by
    ``isinstance(body, Star)``.

    This design supports:
    - single star + planets,
    - multiple planets,
    - future multi-star / eclipsing-binary scenarios.

    Attributes:
        bodies: All dynamical bodies (stars and planets).
        epoch: Reference epoch time in SI seconds.
        metadata: Optional dictionary for scenario-level metadata.
    """

    bodies: list[Body] = field(default_factory=list)
    epoch: float = 0.0
    metadata: dict | None = None

    # -- convenience helpers --------------------------------------------------

    @property
    def stars(self) -> list[Star]:
        """Return all bodies that are stars."""
        return [b for b in self.bodies if isinstance(b, Star)]

    @property
    def num_bodies(self) -> int:
        """Total number of bodies in the system."""
        return len(self.bodies)

    def add_body(self, body: Body) -> None:
        """Append a body to the system."""
        self.bodies.append(body)
