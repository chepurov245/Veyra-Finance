from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_password
from app.services.token_service import create_access_token

from app.models import User, Workspace

from app.schemas.user import UserCreate, UserResponse
from app.schemas.auth import LoginRequest, LoginResponse

from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceResponse,
)

from app.services.auth_service import (
    RegistrationError,
    register_user,
)


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


class RegistrationRequest(BaseModel):
    user: UserCreate
    workspace: WorkspaceCreate


class RegistrationResponse(BaseModel):
    user: UserResponse
    workspace: WorkspaceResponse


@router.post(
    "/register",
    response_model=RegistrationResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    payload: RegistrationRequest,
    db: Session = Depends(get_db),
):
    try:
        user, workspace, _company = register_user(
            db=db,
            user_data=payload.user,
            workspace_data=payload.workspace,
        )

    except RegistrationError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return RegistrationResponse(
        user=user,
        workspace=workspace,
    )


@router.post(
    "/login",
    response_model=LoginResponse,
)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    user = db.scalar(
        select(User).where(User.email == payload.email)
    )

    if user is None or not verify_password(
        payload.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    workspace = db.scalar(
        select(Workspace)
        .where(Workspace.owner_id == user.id)
        .order_by(Workspace.id)
    )

    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found.",
        )

    return LoginResponse(
        access_token=create_access_token(user.id),
        user_id=user.id,
        workspace_id=workspace.id,
    )
