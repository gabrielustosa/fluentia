from fastapi import APIRouter, Query, UploadFile

from fluentia.apps.exercises import schema
from fluentia.apps.exercises.constants import ExerciseType
from fluentia.apps.term.constants import Language, TermLevel
from fluentia.core.api.constants import (
    CARDSET_NOT_FOUND,
    NOT_ENOUGH_PERMISSION,
    TERM_NOT_FOUND,
    USER_NOT_AUTHORIZED,
)

exercise_router = APIRouter(prefix='/term/exercise', tags=['exercises'])


@exercise_router.get(
    path='/',
    status_code=200,
    response_model=schema.ExerciseSchema,
    response_description='Lista dos respectivos exercícios solicitados.',
    responses={404: CARDSET_NOT_FOUND},
    summary='Consulta exercícios sobre termos disponíveis.',
    description="""
    <br> Endpoint para retornar exercícios sobre termos. Os exercícios serão montados com termos aleatórios, a menos que seja específicado o cardset_id.
    <br> Os tipos de exercícios disponíveis são:
    <br> write-sentence: O usuário receberá uma frase na sua tradução embaralhada junto a frase na sua linguagem de origem e terá que reordenar a frase.
    <br> listen-term: O usuário irá escutar um termo e irá digitar o que escutou.
    <br> listen-sentence: O usuario irá escutar uma frase relacionada a um termo e irá digitar o que escutou.
    <br> speak-term: O usuário receberá um termo e ele terá que pronúnciar o termo.
    <br> speak-sentence: O usuário receberá uma frase relacionada a um termo e ele terá que pronúnciar o termo.
    <br> mchoice-term: O usuário receberá uma frase com um termo atrelado faltando, no qual será necessário escolher entre as opções qual completa o espaço.
    <br> mchoice-definition: O usuário receberá uma definição com um termo atrelado, no qual será necessário escolher entre as opções qual dos termos é a definição.
    <br> random: Os exercícios virão aleatoriamente.
    """,
)
def get_exercises(
    exerciseType: ExerciseType,
    origin_language: Language,
    amount: int = Query(default=10, le=256, ge=1, description='Número de exercícios.'),
    term_level: TermLevel | None = Query(
        default=None, description='Filtar por dificuldade do termo.'
    ),
    translation_language: Language | None = None,
    cardset_id: int | None = Query(
        default=None, description='Filtrar por conjunto de cartas.'
    ),
):
    pass


@exercise_router.get(
    path='/write-sentece/{example_id}',
    status_code=200,
    response_model=schema.WriteSentenceSchema,
    response_description='Frase normal e embaralhada sobre o termo.',
    responses={404: TERM_NOT_FOUND},
    summary='Exercício sobre reodernar frases.',
    description="""
    <br> Endpoint que retorna uma frase embaralhada relacionada a um termo e o usuário terá que reordenar a frase na ordem correta.
    <br> As frases embaralhadas e normais poderão ser no idioma original para o idioma traduzido ou do idioma traduzido para o idioma original. 
    """,
)
def write_sentece(example_id: int):
    pass


@exercise_router.get(
    path='/listen-term',
    status_code=200,
    response_model=schema.ListenSchema,
    response_description='Link para o aúdio da pronúncia do termo.',
    responses={404: TERM_NOT_FOUND},
    summary='Exercício sobre escuta de pronúncia de termos.',
    description='Endpoint que retorna a pronúncia em forma de aúdio de um texto para o usuário responder qual o termo correspondente.',
)
def listen_term(term: str, origin_language: Language):
    pass


@exercise_router.get(
    path='/listen-sentence/{example_id}',
    status_code=200,
    response_model=schema.ListenSchema,
    response_description='Link para o aúdio da pronúncia de uma frase.',
    responses={404: TERM_NOT_FOUND},
    summary='Exercício sobre escuta de pronúncia de frase.',
    description='Endpoint que retorna a pronúncia em forma de aúdio de uma frase relacionada ao termo para o usuário escrever a frase corretamente.',
)
def listen_sentence(example_id: int):
    pass


@exercise_router.get(
    path='/speak-term',
    status_code=200,
    response_model=schema.SpeakSchema,
    response_description='Link que recebera a pronúncia e irá avalia-la.',
    responses={401: USER_NOT_AUTHORIZED, 404: TERM_NOT_FOUND},
    summary='Exercício sobre pronúnciação de termos.',
    description='Endpoint que retorna um link para enviar a pronúncia em forma de aúdio de um usuário sobre um termo.',
)
def speak_term(term: str, origin_language: Language):
    pass


@exercise_router.get(
    path='/speak-sentence/{example_id}',
    status_code=200,
    response_model=schema.SpeakSchema,
    response_description='Link que recebera a pronúncia e irá avalia-la.',
    responses={401: USER_NOT_AUTHORIZED, 404: TERM_NOT_FOUND},
    summary='Exercício sobre pronúnciação de termos.',
    description='Endpoint que retorna um link para enviar a pronúncia em forma de aúdio de um usuário sobre um termo.',
)
def speak_sentence(example_id: int):
    pass


@exercise_router.post(
    path='/speak/check/{exercise_speak_id}',
    status_code=200,
    response_model=schema.SpeakCheckSchema,
    response_description='Porcentagem de acerto de prónuncia do texto selecionado.',
    responses={401: USER_NOT_AUTHORIZED, 404: TERM_NOT_FOUND},
    summary='Verificar acerto de pronúncia de texto.',
    description='Endpoint que faz uma verificação de pronúncia através do envio do arquivo do aúdio e faz a comparação com o texto requerido.',
)
def speak_check(exercise_speak_id: int, audio: UploadFile):
    pass


@exercise_router.get(
    path='/mchoice-term',
    status_code=200,
    response_model=schema.MultipleChoiceSchema,
    response_description='Questão e alternativas do exercício.',
    responses={404: TERM_NOT_FOUND},
    summary='Exercício de multipla escolha sobre termos.',
    description='Endpoint que retorará uma frase com um termo atrelado faltando, no qual será necessário escolher entre as opções qual completa o espaço na frase.',
)
def mchoice_term(term: str, origin_language: Language):
    pass


@exercise_router.get(
    path='/mchoice-definition/{example_id}',
    status_code=200,
    response_model=schema.MultipleChoiceSchema,
    response_description='Questão e alternativas do exercício.',
    responses={404: TERM_NOT_FOUND},
    summary='Exercício de multipla escolha sobre definições de termos.',
    description='Endpoint que retorará uma definição com um termo atrelado, no qual será necessário escolher entre as opções qual dos termos é a definição.',
)
def mchoice_sentence(example_id: int):
    pass


@exercise_router.post(
    path='/history',
    status_code=201,
    response_model=schema.ExerciseHistory,
    response_description='Criação do histórico do exercício realizado pelo usuário.',
    responses={
        401: USER_NOT_AUTHORIZED,
        403: NOT_ENOUGH_PERMISSION,
        404: TERM_NOT_FOUND,
    },
    summary='Adicionar ao histórico de exercícios do usuário.',
    description="""
    <br> Endpoint utilizado para armazenar o valor resultante do exercício realizado pelo usuário.
    <br> Deve ser utilizado toda vez que o usuário responder um exercício.
    """,
)
def create_history(history: schema.ExerciseHistory):
    pass
