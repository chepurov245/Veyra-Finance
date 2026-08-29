import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.auth import get_current_workspace
from app.core.database import get_db
from app.models import Workspace

from app.schemas.intelligence import (
    IntelligenceCitation,
    IntelligenceFact,
    IntelligenceRequest,
    IntelligenceResponse,
)
from app.services.data_sources.default_registry import (
    build_search_registry,
)
from app.services.intelligence.orchestrator import (
    IntelligenceOrchestrator,
)

router = APIRouter(
    prefix="/api/intelligence",
    tags=["intelligence"],
)


def build_orchestrator() -> IntelligenceOrchestrator:
    registry = build_search_registry()

    return IntelligenceOrchestrator(
        search_provider=registry.get("openai_web")
    )


@router.post(
    "/query",
    response_model=IntelligenceResponse,
)
async def query_intelligence(
    request: IntelligenceRequest,
    db: Session = Depends(get_db),
    workspace: Workspace = Depends(get_current_workspace),
) -> IntelligenceResponse:

    try:
        orchestrator = build_orchestrator()

        financial_context = None

        if request.has_workspace:
            from app.services.finance.context import build_financial_context

            financial_context = build_financial_context(
                db=db,
                workspace=workspace,
            )

        result = await orchestrator.run(
            message=request.query,
            has_workspace=request.has_workspace,
            financial_context=financial_context,
        )

        citations = []

        if result.reasoning:
            for citation in result.reasoning.citations:
                if isinstance(citation, dict):
                    url = citation.get("url")
                else:
                    url = citation

                if url:
                    citations.append(
                        IntelligenceCitation(
                            url=url,
                        )
                    )

        facts = [
            IntelligenceFact(**fact)
            for fact in result.facts
        ]

        response_verified = (
            result.reasoning.verified
            if financial_context is not None
            else result.analysis.verified
        )

        response_confidence = (
            result.reasoning.confidence
            if financial_context is not None
            else result.analysis.confidence
        )

        response_warnings = (
            result.reasoning.warnings
            if financial_context is not None
            else result.warnings
        )

        return IntelligenceResponse(
            answer=result.answer,
            verified=response_verified,
            confidence=response_confidence,
            citations=citations,
            warnings=response_warnings,
            facts=facts,
        )

    except Exception as exc:
        import traceback

        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=f"Intelligence request failed: {type(exc).__name__}: {exc}",
        ) from exc


@router.post(
    "/query/stream",
    response_class=StreamingResponse,
)
async def stream_intelligence(
    request: IntelligenceRequest,
    db: Session = Depends(get_db),
    workspace: Workspace = Depends(get_current_workspace),
):
    queue: asyncio.Queue[dict | None] = (
        asyncio.Queue()
    )

    async def on_event(event: dict) -> None:
        await queue.put(event)

    async def run_orchestrator():
        try:
            orchestrator = build_orchestrator()

            financial_context = None

            if request.has_workspace:
                from app.services.finance.context import build_financial_context

                financial_context = build_financial_context(
                    db=db,
                    workspace=workspace,
                )

            result = await orchestrator.run(
                message=request.query,
                has_workspace=request.has_workspace,
                financial_context=financial_context,
                on_event=on_event,
            )

            await queue.put(
                {
                    "type": "answer",
                    "status": "complete",
                    "content": result.answer,
                    "verified": (
                        result.reasoning.verified
                        if financial_context is not None
                        else result.analysis.verified
                    ),
                    "confidence": (
                        result.reasoning.confidence
                        if financial_context is not None
                        else result.analysis.confidence
                    ),
                    "sources": len(
                        result.analysis.evidence
                    ),
                    "citations": [
                        {
                            "url": url,
                            "title": None,
                        }
                        for url in (
                            result.reasoning.citations
                            if result.reasoning
                            else []
                        )
                    ],
                    "facts": result.facts,
                    "warnings": result.warnings,
                }
            )

        except Exception as exc:
            await queue.put(
                {
                    "type": "error",
                    "status": "error",
                    "message": (
                        "Не удалось получить "
                        "ответ от Veyra."
                    ),
                    "detail": str(exc),
                }
            )

        finally:
            await queue.put(None)

    async def generate():
        task = asyncio.create_task(
            run_orchestrator()
        )

        try:
            while True:
                event = await queue.get()

                if event is None:
                    break

                yield (
                    f"data: "
                    f"{json.dumps(event, ensure_ascii=False)}"
                    "\n\n"
                )

        finally:
            if not task.done():
                task.cancel()

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
