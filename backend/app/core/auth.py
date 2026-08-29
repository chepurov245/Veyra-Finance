from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import User, Workspace
from app.services.token_service import decode_access_token


_bearer = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    user_id = decode_access_token(credentials.credentials)

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.scalar(
        select(User).where(User.id == user_id)
    )

    if user is None or user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_current_workspace(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Workspace:
    workspace = db.scalar(
        select(Workspace)
        .where(Workspace.owner_id == current_user.id)
        .order_by(Workspace.id)
    )

    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found.",
        )

    return workspace
