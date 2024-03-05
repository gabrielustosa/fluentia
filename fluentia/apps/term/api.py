from fastapi import APIRouter, Query

from fluentia.apps.term import constants, schema
from fluentia.core.api.constants import (
    NOT_ENOUGH_PERMISSION,
    TERM_NOT_FOUND,
    USER_NOT_AUTHORIZED,
)

term_router = APIRouter(prefix='/term', tags=['term'])


@term_router.post(
    path='/',
    status_code=201,
    response_model=schema.TermSchemaBase,
    response_description='O termo criado é retornado.',
    responses={
        409: {
            'description': 'O termo enviado já existe nesta linguagem.',
            'content': {
                'application/json': {
                    'example': {
                        'detail': 'term already registered in this language.'
                    }
                }
            },
        },
        401: USER_NOT_AUTHORIZED,
        403: NOT_ENOUGH_PERMISSION,
    },
    summary='Criação de um novo termo.',
    description="""
        <br> Endpoint utilizado para a criação de um termo, palavra ou expressão de um certo idioma.
        <br> A princípio, poderá existir somente um termo com o mesmo valor de expressão de texto para cada idioma.
    """,
)
def create_term(term: schema.TermSchemaBase):
    pass


@term_router.get(
    path='/',
    status_code=200,
    response_model=schema.TermSchema,
    response_description='O resultado da consulta do termo especificado.',
    responses={404: TERM_NOT_FOUND},
    summary='Consulta de um termo existente.',
    description='Endpoint utilizado para a consultar um termo, palavra ou expressão específica de um certo idioma.',
)
def get_term(
    term: str,
    origin_language: constants.Language,
    translation_language: constants.Language
    | None = Query(
        default=None,
        description='Se existir tradução para tal linguagem, virá os significados do termo no idioma referido.',
    ),
    lexical: bool = Query(
        default=None,
        description='Caso seja verdadeiro, informações como sinônimos, antônimos, pronúncias e conjugações relacionados ao termo serão incluídos na resposta.',
    ),
):
    pass


@term_router.get(
    path='/search',
    status_code=200,
    response_model=list[schema.TermSchema],
    response_description='O resultado da consulta dos termos que batem com o termo.',
    summary='Procura de termos.',
    description='Endpoint utilizado para procurar um termo, palavra ou expressão específica de um certo idioma de acordo com o valor enviado.',
)
def search_terms(
    text: str,
    origin_language: constants.Language,
):
    pass


@term_router.post(
    path='/pronunciation',
    status_code=201,
    response_model=schema.TermPronunciationView,
    response_description='A pronúncia para o modelo referenciado é criada.',
    responses={
        404: TERM_NOT_FOUND,
        403: NOT_ENOUGH_PERMISSION,
        401: USER_NOT_AUTHORIZED,
    },
    summary='Criação de pronúncia.',
    description='Endpoint utilizado para criar pronúncias com áudio, fonemas e descrição sobre um determinado modelo.',
)
def create_pronunciation(
    pronunciation: schema.TermPronunciationSchema,
    model: constants.PronunciationModel,
):
    pass


@term_router.post(
    path='/pronunciation/link',
    status_code=201,
    response_model=schema.TermPronunciationView,
    response_description='A pronúncia para o modelo referenciado é ligada.',
    responses={
        404: TERM_NOT_FOUND,
        403: NOT_ENOUGH_PERMISSION,
        401: USER_NOT_AUTHORIZED,
    },
    summary='Ligar de pronúncia.',
    description='Endpoint utilizado para ligar pronúncias já existentes em um determinado modelo.',
)
def link_pronunciation(
    pronunciation: schema.TermPronunciationLink,
    model: constants.PronunciationModel,
):
    pass


@term_router.get(
    path='/pronunciation',
    status_code=200,
    response_model=list[schema.TermPronunciationView],
    response_description='A consulta das pronúncias do modelo especificado.',
    responses={404: TERM_NOT_FOUND},
    summary='Consulta das pronúncias.',
    description='Endpoint utilizado para consultar pronúncias com áudio, fonemas e descrição sobre um determinado modelo.',
)
def get_pronunciation(
    model: constants.PronunciationModel,
    term: str | None = None,
    origin_language: constants.Language | None = None,
    term_example_id: int | None = None,
    term_lexical_id: int | None = None,
):
    pass


@term_router.patch(
    path='/pronunciation/{pronunciation_id}',
    status_code=200,
    response_model=schema.TermPronunciationView,
    response_description='Atualizar a pronúncia do modelo especificado.',
    responses={
        404: TERM_NOT_FOUND,
        403: NOT_ENOUGH_PERMISSION,
        401: USER_NOT_AUTHORIZED,
    },
    summary='Atualização das pronúncias.',
    description='Endpoint utilizado para atualizar o áudio, fonemas ou descrição de uma pronúncia sobre um determinado modelo.',
)
def update_pronuncation(
    pronunciation_id: int, pronunciation: schema.TermPronunciationUpdate
):
    pass


@term_router.post(
    path='/definition',
    status_code=201,
    response_model=schema.TermDefinitionView,
    response_description='A criação da definição do termo especificado.',
    responses={
        404: TERM_NOT_FOUND,
        403: NOT_ENOUGH_PERMISSION,
        401: USER_NOT_AUTHORIZED,
    },
    summary='Criação das definições de um termo.',
    description='Endpoint utilizado para criar uma definição de um certo termo de um determinado idioma.',
)
def create_definition(definition: schema.TermDefinitionSchema):
    pass


@term_router.get(
    path='/definition',
    status_code=200,
    response_model=list[schema.TermDefinitionView],
    response_description='A consulta das definições de um termo específicado.',
    responses={404: TERM_NOT_FOUND},
    summary='Consulta das definições de um termo.',
    description='Endpoint utilizado para consultar as definição de um certo termo de um determinado idioma, sendo possível escolher a linguagem de tradução.',
)
def get_definition(
    term: str,
    origin_language: constants.Language,
    translation_language: constants.Language
    | None = Query(
        default=None,
        description='Caso houver definições para a tradução requirida ela será retornada.',
    ),
    partOfSpeech: constants.PartOfSpeech
    | None = Query(default=None, description='Filtrar por classe gramatical.'),
    term_level: constants.TermLevel
    | None = Query(default=None, description='Filtrar por level do termo.'),
):
    pass


@term_router.patch(
    path='/definition/{definition_id}',
    status_code=200,
    response_model=schema.TermDefinitionView,
    response_description='Atualização das definições do termo.',
    responses={
        404: TERM_NOT_FOUND,
        403: NOT_ENOUGH_PERMISSION,
        401: USER_NOT_AUTHORIZED,
    },
    summary='Atualizar as definições de um termo.',
    description='Endpoint utilizado para atualizar as definição de um certo termo de um determinado idioma.',
)
def update_definition(
    definition_id: int, definition: schema.TermDefinitionSchemaUpdate
):
    pass


@term_router.post(
    path='/example',
    status_code=201,
    response_model=schema.TermExampleView,
    response_description='Criação de um exemplo para determinado termo ou definição.',
    responses={
        404: TERM_NOT_FOUND,
        403: NOT_ENOUGH_PERMISSION,
        401: USER_NOT_AUTHORIZED,
    },
    summary='Criação de exemplos sobre um termo.',
    description='Endpoint utilizado para criação de exemplos para termos ou definições.',
)
def create_example(example: schema.TermExampleSchema):
    pass


@term_router.get(
    path='/example',
    status_code=200,
    response_model=list[schema.TermExampleView],
    response_description='Consulta de um exemplo para determinado termo.',
    responses={404: TERM_NOT_FOUND},
    summary='Consulta de exemplos sobre um termo.',
    description='Endpoint utilizado para consultar exemplos de termos ou definições.',
)
def get_example(
    term: str,
    origin_language: constants.Language,
    translation_language: constants.Language
    | None = Query(
        default=None,
        description='Caso houver exemplos para a tradução requirida ela será retornada.',
    ),
    term_definition_id: int
    | None = Query(
        default=None,
        description='Filtrar por exemplos sobre a definição de um termo.',
    ),
):
    pass


@term_router.patch(
    path='/example/{example_id}',
    status_code=200,
    response_model=schema.TermExampleView,
    response_description='Atualização do exemplo do termo ou definição.',
    responses={
        404: TERM_NOT_FOUND,
        403: NOT_ENOUGH_PERMISSION,
        401: USER_NOT_AUTHORIZED,
    },
    summary='Atualizar exemplos.',
    description='Endpoint para atualizar um exemplo ligado a um termo ou definição.',
)
def update_example(example_id: int, example: schema.TermExampleSchemaUpdate):
    pass


@term_router.post(
    path='/lexical',
    status_code=201,
    response_model=schema.TermLexicalSchemaView,
    response_description='Criação de uma relação lexical',
    responses={
        404: TERM_NOT_FOUND,
        403: NOT_ENOUGH_PERMISSION,
        401: USER_NOT_AUTHORIZED,
    },
    summary='Criação de relação de uma relação lexical.',
    description='Endpoint utilizado para criação de relações lexicais entre termos, sendo elas sinônimos, antônimos e conjugações.',
)
def post_lexical(lexical: schema.TermLexicalSchema):
    pass


@term_router.get(
    path='/lexical',
    status_code=200,
    response_model=list[schema.TermLexicalSchemaView],
    responses={},
    summary='Consulta de relação de uma relação lexical.',
    description='Endpoint utilizado para consultar de relações lexicais entre termos, sendo elas sinônimos, antônimos e conjugações.',
)
def get_lexical(
    term: str,
    origin_language: constants.Language,
    type: constants.TermLexicalType,
):
    pass
