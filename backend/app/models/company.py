from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)

    workspace_id: Mapped[int] = mapped_column(
        ForeignKey("workspaces.id"),
        unique=True,
        nullable=False,
        index=True,
    )

    legal_name: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
    )

    display_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    country: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    industry: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    business_model: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    website: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    base_currency: Mapped[str] = mapped_column(
        String(10),
        default="RUB",
        nullable=False,
    )

    risk_profile: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
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
        back_populates="company",
    )

    financial_profile = relationship(
        "CompanyFinancialProfile",
        back_populates="company",
        uselist=False,
        cascade="all, delete-orphan",
    )
