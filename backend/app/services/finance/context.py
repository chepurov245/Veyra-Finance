from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Workspace
from app.models.company_financial_profile import (
    CompanyFinancialProfile,
)
from app.services.finance.analysis import (
    analyze_workspace_finances,
    get_workspace_cash_balance,
)
from app.services.finance.insights import generate_cfo_insights
from app.services.finance.cfo_engine import generate_cfo_decision
from app.services.finance.forecast import generate_financial_forecast


def _profile_to_baseline(profile):
    if profile is None:
        return None

    return {
        "annual_revenue": profile.annual_revenue,
        "monthly_revenue": profile.monthly_revenue,
        "monthly_expenses": profile.monthly_expenses,
        "monthly_payroll": profile.monthly_payroll,
        "monthly_marketing": profile.monthly_marketing,
        "monthly_software": profile.monthly_software,
        "cash_balance": profile.cash_balance,
        "accounts_receivable": profile.accounts_receivable,
        "accounts_payable": profile.accounts_payable,
        "total_debt": profile.total_debt,
        "monthly_debt_payment": profile.monthly_debt_payment,
        "employee_count": profile.employee_count,
        "fiscal_year_start": profile.fiscal_year_start,
        "data_source": profile.data_source,
    }


def _baseline_to_financials(baseline):
    monthly_revenue = baseline.get(
        "monthly_revenue"
    ) or 0

    monthly_expenses = baseline.get(
        "monthly_expenses"
    ) or 0

    net_income = (
        monthly_revenue
        - monthly_expenses
    )

    net_margin = (
        (net_income / monthly_revenue) * 100
        if monthly_revenue > 0
        else 0
    )

    cash_balance = (
        baseline.get("cash_balance") or 0
    )

    return {
        "transaction_count": 0,
        "revenue": monthly_revenue,
        "expenses": monthly_expenses,
        "net_income": net_income,
        "net_margin": net_margin,
        "cash_inflow": monthly_revenue,
        "cash_outflow": monthly_expenses,
        "net_cash_flow": net_income,
        "cash_balance": cash_balance,
    }


def build_financial_context(
    db: Session,
    workspace: Workspace,
) -> dict:

    analysis = analyze_workspace_finances(
        db=db,
        workspace_id=workspace.id,
    )

    actual_cash_balance = get_workspace_cash_balance(
        db=db,
        workspace_id=workspace.id,
    )

    actual_transaction_count = (
        analysis["transaction_count"]
    )

    actual_accounts = actual_cash_balance != 0

    company = getattr(
        workspace,
        "company",
        None,
    )

    profile = None

    if company is not None:
        profile = db.scalar(
            select(CompanyFinancialProfile)
            .where(
                CompanyFinancialProfile.company_id
                == company.id
            )
        )

    baseline = _profile_to_baseline(
        profile
    )

    has_actual_transactions = (
        actual_transaction_count > 0
    )

    has_actual_accounts = actual_accounts

    has_actual_financial_data = (
        has_actual_transactions
        or has_actual_accounts
    )

    if has_actual_financial_data:
        data_source = "ACTUAL"

        analysis["cash_balance"] = (
            actual_cash_balance
        )

        financials = {
            "transaction_count": analysis[
                "transaction_count"
            ],
            "revenue": analysis["revenue"],
            "expenses": analysis["expenses"],
            "net_income": analysis["net_income"],
            "net_margin": analysis["net_margin"],
            "cash_inflow": analysis[
                "cash_inflow"
            ],
            "cash_outflow": analysis[
                "cash_outflow"
            ],
            "net_cash_flow": analysis[
                "net_cash_flow"
            ],
            "cash_balance": actual_cash_balance,
        }

        income_breakdown = (
            analysis["income_breakdown"]
        )

        expense_breakdown = (
            analysis["expense_breakdown"]
        )

    elif baseline is not None:
        data_source = "USER_PROVIDED"

        financials = _baseline_to_financials(
            baseline
        )

        income_breakdown = []

        if financials["revenue"] > 0:
            income_breakdown.append(
                {
                    "category": "REPORTED_REVENUE",
                    "amount": financials[
                        "revenue"
                    ],
                    "percentage": 100,
                }
            )

        expense_breakdown = []

        expense_categories = [
            (
                "PAYROLL",
                baseline.get(
                    "monthly_payroll"
                ),
            ),
            (
                "MARKETING",
                baseline.get(
                    "monthly_marketing"
                ),
            ),
            (
                "SOFTWARE",
                baseline.get(
                    "monthly_software"
                ),
            ),
        ]

        known_expenses = sum(
            (
                amount or 0
                for _, amount
                in expense_categories
            ),
            0,
        )

        for category, amount in (
            expense_categories
        ):
            if amount is None or amount <= 0:
                continue

            percentage = (
                (amount / financials["expenses"])
                * 100
                if financials["expenses"] > 0
                else 0
            )

            expense_breakdown.append(
                {
                    "category": category,
                    "amount": amount,
                    "percentage": percentage,
                }
            )

        other_expenses = (
            financials["expenses"]
            - known_expenses
        )

        if other_expenses > 0:
            percentage = (
                (
                    other_expenses
                    / financials["expenses"]
                )
                * 100
                if financials["expenses"] > 0
                else 0
            )

            expense_breakdown.append(
                {
                    "category": "OTHER",
                    "amount": other_expenses,
                    "percentage": percentage,
                }
            )

    else:
        data_source = "NONE"

        financials = {
            "transaction_count": 0,
            "revenue": 0,
            "expenses": 0,
            "net_income": 0,
            "net_margin": 0,
            "cash_inflow": 0,
            "cash_outflow": 0,
            "net_cash_flow": 0,
            "cash_balance": 0,
        }

        income_breakdown = []
        expense_breakdown = []

    analysis_for_cfo = {
        "financials": financials,
        "financial_baseline": baseline,
        "income_breakdown": income_breakdown,
        "expense_breakdown": expense_breakdown,
    }

    insights = generate_cfo_insights(
        analysis=financials
        | {
            "income_breakdown": income_breakdown,
            "expense_breakdown": expense_breakdown,
        }
    )

    context = {
        "workspace": {
            "id": workspace.id,
            "name": workspace.name,
            "type": workspace.type,
            "base_currency": workspace.base_currency,
            "country": workspace.country,
        },

        "company": (
            {
                "id": company.id,
                "legal_name": company.legal_name,
                "display_name": company.display_name,
                "country": company.country,
                "industry": company.industry,
                "business_model": company.business_model,
                "website": company.website,
                "base_currency": company.base_currency,
                "risk_profile": company.risk_profile,
            }
            if company is not None
            else None
        ),

        "data_status": {
            "has_actual_transactions":
                has_actual_transactions,
            "has_actual_accounts":
                has_actual_accounts,
            "has_actual_financial_data":
                has_actual_financial_data,
            "has_user_provided_baseline":
                baseline is not None,
            "primary_source":
                data_source,
        },

        "financial_baseline": baseline,

        "financials": financials,

        "income_breakdown":
            income_breakdown,

        "expense_breakdown":
            expense_breakdown,

        "insights": insights,
    }

    context["cfo_decision"] = (
        generate_cfo_decision(
            {
                **analysis_for_cfo,
                "financial_baseline": baseline,
            }
        )
    )

    context["forecast"] = (
        generate_financial_forecast(
            analysis=context["financials"],
            periods=3,
        )
    )

    return context
