from datetime import datetime

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id: int = Field(primary_key=True)
    username: str
    email: str
    password: str
    created: datetime
    native_language: str
    is_superuser: bool = Field(default=False)
