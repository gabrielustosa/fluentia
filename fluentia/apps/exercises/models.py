from datetime import datetime

from sqlmodel import Field, SQLModel


class Exercise(SQLModel, table=True):
    term: str = Field(primary_key=True, foreign_key='term.term')
    origin_language: str = Field(
        primary_key=True, foreign_key='term.origin_language'
    )
    term_level: str = Field(primary_key=True)
    type: str = Field(primary_key=True)


class ExerciseSpeak(SQLModel, table=True):
    id: int = Field(primary_key=True)
    user_id: int = Field(foreign_key='user.id')
    text: str | None = None


class ExerciseHistory(SQLModel, table=True):
    id: int = Field(primary_key=True)
    term: str = Field(foreign_key='exercise.term')
    origin_language: str = Field(foreign_key='exercise.origin_language')
    term_level: str = Field(foreign_key='exercise.term_level')
    type: str = Field(foreign_key='exercise.type')
    user_id: int = Field(foreign_key='user.id')
    created: datetime = Field(default_factory=datetime.utcnow)
    correct: bool
    text_response: str | None = None
    text_request: str | None = None
