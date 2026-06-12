from pydantic import BaseModel, EmailStr


class UserOut(BaseModel):
    id: str
    email: str
    name: str | None
    avatar_url: str | None

    model_config = {"from_attributes": True}


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
