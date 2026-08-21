from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import Company, User, Workspace
from app.schemas.user import UserCreate
from app.schemas.workspace import WorkspaceCreate


class RegistrationError(Exception):
    pass


def register_user(
    db: Session,
    user_data: UserCreate,
    workspace_data: WorkspaceCreate,
) -> tuple[User, Workspace, Company | None]:

    existing_user = db.scalar(
        select(User).where(User.email == user_data.email)
    )

    if existing_user is not None:
        raise RegistrationError(
            "A user with this email already exists."
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
        company = Company(
            workspace_id=workspace.id,
            legal_name=workspace_data.name,
            display_name=workspace_data.name,
            country=workspace_data.country or "Unknown",
            base_currency=workspace_data.base_currency.upper(),
        )

        db.add(company)

    db.commit()

    db.refresh(user)
    db.refresh(workspace)

    if company is not None:
        db.refresh(company)

    return user, workspace, company
