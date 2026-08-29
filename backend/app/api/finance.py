from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import get_current_workspace
from app.core.database import get_db
from app.models import Workspace
from app.models.finance import (
    FinancialAccount,
    FinancialTransaction,
)
from app.schemas.finance import (
    FinancialAccountCreate,
    FinancialAccountResponse,
    FinancialTransactionCreate,
    FinancialTransactionResponse,
)
from app.services.finance.analysis import (
    analyze_workspace_finances,
    compare_financial_periods,
    get_workspace_cash_balance,
)
from app.services.finance.insights import generate_cfo_insights
from app.services.finance.trends import analyze_financial_trends
from app.services.finance.forecast import generate_financial_forecast


router = APIRouter(
    prefix="/api/finance",
    tags=["finance"],
)


@router.post(
    "/accounts",
    response_model=FinancialAccountResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_account(
    payload: FinancialAccountCreate,
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db),
):
    account = FinancialAccount(
        workspace_id=workspace.id,
        name=payload.name,
        account_type=payload.account_type,
        currency=payload.currency.upper(),
        balance=payload.balance,
    )

    db.add(account)
    db.commit()
    db.refresh(account)

    return account


@router.get(
    "/accounts",
    response_model=list[FinancialAccountResponse],
)
def list_accounts(
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db),
):
    return list(
        db.scalars(
            select(FinancialAccount)
            .where(
                FinancialAccount.workspace_id == workspace.id
            )
            .order_by(FinancialAccount.id)
        )
    )


@router.post(
    "/transactions",
    response_model=FinancialTransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_transaction(
    payload: FinancialTransactionCreate,
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db),
):
    account = db.scalar(
        select(FinancialAccount)
        .where(
            FinancialAccount.id == payload.account_id,
            FinancialAccount.workspace_id == workspace.id,
        )
    )

    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Financial account not found.",
        )

    transaction = FinancialTransaction(
        workspace_id=workspace.id,
        account_id=account.id,
        transaction_type=payload.transaction_type,
        amount=payload.amount,
        currency=payload.currency.upper(),
        category=payload.category,
        description=payload.description,
        transaction_date=payload.transaction_date,
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    return transaction


@router.get(
    "/transactions",
    response_model=list[FinancialTransactionResponse],
)
def list_transactions(
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db),
):
    return list(
        db.scalars(
            select(FinancialTransaction)
            .where(
                FinancialTransaction.workspace_id == workspace.id
            )
            .order_by(
                FinancialTransaction.transaction_date.desc()
            )
        )
    )


@router.get(
    "/analysis",
)
def financial_analysis(
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db),
):
    analysis = analyze_workspace_finances(
        db=db,
        workspace_id=workspace.id,
        start_date=start_date,
        end_date=end_date,
    )

    analysis["cash_balance"] = get_workspace_cash_balance(
        db=db,
        workspace_id=workspace.id,
    )

    analysis["insights"] = generate_cfo_insights(
        analysis=analysis,
    )

    return analysis


@router.get(
    "/trends",
)
def financial_trends(
    periods: int = Query(default=6, ge=1, le=24),
    period_days: int = Query(default=30, ge=1, le=366),
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db),
):
    return analyze_financial_trends(
        db=db,
        workspace_id=workspace.id,
        periods=periods,
        period_days=period_days,
    )



@router.get(
    "/forecast",
)
def financial_forecast(
    periods: int = Query(default=3, ge=1, le=12),
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db),
):
    analysis = analyze_workspace_finances(
        db=db,
        workspace_id=workspace.id,
    )

    analysis["cash_balance"] = get_workspace_cash_balance(
        db=db,
        workspace_id=workspace.id,
    )

    return generate_financial_forecast(
        analysis=analysis,
        periods=periods,
    )



@router.get(
    "/dashboard",
)
def financial_dashboard(
    forecast_periods: int = Query(default=3, ge=1, le=12),
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db),
):
    analysis = analyze_workspace_finances(
        db=db,
        workspace_id=workspace.id,
    )

    analysis["cash_balance"] = get_workspace_cash_balance(
        db=db,
        workspace_id=workspace.id,
    )

    insights = generate_cfo_insights(
        analysis=analysis,
    )

    from app.services.finance.context import build_financial_context

    context = build_financial_context(
        db=db,
        workspace=workspace,
    )

    forecast = generate_financial_forecast(
        analysis=context["financials"],
        periods=forecast_periods,
    )

    accounts = list(
        db.scalars(
            select(FinancialAccount)
            .where(
                FinancialAccount.workspace_id == workspace.id,
                FinancialAccount.status == "active",
            )
            .order_by(FinancialAccount.id)
        )
    )

    return {
        "workspace": {
            "id": workspace.id,
            "name": workspace.name,
            "type": workspace.type,
            "base_currency": workspace.base_currency,
            "country": workspace.country,
        },
        "current_financials": analysis,
        "insights": insights,
        "cfo_decision": context["cfo_decision"],
        "forecast": forecast,
        "accounts": [
            {
                "id": account.id,
                "name": account.name,
                "account_type": account.account_type,
                "currency": account.currency,
                "balance": account.balance,
                "status": account.status,
            }
            for account in accounts
        ],
    }



@router.get(
    "/comparison",
)
def financial_comparison(
    current_start: datetime = Query(...),
    current_end: datetime = Query(...),
    previous_start: datetime = Query(...),
    previous_end: datetime = Query(...),
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db),
):
    current = analyze_workspace_finances(
        db=db,
        workspace_id=workspace.id,
        start_date=current_start,
        end_date=current_end,
    )

    previous = analyze_workspace_finances(
        db=db,
        workspace_id=workspace.id,
        start_date=previous_start,
        end_date=previous_end,
    )

    comparison = compare_financial_periods(
        current=current,
        previous=previous,
    )

    return {
        "current_period": {
            "start": current_start,
            "end": current_end,
            "revenue": current["revenue"],
            "expenses": current["expenses"],
            "net_income": current["net_income"],
            "net_margin": current["net_margin"],
        },
        "previous_period": {
            "start": previous_start,
            "end": previous_end,
            "revenue": previous["revenue"],
            "expenses": previous["expenses"],
            "net_income": previous["net_income"],
            "net_margin": previous["net_margin"],
        },
        "changes": comparison,
    }
