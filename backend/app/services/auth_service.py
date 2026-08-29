from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import Company, User, Workspace
from app.models.company_financial_profile import (
    CompanyFinancialProfile,
)
from app.schemas.user import UserCreate
from app.schemas.workspace import WorkspaceCreate


class RegistrationError(Exception):
    pass


def register_user(
    db: Session,
    user_data: UserCreate,
    workspace_data: WorkspaceCreate,
) -> tuple[
    User,
    Workspace,
    Company | None,
]:

    existing_user = db.scalar(
        select(User).where(User.email == user_data.email)
    )

    if existing_user is not None:
        raise RegistrationError(
            "A user with this email already exists."
        )

    if (
        workspace_data.type == "BUSINESS"
        and workspace_data.company is None
    ):
        raise RegistrationError(
            "Company information is required "
            "for BUSINESS workspace."
        )

    if (
        workspace_data.type == "PERSONAL"
        and workspace_data.company is not None
    ):
        raise RegistrationError(
            "Company information is not allowed "
            "for PERSONAL workspace."
        )

    user = User(
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        name=user_data.name,
    )

    db.add(user)
    db.flush()

    workspace = Workspace(
        owner_id=user.id,
        type=workspace_data.type,
        name=workspace_data.name,
        base_currency=workspace_data.base_currency.upper(),
        country=workspace_data.country,
    )

    db.add(workspace)
    db.flush()

    company = None

    if workspace_data.type == "BUSINESS":
        company_data = workspace_data.company

        company = Company(
            workspace_id=workspace.id,
            legal_name=company_data.legal_name,
            display_name=(
                company_data.display_name
                or workspace_data.name
            ),
            country=(
                workspace_data.country
                or "Unknown"
            ),
            industry=company_data.industry,
            business_model=company_data.business_model,
            website=company_data.website,
            base_currency=(
                workspace_data.base_currency.upper()
            ),
            risk_profile=company_data.risk_profile,
        )

        db.add(company)
        db.flush()

        financial_profile = CompanyFinancialProfile(
            company_id=company.id,
            annual_revenue=company_data.annual_revenue,
            monthly_revenue=company_data.monthly_revenue,
            monthly_expenses=company_data.monthly_expenses,
            monthly_payroll=company_data.monthly_payroll,
            monthly_marketing=company_data.monthly_marketing,
            monthly_software=company_data.monthly_software,
            cash_balance=company_data.cash_balance,
            accounts_receivable=(
                company_data.accounts_receivable
            ),
            accounts_payable=(
                company_data.accounts_payable
            ),
            total_debt=company_data.total_debt,
            monthly_debt_payment=(
                company_data.monthly_debt_payment
            ),
            employee_count=company_data.employee_count,
            fiscal_year_start=(
                company_data.fiscal_year_start
            ),
            data_source="USER_PROVIDED",
        )

        db.add(financial_profile)

    db.commit()

    db.refresh(user)
    db.refresh(workspace)

    if company is not None:
        db.refresh(company)

    return user, workspace, company
