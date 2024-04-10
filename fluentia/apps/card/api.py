from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session as SQLModelSession

from fluentia.apps.card import schema
from fluentia.apps.card.models import Card, CardSet
from fluentia.apps.term.models import TermDefinitionTranslation
from fluentia.apps.user.models import User
from fluentia.apps.user.security import get_current_user
from fluentia.core.api.constants import (
    CARD_NOT_FOUND,
    CARDSET_NOT_FOUND,
    USER_NOT_AUTHORIZED,
)
from fluentia.core.model.shortcut import get_object_or_404
from fluentia.database import get_session

card_router = APIRouter(prefix='/card', tags=['card'])

Session = Annotated[SQLModelSession, Depends(get_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@card_router.post(
    path='/set',
    status_code=201,
    response_model=schema.CardSetSchemaView,
    response_description='Conjunto criado.',
    responses={401: USER_NOT_AUTHORIZED},
    summary='Criação de um conjunto de cartões de aprendizado.',
    description='Endpoint utilizado para criar um conjunto de cartões de aprendizado de um usuário.',
)
def create_cardset(
    current_user: CurrentUser,
    session: Session,
    cardset_schema: schema.CardSetSchema,
):
    return CardSet.create(
        session,
        user_id=current_user.id,
        **cardset_schema.model_dump(),
    )


@card_router.get(
    path='/set/{cardset_id}',
    status_code=200,
    response_model=schema.CardSetSchemaView,
    response_description='Consulta do conjunto de cartões.',
    responses={
        401: USER_NOT_AUTHORIZED,
        404: CARDSET_NOT_FOUND,
    },
    summary='Consulta sobre um conjunto específico de cartões de aprendizado.',
    description='Endpoint utilizado para consultar um conjunto específico de cartões de aprendizado de um usuário.',
)
def get_cardset(current_user: CurrentUser, session: Session, cardset_id: int):
    return get_object_or_404(CardSet, session, id=cardset_id, user_id=current_user.id)


@card_router.get(
    path='/set',
    status_code=200,
    response_model=list[schema.CardSetSchemaView],
    response_description='Consulta dos conjuntos de cartões.',
    responses={401: USER_NOT_AUTHORIZED},
    summary='Consulta sobre os conjuntos de cartões de aprendizado.',
    description='Endpoint utilizado para consultar todos os conjunto de cartões de aprendizado de um usuário.',
)
def list_cardset(
    current_user: CurrentUser,
    session: Session,
    name: str | None = Query(default=None, description='Nome a ser filtrado.'),
):
    return CardSet.list(session, current_user.id, name)


@card_router.patch(
    path='/set/{cardset_id}',
    status_code=200,
    response_model=schema.CardSetSchemaView,
    response_description='Atualização do conjunto de cartões.',
    responses={
        401: USER_NOT_AUTHORIZED,
        404: CARDSET_NOT_FOUND,
    },
    summary='Consulta sobre um conjunto específico de cartões de aprendizado.',
    description='Endpoint utilizado para consultar um conjunto específico de cartões de aprendizado de um usuário.',
)
def update_cardset(
    current_user: CurrentUser,
    session: Session,
    cardset_id: int,
    cardset_schema: schema.CardSetSchemaUpdate,
):
    db_cardset = get_object_or_404(
        CardSet,
        session,
        id=cardset_id,
        user_id=current_user.id,
    )

    return CardSet.update(
        session,
        db_cardset,
        **cardset_schema.model_dump(exclude_none=True),
    )


@card_router.delete(
    path='/set/{cardset_id}',
    status_code=204,
    responses={
        401: USER_NOT_AUTHORIZED,
        404: CARDSET_NOT_FOUND,
    },
    summary='Deleta um conjunto específico de cartões de aprendizado.',
    description='Endpoint utilizado para deletar um conjunto específico de cartões de aprendizado de um usuário.',
)
def delete_cardset(
    current_user: CurrentUser,
    session: Session,
    cardset_id: int,
):
    db_cardset = get_object_or_404(
        CardSet,
        session,
        id=cardset_id,
        user_id=current_user.id,
    )

    CardSet.delete(session, db_cardset)


@card_router.post(
    path='',
    status_code=201,
    response_model=schema.CardSchemaView,
    responses={
        401: USER_NOT_AUTHORIZED,
        404: CARDSET_NOT_FOUND,
    },
    response_description='Criação do cartão de aprendizado.',
    summary='Cria um cartão de aprendizado.',
    description='Endpoint utilizado para criar um cartão de aprendizado de um conjunto de cartões específico.',
)
def create_card(
    current_user: CurrentUser,
    session: Session,
    card_schema: schema.CardSchema,
):
    cardset = get_object_or_404(
        CardSet,
        session,
        id=card_schema.cardset_id,
        user_id=current_user.id,
    )

    if not card_schema.note and cardset.language:
        meanings = TermDefinitionTranslation.list_meaning(
            session,
            card_schema.term,
            card_schema.origin_language,
            cardset.language,
        )
        card_schema.note = ','.join(meanings)

    return Card.create(
        session,
        user_id=current_user.id,
        **card_schema.model_dump(),
    )


@card_router.get(
    path='{card_id}',
    status_code=200,
    response_model=schema.CardSchemaView,
    responses={
        401: USER_NOT_AUTHORIZED,
        404: CARDSET_NOT_FOUND,
    },
    response_description='Consulta do cartão solicitado.',
    summary='Consulta de cartões de aprendizado.',
    description='Endpoint utilizado para consultar cartões.',
)
def get_card(current_user: CurrentUser, session: Session, card_id: int):
    return Card.get_or_404(session, card_id, current_user.id)


@card_router.get(
    path='/set/cards/{cardset_id}',
    status_code=200,
    response_model=list[schema.CardSchemaView],
    responses={
        401: USER_NOT_AUTHORIZED,
        404: CARDSET_NOT_FOUND,
    },
    response_description='Consulta dos cartões de aprendizado do conjunto.',
    summary='Consulta de cartões de aprendizado de um conjunto específico.',
    description='Endpoint utilizado para consultar os cartões de aprendizado de um determinado conjunto de cartões.',
)
def list_cards(
    current_user: CurrentUser,
    session: Session,
    cardset_id: int,
    term: str | None = Query(default=None, description='Filtrar por termo.'),
    note: str | None = Query(default=None, description='Filtrar por anotação.'),
):
    get_object_or_404(
        CardSet,
        session,
        id=cardset_id,
        user_id=current_user.id,
    )

    return Card.list(session, cardset_id, term, note)


@card_router.patch(
    path='/{card_id}',
    status_code=200,
    response_model=schema.CardSchemaView,
    responses={
        401: USER_NOT_AUTHORIZED,
        404: CARD_NOT_FOUND,
    },
    response_description='Atualização do cartão de aprendizado.',
    summary='Atualiza cartões de aprendizado.',
    description='Endpoint utilizado para atualizar um cartão de aprendizado específico.',
)
def update_card(
    current_user: CurrentUser,
    session: Session,
    card_id: int,
    card_schema: schema.CardSchemaUpdate,
):
    db_card = Card.get_or_404(session, card_id, current_user.id)

    return Card.update(session, db_card, **card_schema.model_dump())


@card_router.delete(
    path='/{card_id}',
    status_code=204,
    responses={
        401: USER_NOT_AUTHORIZED,
        404: CARD_NOT_FOUND,
    },
    summary='Deleta cartões de aprendizado.',
    description='Endpoint utilizado para deleta um cartão de aprendizado específico.',
)
def delete_card(
    current_user: CurrentUser,
    session: Session,
    card_id: int,
):
    db_card = Card.get_or_404(session, card_id, current_user.id)

    Card.delete(session, db_card)
