from datetime import datetime

from sqlmodel import Field, ForeignKeyConstraint, SQLModel

from fluentia.apps.exercises.constants import ExerciseType
from fluentia.apps.term.constants import Language


class Exercise(SQLModel, table=True):
    id: int = Field(primary_key=True)
    term: str
    origin_language: Language
    term_definition_id: int | None = None
    term_example_id: int | None = None
    pronunciation_id: int | None = None
    term_lexical_id: int | None = None
    type: ExerciseType

    __table_args__ = (
        ForeignKeyConstraint(
            ['term', 'origin_language'],
            ['term.term', 'term.origin_language'],
            ondelete='CASCADE',
        ),
        ForeignKeyConstraint(
            ['term_definition_id'],
            ['termdefinition.id'],
            ondelete='CASCADE',
        ),
        ForeignKeyConstraint(
            ['term_example_id'],
            ['termexample.id'],
            ondelete='CASCADE',
        ),
        ForeignKeyConstraint(
            ['pronunciation_id'],
            ['pronunciation.id'],
            ondelete='CASCADE',
        ),
        ForeignKeyConstraint(
            ['term_lexical_id'],
            ['termlexical.id'],
            ondelete='CASCADE',
        ),
    )


class ExerciseHistory(SQLModel, table=True):
    id: int = Field(primary_key=True)
    exercise_id: int = Field(foreign_key='exercise.id')
    user_id: int = Field(foreign_key='user.id')
    created: datetime = Field(default_factory=datetime.utcnow)
    correct: bool
    text_response: str | None = None
    text_request: str | None = None
