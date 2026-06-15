from pydantic import AliasChoices, BaseModel, Field, field_validator


class UserOut(BaseModel):
    id: str
    email: str
    # The ORM attribute is `display_name`; expose it as `name` to the client.
    name: str | None = Field(
        default=None, validation_alias=AliasChoices("name", "display_name")
    )
    avatar_url: str | None = None

    model_config = {"from_attributes": True, "populate_by_name": True}

    @field_validator("id", mode="before")
    @classmethod
    def _uuid_to_str(cls, v: object) -> str:
        return str(v)


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
