from datetime import datetime

from sqlmodel import Field, ForeignKeyConstraint, SQLModel

from fluentia.apps.term.constants import Language


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
    term: str
    origin_language: Language

    __table_args__ = (
        ForeignKeyConstraint(
            ['term', 'origin_language'],
            ['term.term', 'term.origin_language'],
            ondelete='CASCADE',
        ),
    )
