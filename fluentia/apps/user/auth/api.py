from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from fluentia.apps.user.auth.schema import Token

auth_router = APIRouter(prefix='/auth', tags=['auth'])


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
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    pass


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
def refresh_access_token(user):
    pass
