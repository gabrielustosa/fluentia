from pydantic import BaseModel, Field, HttpUrl

from fluentia.apps.term import constants


class TermSchemaBase(BaseModel):
    term: str = Field(examples=['Casa'])
    origin_language: constants.Language


class TermSchema(TermSchemaBase):
    meanings: list[str] = Field(examples=[['house', 'place']])
    lexical: list['TermLexicalSchema'] | None = Field(default_factory=list)
    pronunciations: list['TermPronunciationSchema'] | None = Field(default_factory=list)


class TermPronunciationSchema(BaseModel):
    audio_file: HttpUrl | None = Field(
        default=None, examples=['https://mylink.com/my-audio.mp3']
    )
    phonetic: str = Field(examples=['/ˈhaʊ.zɪz/'])
    description: str | None = Field(examples=['português do brasil'], default=None)
    translation_language: constants.Language | None = None
    term: str | None = Field(examples=['Casa'], default=None)
    origin_language: constants.Language | None = None
    term_example_id: int | None = None
    term_lexical_id: int | None = None


class TermPronunciationView(TermPronunciationSchema):
    id: int


class TermPronunciationUpdate(BaseModel):
    phonetic: str | None = Field(default=None, examples=['/ˈhaʊ.zɪz/'])
    description: str | None = Field(examples=['português do brasil'], default=None)
    audio_file: HttpUrl | None = Field(
        default=None, examples=['https://mylink.com/my-audio.mp3']
    )


class TermDefinitionSchema(TermSchemaBase):
    term_level: constants.TermLevel | None = None
    partOfSpeech: constants.PartOfSpeech | None = Field(
        default=None, examples=(['noun'])
    )
    translation_language: constants.Language | None = None
    meaning: str = Field(examples=['Casa, lar'])
    translation: str | None = Field(
        default=None,
        examples=['Conjunto de parades, quartos e teto com a finalidade de habitação.'],
    )
    definition: str = Field(
        examples=['Set of walls, rooms, and roof with specific purpose of habitation.']
    )


class TermDefinitionView(TermDefinitionSchema):
    id: int


class TermDefinitionSchemaUpdate(BaseModel):
    term_level: constants.TermLevel | None = None
    partOfSpeech: str | None = Field(default=None, examples=(['substantivo']))
    meaning: str | None = Field(default=None, examples=['Casa, lar'])
    translation: str | None = Field(
        default=None,
        examples=['Conjunto de parades, quartos e teto com a finalidade de habitação.'],
    )
    definition: str | None = Field(
        examples=['Set of walls, rooms, and roof with specific purpose of habitation.'],
        default=None,
    )


class TermExampleSchema(TermSchemaBase):
    term_definition_id: int | None = None
    translation_language: constants.Language | None = None
    example_translation: str | None = Field(
        default=None,
        examples=['Ontem eu almoçei na **casa** da minha mãe.'],
        description="O termo referido do exemplo será circulado pelos caracteres '**'.",
    )
    example: str = Field(
        examples=["Yesterday a have lunch in my mother's **house**."],
        description="O termo referido do exemplo será circulado pelos caracteres '**'.",
    )


class TermExampleView(TermDefinitionSchema):
    id: int


class TermExampleSchemaUpdate(BaseModel):
    example_translation: str | None = Field(
        default=None,
        examples=['Ontem eu almoçei na **casa** da minha mãe.'],
        description="O termo referido do exemplo será circulado pelos caracteres '*'.",
    )
    example: str | None = Field(
        default=None,
        examples=["Yesterday a have lunch in my mother's **house**."],
        description="O termo referido do exemplo será circulado pelos caracteres '*'.",
    )


class TermLexicalSchema(TermSchemaBase):
    value: str = Field(examples=['Lar'])
    type: constants.TermLexicalType
    description: str | None = Field(default=None, examples=['verbo - outro nome'])


class TermLexicalSchemaView(TermLexicalSchema):
    id: int
