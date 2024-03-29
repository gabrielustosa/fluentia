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
            sm.select(Term).where(
                Term.origin_language == origin_language,
                sm.func.clean_text(Term.term).like(
                    '%' + sm.func.clean_text(text) + '%'
                ),
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
        translation_language=None,
    ):
        if translation_language:
            return TermDefinitionTranslation.list(
                session,
                term,
                origin_language,
                part_of_speech,
                term_level,
                translation_language,
            )

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
        translation_language=None,
    ):
        query_example = sm.select(TermExample).where(
            sm.func.clean_text(TermExample.term) == sm.func.clean_text(term),
            TermExample.origin_language == origin_language,
            TermExample.term_definition_id == term_definition_id,
        )
        if translation_language is not None:
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
                )
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

    __table_args__ = (
        sm.ForeignKeyConstraint(
            ['term_example_id'],
            ['termexample.id'],
            ondelete='CASCADE',
        ),
    )


@listens_for(TermExample, 'after_insert')
def insert_write_exercise(mapper, connection, target):
    session = sm.Session(connection)

    get_or_create_object(
        Exercise,
        session,
        term=target.term,
        origin_language=target.origin_language,
        term_example_id=target.id,
        term_definition_id=target.term_definition_id,
        type=ExerciseType.WRITE_SENTENCE,
    )


# @listens_for(PronunciationLink, 'after_insert')
# @listens_for(PronunciationLink, 'after_update')
# def insert_listen_exercise(mapper, connection, target):
#     session = Session(connection)
