from datetime import datetime

import sqlmodel as sm

from fluentia.apps.exercises.constants import ExerciseType
from fluentia.apps.term.constants import Language
from fluentia.core.api.query import set_url_params
from fluentia.core.api.schema import Page


class Exercise(sm.SQLModel, table=True):
    id: int = sm.Field(primary_key=True)
    language: Language
    type: ExerciseType
    translation_language: Language | None = None
    term: str | None = None
    origin_language: Language | None = None
    term_example_id: int | None = None
    pronunciation_id: int | None = None
    term_lexical_id: int | None = None
    term_definition_id: int | None = None

    __table_args__ = (
        sm.ForeignKeyConstraint(
            ['term', 'origin_language'],
            ['term.term', 'term.origin_language'],
            ondelete='CASCADE',
        ),
        sm.ForeignKeyConstraint(
            ['term_example_id'],
            ['termexample.id'],
            ondelete='CASCADE',
        ),
        sm.ForeignKeyConstraint(
            ['pronunciation_id'],
            ['pronunciation.id'],
            ondelete='CASCADE',
        ),
        sm.ForeignKeyConstraint(
            ['term_lexical_id'],
            ['termlexical.id'],
            ondelete='CASCADE',
        ),
        sm.ForeignKeyConstraint(
            ['term_definition_id'],
            ['termdefinition.id'],
            ondelete='CASCADE',
        ),
    )

    @staticmethod
    def list_(
        session,
        exercise_type,
        language,
        seed,
        translation_language,
        level=None,
        cardset_id=None,
        page=1,
        size=50,
    ):
        from fluentia.apps.card.models import Card
        from fluentia.apps.term.models import (
            PronunciationLink,
            TermDefinition,
            TermExample,
        )
        from fluentia.main import app

        filters = set()
        or_statment = set()
        if level:
            if ExerciseType.is_term_exercise(exercise_type):
                or_statment.add(
                    sm.tuple_(Exercise.term, Exercise.origin_language).in_(
                        sm.select(
                            TermDefinition.term, TermDefinition.origin_language
                        ).where(
                            TermDefinition.level == level,
                            TermDefinition.origin_language == language,
                        )
                    )
                )
                or_statment.add(
                    Exercise.term_lexical_id.in_(  # pyright: ignore[reportOptionalMemberAccess]
                        sm.select(TermDefinition.term_lexical_id).where(
                            TermDefinition.origin_language == language,
                            TermDefinition.level == level,
                            TermDefinition.term_lexical_id.is_not(None),  # pyright: ignore[reportOptionalMemberAccess]
                        )
                    )
                )
            if ExerciseType.is_sentence_exercise(exercise_type):
                or_statment.add(
                    Exercise.term_example_id.in_(  # pyright: ignore[reportOptionalMemberAccess]
                        sm.select(TermExample.id).where(
                            TermExample.level == level,
                            TermExample.language == language,
                        )
                    )
                )
            if ExerciseType.is_pronunciation_exercise(exercise_type):
                if ExerciseType.LISTEN_TERM or ExerciseType.RANDOM:
                    or_statment.add(
                        Exercise.pronunciation_id.in_(  # pyright: ignore[reportOptionalMemberAccess]
                            sm.select(PronunciationLink.pronunciation_id)
                            .where(
                                sm.tuple_(
                                    PronunciationLink.term,
                                    PronunciationLink.origin_language,
                                ).in_(
                                    sm.select(
                                        TermDefinition.term,
                                        TermDefinition.origin_language,
                                    ).where(
                                        TermDefinition.level == level,
                                        TermDefinition.origin_language == language,
                                    )
                                )
                            )
                            .union(
                                sm.select(PronunciationLink.pronunciation_id).where(
                                    PronunciationLink.term_lexical_id.in_(  # pyright: ignore[reportOptionalMemberAccess]
                                        sm.select(TermDefinition.term_lexical_id).where(
                                            TermDefinition.level == level,
                                            TermDefinition.origin_language == language,
                                            TermDefinition.term_lexical_id.is_not(None),  # pyright: ignore[reportOptionalMemberAccess]
                                        )
                                    )
                                )
                            )
                        )
                    )
                elif ExerciseType.LISTEN_SENTENCE or ExerciseType.RANDOM:
                    or_statment.add(
                        Exercise.pronunciation_id.in_(  # pyright: ignore[reportOptionalMemberAccess]
                            sm.select(PronunciationLink.pronunciation_id).where(
                                PronunciationLink.term_example_id.in_(  # pyright: ignore[reportOptionalMemberAccess]
                                    sm.select(TermExample.id).where(
                                        TermExample.level == level,
                                        TermExample.language == language,
                                    )
                                )
                            )
                        )
                    )

        if ExerciseType.is_translation_exercise(exercise_type):
            or_statment.add(Exercise.translation_language == translation_language)

        filters.add(sm.or_(*or_statment))

        if cardset_id:
            filters.add(
                sm.tuple_(Exercise.term, Exercise.origin_language).in_(
                    Card.list_query(cardset_id)
                )
            )
        if exercise_type != ExerciseType.RANDOM:
            filters.add(Exercise.type == exercise_type)

        exercise_query = (
            sm.select(
                Exercise,
                sm.func.count().over().label('total_count'),
            )
            .where(
                Exercise.language == language,
                **filters,
            )
            .offset((page - 1) * size)
            .limit(size)
            .order_by(sm.func.MD5(Exercise.id + seed))
        )
        rows = session.exec(exercise_query).all()

        result_list = []
        for row in rows:
            db_exercise, _ = row
            result_list.append(db_exercise)

        url = app.url_path_for('list_exercises')
        return Page(
            items=result_list,
            total=0 if len(rows) == 0 else rows[0][1],
            next_page=set_url_params(
                url,
                exercise_type=exercise_type,
                language=language,
                level=level,
                cardset_id=cardset_id,
                seed=seed,
                page=page + 1,
                size=size,
            ),
        )


class ExerciseHistory(sm.SQLModel, table=True):
    id: int = sm.Field(primary_key=True)
    exercise_id: int = sm.Field(foreign_key='exercise.id')
    user_id: int = sm.Field(foreign_key='user.id')
    created: datetime = sm.Field(default_factory=datetime.utcnow)
    correct: bool
    text_response: str | None = None
    text_request: str | None = None
