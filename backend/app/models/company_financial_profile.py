from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CompanyFinancialProfile(Base):
    __tablename__ = "company_financial_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id"),
        unique=True,
        nullable=False,
        index=True,
    )

    annual_revenue: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 4), nullable=True
    )

    monthly_revenue: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 4), nullable=True
    )

    monthly_expenses: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 4), nullable=True
    )

    monthly_payroll: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 4), nullable=True
    )

    monthly_marketing: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 4), nullable=True
    )

    monthly_software: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 4), nullable=True
    )

    cash_balance: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 4), nullable=True
    )

    accounts_receivable: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 4), nullable=True
    )

    accounts_payable: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 4), nullable=True
    )

    total_debt: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 4), nullable=True
    )

    monthly_debt_payment: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 4), nullable=True
    )

    employee_count: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )

    fiscal_year_start: Mapped[str | None] = mapped_column(
        String(10), nullable=True
    )

    data_source: Mapped[str] = mapped_column(
        String(50),
        default="USER_PROVIDED",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    company = relationship(
        "Company",
        back_populates="financial_profile",
    )
