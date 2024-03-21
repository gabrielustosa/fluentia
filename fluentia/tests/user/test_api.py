from sqlmodel import select

from fluentia.apps.user.models import User
from fluentia.main import app
from fluentia.tests.factories.user import UserFactory

create_user_url = app.url_path_for('create_user')


def update_user_url(user_id: int):
    return app.url_path_for('update_user', user_id=user_id)


def test_create_user(client, session):
    payload = {
        'username': 'tester',
        'email': 'tester@email.com',
        'password': 'password',
        'native_language': 'pt',
    }

    response = client.post(create_user_url, json=payload)

    assert response.status_code == 201

    user_db = session.exec(select(User).where(User.id == response.json()['id'])).first()
    assert user_db is not None


def test_create_user_email_already_exists(client, session):
    payload = {
        'username': 'tester',
        'email': 'tester@email.com',
        'password': 'password',
        'native_language': 'pt',
    }

    UserFactory(email=payload['email'])
    response = client.post(create_user_url, json=payload)

    assert response.status_code == 409


def test_update_user(session, client, user, token_header):
    payload = {'username': 'my_new_name'}

    response = client.patch(
        update_user_url(user.id), json=payload, headers=token_header
    )
    session.refresh(user)

    assert response.status_code == 200
    assert user.username == payload['username']


def test_update_user_not_authenticated(session, client):
    payload = {'username': 'my_new_name'}

    response = client.patch(update_user_url(1), json=payload)

    assert response.status_code == 401


def test_update_user_credentials_not_match(client, token_header):
    payload = {'username': 'my_new_name'}

    other_user = UserFactory()
    response = client.patch(
        update_user_url(other_user.id), json=payload, headers=token_header
    )

    assert response.status_code == 401
