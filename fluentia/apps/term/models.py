from sqlmodel import Field, SQLModel, select

from fluentia.apps.term.constants import (
    Language,
    PartOfSpeech,
    TermLevel,
    TermLexicalType,
)
from fluentia.core.model.shortcut import create, update


class Term(SQLModel, table=True):
    term: str = Field(primary_key=True)
    origin_language: Language = Field(primary_key=True)

    @staticmethod
    def create(session, **data):
        return create(Term, session, **data)


class TermLexical(SQLModel, table=True):
    id: int = Field(primary_key=True)
    term: str = Field(foreign_key='term.term')
    origin_language: Language = Field(foreign_key='term.origin_language')
    value: str
    type: TermLexicalType

    @staticmethod
    def create(session, **data):
        return create(TermLexical, session, **data)

    @staticmethod
    def list(session, term, origin_language, type=None):
        filters = set()
        if type is not None:
            filters.add(TermLexical.type == type.lower())
        return session.exec(
            select(TermLexical).where(
                TermLexical.term == term,
                TermLexical.origin_language == origin_language,
                *filters,
            )
        )


class Pronunciation(SQLModel, table=True):
    id: int = Field(primary_key=True)
    audio_file: str | None = None
    description: str | None = None
    language: Language
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
        return session.exec(
            select(Pronunciation).where(
                Pronunciation.id.in_(
                    select(PronunciationLink.pronunciation_id).filter_by(
                        **link_attributes
                    )
                )
            )
        ).all()


class PronunciationLink(SQLModel, table=True):
    id: int = Field(primary_key=True)
    pronunciation_id: int = Field(foreign_key='pronunciation.id', unique=True)
    term: str = Field(foreign_key='term.term', nullable=True, default=None)
    origin_language: Language = Field(
        foreign_key='term.origin_language', nullable=True, default=None
    )
    term_example_id: int = Field(
        foreign_key='termexample.id', nullable=True, default=None
    )
    term_lexical_id: int = Field(
        foreign_key='termlexical.id', nullable=True, default=None
    )

    @staticmethod
    def create(session, **data):
        return create(PronunciationLink, session, **data)


class TermDefinition(SQLModel, table=True):
    id: int = Field(primary_key=True)
    term: str = Field(foreign_key='term.term')
    origin_language: Language = Field(foreign_key='term.origin_language')
    term_level: TermLevel | None = None
    part_of_speech: PartOfSpeech
    definition: str

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

        query_definition = select(TermDefinition).where(
            TermDefinition.term == term,
            TermDefinition.origin_language == origin_language,
            *filters,
        )
        return session.exec(query_definition)

    @staticmethod
    def update(session, db_definition, **data):
        return update(session, db_definition, **data)


class TermDefinitionTranslation(SQLModel, table=True):
    language: Language = Field(primary_key=True)
    term_definition_id: int = Field(foreign_key='termdefinition.id', primary_key=True)
    translation: str
    meaning: str

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
            select(
                TermDefinition,
                TermDefinitionTranslation,
            )
            .where(
                TermDefinition.term == term,
                TermDefinition.origin_language == origin_language,
                TermDefinitionTranslation.language == translation_language,
                *filters,
            )
            .join(
                TermDefinitionTranslation,
                TermDefinition.id == TermDefinitionTranslation.term_definition_id,
            )
        )
        return session.exec(query_translation)


class TermExample(SQLModel, table=True):
    id: int = Field(primary_key=True)
    term: str = Field(foreign_key='term.term')
    origin_language: Language = Field(foreign_key='term.origin_language')
    term_definition_id: int | None = Field(
        foreign_key='termdefinition.id', nullable=True, default=None
    )
    example: str

    @staticmethod
    def list(
        session, term, origin_language, term_definition_id, translation_language=None
    ):
        query_example = select(TermExample).where(
            TermExample.term == term,
            TermExample.origin_language == origin_language,
            TermExample.term_definition_id == term_definition_id,
        )
        if translation_language is not None:
            query_example = (
                select(
                    TermExample,
                    TermExampleTranslation,
                )
                .join(
                    TermExampleTranslation,
                    TermExample.id == TermExampleTranslation.term_example_id,
                )
                .where(
                    TermExampleTranslation.language == translation_language,
                    TermExample.term == term,
                    TermExample.origin_language == origin_language,
                    TermExample.term_definition_id == term_definition_id,
                )
            )
        return session.exec(query_example).all()

    @staticmethod
    def update(session, db_example, **data):
        return update(session, db_example, **data)


class TermExampleTranslation(SQLModel, table=True):
    language: Language = Field(primary_key=True)
    term_example_id: int = Field(foreign_key='termexample.id', primary_key=True)
    translation: str

    @staticmethod
    def create(session, **data):
        return create(TermExampleTranslation, session, **data)

    @staticmethod
    def update(session, db_example, **data):
        return update(session, db_example, **data)
