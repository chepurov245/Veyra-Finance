from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=200)


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    name: str
    status: str

    model_config = {
        "from_attributes": True,
    }
