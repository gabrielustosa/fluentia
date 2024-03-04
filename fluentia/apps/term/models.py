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


class TermPronunciation(SQLModel, table=True):
    id: int = Field(primary_key=True)
    term: str = Field(foreign_key='term.term')
    origin_language: str = Field(foreign_key='term.origin_language')
    audio_file: str = Field(nullable=True)
    description: str = Field(nullable=True)
    translation_language: str = Field(nullable=True)
    term_example_id: int = Field(foreign_key='termexample.id', nullable=True)
    phonetic: str


class TermDefinition(SQLModel, table=True):
    id: int = Field(primary_key=True)
    term: str = Field(foreign_key='term.term')
    origin_language: str = Field(foreign_key='term.origin_language')
    term_level: str = Field(nullable=True)
    partOfSpeech: str = Field(nullable=True)
    translation_language: str = Field(nullable=True)
    translation: str = Field(nullable=True)
    definition: str


class TermExample(SQLModel, table=True):
    id: int = Field(primary_key=True)
    term: str = Field(foreign_key='term.term')
    origin_language: str = Field(foreign_key='term.origin_language')
    term_definition_id: int = Field(foreign_key='termdefinition.id', nullable=True)
    example_translation: str = Field(nullable=True)
    translation_language: str = Field(nullable=True)
    example: str
