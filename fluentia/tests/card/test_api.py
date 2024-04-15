import pytest
from sqlalchemy.exc import InvalidRequestError
from sqlmodel import select

from fluentia.apps.card.models import Card, CardSet
from fluentia.apps.card.schema import CardSchemaView, CardSetSchemaView
from fluentia.apps.term.constants import TermLexicalType
from fluentia.core.api.query import set_url_params
from fluentia.core.model.shortcut import get_object_or_404
from fluentia.main import app
from fluentia.tests.factories.card import CardFactory, CardSetFactory
from fluentia.tests.factories.term import (
    TermDefinitionFactory,
    TermDefinitionTranslationFactory,
    TermFactory,
    TermLexicalFactory,
)


class TestCardSet:
    create_cardset_route = app.url_path_for('create_cardset')

    def list_cardset_route(self, name=None):
        url = app.url_path_for('list_cardset')
        return set_url_params(url, name=name)

    def get_cardset_route(self, cardset_id):
        return app.url_path_for('get_cardset', cardset_id=cardset_id)

    def update_cardset_route(self, cardset_id):
        return app.url_path_for('update_cardset', cardset_id=cardset_id)

    def delete_cardset_route(self, cardset_id):
        return app.url_path_for('delete_cardset', cardset_id=cardset_id)

    def test_create_cardset(self, client, session, generate_payload, token_header):
        payload = generate_payload(CardSetFactory)

        response = client.post(
            self.create_cardset_route, json=payload, headers=token_header
        )

        assert response.status_code == 201
        cardset = get_object_or_404(CardSet, session=session, id=response.json()['id'])
        assert CardSetSchemaView(**response.json()) == CardSetSchemaView(
            **cardset.model_dump()
        )

    def test_create_cardset_user_not_authenticated(self, client, generate_payload):
        payload = generate_payload(CardSetFactory)

        response = client.post(self.create_cardset_route, json=payload)

        assert response.status_code == 401

    def test_list_cardset(self, client, session, user, token_header):
        cardsets = CardSetFactory.create_batch(size=5, user_id=user.id)
        CardSetFactory.create_batch(size=10)

        response = client.get(self.list_cardset_route(), headers=token_header)
        [session.refresh(cardset) for cardset in cardsets]

        assert response.status_code == 200
        assert len(response.json()) == 5
        assert [CardSetSchemaView(**cardset) for cardset in response.json()] == [
            CardSetSchemaView(**cardset.model_dump()) for cardset in cardsets
        ]

    def test_list_cardset_filter_name(self, client, session, user, token_header):
        cardsets = CardSetFactory.create_batch(
            size=5, user_id=user.id, name='ãQTéstêQã#!'
        )
        CardSetFactory.create_batch(size=5, user_id=user.id)
        CardSetFactory.create_batch(size=10)

        response = client.get(
            self.list_cardset_route(name='aqtesteqa'), headers=token_header
        )
        [session.refresh(cardset) for cardset in cardsets]

        assert response.status_code == 200
        assert len(response.json()) == 5
        assert [CardSetSchemaView(**cardset) for cardset in response.json()] == [
            CardSetSchemaView(**cardset.model_dump()) for cardset in cardsets
        ]

    def test_list_cardset_user_is_not_authenticated(self, client):
        CardSetFactory.create_batch(size=10)

        response = client.get(self.list_cardset_route())

        assert response.status_code == 401

    def test_list_cardset_dont_belongs_to_user(self, client, token_header):
        CardSetFactory.create_batch(size=5)

        response = client.get(self.list_cardset_route(), headers=token_header)

        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_get_cardset(self, client, user, token_header):
        cardset = CardSetFactory(user_id=user.id)

        response = client.get(self.get_cardset_route(cardset.id), headers=token_header)

        assert response.status_code == 200
        assert CardSetSchemaView(**response.json()) == CardSetSchemaView(
            **cardset.model_dump()
        )

    def test_get_cardset_user_is_not_authenticated(self, client):
        cardset = CardSetFactory()

        response = client.get(self.get_cardset_route(cardset.id))

        assert response.status_code == 401

    def test_get_cardset_dont_belongs_to_user(self, client, token_header):
        cardset = CardSetFactory()

        response = client.get(self.get_cardset_route(cardset.id), headers=token_header)

        assert response.status_code == 404

    def test_get_cardset_does_not_exists(self, client, token_header):
        response = client.get(self.get_cardset_route(123), headers=token_header)

        assert response.status_code == 404

    def test_update_cardset(
        self, client, session, generate_payload, user, token_header
    ):
        cardset = CardSetFactory(user_id=user.id)
        payload = generate_payload(CardSetFactory, include={'name', 'description'})

        response = client.patch(
            self.update_cardset_route(cardset.id), json=payload, headers=token_header
        )
        session.refresh(cardset)

        assert response.status_code == 200
        assert cardset.name == payload['name']
        assert cardset.description == payload['description']
        assert cardset.updated_at is not None

    def test_update_cardset_user_is_not_authenticated(self, client, generate_payload):
        cardset = CardSetFactory()
        payload = generate_payload(CardSetFactory, include={'name', 'description'})

        response = client.patch(self.update_cardset_route(cardset.id), json=payload)

        assert response.status_code == 401

    def test_update_cardset_dont_belongs_to_user(
        self, client, generate_payload, token_header
    ):
        cardset = CardSetFactory()
        payload = generate_payload(CardSetFactory, include={'name', 'description'})

        response = client.patch(
            self.update_cardset_route(cardset.id), json=payload, headers=token_header
        )

        assert response.status_code == 404

    def test_update_cardset_does_not_exists(
        self, client, generate_payload, token_header
    ):
        payload = generate_payload(CardSetFactory, include={'name', 'description'})

        response = client.patch(
            self.update_cardset_route(123), json=payload, headers=token_header
        )

        assert response.status_code == 404

    def test_delete_cardset(self, client, session, user, token_header):
        cardset = CardSetFactory(user_id=user.id)

        response = client.delete(
            self.delete_cardset_route(cardset.id), headers=token_header
        )

        assert response.status_code == 204
        with pytest.raises(InvalidRequestError):
            session.refresh(cardset)

    def test_delete_cardset_user_is_not_authenticated(self, client):
        cardset = CardSetFactory()

        response = client.delete(self.delete_cardset_route(cardset.id))

        assert response.status_code == 401

    def test_delete_cardset_dont_belongs_to_user(self, client, session, token_header):
        cardset = CardSetFactory()

        response = client.delete(
            self.delete_cardset_route(cardset.id), headers=token_header
        )
        session.refresh(cardset)

        assert response.status_code == 404
        assert cardset is not None

    def test_delete_cardset_does_not_exists(self, client, token_header):
        response = client.delete(self.delete_cardset_route(123), headers=token_header)

        assert response.status_code == 404


class TestCard:
    create_card_route = app.url_path_for('create_card')

    def get_card_route(self, card_id):
        return app.url_path_for('get_card', card_id=card_id)

    def list_cards_route(self, cardset_id, term=None, note=None):
        url = app.url_path_for('list_cards', cardset_id=cardset_id)
        return set_url_params(url, term=term, note=note)

    def update_card_route(self, card_id):
        return app.url_path_for('update_card', card_id=card_id)

    def delete_card_route(self, card_id):
        return app.url_path_for('delete_card', card_id=card_id)

    def test_create_card(self, client, session, user, generate_payload, token_header):
        term = TermFactory()
        cardset = CardSetFactory(user_id=user.id)
        payload = generate_payload(
            CardFactory,
            cardset_id=cardset.id,
            term=term.term,
            origin_language=term.origin_language,
        )

        response = client.post(
            self.create_card_route, json=payload, headers=token_header
        )

        assert response.status_code == 201
        card = session.exec(
            select(Card).where(Card.id == response.json()['id'])
        ).first()
        assert CardSchemaView(**response.json()) == CardSchemaView(**card.model_dump())

    def test_create_card_passing_a_term_form_as_term(
        self, session, client, generate_payload, user, token_header
    ):
        term = TermFactory()
        cardset = CardSetFactory(user_id=user.id)
        payload = generate_payload(
            CardFactory,
            cardset_id=cardset.id,
            term=term.term,
            origin_language=term.origin_language,
        )

        TermLexicalFactory(
            term=term.term,
            origin_language=term.origin_language,
            type=TermLexicalType.FORM,
            value='TÉstÎng',
        )
        payload.update(term='testing', origin_language=term.origin_language)

        response = client.post(
            self.create_card_route, json=payload, headers=token_header
        )

        assert response.status_code == 201
        card = session.exec(
            select(Card).where(Card.id == response.json()['id'])
        ).first()
        assert CardSchemaView(**response.json()) == CardSchemaView(**card.model_dump())

    def test_create_card_without_note(
        self, client, session, generate_payload, user, token_header
    ):
        term = TermFactory()
        cardset = CardSetFactory(user_id=user.id)
        definitions = TermDefinitionFactory.create_batch(
            term=term.term,
            origin_language=term.origin_language,
            size=5,
        )
        translations = [
            TermDefinitionTranslationFactory.create(
                term_definition_id=definition.id,
                language=cardset.language,
            )
            for definition in definitions
        ]
        payload = generate_payload(
            CardFactory,
            cardset_id=cardset.id,
            term=term.term,
            origin_language=term.origin_language,
            exclude={'note'},
        )

        response = client.post(
            self.create_card_route, json=payload, headers=token_header
        )
        [session.refresh(trans) for trans in translations]

        assert response.status_code == 201
        card = session.exec(
            select(Card).where(Card.id == response.json()['id'])
        ).first()
        assert CardSchemaView(**response.json()) == CardSchemaView(**card.model_dump())
        assert response.json()['note'] == ','.join(
            [trans.meaning for trans in translations]
        )

    def test_create_card_user_is_not_authenticated(self, client, generate_payload):
        term = TermFactory()
        cardset = CardSetFactory()
        payload = generate_payload(
            CardFactory,
            cardset_id=cardset.id,
            term=term.term,
            origin_language=term.origin_language,
        )

        response = client.post(self.create_card_route, json=payload)

        assert response.status_code == 401

    def test_create_card_term_does_not_exists(
        self, client, generate_payload, user, token_header
    ):
        cardset = CardSetFactory(user_id=user.id)
        payload = generate_payload(
            CardFactory,
            cardset_id=cardset.id,
        )

        response = client.post(
            self.create_card_route, json=payload, headers=token_header
        )

        assert response.status_code == 404
        assert 'Term' in response.json()['detail']

    def test_create_card_cardset_does_not_exists(
        self, client, generate_payload, token_header
    ):
        term = TermFactory()
        payload = generate_payload(
            CardFactory,
            cardset_id=12345,
            term=term.term,
            origin_language=term.origin_language,
        )

        response = client.post(
            self.create_card_route, json=payload, headers=token_header
        )

        assert response.status_code == 404
        assert 'CardSet' in response.json()['detail']

    def test_create_card_cardset_dont_belongs_to_user(
        self, client, generate_payload, token_header
    ):
        term = TermFactory()
        cardset = CardSetFactory()
        payload = generate_payload(
            CardFactory,
            cardset_id=cardset.id,
            term=term.term,
            origin_language=term.origin_language,
        )

        response = client.post(
            self.create_card_route, json=payload, headers=token_header
        )

        assert response.status_code == 404
        assert 'CardSet' in response.json()['detail']

    def test_get_card(self, client, user, token_header):
        cardset = CardSetFactory(user_id=user.id)
        card = CardFactory(cardset_id=cardset.id)

        response = client.get(self.get_card_route(card.id), headers=token_header)

        assert response.status_code == 200
        assert CardSchemaView(**response.json()) == CardSchemaView(**card.model_dump())

    def test_get_card_user_is_not_authenticated(self, client):
        card = CardFactory()

        response = client.get(self.get_card_route(card.id))

        assert response.status_code == 401

    def test_get_card_does_not_exists(self, client, token_header):
        response = client.get(self.get_card_route(123), headers=token_header)

        assert response.status_code == 404

    def test_get_card_cardset_dont_belongs_to_user(self, client, token_header):
        card = CardFactory()

        response = client.get(self.get_card_route(card.id), headers=token_header)

        assert response.status_code == 404

    def test_list_cards(self, client, session, user, token_header):
        cardset = CardSetFactory(user_id=user.id)
        cards = CardFactory.create_batch(cardset_id=cardset.id, size=5)
        CardFactory.create_batch(size=5)

        response = client.get(self.list_cards_route(cardset.id), headers=token_header)
        [session.refresh(card) for card in cards]

        assert response.status_code == 200
        assert len(response.json()) == 5
        assert [CardSchemaView(**card) for card in response.json()] == [
            CardSchemaView(**card.model_dump()) for card in cards
        ]

    def test_list_cards_filter_term(self, client, session, user, token_header):
        cardset = CardSetFactory(user_id=user.id)
        CardFactory.create_batch(cardset_id=cardset.id, size=5)
        cards = CardFactory.create_batch(term='TéSTê!@.', cardset_id=cardset.id, size=5)
        CardFactory.create_batch(size=5)

        response = client.get(
            self.list_cards_route(cardset.id, term='teste'),
            headers=token_header,
        )
        [session.refresh(card) for card in cards]

        assert response.status_code == 200
        assert len(response.json()) == 5
        assert [CardSchemaView(**card) for card in response.json()] == [
            CardSchemaView(**card.model_dump()) for card in cards
        ]

    def test_list_cards_filter_note(self, client, session, user, token_header):
        cardset = CardSetFactory(user_id=user.id)
        CardFactory.create_batch(cardset_id=cardset.id, size=5)
        cards = CardFactory.create_batch(note='TéSTê!@.', cardset_id=cardset.id, size=5)
        CardFactory.create_batch(size=5)

        response = client.get(
            self.list_cards_route(cardset.id, note='teste'),
            headers=token_header,
        )
        [session.refresh(card) for card in cards]

        assert response.status_code == 200
        assert len(response.json()) == 5
        assert [CardSchemaView(**card) for card in response.json()] == [
            CardSchemaView(**card.model_dump()) for card in cards
        ]

    def test_list_cards_user_is_not_authenticated(self, client):
        cardset = CardSetFactory()
        CardFactory.create_batch(size=15)

        response = client.get(self.list_cards_route(cardset.id))

        assert response.status_code == 401

    def test_list_cards_cardset_does_not_exists(self, client, token_header):
        response = client.get(self.list_cards_route(123), headers=token_header)

        assert response.status_code == 404

    def test_list_cards_cardset_dont_belongs_to_user(self, client, token_header):
        cardset = CardSetFactory()
        CardFactory.create_batch(cardset_id=cardset.id, size=15)

        response = client.get(self.list_cards_route(cardset.id), headers=token_header)

        assert response.status_code == 404

    def test_update_card(self, client, session, user, token_header):
        cardset = CardSetFactory(user_id=user.id)
        card = CardFactory(cardset_id=cardset.id)
        payload = {'note': 'test note'}

        response = client.patch(
            self.update_card_route(card.id), json=payload, headers=token_header
        )
        session.refresh(card)

        assert response.status_code == 200
        assert card.note == payload['note']

    def test_update_card_user_is_not_authenticated(self, client):
        cardset = CardSetFactory()
        card = CardFactory(cardset_id=cardset.id)
        payload = {'note': 'test note'}

        response = client.patch(self.update_card_route(card.id), json=payload)

        assert response.status_code == 401

    def test_update_card_does_not_exists(self, client, token_header):
        payload = {'note': 'test note'}

        response = client.patch(
            self.update_card_route(123), json=payload, headers=token_header
        )

        assert response.status_code == 404

    def test_update_card_cardset_dont_belongs_to_user(self, client, token_header):
        cardset = CardSetFactory()
        card = CardFactory(cardset_id=cardset.id)
        payload = {'note': 'test note'}

        response = client.patch(
            self.update_card_route(card.id), json=payload, headers=token_header
        )

        assert response.status_code == 404

    def test_delete_card(self, client, session, user, token_header):
        cardset = CardSetFactory(user_id=user.id)
        card = CardFactory(cardset_id=cardset.id)

        response = client.delete(self.delete_card_route(card.id), headers=token_header)

        assert response.status_code == 204
        with pytest.raises(InvalidRequestError):
            session.refresh(card)

    def test_delete_card_user_is_not_authenticated(self, client):
        cardset = CardSetFactory()
        card = CardFactory(cardset_id=cardset.id)

        response = client.delete(self.delete_card_route(card.id))

        assert response.status_code == 401

    def test_delete_card_does_not_exists(self, client, token_header):
        response = client.delete(self.delete_card_route(123), headers=token_header)

        assert response.status_code == 404

    def test_delete_card_cardset_dont_belongs_to_user(self, client, token_header):
        cardset = CardSetFactory()
        card = CardFactory(cardset_id=cardset.id)

        response = client.delete(self.delete_card_route(card.id), headers=token_header)

        assert response.status_code == 404
