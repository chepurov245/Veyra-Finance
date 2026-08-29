from dataclasses import dataclass, field

from app.services.intelligence.evidence_pack import (
    CFOEvidencePack,
)


@dataclass
class CFOContext:
    internal_facts: list[dict] = field(
        default_factory=list
    )

    external_facts: list[dict] = field(
        default_factory=list
    )

    economic_facts: list[dict] = field(
        default_factory=list
    )

    derived_metrics: dict[str, float] = field(
        default_factory=dict
    )

    cfo_statuses: dict[str, str] = field(
        default_factory=dict
    )

    external_impacts: list[dict] = field(
        default_factory=list
    )

    cfo_decisions: list[dict] = field(
        default_factory=list
    )

    calculation_warnings: list[str] = field(
        default_factory=list
    )

    @classmethod
    def from_pack(
        cls,
        pack: CFOEvidencePack,
    ) -> "CFOContext":

        return cls(
            internal_facts=list(
                pack.internal_facts
            ),
            external_facts=list(
                pack.external_facts
            ),
            economic_facts=list(
                pack.economic_facts
            ),
            derived_metrics=dict(
                pack.derived_metrics
            ),
            cfo_statuses=dict(
                pack.cfo_statuses
            ),
            external_impacts=list(
                pack.external_impacts
            ),
            cfo_decisions=list(
                pack.cfo_decisions
            ),
            calculation_warnings=list(
                pack.calculation_warnings
            ),
        )

    def to_dict(self) -> dict:
        return {
            "internal_facts": self.internal_facts,
            "external_facts": self.external_facts,
            "economic_facts": self.economic_facts,
            "derived_metrics": self.derived_metrics,
            "cfo_statuses": self.cfo_statuses,
            "external_impacts": self.external_impacts,
            "cfo_decisions": self.cfo_decisions,
            "calculation_warnings": (
                self.calculation_warnings
            ),
        }
