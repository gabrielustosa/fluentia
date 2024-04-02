import sqlmodel as sm
from fastapi import HTTPException
from sqlalchemy.event import listens_for

from fluentia.apps.exercises.constants import ExerciseType
from fluentia.apps.exercises.models import Exercise
from fluentia.apps.term import constants
from fluentia.apps.term.schema import TermDefinitionSchema, TermExampleSchema
from fluentia.core.model.shortcut import create, get_or_create_object, update


class Term(sm.SQLModel, table=True):
    term: str = sm.Field(primary_key=True)
    origin_language: constants.Language = sm.Field(primary_key=True)

    __table_args__ = (sm.UniqueConstraint('term', 'origin_language'),)

    @staticmethod
    def get(session, term, origin_language):
        return session.exec(
            sm.select(Term).where(
                sm.func.clean_text(Term.term) == sm.func.clean_text(term),
                Term.origin_language == origin_language,
            )
        ).first()

    @staticmethod
    def get_or_404(session, term, origin_language):
        obj = Term.get(session, term, origin_language)
        if obj is None:
            raise HTTPException(status_code=404, detail='term was not found.')
        return obj

    @staticmethod
    def get_or_create(session, **data):
        obj = Term.get(session, **data)
        if obj is not None:
            return obj, False
        return create(Term, session, **data), True

    @staticmethod
    def search(session, text, origin_language):
        return session.exec(
            sm.select(Term)
            .where(
                Term.origin_language == origin_language,
                sm.func.clean_text(Term.term).like(
                    '%' + sm.func.clean_text(text) + '%'
                ),
            )
            .union(
                sm.select(Term).where(
                    sm.tuple_(Term.term, Term.origin_language).in_(
                        sm.select(TermLexical.term, TermLexical.origin_language).where(
                            sm.func.clean_text(TermLexical.value).like(
                                '%' + sm.func.clean_text(text) + '%'
                            ),
                            TermLexical.origin_language == origin_language,
                            TermLexical.type == constants.TermLexicalType.FORM,
                        )
                    ),
                )
            )
        )

    @staticmethod
    def search_term_meaning(session, text, origin_language, translation_language):
        translation_query = (
            sm.select(
                TermDefinition.term,
                TermDefinition.origin_language,
            )
            .where(
                sm.func.clean_text(TermDefinitionTranslation.meaning).like(
                    '%' + sm.func.clean_text(text) + '%'
                ),
                TermDefinition.origin_language == origin_language,
                TermDefinitionTranslation.language == translation_language,
            )
            .join(
                TermDefinitionTranslation,
                TermDefinition.id == TermDefinitionTranslation.term_definition_id,  # pyright: ignore[reportArgumentType]
            )
        )
        return session.exec(
            sm.select(Term).where(
                sm.tuple_(Term.term, Term.origin_language).in_(translation_query)
            )
        )


class TermLexical(sm.SQLModel, table=True):
    id: int = sm.Field(primary_key=True)
    term: str
    origin_language: constants.Language
    value: str
    type: constants.TermLexicalType

    __table_args__ = (
        sm.ForeignKeyConstraint(
            ['term', 'origin_language'],
            ['term.term', 'term.origin_language'],
            ondelete='CASCADE',
        ),
    )

    @staticmethod
    def create(session, **data):
        return create(TermLexical, session, **data)

    @staticmethod
    def list(session, term, origin_language, type=None):
        filters = set()
        if type is not None:
            filters.add(TermLexical.type == type.lower())
        return session.exec(
            sm.select(TermLexical).where(
                sm.func.clean_text(TermLexical.term) == sm.func.clean_text(term),
                TermLexical.origin_language == origin_language,
                *filters,
            )
        )


class Pronunciation(sm.SQLModel, table=True):
    id: int = sm.Field(primary_key=True)
    audio_file: str | None = None
    description: str | None = None
    language: constants.Language
    phonetic: str
    text: str

    @staticmethod
    def create(session, **data):
        return create(Pronunciation, session, **data)

    @staticmethod
    def update(session, db_pronuciation, **data):
        return update(session, db_pronuciation, **data)

    @staticmethod
    def list(session, **link_attributes):
        filter_term = set()
        term = link_attributes.pop('term')
        if term:
            filter_term.add(
                sm.func.clean_text(PronunciationLink.term) == sm.func.clean_text(term)
            )
        return session.exec(
            sm.select(Pronunciation).where(
                Pronunciation.id.in_(
                    sm.select(PronunciationLink.pronunciation_id)
                    .filter_by(**link_attributes)
                    .where(*filter_term)
                )
            )
        ).all()


class PronunciationLink(sm.SQLModel, table=True):
    pronunciation_id: int = sm.Field(primary_key=True)
    term: str | None = None
    origin_language: constants.Language | None = None
    term_example_id: int | None = None
    term_lexical_id: int | None = None

    __table_args__ = (
        sm.ForeignKeyConstraint(
            ['pronunciation_id'],
            ['pronunciation.id'],
            ondelete='CASCADE',
        ),
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
            ['term_lexical_id'],
            ['termlexical.id'],
            ondelete='CASCADE',
        ),
    )

    @staticmethod
    def create(session, **data):
        return create(PronunciationLink, session, **data)


class TermDefinition(sm.SQLModel, table=True):
    id: int = sm.Field(primary_key=True)
    term: str
    origin_language: constants.Language
    term_level: constants.TermLevel | None = None
    part_of_speech: constants.PartOfSpeech
    definition: str

    __table_args__ = (
        sm.ForeignKeyConstraint(
            ['term', 'origin_language'],
            ['term.term', 'term.origin_language'],
            ondelete='CASCADE',
        ),
    )

    @staticmethod
    def list(
        session,
        term,
        origin_language,
        part_of_speech=None,
        term_level=None,
    ):
        filters = set()
        if term_level:
            filters.add(TermDefinition.term_level == term_level)
        if part_of_speech:
            filters.add(TermDefinition.part_of_speech == part_of_speech)

        query_definition = sm.select(TermDefinition).where(
            sm.func.clean_text(TermDefinition.term) == sm.func.clean_text(term),
            TermDefinition.origin_language == origin_language,
            *filters,
        )
        return session.exec(query_definition)

    @staticmethod
    def get_or_create(session, model_schema: TermDefinitionSchema):
        db_definition = session.exec(
            sm.select(TermDefinition)
            .where(
                sm.func.clean_text(TermDefinition.term)
                == sm.func.clean_text(model_schema.term),
                sm.func.clean_text(TermDefinition.definition)
                == sm.func.clean_text(model_schema.definition),
            )
            .filter_by(
                **model_schema.model_dump(exclude={'term_level', 'term', 'definition'})
            )
        ).first()
        if db_definition is not None:
            return db_definition, False
        return create(TermDefinition, session, **model_schema.model_dump()), True

    @staticmethod
    def update(session, db_definition, **data):
        return update(session, db_definition, **data)


class TermDefinitionTranslation(sm.SQLModel, table=True):
    language: constants.Language = sm.Field(primary_key=True)
    term_definition_id: int = sm.Field(primary_key=True)
    translation: str
    meaning: str

    __table_args__ = (
        sm.ForeignKeyConstraint(
            ['term_definition_id'],
            ['termdefinition.id'],
            ondelete='CASCADE',
        ),
    )

    @staticmethod
    def create(session, **data):
        return create(TermDefinitionTranslation, session, **data)

    @staticmethod
    def update(session, db_definition_translation, **data):
        return update(session, db_definition_translation, **data)

    @staticmethod
    def list(
        session,
        term,
        origin_language,
        part_of_speech=None,
        term_level=None,
        translation_language=None,
    ):
        filters = set()
        if term_level:
            filters.add(TermDefinition.term_level == term_level)
        if part_of_speech:
            filters.add(TermDefinition.part_of_speech == part_of_speech)
        query_translation = (
            sm.select(
                TermDefinition,
                TermDefinitionTranslation,
            )
            .where(
                sm.func.clean_text(TermDefinition.term) == sm.func.clean_text(term),
                TermDefinition.origin_language == origin_language,
                TermDefinitionTranslation.language == translation_language,
                *filters,
            )
            .join(
                TermDefinitionTranslation,
                TermDefinition.id == TermDefinitionTranslation.term_definition_id,  # pyright: ignore[reportArgumentType]
            )
        )
        return session.exec(query_translation)

    @staticmethod
    def list_meaning(session, term, origin_language, translation_language):
        translation_query = (
            sm.select(
                TermDefinitionTranslation.meaning,
            )
            .select_from(
                sm.join(
                    TermDefinition,
                    TermDefinitionTranslation,
                    TermDefinition.id == TermDefinitionTranslation.term_definition_id,  # pyright: ignore[reportArgumentType]
                )
            )
            .where(
                TermDefinition.term == term,
                TermDefinition.origin_language == origin_language,
                TermDefinitionTranslation.language == translation_language,
            )
        )
        return session.exec(translation_query)


class TermExample(sm.SQLModel, table=True):
    id: int = sm.Field(primary_key=True)
    term: str
    origin_language: constants.Language
    term_definition_id: int | None = None
    term_lexical_id: int | None = sm.Field(foreign_key='termlexical.id', default=None)
    example: str

    __table_args__ = (
        sm.ForeignKeyConstraint(
            ['term', 'origin_language'],
            ['term.term', 'term.origin_language'],
            ondelete='CASCADE',
        ),
        sm.ForeignKeyConstraint(
            ['term_definition_id'],
            ['termdefinition.id'],
            ondelete='CASCADE',
        ),
        sm.ForeignKeyConstraint(
            ['term_lexical_id'],
            ['termlexical.id'],
            ondelete='CASCADE',
        ),
    )

    @staticmethod
    def get_or_create(session, model_schema: TermExampleSchema):
        db_example = session.exec(
            sm.select(TermExample)
            .where(
                sm.func.clean_text(TermExample.term)
                == sm.func.clean_text(model_schema.term),
                sm.func.clean_text(TermExample.example)
                == sm.func.clean_text(model_schema.example),
            )
            .filter_by(**model_schema.model_dump(exclude={'term', 'example'}))
        ).first()

        if db_example is not None:
            return db_example, False
        return create(TermExample, session, **model_schema.model_dump()), True

    @staticmethod
    def list(
        session,
        term,
        origin_language,
        term_definition_id=None,
        term_lexical_id=None,
    ):
        query_example = sm.select(TermExample).where(
            sm.func.clean_text(TermExample.term) == sm.func.clean_text(term),
            TermExample.origin_language == origin_language,
            TermExample.term_definition_id == term_definition_id,
            TermExample.term_lexical_id == term_lexical_id,
        )
        return session.exec(query_example).all()

    @staticmethod
    def update(session, db_example, **data):
        return update(session, db_example, **data)


class TermExampleTranslation(sm.SQLModel, table=True):
    language: constants.Language = sm.Field(primary_key=True)
    term_example_id: int = sm.Field(foreign_key='termexample.id', primary_key=True)
    translation: str

    @staticmethod
    def create(session, **data):
        return create(TermExampleTranslation, session, **data)

    @staticmethod
    def update(session, db_example, **data):
        return update(session, db_example, **data)

    @staticmethod
    def list(
        session,
        term,
        origin_language,
        translation_language,
        term_definition_id=None,
        term_lexical_id=None,
    ):
        query_example = (
            sm.select(
                TermExample,
                TermExampleTranslation,
            )
            .join(
                TermExampleTranslation,
                TermExample.id == TermExampleTranslation.term_example_id,  # pyright: ignore[reportArgumentType]
            )
            .where(
                TermExampleTranslation.language == translation_language,
                sm.func.clean_text(TermExample.term) == sm.func.clean_text(term),
                TermExample.origin_language == origin_language,
                TermExample.term_definition_id == term_definition_id,
                TermExample.term_lexical_id == term_lexical_id,
            )
        )
        return session.exec(query_example).all()

    __table_args__ = (
        sm.ForeignKeyConstraint(
            ['term_example_id'],
            ['termexample.id'],
            ondelete='CASCADE',
        ),
    )


@listens_for(TermExample, 'after_insert')
def insert_write_exercise(_, connection, target):
    session = sm.Session(connection)

    get_or_create_object(
        Exercise,
        session,
        term=target.term,
        origin_language=target.origin_language,
        term_example_id=target.id,
        type=ExerciseType.WRITE_SENTENCE,
    )


@listens_for(PronunciationLink, 'after_insert')
def insert_listen_exercise(_, connection, target):
    session = sm.Session(connection)

    pronunciation = session.exec(
        sm.select(Pronunciation).where(Pronunciation.id == target.pronunciation_id)
    ).one()
    if pronunciation.audio_file is None:
        return

    exercise_attr = {}
    if target.term:
        exercise_attr.update(
            {
                'term': target.term,
                'origin_language': target.origin_language,
                'type': ExerciseType.LISTEN_TERM,
            }
        )
    elif target.term_example_id:
        db_example = session.exec(
            sm.select(TermExample).where(TermExample.id == target.term_example_id)
        ).one()

        exercise_attr.update(
            {
                'term': db_example.term,
                'origin_language': db_example.origin_language,
                'term_example_id': target.term_example_id,
                'type': ExerciseType.LISTEN_SENTENCE,
            }
        )
    elif target.term_lexical_id:
        db_lexical = session.exec(
            sm.select(TermLexical).where(TermLexical.id == target.term_lexical_id)
        ).one()

        exercise_attr.update(
            {
                'term': db_lexical.term,
                'origin_language': db_lexical.origin_language,
                'term_lexical_id': target.term_lexical_id,
                'type': ExerciseType.LISTEN_TERM,
            }
        )

    get_or_create_object(
        Exercise,
        session,
        pronunciation_id=target.pronunciation_id,
        **exercise_attr,
    )


@listens_for(Pronunciation, 'after_update')
def update_listen_exercise(_, connection, target):
    session = sm.Session(connection)

    if not target.audio_file:
        db_exercise = session.exec(
            sm.select(Exercise).where(
                Exercise.pronunciation_id == target.id,
                Exercise.type.in_(
                    (ExerciseType.LISTEN_SENTENCE, ExerciseType.LISTEN_TERM)
                ),
            )
        ).first()
        if db_exercise:
            session.delete(db_exercise)
            session.commit()
    else:
        link = session.exec(
            sm.select(PronunciationLink).where(
                PronunciationLink.pronunciation_id == target.id
            )
        ).first()
        if link:
            insert_listen_exercise(None, connection, link)


@listens_for(Term, 'after_insert')
def insert_speak_term_exercise(_, connection, target):
    session = sm.Session(connection)

    get_or_create_object(
        Exercise,
        session,
        term=target.term,
        origin_language=target.origin_language,
        type=ExerciseType.SPEAK_TERM,
    )


@listens_for(TermExample, 'after_insert')
def insert_speak_sentence_exercise(_, connection, target):
    session = sm.Session(connection)

    get_or_create_object(
        Exercise,
        session,
        term=target.term,
        origin_language=target.origin_language,
        term_example_id=target.id,
        type=ExerciseType.SPEAK_SENTENCE,
    )


@listens_for(TermLexical, 'after_insert')
def insert_mchoice_term_exercise(_, connection, target):
    if target.type != constants.TermLexicalType.ANTONYM:
        return

    session = sm.Session(connection)

    count = session.exec(
        sm.select(
            sm.func.count(TermLexical.id),  # pyright: ignore[reportArgumentType]
        ).where(
            TermLexical.term == target.term,
            TermLexical.origin_language == target.origin_language,
            TermLexical.type == constants.TermLexicalType.ANTONYM,
        )
    ).all()[0]
    if count >= 3:
        get_or_create_object(
            Exercise,
            session,
            term=target.term,
            origin_language=target.origin_language,
            type=ExerciseType.MCHOICE_TERM,
        )
