import pytest
from factory.alchemy import SQLAlchemyModelFactory
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from fluentia.apps.user.security import get_password_hash
from fluentia.database import get_session
from fluentia.main import app
from fluentia.settings import Settings
from fluentia.tests.factories.user import UserFactory


@pytest.fixture
def client(session):
    def get_session_override():
        return session

    with TestClient(app) as client:
        app.dependency_overrides[get_session] = get_session_override
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def engine():
    engine = create_engine(Settings().database_url('fluentia_test'))
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def session(engine):
    session = Session(engine)

    def set_session(cls):
        for factory in cls.__subclasses__():
            factory._meta.sqlalchemy_session = session
            set_session(factory)

    set_session(SQLAlchemyModelFactory)
    session.begin()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def user(session, request):
    param = getattr(request, 'param', {})
    password = param.pop('password', 'pass123')

    user = UserFactory(password=get_password_hash(password), **param)

    session.add(user)
    session.commit()
    session.refresh(user)

    user.__dict__['clean_password'] = password
    return user


@pytest.fixture
def token_header(client, user):
    response = client.post(
        '/auth/token',
        data={'username': user.email, 'password': user.clean_password},
    )
    return {'Authorization': f'Bearer {response.json()["access_token"]}'}


@pytest.fixture
def generate_payload():
    def _generate(factory, exclude=None, include=None, **kwargs):
        result = factory.build(**kwargs)
        return result.model_dump(exclude=exclude, include=include)

    return _generate
