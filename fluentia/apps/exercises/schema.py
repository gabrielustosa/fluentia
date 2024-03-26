from datetime import datetime

from pydantic import BaseModel, Field

from fluentia.apps.exercises.constants import ExerciseType
from fluentia.apps.term.schema import TermSchemaBase


class ExerciseSchema(BaseModel):
    amount: int = Field(
        examples=[21], description='Quantidade real de exercicios retornados.'
    )
    exercises: list['ExerciseSchemaView']


class ExerciseSchemaView(BaseModel):
    type: ExerciseType
    url: str = Field(
        examples=['https://example.com/my-exercise/'],
        description='Usada para coletar a url que informará sobre o exercício requirido.',
    )


class WriteSentenceSchema(BaseModel):
    shuffled_sentence: list[str] = Field(
        examples=[['almoçei', 'na', 'Ontem', 'casa', 'da', 'eu', 'mãe minha.']]
    )
    sentence: str = Field(examples=["Yesterday a have lunch in my mother's house."])


class ListenSchema(BaseModel):
    text: str = Field(examples=['Texto pra ouvir.'])
    audio_link: str = Field(examples=['https://example.com/my-audio.mp3'])


class SpeakSchema(BaseModel):
    correct_percentage: float = Field(examples=['75.7'])


class MultipleChoiceSchema(BaseModel):
    header: str = Field(examples=['Cabeçalho das alternativas.'])
    choices: list[str] = Field(
        examples=[['casa', 'fogueira', 'semana', 'avião']],
        description='Será retornada sempre 4 alternativas, incluindo a correta.',
    )


class ExerciseHistory(TermSchemaBase):
    type: ExerciseType
    user_id: int
    created: datetime
    correct: bool
    text_request: str | None = Field(
        default=None, examples=['O que o usuário foi perguntado.']
    )
    text_response: str | None = Field(
        default=None, examples=['O que o usuário respondeu.']
    )
