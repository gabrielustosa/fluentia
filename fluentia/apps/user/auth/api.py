from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session as SQLModelSession
from sqlmodel import select

from fluentia.apps.user.auth.schema import Token
from fluentia.apps.user.models import User
from fluentia.apps.user.security import (
    create_access_token,
    get_current_user,
    verify_password,
)
from fluentia.database import get_session

auth_router = APIRouter(prefix='/auth', tags=['auth'])
OAuth2Form = Annotated[OAuth2PasswordRequestForm, Depends()]
Session = Annotated[SQLModelSession, Depends(get_session)]


@auth_router.post(
    path='/token',
    status_code=201,
    response_model=Token,
    response_description='Login com o token de autenticação.',
    responses={
        400: {
            'description': 'E-mail ou senha estão incorretos.',
            'content': {
                'application/json': {
                    'example': {'detail': 'incorret e-mail or password.'}
                }
            },
        },
    },
    summary='Endpoint para solicitar o token de autenticação do usuário.',
    description="""
        Endpoint para a solicitação do token JWT para autenticação do usuário.
    """,
)
def login_for_access_token(
    form_data: OAuth2Form,
    session: Session,
):
    user = session.exec(select(User).where(User.email == form_data.username)).first()

    if not user:
        raise HTTPException(status_code=400, detail='Incorrect email or password')

    if not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=400, detail='Incorrect email or password')

    access_token = create_access_token(data={'sub': user.email})

    return {'access_token': access_token, 'token_type': 'bearer'}


@auth_router.post(
    path='/refresh_token',
    status_code=201,
    response_model=Token,
    response_description='Novo token de autenticação do usuário.',
    summary='Endpoint para solicitar um novo token de autenticação do usuário.',
    description="""
        Endpoint para a solicitação de um novo token JWT para autenticação do usuário.
    """,
)
def refresh_access_token(user: Annotated[User, Depends(get_current_user)]):
    new_access_token = create_access_token(data={'sub': user.email})

    return {'access_token': new_access_token, 'token_type': 'bearer'}
