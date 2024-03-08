from unittest.mock import MagicMock

import pytest
from factory.alchemy import SQLAlchemyModelFactory
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from fluentia.apps.user.security import get_password_hash
from fluentia.database import get_session
from fluentia.main import app
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
def session():
    engine = create_engine(
        'sqlite:///tests.db',
    )
    SQLModel.metadata.create_all(engine)
    session = Session(engine)
    for factory in SQLAlchemyModelFactory.__subclasses__():
        factory._meta.sqlalchemy_session = session

    yield session

    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def user(session):
    password = 'test'
    user = UserFactory(password=get_password_hash(password))

    session.add(user)
    session.commit()
    session.refresh(user)

    mock = MagicMock(**user.model_dump(), clean_password=password)
    mock.mock_add_spec(spec=user.model_dump().keys(), spec_set=True)
    return mock


@pytest.fixture
def token_header(client, user):
    response = client.post(
        '/auth/token',
        data={'username': user.email, 'password': user.clean_password},
    )
    return {'Authorization': f'Bearer {response.json()["access_token"]}'}
