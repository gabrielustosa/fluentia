from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from fluentia.apps.term.constants import Language


class UserSchema(BaseModel):
    username: str = Field(default=None, examples=['tester'])
    email: EmailStr
    password: str = Field(default=None, examples=['pass123'])
    native_language: Language


class UserView(BaseModel):
    id: int
    username: str = Field(examples=['tester'])
    native_language: Language
    created: datetime
    is_superuser: bool


class UserSchemaUpdate(BaseModel):
    username: str | None = Field(default=None, examples=['tester'])
    email: EmailStr | None = None
    password: str | None = Field(default=None, examples=['pass123'])
    native_language: Language | None = None
