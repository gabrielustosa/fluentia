from typing import ClassVar

from pydantic import BaseModel, Field, field_validator, model_validator

from fluentia.apps.term import constants
from fluentia.core.api.highlight import check_text_highlight


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

    @model_validator(mode='before')
    def pre_validation(cls, values):
        if isinstance(values, dict):
            valid_values = dict(
                filter(lambda item: item[1] is not None, values.items())
            )
            attr = [valid_values.get(field) for field in cls.link_fields]
            link_attr = sum(x is not None for x in attr)
            if link_attr == 0:
                raise ValueError('you need to provide at least one object to link.')
            elif 'term' in valid_values:
                if 'origin_language' not in valid_values:
                    raise ValueError(
                        'you need to provide term and origin_language attributes.'
                    )
                if link_attr > 2:
                    raise ValueError('you cannot reference two objects at once.')
            elif link_attr > 1:
                raise ValueError('you cannot reference two objects at once.')
        return values

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
    term_level: constants.TermLevel | None = None
    part_of_speech: constants.PartOfSpeech = Field(examples=(['noun']))
    term_lexical_id: int | None = None
    definition: str = Field(
        examples=['Set of walls, rooms, and roof with specific purpose of habitation.']
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
    term_level: constants.TermLevel | None = None
    definition: str | None = Field(
        examples=['Set of walls, rooms, and roof with specific purpose of habitation.'],
        default=None,
    )
    part_of_speech: str | None = Field(default=None, examples=(['substantivo']))


class TermDefinitionTranslationSchema(BaseModel):
    term_definition_id: int
    language: constants.Language
    meaning: str = Field(examples=['Casa, lar'])
    translation: str = Field(
        examples=['Conjunto de parades, quartos e teto com a finalidade de habitação.'],
    )


class TermDefinitionTranslationUpdate(BaseModel):
    meaning: str | None = Field(default=None, examples=['Casa, lar'])
    translation: str | None = Field(
        default=None,
        examples=['Conjunto de parades, quartos e teto com a finalidade de habitação.'],
    )


def _check_highlight(value: str) -> str:
    if not check_text_highlight(value):
        raise ValueError('term is not highlighted in the example.')
    return value


class TermExampleSchema(TermSchemaBase):
    term_definition_id: int | None = None
    term_lexical_id: int | None = None
    example: str = Field(
        examples=["Yesterday a have lunch in my mother's *house*."],
        description="O termo referido do exemplo será circulado pelos caracteres '*'.",
    )

    example_validation = field_validator('example')(_check_highlight)


class TermExampleView(TermExampleSchema):
    id: int
    translation_language: constants.Language | None = None
    translation_example: str | None = Field(
        default=None,
        examples=['Ontem eu almoçei na *casa* da minha mãe.'],
        description="O termo referido do exemplo será circulado pelos caracteres '*'.",
    )


class TermExampleSchemaUpdate(BaseModel):
    example: str | None = Field(
        default=None,
        examples=["Yesterday a have lunch in my mother's *house*."],
        description="O termo referido do exemplo será circulado pelos caracteres '*'.",
    )

    example_validation = field_validator('example')(_check_highlight)


class TermExampleTranslationSchema(BaseModel):
    term_example_id: int
    language: constants.Language
    translation: str = Field(
        examples=['Ontem eu almoçei na *casa* da minha mãe.'],
        description="O termo referido do exemplo será circulado pelos caracteres '*'.",
    )

    translation_validation = field_validator('translation')(_check_highlight)


class TermExampleTranslationUpdateSchema(BaseModel):
    translation: str | None = Field(
        default=None,
        examples=['Ontem eu almoçei na *casa* da minha mãe.'],
        description="O termo referido do exemplo será circulado pelos caracteres '*'.",
    )

    translation_validation = field_validator('translation')(_check_highlight)


class TermLexicalSchema(TermSchemaBase):
    value: str = Field(examples=['Lar'])
    type: constants.TermLexicalType
    description: str | None = Field(default=None, examples=['verbo - outro nome'])


class TermLexicalView(TermLexicalSchema):
    id: int
