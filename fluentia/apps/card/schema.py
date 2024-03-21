from datetime import datetime

from pydantic import BaseModel, Field

from fluentia.apps.term.constants import Language
from fluentia.apps.term.schema import TermSchemaBase


class CardSetSchema(BaseModel):
    name: str = Field(examples=['Palavras novas'])
    description: str | None = Field(
        default=None, examples=['Um cartão sobre palavras novas.']
    )
    language: Language | None = None
    tags: list[str] | None = Field(
        default_factory=list, examples=[['casa', 'substantivo', 'viagem']]
    )


class CardSetSchemaView(CardSetSchema):
    id: int
    created: datetime
    modified: datetime


class CardSetSchemaUpdate(BaseModel):
    name: str | None = Field(examples=['Palavras novas'], default=None)
    description: str | None = Field(
        default=None, examples=['Um cartão sobre palavras novas.']
    )
    language: Language | None = None
    tags: list[str] | None = Field(
        default_factory=list, examples=[['casa', 'substantivo', 'viagem']]
    )


class CardSchema(TermSchemaBase):
    cardset_id: int
    note: str | None = Field(
        default=None,
        examples=['Casa pode ser um lugar grande.'],
        description='Pode usar HTML para escrevar as notas.',
    )
    tags: list[str] | None = Field(
        default_factory=list, examples=[['casa', 'substantivo', 'viagem']]
    )


class CardSchemaView(CardSchema):
    id: int
    created: datetime
    modified: datetime
    tags: list[str] | None = Field(
        default_factory=list, examples=[['casa', 'substantivo', 'viagem']]
    )


class CardSchemaUpdate(BaseModel):
    note: str | None = Field(default=None, examples=['Casa pode ser um lugar grande.'])
    tags: list[str] | None = Field(
        default_factory=list, examples=[['casa', 'substantivo', 'viagem']]
    )
