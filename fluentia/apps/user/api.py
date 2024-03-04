from fastapi.routing import APIRouter

from fluentia.apps.user.schema import UserSchema, UserSchemaUpdate, UserView
from fluentia.core.api.constants import USER_NOT_AUTHORIZED

user_router = APIRouter(prefix='/user', tags=['user'])


@user_router.post(
    path='/',
    status_code=201,
    response_model=UserView,
    response_description='Dados do novo usuário',
    summary='Criação de um novo usuário.',
    description='Endpoint utilizado para a criação de um novo usuário.',
)
def create_user(user: UserSchema):
    pass


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
def update_user(user_id: int, user: UserSchemaUpdate):
    pass
