from sqlmodel import Field, SQLModel

from fluentia.apps.term.constants import (
    Language,
    PartOfSpeech,
    TermLevel,
    TermLexicalType,
)


class Term(SQLModel, table=True):
    term: str = Field(primary_key=True)
    origin_language: Language = Field(primary_key=True)


class TermLexical(SQLModel, table=True):
    id: int = Field(primary_key=True)
    term: str = Field(foreign_key='term.term')
    origin_language: Language = Field(foreign_key='term.origin_language')
    value: str
    type: TermLexicalType


class Pronunciation(SQLModel, table=True):
    id: int = Field(primary_key=True)
    audio_file: str | None = None
    description: str | None = None
    language: Language
    phonetic: str
    text: str


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


class TermDefinition(SQLModel, table=True):
    id: int = Field(primary_key=True)
    term: str = Field(foreign_key='term.term')
    origin_language: Language = Field(foreign_key='term.origin_language')
    term_level: TermLevel | None = None
    part_of_speech: PartOfSpeech
    definition: str


class TermDefinitionTranslation(SQLModel, table=True):
    language: Language = Field(primary_key=True)
    term_definition_id: int = Field(foreign_key='termdefinition.id', primary_key=True)
    translation: str
    meaning: str


class TermExample(SQLModel, table=True):
    id: int = Field(primary_key=True)
    term: str = Field(foreign_key='term.term')
    origin_language: Language = Field(foreign_key='term.origin_language')
    term_definition_id: int | None = Field(
        foreign_key='termdefinition.id', nullable=True, default=None
    )
    example: str


class TermExampleTranslation(SQLModel, table=True):
    language: Language = Field(primary_key=True)
    term_example_id: int = Field(foreign_key='termexample.id', primary_key=True)
    translation: str
