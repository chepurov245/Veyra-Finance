"""add company financial profiles

Revision ID: add_company_financial_profiles
Revises: b0c556800f3c
Create Date: 2026-08-27
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "add_company_financial_profiles"
down_revision: Union[str, Sequence[str], None] = "b0c556800f3c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "company_financial_profiles",

        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "company_id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "annual_revenue",
            sa.Numeric(20, 4),
            nullable=True,
        ),

        sa.Column(
            "monthly_revenue",
            sa.Numeric(20, 4),
            nullable=True,
        ),

        sa.Column(
            "monthly_expenses",
            sa.Numeric(20, 4),
            nullable=True,
        ),

        sa.Column(
            "monthly_payroll",
            sa.Numeric(20, 4),
            nullable=True,
        ),

        sa.Column(
            "monthly_marketing",
            sa.Numeric(20, 4),
            nullable=True,
        ),

        sa.Column(
            "monthly_software",
            sa.Numeric(20, 4),
            nullable=True,
        ),

        sa.Column(
            "cash_balance",
            sa.Numeric(20, 4),
            nullable=True,
        ),

        sa.Column(
            "accounts_receivable",
            sa.Numeric(20, 4),
            nullable=True,
        ),

        sa.Column(
            "accounts_payable",
            sa.Numeric(20, 4),
            nullable=True,
        ),

        sa.Column(
            "total_debt",
            sa.Numeric(20, 4),
            nullable=True,
        ),

        sa.Column(
            "monthly_debt_payment",
            sa.Numeric(20, 4),
            nullable=True,
        ),

        sa.Column(
            "employee_count",
            sa.Integer(),
            nullable=True,
        ),

        sa.Column(
            "fiscal_year_start",
            sa.String(10),
            nullable=True,
        ),

        sa.Column(
            "data_source",
            sa.String(50),
            nullable=False,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
        ),

        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_company_financial_profiles_company_id",
        "company_financial_profiles",
        ["company_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_company_financial_profiles_company_id",
        table_name="company_financial_profiles",
    )

    op.drop_table(
        "company_financial_profiles",
    )
