from dataclasses import dataclass, field


@dataclass
class CFOEvidencePack:
    internal_facts: list[dict] = field(
        default_factory=list
    )

    external_facts: list[dict] = field(
        default_factory=list
    )

    economic_facts: list[dict] = field(
        default_factory=list
    )

    all_facts: list[dict] = field(
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

    def rebuild(self) -> None:
        self.all_facts = (
            self.internal_facts
            + self.external_facts
            + self.economic_facts
        )

    @property
    def fact_count(self) -> int:
        return len(self.all_facts)

    @property
    def verified_count(self) -> int:
        return sum(
            1
            for fact in self.all_facts
            if fact.get("verified") is True
        )

    def by_metric(
        self,
        metric: str,
    ) -> list[dict]:

        return [
            fact
            for fact in self.all_facts
            if fact.get("metric") == metric
        ]

    def by_category(
        self,
        category: str,
    ) -> list[dict]:

        return [
            fact
            for fact in self.all_facts
            if fact.get("category") == category
        ]
