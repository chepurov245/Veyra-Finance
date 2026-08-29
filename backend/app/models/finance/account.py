from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class FinancialAccount(Base):
    __tablename__ = "financial_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)

    workspace_id: Mapped[int] = mapped_column(
        ForeignKey("workspaces.id"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    account_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    balance: Mapped[Decimal] = mapped_column(
        Numeric(20, 4),
        default=Decimal("0"),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="active",
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

    workspace = relationship(
        "Workspace",
    )

    transactions = relationship(
        "FinancialTransaction",
        back_populates="account",
        cascade="all, delete-orphan",
    )
