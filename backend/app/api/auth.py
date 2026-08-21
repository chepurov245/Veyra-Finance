from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.user import UserCreate, UserResponse
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
