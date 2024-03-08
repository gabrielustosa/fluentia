from sqlmodel import Field, SQLModel


class Term(SQLModel, table=True):
    term: str = Field(primary_key=True)
    origin_language: str = Field(primary_key=True)


class TermLexical(SQLModel, table=True):
    id: int = Field(primary_key=True)
    term: str = Field(foreign_key='term.term')
    origin_language: str = Field(foreign_key='term.origin_language')
    value: str
    type: str


class Pronunciation(SQLModel, table=True):
    id: int = Field(primary_key=True)
    audio_file: str | None = None
    description: str | None = None
    origin_language: str
    phonetic: str


class PronunciationLink(SQLModel, table=True):
    id: int = Field(primary_key=True)
    pronunciation_id: int = Field(foreign_key='pronunciation.id')
    term: str = Field(foreign_key='term.term', nullable=True, default=None)
    origin_language: str = Field(
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
    origin_language: str = Field(foreign_key='term.origin_language')
    term_level: str | None = None
    partOfSpeech: str
    definition: str


class TermDefinitionTranslation(SQLModel, table=True):
    id: int = Field(primary_key=True)
    translation_language: str
    translation: str
    term_definition_id: int | None = Field(foreign_key='termdefinition.id')


class TermExample(SQLModel, table=True):
    id: int = Field(primary_key=True)
    term: str = Field(foreign_key='term.term')
    origin_language: str = Field(foreign_key='term.origin_language')
    term_definition_id: int | None = Field(
        foreign_key='termdefinition.id', nullable=True, default=None
    )
    example: str


class TermExampleTranslation(SQLModel, table=True):
    id: int = Field(primary_key=True)
    translation_language: str
    translation: str
    term_example_id: int = Field(foreign_key='termexample.id')
