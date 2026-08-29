from dataclasses import dataclass, field

from app.services.intelligence.calculations import (
    CalculationEngine,
    CalculationResult,
)
from app.services.intelligence.evidence import Evidence
from app.services.intelligence.verification import (
    EvidenceVerifier,
    VerificationResult,
)
from app.services.intelligence.evidence_dedup import (
    EvidenceDeduplicator,
)
from app.services.intelligence.task_types import TaskDomain


@dataclass
class AnalysisResult:
    verified: bool
    confidence: float
    evidence: list[Evidence] = field(default_factory=list)
    calculations: list[CalculationResult] = field(
        default_factory=list
    )
    warnings: list[str] = field(default_factory=list)


class AnalysisEngine:

    def __init__(self) -> None:
        self.verifier = EvidenceVerifier()
        self.calculator = CalculationEngine()

    def analyze(
        self,
        evidence: list[Evidence],
        calculations: list[CalculationResult] | None = None,
        domain: TaskDomain | None = None,
    ) -> AnalysisResult:

        verification = self.verifier.verify(
            evidence,
            domain=domain,
        )

        return self._build_result(
            verification=verification,
            calculations=calculations or [],
        )

    @staticmethod
    def build_facts(
        analysis: AnalysisResult,
    ) -> list[dict]:

        facts: list[dict] = []

        for item in analysis.evidence:

            if not item.claim.strip():
                continue

            metadata = item.metadata or {}

            category = "external"

            if metadata.get("economic_data"):
                category = "economic"

            # A fact is considered verified only when the
            # analysis verification layer confirms the
            # evidence set. Source confidence remains
            # separate and reflects source quality.
            fact_verified = (
                analysis.verified
                and item.confidence >= 0.80
            )

            facts.append(
                {
                    "category": category,
                    "claim": item.claim,
                    "value": metadata.get("value"),
                    "unit": metadata.get("unit"),
                    "country": metadata.get("country"),
                    "period": metadata.get("period"),
                    "source": item.source_name,
                    "source_type": item.source_type,
                    "verified": fact_verified,
                    "confidence": item.confidence,
                    "url": item.url,
                }
            )

        return facts

    @staticmethod
    def build_internal_facts(
        financial_context: dict | None,
    ) -> list[dict]:

        if not financial_context:
            return []

        facts: list[dict] = []

        financials = (
            financial_context.get(
                "financials",
                {},
            )
        )

        baseline = (
            financial_context.get(
                "financial_baseline",
                {},
            )
            or {}
        )

        workspace = (
            financial_context.get(
                "workspace",
                {},
            )
        )

        currency = (
            workspace.get(
                "base_currency"
            )
            or "EUR"
        )

        metric_units = {
            "revenue": currency,
            "expenses": currency,
            "net_income": currency,
            "cash_inflow": currency,
            "cash_outflow": currency,
            "net_cash_flow": currency,
            "cash_balance": currency,
        }

        for metric, value in financials.items():

            if metric == "transaction_count":
                continue

            if value is None:
                continue

            unit = metric_units.get(metric)

            facts.append(
                {
                    "category": "internal",
                    "metric": metric,
                    "claim": (
                        f"{metric}: {value}"
                    ),
                    "value": float(value),
                    "unit": unit,
                    "period": None,
                    "country": workspace.get(
                        "country"
                    ),
                    "source": "workspace_financials",
                    "source_type": "internal",
                    "verified": True,
                    "confidence": 1.0,
                }
            )

        for metric, value in baseline.items():

            if value is None:
                continue

            if metric in {
                "data_source",
                "fiscal_year_start",
            }:
                continue

            if metric in financials:
                continue

            unit = currency

            if metric == "employee_count":
                unit = "employees"

            facts.append(
                {
                    "category": "internal",
                    "metric": metric,
                    "claim": (
                        f"{metric}: {value}"
                    ),
                    "value": float(value),
                    "unit": unit,
                    "period": None,
                    "country": workspace.get(
                        "country"
                    ),
                    "source": "financial_baseline",
                    "source_type": "internal",
                    "verified": True,
                    "confidence": 1.0,
                }
            )

        return facts

    @staticmethod
    def primary_facts(
        analysis: AnalysisResult,
    ) -> list[Evidence]:

        if not analysis.verified:
            return []

        groups = EvidenceDeduplicator.group(
            analysis.evidence
        )

        if not groups:
            return []

        best_group = max(
            groups,
            key=lambda group: max(
                item.confidence
                for item in group.evidence
            ),
        )

        return best_group.evidence

    @staticmethod
    def _build_result(
        verification: VerificationResult,
        calculations: list[CalculationResult],
    ) -> AnalysisResult:

        warnings = list(
            verification.warnings
        )

        if not verification.verified:
            warnings.append(
                "Analysis is not sufficiently verified."
            )

        return AnalysisResult(
            verified=verification.verified,
            confidence=verification.confidence,
            evidence=verification.evidence,
            calculations=calculations,
            warnings=warnings,
        )
