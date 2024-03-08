from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.routing import APIRouter
from sqlmodel import Session as SQLModelSession
from sqlmodel import select

from fluentia.apps.user.models import User
from fluentia.apps.user.schema import UserSchema, UserSchemaUpdate, UserView
from fluentia.apps.user.security import get_current_user, get_password_hash
from fluentia.core.api.constants import USER_NOT_AUTHORIZED
from fluentia.database import get_session

user_router = APIRouter(prefix='/user', tags=['user'])
Session = Annotated[SQLModelSession, Depends(get_session)]


@user_router.post(
    path='/',
    status_code=201,
    response_model=UserView,
    response_description='Dados do novo usuário',
    responses={
        409: {
            'description': 'Email já cadastrado.',
            'content': {
                'application/json': {
                    'example': {'detail': 'email already registered.'}
                }
            },
        },
    },
    summary='Criação de um novo usuário.',
    description='Endpoint utilizado para a criação de um novo usuário.',
)
def create_user(user_schema: UserSchema, session: Session):
    db_user = session.exec(
        select(User).where(User.email == user_schema.email)
    ).first()
    if db_user is not None:
        raise HTTPException(
            status_code=409, detail='email already registered.'
        )

    payload = user_schema.dict()
    password = payload.pop('password')
    hashed_password = get_password_hash(password)
    payload['password'] = hashed_password

    db_user = User(**payload)

    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    return db_user


@user_router.patch(
    path='/{user_id}',
    status_code=200,
    response_model=UserView,
    response_description='Dados atualizados do usuário.',
    responses={
        401: USER_NOT_AUTHORIZED,
        404: {
            'description': 'Usuário especificado não foi encontrado.',
            'content': {
                'application/json': {
                    'example': {'detail': 'user does not exists.'}
                }
            },
        },
    },
    summary='Atualizar um usuário existente.',
    description='Endpoint utilizado para a atualizar um usuário existente.',
)
def update_user(
    user_id: int,
    user_schema: UserSchemaUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session,
):
    if user_id != current_user.id:
        raise HTTPException(
            status_code=401, detail='credentials do not match.'
        )

    for key, value in user_schema.model_dump().items():
        if value is not None:
            setattr(current_user, key, value)

    session.commit()
    session.refresh(current_user)

    return current_user
