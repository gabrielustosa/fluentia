from fastapi import APIRouter, Query

from fluentia.apps.card import schema
from fluentia.core.api.constants import (
    CARD_NOT_FOUND,
    CARDSET_NOT_FOUND,
    NOT_ENOUGH_PERMISSION,
    USER_NOT_AUTHORIZED,
)

card_router = APIRouter(prefix='/card', tags=['card'])


@card_router.post(
    path='/set',
    status_code=201,
    response_model=schema.CardSetSchemaView,
    response_description='Conjunto criado.',
    responses={401: USER_NOT_AUTHORIZED},
    summary='Criação de um conjunto de cartões de aprendizado.',
    description='Endpoint utilizado para criar um conjunto de cartões de aprendizado de um usuário.',
)
def create_cardset(cardset: schema.CardSetSchema):
    pass


@card_router.get(
    path='/set',
    status_code=200,
    response_model=list[schema.CardSetSchemaView],
    response_description='Consulta dos conjuntos de cartões.',
    responses={401: USER_NOT_AUTHORIZED, 403: NOT_ENOUGH_PERMISSION},
    summary='Consulta sobre os conjuntos de cartões de aprendizado.',
    description='Endpoint utilizado para consultar todos os conjunto de cartões de aprendizado de um usuário.',
)
def get_cardsets(
    name: str = Query(default='', description='Nome a ser filtrado.')
):
    pass


@card_router.get(
    path='/set/{cardset_id}',
    status_code=200,
    response_model=schema.CardSetSchemaView,
    response_description='Consulta do conjunto de cartões.',
    responses={
        401: USER_NOT_AUTHORIZED,
        403: NOT_ENOUGH_PERMISSION,
        404: CARDSET_NOT_FOUND,
    },
    summary='Consulta sobre um conjunto específico de cartões de aprendizado.',
    description='Endpoint utilizado para consultar um conjunto específico de cartões de aprendizado de um usuário.',
)
def get_cardset(cardset_id: int):
    pass


@card_router.patch(
    path='/set/{cardset_id}',
    status_code=200,
    response_model=schema.CardSetSchemaView,
    response_description='Atualização do conjunto de cartões.',
    responses={
        401: USER_NOT_AUTHORIZED,
        403: NOT_ENOUGH_PERMISSION,
        404: CARDSET_NOT_FOUND,
    },
    summary='Consulta sobre um conjunto específico de cartões de aprendizado.',
    description='Endpoint utilizado para consultar um conjunto específico de cartões de aprendizado de um usuário.',
)
def update_cardset(cardset_id: int, cardset: schema.CardSetSchemaUpdate):
    pass


@card_router.delete(
    path='/set/{cardset_id}',
    status_code=204,
    responses={
        401: USER_NOT_AUTHORIZED,
        403: NOT_ENOUGH_PERMISSION,
        404: CARDSET_NOT_FOUND,
    },
    summary='Deleta um conjunto específico de cartões de aprendizado.',
    description='Endpoint utilizado para deletar um conjunto específico de cartões de aprendizado de um usuário.',
)
def delete_cardset(cardset_id: int):
    pass


@card_router.post(
    path='/{cardset_id}',
    status_code=201,
    response_model=schema.CardSchemaView,
    responses={
        401: USER_NOT_AUTHORIZED,
        403: NOT_ENOUGH_PERMISSION,
        404: CARDSET_NOT_FOUND,
    },
    response_description='Criação do cartão de aprendizado.',
    summary='Cria um cartão de aprendizado.',
    description='Endpoint utilizado para criar um cartão de aprendizado de um conjunto de cartões específico.',
)
def create_card(cardset_id: int, card: schema.CardSchema):
    pass


@card_router.get(
    path='/{cardset_id}',
    status_code=290,
    response_model=list[schema.CardSchemaView],
    responses={
        401: USER_NOT_AUTHORIZED,
        403: NOT_ENOUGH_PERMISSION,
        404: CARDSET_NOT_FOUND,
    },
    response_description='Consulta dos cartões de aprendizado do conjunto.',
    summary='Consulta de cartões de aprendizado.',
    description='Endpoint utilizado para consultar os cartões de aprendizado de um determinado conjunto de cartões.',
)
def get_cards(
    cardset_id: int,
    term: str = Query(default='', description='Termo a ser filtrado.'),
    note: str = Query(default='', description='Anotação a ser filtrada.'),
):
    pass


@card_router.patch(
    path='/{card_id}',
    status_code=200,
    response_model=schema.CardSchemaView,
    responses={
        401: USER_NOT_AUTHORIZED,
        403: NOT_ENOUGH_PERMISSION,
        404: CARD_NOT_FOUND,
    },
    response_description='Atualização do cartão de aprendizado.',
    summary='Atualiza cartões de aprendizado.',
    description='Endpoint utilizado para atualizar um cartão de aprendizado específico.',
)
def update_card(card_id: int, card: schema.CardSchemaUpdate):
    pass


@card_router.delete(
    path='/{card_id}',
    status_code=204,
    responses={
        401: USER_NOT_AUTHORIZED,
        403: NOT_ENOUGH_PERMISSION,
        404: CARD_NOT_FOUND,
    },
    summary='Deleta cartões de aprendizado.',
    description='Endpoint utilizado para deleta um cartão de aprendizado específico.',
)
def delete_card(card_id: int):
    pass
