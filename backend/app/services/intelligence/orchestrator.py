from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from collections.abc import Awaitable, Callable

from app.services.data_sources.search import (
    SearchProvider,
    SearchRequest,
)
from app.services.data_sources.economic.default_registry import (
    build_economic_registry,
)
from app.services.data_sources.economic.provider import (
    EconomicDataRequest,
)
from app.services.intelligence.economic_evidence import (
    economic_data_to_evidence,
)
from app.services.intelligence.economic_research import (
    collect_economic_evidence,
)
from app.services.intelligence.analysis_engine import (
    AnalysisEngine,
    AnalysisResult,
)
from app.services.intelligence.evidence_extractor import (
    EvidenceExtractor,
)
from app.services.intelligence.research_plan import (
    ResearchPlan,
    ResearchPlanner,
)
from app.services.intelligence.task_router import (
    TaskRouter,
)
from app.services.intelligence.query_enricher import (
    QueryEnricher,
)
from app.services.intelligence.research_queries import (
    ResearchQueryBuilder,
)
from app.services.intelligence.reasoning import (
    ReasoningEngine,
    ReasoningResult,
)
from app.services.intelligence.llm_reasoning import (
    OpenAIReasoningProvider,
)
from app.services.intelligence.answer_composer import (
    AnswerComposer,
)
from app.services.intelligence.task_types import (
    AnalysisTask,
    TaskDomain,
)
from app.services.intelligence.cfo_context import (
    CFOContext,
)
from app.services.intelligence.evidence_pack import (
    CFOEvidencePack,
)
from app.services.intelligence.cfo_calculations import (
    CFOCalculationEngine,
)
from app.services.intelligence.external_impact import (
    ExternalImpactEngine,
)
from app.services.intelligence.cfo_decision import (
    CFODecisionEngine,
)


@dataclass
class IntelligenceResult:
    message: str
    task: AnalysisTask
    plan: ResearchPlan
    analysis: AnalysisResult
    reasoning: ReasoningResult | None = None
    answer: str = ""
    facts: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class IntelligenceOrchestrator:

    async def _emit(
        self,
        on_event: Callable[
            [dict],
            Awaitable[None],
        ] | None,
        event: dict,
    ) -> None:
        if on_event is not None:
            await on_event(event)

    def __init__(
        self,
        search_provider: SearchProvider,
    ) -> None:
        self.router = TaskRouter()
        self.planner = ResearchPlanner()
        self.extractor = EvidenceExtractor()
        self.analysis_engine = AnalysisEngine()
        self.search_provider = search_provider

        economic_registry = build_economic_registry()
        self.economic_provider = economic_registry.get(
            "openai_economic"
        )

        self.query_enricher = QueryEnricher()
        self.query_builder = ResearchQueryBuilder()
        self.reasoning_engine = ReasoningEngine()
        self.llm_reasoning = OpenAIReasoningProvider()
        self.answer_composer = AnswerComposer()
        self.cfo_calculator = CFOCalculationEngine()
        self.external_impact_engine = ExternalImpactEngine()
        self.cfo_decision_engine = CFODecisionEngine()

    async def _search_one(
        self,
        query: str,
    ):
        enriched_query = self.query_enricher.enrich(
            query
        )

        return await self.search_provider.search(
            SearchRequest(
                query=enriched_query,
                max_results=10,
            )
        )

    @staticmethod
    def _deduplicate_results(
        evidence,
    ):
        unique = []
        seen: set[str] = set()

        for item in evidence:
            key = (
                item.url.strip().lower()
                if item.url
                else item.claim.strip().lower()
            )

            if key in seen:
                continue

            seen.add(key)
            unique.append(item)

        return unique

    async def run(
        self,
        message: str,
        has_workspace: bool = False,
        financial_context: dict | None = None,
        on_event: Callable[
            [dict],
            Awaitable[None],
        ] | None = None,
    ) -> IntelligenceResult:

        # -------------------------------------------------
        # 1. TASK ROUTING
        # -------------------------------------------------

        task = self.router.route(
            message=message,
            has_workspace=has_workspace,
        )

        await self._emit(
            on_event,
            {
                "type": "research_started",
                "status": "active",
                "label": "Изучаю запрос",
            },
        )

        # -------------------------------------------------
        # 2. RESEARCH PLAN
        # -------------------------------------------------

        plan = self.planner.create_plan(
            domain=task.domain,
            message=message,
            has_workspace=has_workspace,
        )

        warnings: list[str] = []
        evidence = []

        # -------------------------------------------------
        # 3. MULTI-QUERY RESEARCH
        # -------------------------------------------------

        if plan.requires_web:

            queries = self.query_builder.build(
                message=message,
                domain=task.domain,
                has_workspace=has_workspace,
            )

            await self._emit(
                on_event,
                {
                    "type": "search_started",
                    "status": "active",
                    "label": (
                        f"Исследую {len(queries)} "
                        "направлений"
                    ),
                    "query_count": len(queries),
                },
            )

            if queries:

                responses = await asyncio.gather(
                    *(
                        self._search_one(query)
                        for query in queries
                    ),
                    return_exceptions=True,
                )

                for response in responses:

                    if isinstance(
                        response,
                        Exception,
                    ):
                        warnings.append(
                            f"Search error: {response}"
                        )
                        continue

                    if not response.success:
                        if response.error:
                            warnings.append(
                                response.error
                            )
                        continue

                    extracted = self.extractor.extract(
                        response,
                        domain=task.domain,
                    )

                    evidence.extend(extracted)

            # -------------------------------------------------
            # 3A. STRUCTURED ECONOMIC DATA
            # -------------------------------------------------

            if (
                task.domain
                in {
                    TaskDomain.MACROECONOMICS,
                    TaskDomain.COMPANY_FINANCE,
                    TaskDomain.FORECASTING,
                    TaskDomain.STOCKS,
                    TaskDomain.CRYPTO,
                    TaskDomain.GEOPOLITICS,
                }
                and financial_context
            ):
                country = (
                    financial_context
                    .get("workspace", {})
                    .get("country")
                )

                if country:
                    try:
                        economic_evidence = (
                            await collect_economic_evidence(
                                provider=self.economic_provider,
                                country=country,
                            )
                        )

                        evidence.extend(
                            economic_evidence
                        )

                    except Exception as exc:
                        warnings.append(
                            f"Economic data error: {exc}"
                        )

            evidence = self._deduplicate_results(
                evidence
            )

            # -------------------------------------------------
            # 3B. CFO EVIDENCE PACK
            # -------------------------------------------------

            external_facts = (
                self.analysis_engine.build_facts(
                    self.analysis_engine.analyze(
                        evidence=evidence,
                    )
                )
            )

            internal_facts = (
                self.analysis_engine.build_internal_facts(
                    financial_context
                )
            )

            economic_facts = [
                fact
                for fact in external_facts
                if fact.get("category") == "economic"
            ]

            external_facts = [
                fact
                for fact in external_facts
                if fact.get("category") != "economic"
            ]

            evidence_pack = CFOEvidencePack(
                internal_facts=internal_facts,
                external_facts=external_facts,
                economic_facts=economic_facts,
            )

            evidence_pack.rebuild()

            calculation_result = (
                self.cfo_calculator.calculate(
                    evidence_pack.internal_facts
                )
            )

            evidence_pack.derived_metrics = (
                calculation_result.metrics
            )

            evidence_pack.cfo_statuses = (
                calculation_result.statuses
            )

            evidence_pack.calculation_warnings = (
                calculation_result.warnings
            )

            external_impacts = (
                self.external_impact_engine.analyze(
                    economic_facts=(
                        evidence_pack.economic_facts
                    ),
                    derived_metrics=(
                        evidence_pack.derived_metrics
                    ),
                )
            )

            evidence_pack.external_impacts = [
                {
                    "metric": impact.metric,
                    "value": impact.value,
                    "unit": impact.unit,
                    "period": impact.period,
                    "direction": impact.direction,
                    "severity": impact.severity,
                    "impact_area": impact.impact_area,
                    "explanation": impact.explanation,
                    "recommended_action": (
                        impact.recommended_action
                    ),
                }
                for impact in external_impacts
            ]

            cfo_decisions = (
                self.cfo_decision_engine.analyze(
                    derived_metrics=(
                        evidence_pack.derived_metrics
                    ),
                    cfo_statuses=(
                        evidence_pack.cfo_statuses
                    ),
                    external_impacts=(
                        evidence_pack.external_impacts
                    ),
                )
            )

            evidence_pack.cfo_decisions = [
                {
                    "priority": decision.priority,
                    "category": decision.category,
                    "severity": decision.severity,
                    "decision": decision.decision,
                    "reason": decision.reason,
                    "expected_impact": (
                        decision.expected_impact
                    ),
                    "recommended_action": (
                        decision.recommended_action
                    ),
                }
                for decision in cfo_decisions
            ]

            await self._emit(
                on_event,
                {
                    "type": "sources_found",
                    "status": "complete",
                    "label": (
                        f"Найдено {len(evidence)} "
                        "уникальных источников"
                    ),
                    "count": len(evidence),
                },
            )

        # -------------------------------------------------
        # 4. VERIFICATION PASS
        # -------------------------------------------------

        await self._emit(
            on_event,
            {
                "type": "verification_started",
                "status": "active",
                "label": "Сверяю показатели",
            },
        )

        analysis = self.analysis_engine.analyze(
            evidence=evidence,
            domain=task.domain,
        )

        # -------------------------------------------------
        # 5. TARGETED VERIFICATION
        # -------------------------------------------------

        if (
            plan.requires_web
            and evidence
            and not analysis.verified
        ):

            verification_claim = max(
                evidence,
                key=lambda item: (
                    item.confidence
                ),
            )

            verification_query = (
                "Найди независимые официальные или "
                "высоконадежные источники, "
                "подтверждающие следующий факт.\n\n"
                "Требования:\n"
                "- тот же показатель;\n"
                "- тот же период;\n"
                "- не использовать прогнозы;\n"
                "- приоритет первичным источникам;\n"
                "- если факт невозможно подтвердить, "
                "не придумывай подтверждение.\n\n"
                f"ФАКТ:\n"
                f"{verification_claim.claim}"
            )

            verification_response = (
                await self.search_provider.search(
                    SearchRequest(
                        query=(
                            self.query_enricher.enrich(
                                verification_query
                            )
                        ),
                        max_results=6,
                    )
                )
            )

            if verification_response.success:

                verification_evidence = (
                    self.extractor.extract(
                        verification_response,
                        domain=task.domain,
                    )
                )

                evidence.extend(
                    verification_evidence
                )

                evidence = (
                    self._deduplicate_results(
                        evidence
                    )
                )

                analysis = (
                    self.analysis_engine.analyze(
                        evidence=evidence,
                        domain=task.domain,
                    )
                )

        # -------------------------------------------------
        # 6. REASONING
        # -------------------------------------------------

        await self._emit(
            on_event,
            {
                "type": "reasoning_started",
                "status": "active",
                "label": "Формирую ответ",
            },
        )

        reasoning = self.reasoning_engine.reason(
            task=task,
            analysis=analysis,
        )

        # -------------------------------------------------
        # 7. CFO CONTEXT
        # -------------------------------------------------

        cfo_context = None

        if (
            has_workspace
            and "evidence_pack" in locals()
        ):
            cfo_context = CFOContext.from_pack(
                evidence_pack
            )

        # -------------------------------------------------
        # 7A. LLM SYNTHESIS
        # -------------------------------------------------

        if (
            analysis.evidence
            or financial_context is not None
        ):
            reasoning = await self.llm_reasoning.generate(
                task=task,
                analysis=analysis,
                financial_context=financial_context,
                cfo_context=cfo_context,
            )

        # -------------------------------------------------
        # 8. ANSWER COMPOSITION
        # -------------------------------------------------

        answer = self.answer_composer.compose(
            reasoning
        )

        # -------------------------------------------------
        # 9. FACTS
        # -------------------------------------------------

        facts: list[dict] = []

        if (
            has_workspace
            and "evidence_pack" in locals()
        ):
            # CFO Evidence Pack is the authoritative
            # structured fact layer when workspace data exists.
            #
            # This prevents internal workspace facts from
            # being added a second time through analysis.evidence.

            for fact in evidence_pack.all_facts:

                if fact.get("verified") is not True:
                    continue

                facts.append(
                    {
                        "category": fact.get(
                            "category"
                        ),
                        "metric": fact.get(
                            "metric"
                        ),
                        "claim": fact.get(
                            "claim"
                        ),
                        "value": fact.get(
                            "value"
                        ),
                        "unit": fact.get(
                            "unit"
                        ),
                        "period": fact.get(
                            "period"
                        ),
                        "country": fact.get(
                            "country"
                        ),
                        "source": fact.get(
                            "source"
                        ),
                        "source_type": fact.get(
                            "source_type"
                        ),
                        "verified": True,
                        "confidence": fact.get(
                            "confidence"
                        ),
                        "url": fact.get(
                            "url"
                        ),
                    }
                )

        else:
            # Without workspace, external verified facts
            # remain the public structured fact layer.

            if analysis.verified:
                facts.extend(
                    self.analysis_engine.build_facts(
                        analysis
                    )
                )

        # -------------------------------------------------
        # FACT DEDUPLICATION
        # -------------------------------------------------

        unique_facts: list[dict] = []
        seen_fact_keys: set[tuple] = set()

        for fact in facts:

            key = (
                fact.get("category"),
                fact.get("metric"),
                fact.get("claim"),
                fact.get("period"),
            )

            if key in seen_fact_keys:
                continue

            seen_fact_keys.add(key)
            unique_facts.append(fact)

        facts = unique_facts

        # -------------------------------------------------
        # 11. RESULT STATE
        # -------------------------------------------------

        result_verified = (
            reasoning.verified
            if financial_context is not None
            else analysis.verified
        )

        result_confidence = (
            reasoning.confidence
            if financial_context is not None
            else analysis.confidence
        )

        await self._emit(
            on_event,
            {
                "type": "completed",
                "status": "complete",
                "label": "Исследование завершено",
                "verified": result_verified,
                "confidence": result_confidence,
                "sources": len(analysis.evidence),
            },
        )

        return IntelligenceResult(
            message=message,
            task=task,
            plan=plan,
            analysis=analysis,
            reasoning=reasoning,
            answer=answer,
            facts=facts,
            warnings=warnings,
        )
