import re
from dataclasses import dataclass
from enum import Enum


class FactStatus(str, Enum):
    SUPPORTED = "supported"
    CONFLICTING = "conflicting"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass(frozen=True)
class NumericFact:
    value: float
    unit: str | None = None


@dataclass
class FactComparisonResult:
    status: FactStatus
    facts: list[NumericFact]
    normalized_values: list[float]
    difference: float | None = None
    relative_difference: float | None = None


class FactComparisonEngine:

    NUMBER_PATTERN = re.compile(
        r"(?P<number>\d+(?:[.,]\d+)?)"
        r"\s*"
        r"(?P<unit>%|руб\.?|rub|usd|\$|eur|€)?",
        re.IGNORECASE,
    )

    def extract(self, text: str) -> list[NumericFact]:
        facts: list[NumericFact] = []

        for match in self.NUMBER_PATTERN.finditer(text):
            raw_number = match.group("number")
            unit = match.group("unit")

            try:
                value = float(
                    raw_number.replace(",", ".")
                )
            except ValueError:
                continue

            normalized_unit = (
                unit.lower()
                if unit
                else None
            )

            facts.append(
                NumericFact(
                    value=value,
                    unit=normalized_unit,
                )
            )

        return facts

    def compare(
        self,
        facts: list[NumericFact],
        tolerance: float = 0.01,
    ) -> FactComparisonResult:

        if len(facts) < 2:
            return FactComparisonResult(
                status=FactStatus.INSUFFICIENT_DATA,
                facts=facts,
                normalized_values=[
                    fact.value for fact in facts
                ],
            )

        first = facts[0]

        comparable = [
            fact
            for fact in facts[1:]
            if fact.unit == first.unit
        ]

        if not comparable:
            return FactComparisonResult(
                status=FactStatus.INSUFFICIENT_DATA,
                facts=facts,
                normalized_values=[
                    fact.value for fact in facts
                ],
            )

        values = [
            first.value,
            *[
                fact.value
                for fact in comparable
            ],
        ]

        minimum = min(values)
        maximum = max(values)

        difference = maximum - minimum

        if minimum == 0:
            relative_difference = None
        else:
            relative_difference = (
                difference / abs(minimum)
            )

        if difference <= tolerance:
            status = FactStatus.SUPPORTED
        else:
            status = FactStatus.CONFLICTING

        return FactComparisonResult(
            status=status,
            facts=facts,
            normalized_values=values,
            difference=difference,
            relative_difference=relative_difference,
        )
