from datetime import datetime

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id: int = Field(primary_key=True)
    username: str
    email: str
    password: str
    created: datetime = Field(default_factory=datetime.utcnow)
    native_language: str
    is_superuser: bool = False
