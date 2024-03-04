from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: str = Field(examples=['abc123'])
    token_type: str = Field(examples=['bearer'])


class TokenData(BaseModel):
    username: str | None = None
