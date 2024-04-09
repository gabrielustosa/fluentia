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


class CardSetSchemaView(CardSetSchema):
    id: int
    created_at: datetime
    modified_at: datetime | None = None


class CardSetSchemaUpdate(BaseModel):
    name: str | None = Field(examples=['Palavras novas'], default=None)
    description: str | None = Field(
        default=None, examples=['Um cartão sobre palavras novas.']
    )
    language: Language | None = None


class CardSchema(TermSchemaBase):
    cardset_id: int
    note: str | None = Field(
        default=None,
        examples=['Casa pode ser um lugar grande.'],
        description='Pode usar HTML para escrevar as notas.',
    )


class CardSchemaView(CardSchema):
    id: int
    created_at: datetime
    modified_at: datetime | None = None


class CardSchemaUpdate(BaseModel):
    note: str | None = Field(default=None, examples=['Casa pode ser um lugar grande.'])
