from datetime import datetime

from sqlmodel import Field, SQLModel


class CardSet(SQLModel, table=True):
    id: int = Field(primary_key=True)
    name: str
    description: str | None = None
    created: datetime = Field(default_factory=datetime.utcnow)
    modified: datetime = Field(nullable=True, default=None)
    language: str | None = None
    user_id: int = Field(foreign_key='user.id')


class Card(SQLModel, table=True):
    id: int = Field(primary_key=True)
    cardset_id: int = Field(foreign_key='cardset.id')
    created: datetime = Field(default_factory=datetime.utcnow)
    modified: datetime = Field(nullable=True, default=None)
    note: str | None = None
    term: str = Field(foreign_key='term.term')
    origin_language: str = Field(foreign_key='term.origin_language')
