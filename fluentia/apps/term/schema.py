from typing import ClassVar, Self

from pydantic import BaseModel, Field, model_validator

from fluentia.apps.term import constants


class TermSchemaBase(BaseModel):
    term: str = Field(examples=['Casa'])
    origin_language: constants.Language


class TermSchema(TermSchemaBase):
    meanings: list[str] | None = Field(
        examples=[['house', 'place']], default_factory=list
    )
    lexical: list['TermLexicalSchema'] | None = Field(default_factory=list)
    pronunciations: list['PronunciationView'] | None = Field(default_factory=list)


class PronunciationLinkSchema(BaseModel):
    term: str | None = Field(examples=['Casa'], default=None)
    origin_language: constants.Language | None = None
    term_example_id: int | None = None
    term_lexical_id: int | None = None

    link_fields: ClassVar[set] = {
        'term',
        'origin_language',
        'term_example_id',
        'term_lexical_id',
    }

    @model_validator(mode='after')
    def link_validation(self) -> Self:
        link_attributes = {
            field: getattr(self, field)
            for field in PronunciationLinkSchema.link_fields
            if getattr(self, field, None) is not None
        }
        link_count = len(link_attributes.values())
        if link_count == 0:
            raise ValueError('you need to provide at least one object to link.')
        elif 'term' in link_attributes or 'origin_language' in link_attributes:
            if not all(
                [link_attributes.get('term'), link_attributes.get('origin_language')]
            ):
                raise ValueError(
                    'you need to provide term and origin_language attributes.'
                )
            if link_count > 2:
                raise ValueError('you cannot reference two objects at once.')
        elif link_count > 1:
            raise ValueError('you cannot reference two objects at once.')
        return self

    def model_link_dump(self):
        return super().model_dump(include=self.link_fields, exclude_none=True)


class PronunciationSchema(PronunciationLinkSchema):
    phonetic: str = Field(examples=['/ˈhaʊ.zɪz/'])
    language: constants.Language
    text: str = Field(examples=['Texto que está sendo pronúnciado.'])
    audio_file: str | None = Field(
        default=None, examples=['https://mylink.com/my-audio.mp3']
    )
    description: str | None = Field(examples=['português do brasil'], default=None)

    def model_dump(self, *args, **kwargs):
        exclude = kwargs.pop('exclude', {})
        return super().model_dump(
            *args, **kwargs, exclude={*self.link_fields, *exclude}
        )


class PronunciationView(BaseModel):
    id: int
    phonetic: str = Field(examples=['/ˈhaʊ.zɪz/'])
    language: constants.Language
    text: str = Field(examples=['Texto que está sendo pronúnciado.'])
    audio_file: str | None = Field(
        default=None, examples=['https://mylink.com/my-audio.mp3']
    )
    description: str | None = Field(examples=['português do brasil'], default=None)


class TermPronunciationUpdate(BaseModel):
    phonetic: str | None = Field(default=None, examples=['/ˈhaʊ.zɪz/'])
    description: str | None = Field(examples=['português do brasil'], default=None)
    audio_file: str | None = Field(
        default=None, examples=['https://mylink.com/my-audio.mp3']
    )


class TermDefinitionSchema(TermSchemaBase):
    part_of_speech: constants.PartOfSpeech = Field(examples=(['noun']))
    definition: str = Field(
        examples=['Set of walls, rooms, and roof with specific purpose of habitation.']
    )
    level: constants.Level | None = None
    term_lexical_id: int | None = None
    extra: dict | None = Field(
        default=None,
        examples=[{'syllable': ['ca', 'sa'], 'part': 'en'}],
    )


class TermDefinitionView(TermDefinitionSchema):
    id: int
    translation_language: constants.Language | None = None
    translation_meaning: str | None = Field(examples=['Casa, lar'], default=None)
    translation_definition: str | None = Field(
        default=None,
        examples=['Conjunto de parades, quartos e teto com a finalidade de habitação.'],
    )


class TermDefinitionSchemaUpdate(BaseModel):
    level: constants.Level | None = None
    definition: str | None = Field(
        examples=['Set of walls, rooms, and roof with specific purpose of habitation.'],
        default=None,
    )
    part_of_speech: str | None = Field(default=None, examples=(['substantivo']))
    extra: dict | None = Field(
        default=None,
        examples=[{'syllable': ['ca', 'sa'], 'part': 'en'}],
    )


class TermDefinitionTranslationSchema(BaseModel):
    term_definition_id: int
    language: constants.Language
    meaning: str = Field(examples=['Casa, lar'])
    translation: str = Field(
        examples=['Conjunto de parades, quartos e teto com a finalidade de habitação.'],
    )
    extra: dict | None = Field(
        default=None,
        examples=[{'syllable': ['ca', 'sa'], 'part': 'en'}],
    )


class TermDefinitionTranslationUpdate(BaseModel):
    meaning: str | None = Field(default=None, examples=['Casa, lar'])
    translation: str | None = Field(
        default=None,
        examples=['Conjunto de parades, quartos e teto com a finalidade de habitação.'],
    )
    extra: dict | None = Field(
        default=None,
        examples=[{'syllable': ['ca', 'sa'], 'part': 'en'}],
    )


class ExampleHighlightValidator:
    @model_validator(mode='after')
    def validate_highlight(self) -> Self:
        example = getattr(self, 'example', None) or getattr(self, 'translation')

        intervals = []
        for value in self.highlight:
            if len(value) != 2:
                raise ValueError(
                    'highlight must consist of pairs of numbers representing the start and end positions.'
                )

            v1, v2 = value
            example_len = len(example) - 1
            if v1 > example_len or v2 > example_len:
                raise ValueError(
                    'highlight cannot be greater than the length of the example.'
                )
            if v1 < 0 or v2 < 0:
                raise ValueError(
                    'both highlight values must be greater than or equal to 0.'
                )
            if v1 > v2:
                raise ValueError(
                    'highlight beginning value cannot be greater than the ending value, since it represents the start and end positions.'
                )

            interval = range(v1, v2 + 1)
            if any([i in intervals for i in interval]):
                raise ValueError(
                    'highlight interval must not overlap with any other intervals in highlight list.'
                )
            intervals.extend(interval)

        return self


class TermExampleLinkSchema(BaseModel):
    term: str | None = None
    origin_language: constants.Language | None = None
    term_definition_id: int | None = None
    term_lexical_id: int | None = None

    link_fields: ClassVar[set] = {
        'term',
        'origin_language',
        'term_definition_id',
        'term_lexical_id',
    }

    @model_validator(mode='after')
    def link_validation(self) -> Self:
        link_attributes = {
            field: getattr(self, field)
            for field in TermExampleLinkSchema.link_fields
            if getattr(self, field, None) is not None
        }
        link_count = len(link_attributes.values())
        if link_count == 0:
            raise ValueError('you need to provide at least one object to link.')
        elif 'term' in link_attributes or 'origin_language' in link_attributes:
            if not all(
                [link_attributes.get('term'), link_attributes.get('origin_language')]
            ):
                raise ValueError(
                    'you need to provide term and origin_language attributes.'
                )
            if link_count > 2:
                raise ValueError('you cannot reference two objects at once.')
        elif link_count > 1:
            raise ValueError('you cannot reference two objects at once.')
        return self


class TermExampleSchema(TermExampleLinkSchema, ExampleHighlightValidator):
    language: constants.Language
    example: str = Field(examples=["Yesterday a have lunch in my mother's house."])
    highlight: list[list[int]] = Field(
        examples=[[[4, 8], [11, 16]]],
        description='Highlighted positions in the given sentence where the term appears.',
    )
    level: constants.Level | None = None


class TermExampleView(TermExampleSchema):
    id: int


class TermExampleTranslationSchema(BaseModel, ExampleHighlightValidator):
    term_example_id: int
    language: constants.Language
    translation: str = Field(
        examples=['Ontem eu almoçei na casa da minha mãe.'],
    )
    highlight: list[list[int]] = Field(
        examples=[[[4, 8], [11, 16]]],
        description='Highlighted positions in the given translation sentence where the term appears.',
    )


class TermExampleTranslationView(TermExampleView):
    translation_language: constants.Language | None = None
    translation_example: str | None = Field(
        default=None, examples=['Ontem eu almoçei na casa da minha mãe.']
    )
    translation_highlight: list[list[int]] | None = Field(
        default=None,
        examples=[[[4, 8], [11, 16]]],
        description='Highlighted positions in the given sentence where the term appears.',
    )


class TermLexicalSchema(TermSchemaBase):
    value: str = Field(examples=['Lar'])
    type: constants.TermLexicalType
    extra: dict | None = Field(
        default=None,
        examples=[{'syllable': ['ca', 'sa'], 'part': 'en'}],
    )


class TermLexicalView(TermLexicalSchema):
    id: int


class TermLexicalUpdate(BaseModel):
    value: str | None = Field(default=None, examples=['Lar'])
    extra: dict | None = Field(
        default=None,
        examples=[{'syllable': ['ca', 'sa'], 'part': 'en'}],
    )
