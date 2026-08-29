import json

from openai import AsyncOpenAI

from app.core.config import settings
from app.services.intelligence.analysis_engine import AnalysisResult
from app.services.intelligence.reasoning import ReasoningResult
from app.services.intelligence.task_types import AnalysisTask
from app.services.intelligence.cfo_context import CFOContext


class OpenAIReasoningProvider:

    def __init__(self) -> None:
        if not settings.openai_api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not configured."
            )

        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
        )

    async def generate(
        self,
        task: AnalysisTask,
        analysis: AnalysisResult,
        financial_context: dict | None = None,
        cfo_context: CFOContext | None = None,
    ) -> ReasoningResult:

        if not analysis.evidence and financial_context is None:
            return ReasoningResult(
                answer=(
                    "Сейчас у меня недостаточно "
                    "данных для полноценного ответа."
                ),
                confidence=0.0,
                verified=False,
                warnings=[
                    "No evidence available."
                ],
            )

        # -------------------------------------------------
        # External evidence
        # -------------------------------------------------

        evidence_blocks = []

        for item in analysis.evidence:
            period = item.metadata.get("period")

            published_at = (
                item.published_at.isoformat()
                if item.published_at
                else None
            )

            evidence_blocks.append(
                "\n".join(
                    [
                        f"SOURCE_TITLE: {item.metadata.get("title", "")}",
                        f"SOURCE_URL: {item.url}",
                        f"CONFIDENCE: {item.confidence}",
                        f"PUBLISHED_AT: {published_at}",
                        f"INDICATOR_PERIOD: {period}",
                        f"CLAIM: {item.claim}",
                    ]
                )
            )

        evidence_text = "\n\n".join(
            evidence_blocks
        )

        if not evidence_text:
            evidence_text = (
                "NO EXTERNAL EVIDENCE AVAILABLE"
            )

        # -------------------------------------------------
        # CFO STRUCTURED CONTEXT
        # -------------------------------------------------

        cfo_context_text = (
            "NO STRUCTURED CFO CONTEXT AVAILABLE"
        )

        if cfo_context is not None:
            cfo_context_text = json.dumps(
                cfo_context.to_dict(),
                ensure_ascii=False,
                default=str,
                indent=2,
            )

        # -------------------------------------------------
        # Legacy financial context
        # -------------------------------------------------

        financial_context_text = (
            "NO RAW INTERNAL FINANCIAL DATA AVAILABLE"
        )

        if financial_context is not None:
            financial_context_text = json.dumps(
                financial_context,
                ensure_ascii=False,
                default=str,
                indent=2,
            )

        # -------------------------------------------------
        # System prompt
        # -------------------------------------------------

        system_prompt = """
You are Veyra Finance Intelligence — an AI CFO.

Your task is to produce a fact-grounded CFO analysis
using ONLY information supplied by the backend.

==================================================
ABSOLUTE FACT BOUNDARY
==================================================

A fact or metric is AVAILABLE only when it explicitly
appears in the supplied backend context.

A metric mentioned in these instructions is NOT evidence.

If a metric is absent, it is UNKNOWN.

Never estimate, guess, interpolate, reverse-engineer,
or invent an unavailable metric.

For example, if payroll is absent:

CORRECT:
"В доступных данных нет показателя payroll."

INCORRECT:
"Payroll составляет 57% расходов."

Also incorrect:

- "Payroll вероятно составляет..."
- "Зарплаты могут занимать около..."
- "Можно предположить, что..."
- any unsupported percentage or monetary estimate.

This rule applies to every company metric.

==================================================
INTERNAL COMPANY DATA
==================================================

Internal financial data supplied by the backend is
authoritative for the company's own financial position.

Use only values actually present in:

- internal_facts;
- raw internal financial context;
- deterministic CFO metrics.

Never invent:

- revenue;
- expenses;
- net income;
- cash;
- cash flow;
- payroll;
- salaries;
- employees;
- debt;
- receivables;
- payables;
- taxes;
- EBITDA;
- margins;
- cost structure;
- revenue structure;
- any other missing metric.

Do not infer a missing metric from total expenses.

==================================================
DETERMINISTIC CFO METRICS
==================================================

The following are authoritative backend calculations:

- derived_metrics;
- cfo_statuses.

Do not independently recalculate them.

Do not replace their values.

Do not change their priority or severity.

You may explain their business significance.

==================================================
CFO DECISIONS
==================================================

cfo_decisions are deterministic backend-generated
decision-support outputs.

Treat these fields as authoritative:

- priority;
- category;
- severity;
- decision;
- reason;
- expected_impact;
- recommended_action.

Use them as the primary basis for CFO priorities.

Do not silently replace or contradict them.

==================================================
EXTERNAL IMPACTS
==================================================

external_impacts are structured outputs generated by
the backend External Impact Engine.

Treat them as analytical inputs.

Use their:

- metric;
- value;
- unit;
- period;
- direction;
- severity;
- impact_area;
- explanation;
- recommended_action.

Do not invent additional external impacts.

==================================================
ECONOMIC FACTS
==================================================

economic_facts represent structured external economic
information.

Preserve exactly:

- numerical value;
- unit;
- country;
- period;
- date;
- forecast status when available.

Do not describe an historical indicator as today's
value.

Do not describe a forecast as an observed fact.

Do not mix different periods.

==================================================
EXTERNAL EVIDENCE
==================================================

External search evidence may contain:

- macroeconomic information;
- market information;
- interest rates;
- inflation;
- currency conditions;
- regulation;
- industry developments;
- geopolitical developments.

Never invent external facts.

External search may be broad.

However, only use external information that is
materially relevant to the actual company.

==================================================
COMPANY RELEVANCE
==================================================

Interpret external information using the supplied
company context:

- country;
- base currency;
- industry;
- business model;
- website;
- risk profile.

For a German company using EUR, prioritize:

- Germany;
- euro area;
- European Union;
- directly relevant international markets.

Do not include Russian macroeconomic indicators
unless the supplied company context establishes
a direct business connection.

Do not include an external search result merely
because it exists.

==================================================
NUMERICAL INTEGRITY
==================================================

Every number in the final answer must be:

1. explicitly supplied by the backend; OR
2. a deterministic metric supplied by the backend; OR
3. directly supported by relevant external evidence; OR
4. a simple mathematical result explicitly requested
   by the user and based only on supplied values.

Never introduce an unsupported percentage.

Never introduce an unsupported monetary amount.

Never introduce an unsupported date.

Never introduce an unsupported employee count.

Never introduce an unsupported ratio.

==================================================
MISSING DATA
==================================================

If the user asks for unavailable information:

- explicitly say it is unavailable;
- do not estimate it;
- do not provide a range;
- do not provide an approximate percentage;
- do not infer it from unrelated metrics.

Example:

"В доступных данных нет расходов на payroll,
поэтому я не могу достоверно определить их сумму
или долю в общих расходах."

==================================================
COMBINED CFO ANALYSIS
==================================================

When both internal and external information exist,
produce one unified CFO analysis.

Answer:

1. What is happening financially inside the company?
2. Which external factors matter?
3. How do they affect the company?
4. What are the material risks?
5. What opportunities exist?
6. What should the CFO do next?

Prioritize materiality.

Do not simply list news.

Explain the business relevance of external factors.

==================================================
SOURCE VISIBILITY
==================================================

Do not expose:

- URLs;
- hyperlinks;
- source IDs;
- citation syntax;
- publisher counts;
- verification mechanics;
- technical backend details.

The backend retains source metadata separately.

==================================================
LANGUAGE AND STYLE
==================================================

Answer in the same language as the user's request.

For Russian:

- use natural professional Russian;
- use CFO terminology;
- be concise but substantive;
- clearly distinguish facts from analytical conclusions;
- explicitly identify unavailable information.

Never fabricate missing information.
"""

        user_prompt = f"""
USER QUESTION:

{task.domain.value}

==================================================
CFO STRUCTURED CONTEXT
==================================================

The following data is authoritative structured
decision-support data generated by the backend.

Do not invent or modify values.

------------------------------
VERIFIED INTERNAL FACTS
------------------------------

{json.dumps(
    cfo_context.internal_facts
    if cfo_context is not None
    else [],
    ensure_ascii=False,
    default=str,
    indent=2,
)}

------------------------------
VERIFIED EXTERNAL FACTS
------------------------------

{json.dumps(
    cfo_context.external_facts
    if cfo_context is not None
    else [],
    ensure_ascii=False,
    default=str,
    indent=2,
)}

------------------------------
ECONOMIC FACTS
------------------------------

{json.dumps(
    cfo_context.economic_facts
    if cfo_context is not None
    else [],
    ensure_ascii=False,
    default=str,
    indent=2,
)}

------------------------------
DERIVED CFO METRICS
------------------------------

{json.dumps(
    cfo_context.derived_metrics
    if cfo_context is not None
    else {},
    ensure_ascii=False,
    default=str,
    indent=2,
)}

------------------------------
CFO STATUSES
------------------------------

{json.dumps(
    cfo_context.cfo_statuses
    if cfo_context is not None
    else {},
    ensure_ascii=False,
    default=str,
    indent=2,
)}

------------------------------
EXTERNAL IMPACTS
------------------------------

{json.dumps(
    cfo_context.external_impacts
    if cfo_context is not None
    else [],
    ensure_ascii=False,
    default=str,
    indent=2,
)}

------------------------------
CFO DECISIONS
------------------------------

{json.dumps(
    cfo_context.cfo_decisions
    if cfo_context is not None
    else [],
    ensure_ascii=False,
    default=str,
    indent=2,
)}

------------------------------
CALCULATION WARNINGS
------------------------------

{json.dumps(
    cfo_context.calculation_warnings
    if cfo_context is not None
    else [],
    ensure_ascii=False,
    default=str,
    indent=2,
)}

==================================================
RAW INTERNAL FINANCIAL CONTEXT
==================================================

{financial_context_text}

==================================================
EXTERNAL EVIDENCE
==================================================

{evidence_text}

==================================================
FACT-GROUNDING CONTRACT
==================================================

The structured CFO context is authoritative.

1. Every numerical value in the answer must come
   from the supplied context or be mathematically
   valid based on supplied deterministic metrics.

2. Never invent a financial percentage.

3. Never invent payroll, salary, employee costs,
   customer metrics, debt, margins, cash flow,
   revenue breakdowns or any other company metric.

4. If a metric is absent, do not estimate it.

5. Never convert a qualitative statement into a
   precise numerical value.

6. Never create unsupported percentages.

7. Never create unsupported dates.

8. Never create unsupported economic indicators.

9. Never contradict CFO decisions.

10. Never independently recalculate deterministic
    CFO metrics.

11. Preserve the original indicator period.

12. Distinguish current data, historical data,
    forecasts and scenarios.

13. If requested information is unavailable,
    explicitly state that it is unavailable.

14. Recommendations may be analytical, but their
    factual premises must be supported by the
    supplied context.

==================================================
ORIGINAL USER REQUEST
==================================================

Generate a unified CFO analysis answering the
user's actual request.

Integrate:

1. Internal financial position.
2. Deterministic CFO metrics.
3. CFO statuses.
4. Relevant economic conditions.
5. External impacts.
6. CFO decisions.
7. Material risks.
8. Opportunities.
9. Prioritized actions.

Do not output URLs, citations, source IDs,
verification mechanics or technical backend details.

Answer in the same language as the user.
"""

        response = await self.client.responses.create(
            model="gpt-4.1-mini",
            input=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
        )

        answer = (
            response.output_text or ""
        ).strip()

        # -------------------------------------------------
        # Backend citations
        # -------------------------------------------------

        citations = [
            {
                "url": item.url,
                "title": item.metadata.get("title"),
            }
            for item in analysis.evidence
            if item.url
        ]

        # -------------------------------------------------
        # Verification boundary
        # -------------------------------------------------

        has_internal_data = (
            financial_context is not None
        )

        has_external_data = bool(
            analysis.evidence
        )

        external_verified = analysis.verified
        external_confidence = analysis.confidence

        if has_internal_data and has_external_data:

            # Internal company data is authoritative for
            # the company's own financial metrics.
            #
            # Overall verification still depends on the
            # external evidence when external information
            # is used in the answer.

            if external_verified:
                reasoning_verified = True
                reasoning_confidence = min(
                    0.98,
                    max(
                        0.90,
                        external_confidence,
                    ),
                )
                reasoning_warnings = list(
                    analysis.warnings
                )

            else:
                reasoning_verified = False
                reasoning_confidence = min(
                    0.85,
                    external_confidence,
                )

                reasoning_warnings = list(
                    analysis.warnings
                )

                reasoning_warnings.append(
                    "Internal financial data is available, "
                    "but external evidence is not sufficiently "
                    "verified for a fully verified combined analysis."
                )

        elif has_internal_data:

            # Internal-only CFO analysis.
            reasoning_verified = True
            reasoning_confidence = 0.95
            reasoning_warnings = []

        else:

            reasoning_verified = external_verified
            reasoning_confidence = external_confidence
            reasoning_warnings = list(
                analysis.warnings
            )

        return ReasoningResult(
            answer=answer,
            confidence=reasoning_confidence,
            verified=reasoning_verified,
            citations=citations,
            warnings=reasoning_warnings,
        )
