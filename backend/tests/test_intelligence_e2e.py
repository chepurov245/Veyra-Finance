import asyncio

from app.services.data_sources.default_registry import (
    build_search_registry,
)
from app.services.intelligence.orchestrator import (
    IntelligenceOrchestrator,
)


async def main():
    registry = build_search_registry()

    provider = registry.get("openai_web")

    orchestrator = IntelligenceOrchestrator(
        search_provider=provider,
    )

    result = await orchestrator.run(
        "Какая сейчас инфляция в России?",
        has_workspace=False,
    )

    print("=== VEYRA INTELLIGENCE ===")
    print("TASK:", result.task.domain.value)
    print("PLAN STEPS:", len(result.plan.steps))
    print("EVIDENCE:", len(result.analysis.evidence))
    print("VERIFIED:", result.analysis.verified)
    print("CONFIDENCE:", result.analysis.confidence)

    print("\n=== EVIDENCE ===")

    for item in result.analysis.evidence:
        print(
            f"- {item.source_name}: "
            f"{item.source_reliability.name} "
            f"(confidence={item.confidence})"
        )
        print(f"  {item.claim[:500]}")

    print("\n=== WARNINGS ===")

    for warning in result.warnings:
        print("-", warning)


if __name__ == "__main__":
    asyncio.run(main())
