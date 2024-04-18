import pytest
from sqlmodel import select

from fluentia.apps.term.constants import Language, Level, PartOfSpeech, TermLexicalType
from fluentia.apps.term.models import (
    Pronunciation,
    PronunciationLink,
    Term,
    TermDefinition,
    TermDefinitionTranslation,
    TermExample,
    TermExampleLink,
    TermExampleTranslation,
    TermLexical,
)
from fluentia.apps.term.schema import (
    PronunciationView,
    TermDefinitionView,
    TermExampleTranslationView,
    TermExampleView,
    TermLexicalSchema,
    TermSchema,
)
from fluentia.core.api.query import set_url_params
from fluentia.core.model.shortcut import get_object_or_404
from fluentia.main import app
from fluentia.tests.factories.term import (
    PronunciationFactory,
    TermDefinitionFactory,
    TermDefinitionTranslationFactory,
    TermExampleFactory,
    TermExampleTranslationFactory,
    TermFactory,
    TermLexicalFactory,
)
from fluentia.tests.utils import assert_json_response


class TestTerm:
    term_create_route = app.url_path_for('create_term')

    def get_term_route(
        self,
        term,
        origin_language,
        translation_language=None,
        lexical=None,
        pronunciation=None,
    ):
        url = app.url_path_for('get_term')
        return set_url_params(
            url,
            term=term,
            origin_language=origin_language,
            translation_language=translation_language,
            lexical=lexical,
            pronunciation=pronunciation,
        )

    def search_term_route(
        self,
        text,
        origin_language,
    ):
        url = app.url_path_for('search_term')
        return set_url_params(url, text=text, origin_language=origin_language)

    def search_term_meaning_route(self, text, origin_language, translation_language):
        url = app.url_path_for('search_term_meaning')
        return set_url_params(
            url,
            text=text,
            origin_language=origin_language,
            translation_language=translation_language,
        )

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_create_term_already_exists(
        self, client, session, token_header, generate_payload
    ):
        payload = generate_payload(TermFactory)
        term = TermFactory(**payload)

        response = client.post(
            self.term_create_route,
            json=payload,
            headers=token_header,
        )
        session.refresh(term)

        assert response.status_code == 200
        assert Term(**response.json()) == term

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_create_term(self, session, client, generate_payload, token_header):
        payload = generate_payload(TermFactory)

        response = client.post(
            self.term_create_route,
            json=payload,
            headers=token_header,
        )

        assert response.status_code == 201
        assert_json_response(
            session,
            Term,
            response.json(),
            term=payload['term'],
            origin_language=payload['origin_language'],
        )

    def test_create_term_user_is_not_authenticated(self, client, generate_payload):
        payload = generate_payload(TermFactory)

        response = client.post(self.term_create_route, json=payload)

        assert response.status_code == 401

    def test_create_term_user_does_not_have_permission(
        self, client, token_header, generate_payload
    ):
        payload = generate_payload(TermFactory)

        response = client.post(
            self.term_create_route,
            json=payload,
            headers=token_header,
        )

        assert response.status_code == 403

    def test_get_term(self, client):
        term = TermFactory()

        response = client.get(
            self.get_term_route(term=term.term, origin_language=term.origin_language)
        )

        assert response.status_code == 200
        assert Term(**response.json()) == term

    def test_get_term_special_characteres(self, client):
        term = TermFactory(term='TésTé')

        response = client.get(
            self.get_term_route(term='teste', origin_language=term.origin_language)
        )

        assert response.status_code == 200
        assert Term(**response.json()) == term

    def test_get_term_with_form(self, client, session):
        term = TermFactory(origin_language=Language.PORTUGUESE)
        TermLexicalFactory(
            term=term.term,
            origin_language=term.origin_language,
            type=TermLexicalType.FORM,
            value='tÉstÎng',
        )

        response = client.get(
            self.get_term_route(term='testing', origin_language=Language.PORTUGUESE)
        )
        session.refresh(term)

        assert response.status_code == 200
        assert Term(**response.json()) == term

    def test_get_term_with_meanings(self, client):
        term = TermFactory()
        definitions = TermDefinitionFactory.create_batch(
            term=term.term, origin_language=term.origin_language, size=5
        )
        meanings = [
            TermDefinitionTranslationFactory(
                language=Language.DEUTSCH, term_definition_id=definition.id, size=5
            )
            for definition in definitions
        ]

        response = client.get(
            self.get_term_route(
                term=term.term,
                origin_language=term.origin_language,
                translation_language=Language.DEUTSCH,
            )
        )

        assert response.status_code == 200
        assert TermSchema(**response.json()) == TermSchema(
            **term.model_dump(),
            meanings=[meaning.meaning for meaning in meanings],  # pyright: ignore[reportArgumentType]
        )

    def test_get_term_with_lexical(self, client):
        term = TermFactory()
        lexical_list = TermLexicalFactory.create_batch(
            term=term.term, origin_language=term.origin_language, size=5
        )

        response = client.get(
            self.get_term_route(
                term=term.term, origin_language=term.origin_language, lexical=True
            )
        )

        assert response.status_code == 200
        assert TermSchema(**response.json()) == TermSchema(
            **term.model_dump(),
            lexical=[
                TermLexicalSchema(**lexical.model_dump()) for lexical in lexical_list
            ],
        )

    def test_get_term_with_pronunciation(self, client, session):
        term = TermFactory()
        pronunciations = PronunciationFactory.create_batch(size=5)
        links = [
            PronunciationLink(
                pronunciation_id=pronunciation.id,
                term=term.term,  # pyright: ignore[reportArgumentType]
                origin_language=term.origin_language,  # pyright: ignore[reportArgumentType]
            )
            for pronunciation in pronunciations
        ]
        session.add_all(links)
        session.commit()

        response = client.get(
            self.get_term_route(
                term=term.term, origin_language=term.origin_language, pronunciation=True
            )
        )

        assert response.status_code == 200
        assert TermSchema(**response.json()) == TermSchema(
            **term.model_dump(),
            pronunciations=[
                PronunciationView(**pronunciation.model_dump())
                for pronunciation in pronunciations
            ],
        )

    def test_get_term_does_not_exists(self, client):
        response = client.get(
            self.get_term_route(term='teste', origin_language=Language.PORTUGUESE)
        )

        assert response.status_code == 404

    def test_search_term(self, client, session):
        terms = [
            TermFactory(term=f'test {i}', origin_language=Language.PORTUGUESE)
            for i in range(5)
        ]

        response = client.get(
            self.search_term_route(text='test', origin_language=Language.PORTUGUESE)
        )
        [session.refresh(term) for term in terms]

        assert response.status_code == 200
        assert len(response.json()) == 5
        assert [Term(**term) for term in response.json()] == terms

    def test_search_term_special_character(self, client, session):
        terms = [
            TermFactory(term=f'tésté {i}', origin_language=Language.PORTUGUESE)
            for i in range(5)
        ]

        response = client.get(
            self.search_term_route(text='teste', origin_language=Language.PORTUGUESE)
        )
        [session.refresh(term) for term in terms]

        assert response.status_code == 200
        assert len(response.json()) == 5
        assert [Term(**term) for term in response.json()] == terms

    def test_search_term_empty(self, client):
        TermFactory.create_batch(20)

        response = client.get(
            self.search_term_route(
                text='biasdf12480u12az1', origin_language=Language.PORTUGUESE
            )
        )

        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_search_term_form(self, client, session):
        terms = TermFactory.create_batch(5, origin_language=Language.PORTUGUESE)
        for i, term in enumerate(terms):
            TermLexicalFactory(
                term=term.term,
                origin_language=term.origin_language,
                type=TermLexicalType.FORM,
                value=f'testing - {i}',
            )

        response = client.get(
            self.search_term_route(text='testing', origin_language=Language.PORTUGUESE)
        )
        [session.refresh(term) for term in terms]

        assert response.status_code == 200
        json = [Term(**term) for term in response.json()]
        assert len(json) == 5
        for value in json:
            assert value in terms

    def test_search_term_form_special_character(self, client, session):
        terms = TermFactory.create_batch(5, origin_language=Language.PORTUGUESE)
        for i, term in enumerate(terms):
            TermLexicalFactory(
                term=term.term,
                origin_language=term.origin_language,
                type=TermLexicalType.FORM,
                value=f'tÊsTíng {i}',
            )

        response = client.get(
            self.search_term_route(text='testing', origin_language=Language.PORTUGUESE)
        )
        [session.refresh(term) for term in terms]

        assert response.status_code == 200
        json = [Term(**term) for term in response.json()]
        assert len(json) == 5
        for value in json:
            assert value in terms

    def test_search_meaning(self, client):
        terms = TermFactory.create_batch(origin_language=Language.PORTUGUESE, size=5)
        definitions = [
            TermDefinitionFactory.create_batch(
                term=term.term, origin_language=term.origin_language, size=5
            )
            for term in terms
        ]
        [
            TermDefinitionTranslationFactory(
                meaning=f'test {i}',
                language=Language.DEUTSCH,
                term_definition_id=definition.id,
                size=5,
            )
            for i, definition_list in enumerate(definitions)
            for definition in definition_list
        ]

        response = client.get(
            self.search_term_meaning_route(
                'test',
                origin_language=Language.PORTUGUESE,
                translation_language=Language.DEUTSCH,
            )
        )

        assert response.status_code == 200
        json = [Term(**term) for term in response.json()]
        assert len(json) == 5
        for value in json:
            assert value in terms

    def test_search_meaning_special_character(self, client):
        terms = TermFactory.create_batch(origin_language=Language.PORTUGUESE, size=5)
        definitions = [
            TermDefinitionFactory.create_batch(
                term=term.term, origin_language=term.origin_language, size=5
            )
            for term in terms
        ]
        [
            TermDefinitionTranslationFactory(
                meaning=f'Téstê {i}',
                language=Language.DEUTSCH,
                term_definition_id=definition.id,
                size=5,
            )
            for i, definition_list in enumerate(definitions)
            for definition in definition_list
        ]

        response = client.get(
            self.search_term_meaning_route(
                'teste',
                origin_language=Language.PORTUGUESE,
                translation_language=Language.DEUTSCH,
            )
        )

        assert response.status_code == 200
        json = [Term(**term) for term in response.json()]
        assert len(json) == 5
        for value in json:
            assert value in terms

    def test_search_meaning_empty(self, client):
        terms = TermFactory.create_batch(origin_language=Language.PORTUGUESE, size=5)
        definitions = [
            TermDefinitionFactory.create_batch(
                term=term.term, origin_language=term.origin_language, size=5
            )
            for term in terms
        ]
        [
            TermDefinitionTranslationFactory(
                meaning=f'value-{i}',
                language=Language.DEUTSCH,
                term_definition_id=definition.id,
                size=5,
            )
            for i, definition_list in enumerate(definitions)
            for definition in definition_list
        ]

        response = client.get(
            self.search_term_meaning_route(
                'test',
                origin_language=Language.PORTUGUESE,
                translation_language=Language.DEUTSCH,
            )
        )

        assert response.status_code == 200
        assert len(response.json()) == 0


class TestPronunciation:
    create_pronunciation_route = app.url_path_for('create_pronunciation')

    def list_pronunciation_route(
        self,
        term=None,
        origin_language=None,
        term_example_id=None,
        term_lexical_id=None,
    ):
        url = app.url_path_for('list_pronunciation')
        return set_url_params(
            url,
            term=term,
            origin_language=origin_language,
            term_example_id=term_example_id,
            term_lexical_id=term_lexical_id,
        )

    def update_pronunciation_route(self, pronunciation_id):
        return app.url_path_for(
            'update_pronunciation', pronunciation_id=pronunciation_id
        )

    def _get_linked_attributes(self, attr, db_model):
        linked_attr = {}
        for attr_model, attr_real in zip(attr[0], attr[1]):
            linked_attr.update({attr_real: getattr(db_model, attr_model)})
        return linked_attr

    parametrize_pronunciation_link = pytest.mark.parametrize(
        'item',
        [
            (
                TermFactory,
                ({'term', 'origin_language'}, {'term', 'origin_language'}),
            ),
            (
                TermExampleFactory,
                ({'id'}, {'term_example_id'}),
            ),
            (
                TermLexicalFactory,
                ({'id'}, {'term_lexical_id'}),
            ),
        ],
    )

    @parametrize_pronunciation_link
    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_create_pronunciation(
        self, client, session, generate_payload, token_header, item
    ):
        payload = generate_payload(PronunciationFactory)
        Factory, attr = item
        db_factory = Factory()
        linked_attr = self._get_linked_attributes(attr, db_factory)
        payload.update(linked_attr)

        response = client.post(
            self.create_pronunciation_route, json=payload, headers=token_header
        )

        assert response.status_code == 201
        db_pronunciation = get_object_or_404(
            Pronunciation, session=session, id=response.json()['id']
        )
        assert PronunciationView(**response.json()) == PronunciationView(
            **db_pronunciation.model_dump(), **linked_attr
        )

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_create_pronunciation_passing_a_term_form_as_term(
        self, client, session, generate_payload, token_header
    ):
        payload = generate_payload(PronunciationFactory)
        term = TermFactory()
        TermLexicalFactory(
            term=term.term,
            origin_language=term.origin_language,
            type=TermLexicalType.FORM,
            value='TÉstÎng',
        )
        payload.update(term='testing', origin_language=term.origin_language)

        response = client.post(
            self.create_pronunciation_route, json=payload, headers=token_header
        )
        assert response.status_code == 201
        db_pronunciation = get_object_or_404(
            Pronunciation, session=session, id=response.json()['id']
        )
        assert PronunciationView(**response.json()) == PronunciationView(
            **db_pronunciation.model_dump(),
            term=term.term,
            origin_language=term.origin_language,
        )

    def test_create_pronunciation_user_is_not_authenticated(
        self, client, generate_payload
    ):
        payload = generate_payload(PronunciationFactory)

        response = client.post(self.create_pronunciation_route, json=payload)

        assert response.status_code == 401

    def test_create_pronunciation_user_not_enough_permission(
        self, client, generate_payload, token_header
    ):
        payload = generate_payload(PronunciationFactory)

        response = client.post(
            self.create_pronunciation_route,
            json=payload,
            headers=token_header,
        )

        assert response.status_code == 403

    @parametrize_pronunciation_link
    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_create_pronunciation_model_link_not_found(
        self, client, session, generate_payload, token_header, item
    ):
        payload = generate_payload(PronunciationFactory)
        Factory, attr = item
        db_factory = Factory()
        linked_attr = self._get_linked_attributes(attr, db_factory)
        payload.update(linked_attr)
        session.delete(db_factory)
        session.commit()

        response = client.post(
            self.create_pronunciation_route, json=payload, headers=token_header
        )

        assert response.status_code == 404
        assert db_factory.__class__.__name__ in response.json()['detail']

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_create_pronunciation_model_link_attribute_not_set(
        self, client, generate_payload, token_header
    ):
        payload = generate_payload(PronunciationFactory)

        response = client.post(
            self.create_pronunciation_route, json=payload, headers=token_header
        )

        assert response.status_code == 422
        assert 'at least one object to link' in response.json()['detail'][0]['msg']

    @pytest.mark.parametrize('term_attr', ['term', 'origin_language'])
    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_create_pronunciation_model_link_term_not_right_setted(
        self, client, generate_payload, token_header, term_attr
    ):
        term = TermFactory()
        payload = generate_payload(PronunciationFactory)
        payload.update({term_attr: getattr(term, term_attr)})

        response = client.post(
            self.create_pronunciation_route, json=payload, headers=token_header
        )

        assert response.status_code == 422
        assert (
            'you need to provide term and origin_language attributes'
            in response.json()['detail'][0]['msg']
        )

    @pytest.mark.parametrize(
        'link_attr',
        [
            {
                'term_example_id': 123,
                'term': 'test',
                'origin_language': Language.PORTUGUESE,
            },
            {
                'term_example_id': 123,
                'term_lexical_id': 400,
            },
        ],
    )
    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_create_pronunciation_multiple_models(
        self, client, generate_payload, token_header, link_attr
    ):
        payload = generate_payload(PronunciationFactory)
        payload.update(link_attr)

        response = client.post(
            self.create_pronunciation_route, json=payload, headers=token_header
        )

        assert response.status_code == 422
        assert 'reference two objects at once' in response.json()['detail'][0]['msg']

    @parametrize_pronunciation_link
    def test_list_pronunciation(self, client, session, item):
        Factory, attr = item
        db_factory = Factory()
        linked_attr = self._get_linked_attributes(attr, db_factory)
        pronunciations = PronunciationFactory.create_batch(5)
        PronunciationFactory.create_batch(5)
        links = [
            PronunciationLink(pronunciation_id=pronunciation.id, **linked_attr)
            for pronunciation in pronunciations
        ]
        session.add_all(links)
        session.commit()

        response = client.get(self.list_pronunciation_route(**linked_attr))

        assert response.status_code == 200
        assert len(response.json()) == 5
        assert [
            Pronunciation(**pronunciation) for pronunciation in response.json()
        ] == pronunciations

    def test_list_pronunciation_passing_a_term_form_as_term(
        self,
        client,
        session,
    ):
        term = TermFactory()
        TermLexicalFactory(
            term=term.term,
            origin_language=term.origin_language,
            type=TermLexicalType.FORM,
            value='TÉstÎng',
        )
        pronunciations = PronunciationFactory.create_batch(5)
        PronunciationFactory.create_batch(5)
        links = [
            PronunciationLink(
                pronunciation_id=pronunciation.id,
                term=term.term,  # pyright: ignore[reportArgumentType]
                origin_language=term.origin_language,  # pyright: ignore[reportArgumentType]
            )
            for pronunciation in pronunciations
        ]
        session.add_all(links)
        session.commit()

        response = client.get(
            self.list_pronunciation_route(
                term='testing', origin_language=term.origin_language
            )
        )

        assert response.status_code == 200
        assert len(response.json()) == 5
        assert [
            Pronunciation(**pronunciation) for pronunciation in response.json()
        ] == pronunciations

    def test_list_pronunciation_term_special_character(self, client, session):
        term = TermFactory(term='TésTê')
        session.refresh(term)
        pronunciations = PronunciationFactory.create_batch(5)
        PronunciationFactory.create_batch(5)
        links = [
            PronunciationLink(
                pronunciation_id=pronunciation.id,
                term=term.term,  # pyright: ignore[reportArgumentType]
                origin_language=term.origin_language,  # pyright: ignore[reportArgumentType]
            )
            for pronunciation in pronunciations
        ]
        session.add_all(links)
        session.commit()

        response = client.get(
            self.list_pronunciation_route(
                term='teste', origin_language=term.origin_language
            )
        )

        assert response.status_code == 200
        assert len(response.json()) == 5
        assert [
            Pronunciation(**pronunciation) for pronunciation in response.json()
        ] == pronunciations

    @parametrize_pronunciation_link
    def test_list_pronunciation_empty(self, client, item):
        Factory, attr = item
        db_factory = Factory()
        linked_attr = self._get_linked_attributes(attr, db_factory)
        PronunciationFactory.create_batch(5)

        response = client.get(self.list_pronunciation_route(**linked_attr))

        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_list_pronunciation_model_not_set(self, client):
        response = client.get(self.list_pronunciation_route())

        assert response.status_code == 422

    def test_list_pronunciation_term_model_invalid(self, client):
        response = client.get(self.list_pronunciation_route(term='test'))

        assert response.status_code == 422

    def test_list_pronunciation_term_model_multiple_invalid(self, client):
        response = client.get(
            self.list_pronunciation_route(
                term='test', origin_language=Language.PORTUGUESE, term_example_id=1
            )
        )

        assert response.status_code == 422

    def test_list_pronunciation_multiple_models(self, client):
        response = client.get(
            self.list_pronunciation_route(term_example_id=1, term_lexical_id=2)
        )

        assert response.status_code == 422

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_update_pronunciation(
        self, client, session, generate_payload, token_header
    ):
        payload = generate_payload(
            PronunciationFactory, include={'description', 'phonetic'}
        )
        db_pronunciation = PronunciationFactory()

        response = client.patch(
            self.update_pronunciation_route(db_pronunciation.id),
            json=payload,
            headers=token_header,
        )
        session.refresh(db_pronunciation)

        assert response.status_code == 200
        assert db_pronunciation.description == payload['description']
        assert db_pronunciation.phonetic == payload['phonetic']

    def test_update_pronunciation_user_is_not_authenticated(
        self, client, generate_payload
    ):
        payload = generate_payload(
            PronunciationFactory, include={'description', 'phonetic'}
        )
        db_pronunciation = PronunciationFactory()

        response = client.patch(
            self.update_pronunciation_route(db_pronunciation.id), json=payload
        )

        assert response.status_code == 401

    def test_update_pronunciation_user_not_enough_permission(
        self, client, generate_payload, token_header
    ):
        payload = generate_payload(
            PronunciationFactory, include={'description', 'phonetic'}
        )
        db_pronunciation = PronunciationFactory()

        response = client.patch(
            self.update_pronunciation_route(db_pronunciation.id),
            json=payload,
            headers=token_header,
        )

        assert response.status_code == 403

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_update_pronunciation_does_not_exists(
        self, client, generate_payload, token_header
    ):
        payload = generate_payload(
            PronunciationFactory, include={'description', 'phonetic'}
        )

        response = client.patch(
            self.update_pronunciation_route(123),
            json=payload,
            headers=token_header,
        )

        assert response.status_code == 404


class TestTermDefinition:
    create_definition_route = app.url_path_for('create_definition')
    create_definition_translation_route = app.url_path_for(
        'create_definition_translation'
    )

    def list_definition_route(
        self,
        term=None,
        origin_language=None,
        translation_language=None,
        part_of_speech=None,
        level=None,
    ):
        url = app.url_path_for('list_definition')
        return set_url_params(
            url,
            term=term,
            origin_language=origin_language,
            translation_language=translation_language,
            part_of_speech=part_of_speech,
            level=level,
        )

    def update_definition_route(self, definition_id):
        return app.url_path_for('update_definition', definition_id=definition_id)

    def update_definition_translation_route(self, definition_id, language):
        return app.url_path_for(
            'update_definition_translation',
            definition_id=definition_id,
            language=language.value,
        )

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_create_definition(self, client, session, generate_payload, token_header):
        payload = generate_payload(TermDefinitionFactory)
        TermFactory(term=payload['term'], origin_language=payload['origin_language'])

        response = client.post(
            self.create_definition_route,
            json=payload,
            headers=token_header,
        )

        assert response.status_code == 201
        assert_json_response(
            session, TermDefinition, response.json(), id=response.json()['id']
        )

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_create_definition_with_lexical_id(
        self, client, session, generate_payload, token_header
    ):
        term = TermFactory()
        lexical = TermLexicalFactory(
            term=term.term, origin_language=term.origin_language
        )
        payload = generate_payload(
            TermDefinitionFactory,
            part_of_speech=PartOfSpeech.LEXICAL,
            term=term.term,
            origin_language=term.origin_language,
        )
        payload.update(term_lexical_id=lexical.id)

        response = client.post(
            self.create_definition_route,
            json=payload,
            headers=token_header,
        )

        assert response.status_code == 201
        assert response.json()['term_lexical_id'] == lexical.id
        assert_json_response(
            session, TermDefinition, response.json(), id=response.json()['id']
        )

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_create_definition_already_exists(
        self, client, generate_payload, session, token_header
    ):
        payload = generate_payload(
            TermDefinitionFactory,
            level=None,
            definition='Tésté',
            term='TésTê',
        )
        db_definition = TermDefinitionFactory(**payload)
        payload.update({'definition': 'teste', 'term': 'teste'})

        response = client.post(
            self.create_definition_route,
            json=payload,
            headers=token_header,
        )
        session.refresh(db_definition)

        assert response.status_code == 200
        assert TermDefinition(**response.json()) == db_definition

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_create_definition_passing_a_term_form_as_term(
        self, client, session, generate_payload, token_header
    ):
        payload = generate_payload(TermDefinitionFactory)
        term = TermFactory(
            term=payload['term'], origin_language=payload['origin_language']
        )
        TermLexicalFactory(
            term=term.term,
            origin_language=term.origin_language,
            type=TermLexicalType.FORM,
            value='TÉstÎng',
        )
        payload.update(term='testing', origin_language=term.origin_language)

        response = client.post(
            self.create_definition_route,
            json=payload,
            headers=token_header,
        )

        assert response.status_code == 201
        assert_json_response(
            session, TermDefinition, response.json(), id=response.json()['id']
        )

    def test_create_definition_user_is_not_authenticated(
        self, client, generate_payload
    ):
        payload = generate_payload(TermDefinitionFactory)

        response = client.post(self.create_definition_route, json=payload)

        assert response.status_code == 401

    def test_create_definition_user_not_enough_permission(
        self, client, generate_payload, token_header
    ):
        payload = generate_payload(TermDefinitionFactory)

        response = client.post(
            self.create_definition_route, json=payload, headers=token_header
        )

        assert response.status_code == 403

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_create_definition_term_does_not_exists(
        self, client, generate_payload, token_header
    ):
        payload = generate_payload(TermDefinitionFactory)

        response = client.post(
            self.create_definition_route, json=payload, headers=token_header
        )

        assert response.status_code == 404

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_create_definition_translation(
        self, client, session, generate_payload, token_header
    ):
        payload = generate_payload(TermDefinitionTranslationFactory)
        definition = TermDefinitionFactory()
        payload.update({'term_definition_id': definition.id})

        response = client.post(
            self.create_definition_translation_route, json=payload, headers=token_header
        )

        assert response.status_code == 201
        assert_json_response(
            session,
            TermDefinitionTranslation,
            response.json(),
            term_definition_id=payload['term_definition_id'],
            language=payload['language'],
        )

    def test_create_definition_translation_user_is_not_authenticated(
        self, client, generate_payload
    ):
        payload = generate_payload(TermDefinitionTranslationFactory)
        definition = TermDefinitionFactory()
        payload.update({'term_definition_id': definition.id})

        response = client.post(self.create_definition_translation_route, json=payload)

        assert response.status_code == 401

    def test_create_definition_translation_user_not_enough_permission(
        self, client, generate_payload, token_header
    ):
        payload = generate_payload(TermDefinitionTranslationFactory)
        definition = TermDefinitionFactory()
        payload.update({'term_definition_id': definition.id})

        response = client.post(
            self.create_definition_translation_route, json=payload, headers=token_header
        )

        assert response.status_code == 403

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_create_definition_translation_definition_does_not_exists(
        self, client, generate_payload, token_header
    ):
        payload = generate_payload(TermDefinitionTranslationFactory)
        payload.update({'term_definition_id': 512351})

        response = client.post(
            self.create_definition_translation_route, json=payload, headers=token_header
        )

        assert response.status_code == 404

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_create_definition_translation_conflict(
        self, client, generate_payload, token_header
    ):
        payload = generate_payload(TermDefinitionTranslationFactory)
        definition = TermDefinitionFactory()
        payload.update({'term_definition_id': definition.id})
        TermDefinitionTranslationFactory(**payload)

        response = client.post(
            self.create_definition_translation_route, json=payload, headers=token_header
        )

        assert response.status_code == 409

    def test_list_definition(self, client):
        term = TermFactory()
        definitions = TermDefinitionFactory.create_batch(
            term=term.term, origin_language=term.origin_language, size=5
        )
        TermDefinitionFactory.create_batch(size=5)

        response = client.get(
            self.list_definition_route(
                term=term.term, origin_language=term.origin_language
            )
        )

        assert response.status_code == 200
        assert len(response.json()) == 5
        assert [
            TermDefinition(**definition) for definition in response.json()
        ] == definitions

    def test_list_definition_passing_a_term_form_as_term(
        self,
        client,
    ):
        term = TermFactory()
        TermLexicalFactory(
            term=term.term,
            origin_language=term.origin_language,
            type=TermLexicalType.FORM,
            value='TÉstÎng',
        )
        definitions = TermDefinitionFactory.create_batch(
            term=term.term, origin_language=term.origin_language, size=5
        )
        TermDefinitionFactory.create_batch(size=5)

        response = client.get(
            self.list_definition_route(
                term='testing', origin_language=term.origin_language
            )
        )

        assert response.status_code == 200
        assert len(response.json()) == 5
        assert [
            TermDefinition(**definition) for definition in response.json()
        ] == definitions

    def test_list_definition_term_special_character(self, client):
        term = TermFactory(term='TêStÉ')
        definitions = TermDefinitionFactory.create_batch(
            term=term.term, origin_language=term.origin_language, size=5
        )
        TermDefinitionFactory.create_batch(size=5)

        response = client.get(
            self.list_definition_route(
                term='teste', origin_language=term.origin_language
            )
        )

        assert response.status_code == 200
        assert len(response.json()) == 5
        assert [
            TermDefinition(**definition) for definition in response.json()
        ] == definitions

    def test_list_definition_translation(self, client):
        term = TermFactory()
        definitions = TermDefinitionFactory.create_batch(
            term=term.term, origin_language=term.origin_language, size=5
        )
        translations = [
            TermDefinitionTranslationFactory(
                language=Language.ITALIAN, term_definition_id=definition.id
            )
            for definition in definitions
        ]

        definitions2 = TermDefinitionFactory.create_batch(
            term=term.term, origin_language=term.origin_language, size=5
        )
        for definition in definitions2:
            TermDefinitionTranslationFactory(
                language=Language.RUSSIAN, term_definition_id=definition.id
            )

        response = client.get(
            self.list_definition_route(
                term=term.term,
                origin_language=term.origin_language,
                translation_language=Language.ITALIAN,
            )
        )

        assert response.status_code == 200
        assert len(response.json()) == 5
        assert [TermDefinitionView(**definition) for definition in response.json()] == [
            TermDefinitionView(
                **definition.model_dump(),
                translation_definition=translation.translation,  # pyright: ignore[reportArgumentType]
                translation_meaning=translation.meaning,  # pyright: ignore[reportArgumentType]
                translation_language=translation.language,  # pyright: ignore[reportArgumentType]
            )
            for definition, translation in zip(definitions, translations)
        ]

    def test_list_definition_translation_passing_a_term_form_as_term(
        self,
        client,
    ):
        term = TermFactory()
        TermLexicalFactory(
            term=term.term,
            origin_language=term.origin_language,
            type=TermLexicalType.FORM,
            value='TÉstÎng',
        )
        definitions = TermDefinitionFactory.create_batch(
            term=term.term, origin_language=term.origin_language, size=5
        )
        translations = [
            TermDefinitionTranslationFactory(
                language=Language.ITALIAN, term_definition_id=definition.id
            )
            for definition in definitions
        ]

        definitions2 = TermDefinitionFactory.create_batch(
            term=term.term, origin_language=term.origin_language, size=5
        )
        for definition in definitions2:
            TermDefinitionTranslationFactory(
                language=Language.RUSSIAN, term_definition_id=definition.id
            )

        response = client.get(
            self.list_definition_route(
                term='testing',
                origin_language=term.origin_language,
                translation_language=Language.ITALIAN,
            )
        )

        assert response.status_code == 200
        assert len(response.json()) == 5
        assert [TermDefinitionView(**definition) for definition in response.json()] == [
            TermDefinitionView(
                **definition.model_dump(),
                translation_definition=translation.translation,  # pyright: ignore[reportArgumentType]
                translation_meaning=translation.meaning,  # pyright: ignore[reportArgumentType]
                translation_language=translation.language,  # pyright: ignore[reportArgumentType]
            )
            for definition, translation in zip(definitions, translations)
        ]

    def test_list_definition_empty(self, client):
        term = TermFactory()
        TermDefinitionFactory.create_batch(size=5)

        response = client.get(
            self.list_definition_route(
                term=term.term, origin_language=term.origin_language
            )
        )

        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_list_definition_translation_empty(self, client):
        term = TermFactory()
        TermDefinitionFactory.create_batch(
            term=term.term, origin_language=term.origin_language, size=5
        )

        response = client.get(
            self.list_definition_route(
                term=term.term,
                origin_language=term.origin_language,
                translation_language=Language.ITALIAN,
            )
        )

        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_list_definition_filter_part_of_speech(self, client):
        term = TermFactory()
        definitions = TermDefinitionFactory.create_batch(
            term=term.term,
            origin_language=term.origin_language,
            size=5,
            part_of_speech=PartOfSpeech.ADJECTIVE,
        )
        TermDefinitionFactory.create_batch(
            term=term.term,
            origin_language=term.origin_language,
            size=5,
            part_of_speech=PartOfSpeech.VERB,
        )

        response = client.get(
            self.list_definition_route(
                term=term.term,
                origin_language=term.origin_language,
                part_of_speech=PartOfSpeech.ADJECTIVE,
            )
        )

        assert response.status_code == 200
        assert len(response.json()) == 5
        assert [
            TermDefinition(**definition) for definition in response.json()
        ] == definitions

    def test_list_definition_filter_level(self, client):
        term = TermFactory()
        definitions = TermDefinitionFactory.create_batch(
            term=term.term,
            origin_language=term.origin_language,
            size=5,
            level=Level.ADVANCED,
        )
        TermDefinitionFactory.create_batch(
            term=term.term,
            origin_language=term.origin_language,
            size=5,
            level=Level.BEGINNER,
        )

        response = client.get(
            self.list_definition_route(
                term=term.term,
                origin_language=term.origin_language,
                level=Level.ADVANCED,
            )
        )

        assert response.status_code == 200
        assert len(response.json()) == 5
        assert [
            TermDefinition(**definition) for definition in response.json()
        ] == definitions

    def test_list_definition_translation_filter_part_of_speech(self, client):
        term = TermFactory()
        definitions_with_translation = TermDefinitionFactory.create_batch(
            term=term.term,
            origin_language=term.origin_language,
            size=5,
            part_of_speech=PartOfSpeech.ADJECTIVE,
        )
        translations = [
            TermDefinitionTranslationFactory(
                language=Language.ITALIAN, term_definition_id=definition.id
            )
            for definition in definitions_with_translation
        ]

        definitions_with_translation2 = TermDefinitionFactory.create_batch(
            term=term.term,
            origin_language=term.origin_language,
            size=5,
            part_of_speech=PartOfSpeech.VERB,
        )
        for definition in definitions_with_translation2:
            TermDefinitionTranslationFactory(
                language=Language.ITALIAN, term_definition_id=definition.id
            )

        response = client.get(
            self.list_definition_route(
                term=term.term,
                origin_language=term.origin_language,
                part_of_speech=PartOfSpeech.ADJECTIVE,
                translation_language=Language.ITALIAN,
            )
        )

        assert response.status_code == 200
        assert len(response.json()) == 5
        assert [TermDefinitionView(**definition) for definition in response.json()] == [
            TermDefinitionView(
                **definition.model_dump(),
                translation_definition=translation.translation,  # pyright: ignore[reportArgumentType]
                translation_meaning=translation.meaning,  # pyright: ignore[reportArgumentType]
                translation_language=translation.language,  # pyright: ignore[reportArgumentType]
            )
            for definition, translation in zip(
                definitions_with_translation, translations
            )
        ]

    def test_list_definition_translation_filter_level(self, client):
        term = TermFactory()
        definitions_with_translation = TermDefinitionFactory.create_batch(
            term=term.term,
            origin_language=term.origin_language,
            size=5,
            level=Level.ADVANCED,
        )
        translations = [
            TermDefinitionTranslationFactory(
                language=Language.ITALIAN, term_definition_id=definition.id
            )
            for definition in definitions_with_translation
        ]

        definitions_with_translation2 = TermDefinitionFactory.create_batch(
            term=term.term,
            origin_language=term.origin_language,
            size=5,
            level=Level.BEGINNER,
        )
        for definition in definitions_with_translation2:
            TermDefinitionTranslationFactory(
                language=Language.ITALIAN, term_definition_id=definition.id
            )

        response = client.get(
            self.list_definition_route(
                term=term.term,
                origin_language=term.origin_language,
                level=Level.ADVANCED,
                translation_language=Language.ITALIAN,
            )
        )

        assert response.status_code == 200
        assert len(response.json()) == 5
        assert [TermDefinitionView(**definition) for definition in response.json()] == [
            TermDefinitionView(
                **definition.model_dump(),
                translation_definition=translation.translation,  # pyright: ignore[reportArgumentType]
                translation_meaning=translation.meaning,  # pyright: ignore[reportArgumentType]
                translation_language=translation.language,  # pyright: ignore[reportArgumentType]
            )
            for definition, translation in zip(
                definitions_with_translation, translations
            )
        ]

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_update_definition(self, session, client, generate_payload, token_header):
        definition = TermDefinitionFactory(extra={'test1': 1})
        payload = generate_payload(
            TermDefinitionFactory, include={'definition', 'level'}
        )
        payload.update(extra={'test2': 2})

        response = client.patch(
            self.update_definition_route(definition.id),
            json=payload,
            headers=token_header,
        )
        session.refresh(definition)

        assert response.status_code == 200
        assert definition.definition == payload['definition']
        assert definition.level == payload['level']
        assert definition.extra == {'test1': 1, 'test2': 2}

    def test_update_definition_user_not_authenticated(self, client, generate_payload):
        definition = TermDefinitionFactory()
        payload = generate_payload(
            TermDefinitionFactory, include={'definition', 'level'}
        )

        response = client.patch(
            self.update_definition_route(definition.id),
            json=payload,
        )

        assert response.status_code == 401

    def test_update_definition_user_not_enough_permission(
        self, client, generate_payload, token_header
    ):
        definition = TermDefinitionFactory()
        payload = generate_payload(
            TermDefinitionFactory, include={'definition', 'level'}
        )

        response = client.patch(
            self.update_definition_route(definition.id),
            json=payload,
            headers=token_header,
        )

        assert response.status_code == 403

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_update_definition_not_found(self, client, generate_payload, token_header):
        payload = generate_payload(
            TermDefinitionFactory, include={'definition', 'level'}
        )

        response = client.patch(
            self.update_definition_route(1),
            json=payload,
            headers=token_header,
        )

        assert response.status_code == 404

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_update_definition_translation(
        self, session, client, generate_payload, token_header
    ):
        definition = TermDefinitionFactory()
        definition_translation = TermDefinitionTranslationFactory(
            term_definition_id=definition.id, extra={'test1': 1}
        )
        payload = generate_payload(
            TermDefinitionTranslationFactory, include={'meaning', 'translation'}
        )
        payload.update(extra={'test2': 2})

        response = client.patch(
            self.update_definition_translation_route(
                definition.id, definition_translation.language
            ),
            json=payload,
            headers=token_header,
        )
        session.refresh(definition_translation)

        assert response.status_code == 200
        assert definition_translation.meaning == payload['meaning']
        assert definition_translation.translation == payload['translation']
        assert definition_translation.extra == {'test1': 1, 'test2': 2}

    def test_update_definition_translation_user_not_authenticated(
        self, session, client, generate_payload
    ):
        definition = TermDefinitionFactory()
        definition_translation = TermDefinitionTranslationFactory(
            term_definition_id=definition.id
        )
        payload = generate_payload(
            TermDefinitionTranslationFactory, include={'meaning', 'translation'}
        )

        response = client.patch(
            self.update_definition_translation_route(
                definition.id, definition_translation.language
            ),
            json=payload,
        )
        session.refresh(definition_translation)

        assert response.status_code == 401

    def test_update_definition_translation_user_not_enough_permission(
        self, session, client, generate_payload, token_header
    ):
        definition = TermDefinitionFactory()
        definition_translation = TermDefinitionTranslationFactory(
            term_definition_id=definition.id
        )
        payload = generate_payload(
            TermDefinitionTranslationFactory, include={'meaning', 'translation'}
        )

        response = client.patch(
            self.update_definition_translation_route(
                definition.id, definition_translation.language
            ),
            json=payload,
            headers=token_header,
        )
        session.refresh(definition_translation)

        assert response.status_code == 403

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_update_definition_translation_definition_not_found(
        self, client, generate_payload, token_header
    ):
        payload = generate_payload(
            TermDefinitionTranslationFactory, include={'meaning', 'translation'}
        )

        response = client.patch(
            self.update_definition_translation_route(123, Language.CHINESE),
            json=payload,
            headers=token_header,
        )

        assert response.status_code == 404


class TestTermExample:
    create_example_route = app.url_path_for('create_example')
    create_example_translation_route = app.url_path_for('create_example_translation')

    def list_example_route(
        self,
        term=None,
        origin_language=None,
        translation_language=None,
        term_definition_id=None,
        term_lexical_id=None,
        page=None,
        size=None,
    ):
        url = app.url_path_for('list_example')
        return set_url_params(
            url,
            term=term,
            origin_language=origin_language,
            translation_language=translation_language,
            term_definition_id=term_definition_id,
            term_lexical_id=term_lexical_id,
            page=page,
            size=size,
        )

    def _get_linked_attributes(self, attr, db_model):
        linked_attr = {}
        for attr_model, attr_real in zip(attr[0], attr[1]):
            linked_attr.update({attr_real: getattr(db_model, attr_model)})
        return linked_attr

    parametrize_example_link = pytest.mark.parametrize(
        'item',
        [
            (
                TermFactory,
                ({'term', 'origin_language'}, {'term', 'origin_language'}),
            ),
            (
                TermDefinitionFactory,
                ({'id'}, {'term_definition_id'}),
            ),
            (
                TermLexicalFactory,
                ({'id'}, {'term_lexical_id'}),
            ),
        ],
    )

    @parametrize_example_link
    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_create_example_already_exists(
        self, client, session, generate_payload, token_header, item
    ):
        payload = generate_payload(TermExampleFactory)
        example = TermExampleFactory(**payload)
        Factory, attr = item
        db_factory = Factory()
        linked_attr = self._get_linked_attributes(attr, db_factory)
        payload.update(linked_attr, highlight=[[1, 4], [6, 8]])

        response = client.post(
            self.create_example_route, json=payload, headers=token_header
        )

        assert response.status_code == 200
        assert response.json()['id'] == example.id
        db_link = session.exec(
            select(TermExampleLink)
            .where(
                TermExampleLink.term_example_id == example.id,
            )
            .filter_by(**linked_attr)
        ).first()
        assert db_link is not None

    @parametrize_example_link
    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_create_example(
        self, session, client, generate_payload, token_header, item
    ):
        payload = generate_payload(TermExampleFactory)
        Factory, attr = item
        db_factory = Factory()
        linked_attr = self._get_linked_attributes(attr, db_factory)
        payload.update(linked_attr, highlight=[[1, 4], [6, 8]])

        response = client.post(
            self.create_example_route, json=payload, headers=token_header
        )

        assert response.status_code == 201
        assert_json_response(
            session, TermExample, response.json(), id=response.json()['id']
        )
        db_link = session.exec(
            select(TermExampleLink)
            .where(
                TermExampleLink.term_example_id == response.json()['id'],
            )
            .filter_by(**linked_attr)
        ).first()
        assert db_link is not None

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_create_example_passing_a_term_form_as_term(
        self, session, client, generate_payload, token_header
    ):
        term = TermFactory()
        payload = generate_payload(TermExampleFactory, language=term.origin_language)
        TermLexicalFactory(
            term=term.term,
            origin_language=term.origin_language,
            type=TermLexicalType.FORM,
            value='TÉstÎng',
        )
        payload.update(
            term='testing',
            origin_language=term.origin_language,
            highlight=[[1, 4], [6, 8]],
        )

        response = client.post(
            self.create_example_route, json=payload, headers=token_header
        )

        assert response.status_code == 201
        assert_json_response(
            session, TermExample, response.json(), id=response.json()['id']
        )

    def test_create_example_user_is_not_authenticated(self, client, generate_payload):
        term = TermFactory()
        payload = generate_payload(
            TermExampleFactory,
            language=term.origin_language,
        )
        payload.update(term.model_dump(), highlight=[[1, 4], [6, 8]])

        response = client.post(self.create_example_route, json=payload)

        assert response.status_code == 401

    def test_create_example_user_not_enough_permission(
        self, client, generate_payload, token_header
    ):
        term = TermFactory()
        payload = generate_payload(
            TermExampleFactory,
            language=term.origin_language,
        )
        payload.update(term.model_dump(), highlight=[[1, 4], [6, 8]])

        response = client.post(
            self.create_example_route, json=payload, headers=token_header
        )

        assert response.status_code == 403

    @parametrize_example_link
    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_create_example_with_model_link_not_found(
        self, client, session, generate_payload, token_header, item
    ):
        payload = generate_payload(TermExampleFactory)
        payload.update(highlight=[[1, 4], [6, 8]])
        Factory, attr = item
        db_factory = Factory()
        linked_attr = self._get_linked_attributes(attr, db_factory)
        payload.update(linked_attr)
        session.delete(db_factory)
        session.commit()

        response = client.post(
            self.create_example_route, json=payload, headers=token_header
        )

        assert response.status_code == 404
        assert db_factory.__class__.__name__ in response.json()['detail']

    @parametrize_example_link
    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_create_example_with_conflict_link(
        self, session, client, generate_payload, token_header, item
    ):
        payload = generate_payload(TermExampleFactory)
        db_example = TermExampleFactory(**payload)
        Factory, attr = item
        db_factory = Factory()
        link_attr = self._get_linked_attributes(attr, db_factory)
        TermExampleLink.create(
            session,
            highlight=[[1, 4], [6, 8]],
            term_example_id=db_example.id,
            **link_attr,
        )
        payload.update(link_attr, highlight=[[1, 4], [6, 8]])

        response = client.post(
            self.create_example_route, json=payload, headers=token_header
        )

        assert response.status_code == 409

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_create_example_model_link_not_set(
        self, client, generate_payload, token_header
    ):
        payload = generate_payload(TermExampleFactory)
        payload.update(highlight=[[1, 4], [6, 8]])

        response = client.post(
            self.create_example_route, json=payload, headers=token_header
        )

        assert response.status_code == 422
        assert 'at least one object to link' in response.json()['detail'][0]['msg']

    @pytest.mark.parametrize('term_attr', ['term', 'origin_language'])
    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_create_example_model_link_term_not_right_setted(
        self, client, generate_payload, token_header, term_attr
    ):
        term = TermFactory()
        payload = generate_payload(TermExampleFactory)
        payload.update(
            {term_attr: getattr(term, term_attr)}, highlight=[[1, 4], [6, 8]]
        )

        response = client.post(
            self.create_example_route, json=payload, headers=token_header
        )

        assert response.status_code == 422
        assert (
            'you need to provide term and origin_language attributes'
            in response.json()['detail'][0]['msg']
        )

    @pytest.mark.parametrize(
        'link_attr',
        [
            {
                'term_definition_id': 123,
                'term': 'test',
                'origin_language': Language.PORTUGUESE,
            },
            {
                'term_definition_id': 123,
                'term_lexical_id': 400,
            },
        ],
    )
    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_create_example_multiple_models(
        self, client, generate_payload, token_header, link_attr
    ):
        payload = generate_payload(TermExampleFactory)
        payload.update(link_attr, highlight=[[1, 4], [6, 8]])

        response = client.post(
            self.create_example_route, json=payload, headers=token_header
        )

        assert response.status_code == 422
        assert 'reference two objects at once' in response.json()['detail'][0]['msg']

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_create_example_invalid_num_highlight(
        self, client, generate_payload, token_header
    ):
        term = TermFactory()
        payload = generate_payload(
            TermExampleFactory,
            language=term.origin_language,
        )
        payload.update(term.model_dump(), highlight=[[1, 4, 5], [6, 8]])

        response = client.post(
            self.create_example_route, json=payload, headers=token_header
        )

        assert response.status_code == 422
        assert (
            'highlight must consist of pairs of numbers'
            in response.json()['detail'][0]['msg']
        )

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    @pytest.mark.parametrize(
        'highlight', [[[1, 4], [4, 6]], [[10, 14], [13, 16]], [[0, 3], [0, 9]]]
    )
    def test_create_example_invalid_highlight_interval(
        self, client, generate_payload, token_header, highlight
    ):
        term = TermFactory()
        payload = generate_payload(
            TermExampleFactory,
            language=term.origin_language,
        )
        payload.update(term.model_dump(), highlight=highlight)

        response = client.post(
            self.create_example_route, json=payload, headers=token_header
        )

        assert response.status_code == 422
        assert (
            'highlight interval must not overlap' in response.json()['detail'][0]['msg']
        )

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    @pytest.mark.parametrize('highlight', [[[399, 5]], [[5, 699]]])
    def test_create_example_invalid_highlight_len(
        self, client, generate_payload, token_header, highlight
    ):
        term = TermFactory()
        payload = generate_payload(
            TermExampleFactory,
            language=term.origin_language,
        )
        payload.update(term.model_dump(), highlight=highlight)

        response = client.post(
            self.create_example_route, json=payload, headers=token_header
        )

        assert response.status_code == 422
        assert (
            'highlight cannot be greater than the length of the example.'
            in response.json()['detail'][0]['msg']
        )

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    @pytest.mark.parametrize('highlight', [[[-1, 5]], [[-5, -1]]])
    def test_create_example_invalid_highlight_values_lower_than_0(
        self, client, generate_payload, token_header, highlight
    ):
        term = TermFactory()
        payload = generate_payload(
            TermExampleFactory,
            language=term.origin_language,
        )
        payload.update(term.model_dump(), highlight=highlight)

        response = client.post(
            self.create_example_route, json=payload, headers=token_header
        )

        assert response.status_code == 422
        assert (
            'both highlight values must be greater than or equal to 0.'
            in response.json()['detail'][0]['msg']
        )

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_create_example_invalid_highlight_value1_greater_than_value2(
        self, client, generate_payload, token_header
    ):
        term = TermFactory()
        payload = generate_payload(
            TermExampleFactory,
            language=term.origin_language,
        )
        payload.update(term.model_dump(), highlight=[[7, 1]])

        response = client.post(
            self.create_example_route, json=payload, headers=token_header
        )

        assert response.status_code == 422
        assert (
            'highlight beginning value cannot be greater than the ending value'
            in response.json()['detail'][0]['msg']
        )

    @parametrize_example_link
    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_create_example_translation_already_exists(
        self, client, session, generate_payload, token_header, item
    ):
        example = TermExampleFactory()
        payload = generate_payload(TermExampleTranslationFactory)
        payload.update(term_example_id=example.id)
        TermExampleTranslationFactory(**payload)
        Factory, attr = item
        db_factory = Factory()
        linked_attr = self._get_linked_attributes(attr, db_factory)
        payload.update(
            linked_attr,
            highlight=[[1, 4], [6, 8]],
        )

        response = client.post(
            self.create_example_translation_route,
            json=payload,
            headers=token_header,
        )

        assert response.status_code == 200
        db_link = session.exec(
            select(TermExampleLink)
            .where(
                TermExampleLink.term_example_id == example.id,
                TermExampleLink.translation_language == payload['language'],
            )
            .filter_by(**linked_attr)
        ).first()
        assert db_link is not None

    @parametrize_example_link
    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_create_example_translation(
        self, session, client, generate_payload, token_header, item
    ):
        example = TermExampleFactory()
        payload = generate_payload(TermExampleTranslationFactory)
        Factory, attr = item
        db_factory = Factory()
        linked_attr = self._get_linked_attributes(attr, db_factory)
        payload.update(
            linked_attr,
            highlight=[[1, 4], [6, 8]],
            term_example_id=example.id,
        )

        response = client.post(
            self.create_example_translation_route, json=payload, headers=token_header
        )

        assert response.status_code == 201
        assert_json_response(
            session,
            TermExampleTranslation,
            response.json(),
            term_example_id=example.id,
            language=payload['language'],
        )
        db_link = session.exec(
            select(TermExampleLink)
            .where(
                TermExampleLink.term_example_id == example.id,
                TermExampleLink.translation_language == payload['language'],
            )
            .filter_by(**linked_attr)
        ).first()
        assert db_link is not None

    def test_create_example_translation_user_is_not_authenticated(
        self, client, generate_payload
    ):
        example = TermExampleFactory()
        payload = generate_payload(TermExampleTranslationFactory)
        payload.update(term_example_id=example.id, highlight=[[1, 4], [6, 8]])

        response = client.post(self.create_example_translation_route, json=payload)

        assert response.status_code == 401

    def test_create_example_translation_user_not_enough_permission(
        self, client, generate_payload, token_header
    ):
        example = TermExampleFactory()
        payload = generate_payload(TermExampleTranslationFactory)
        payload.update(term_example_id=example.id, highlight=[[1, 4], [6, 8]])

        response = client.post(
            self.create_example_translation_route, json=payload, headers=token_header
        )

        assert response.status_code == 403

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_create_example_translation_example_was_not_found(
        self, client, session, generate_payload, token_header
    ):
        payload = generate_payload(TermExampleTranslationFactory)
        term = TermFactory()
        session.refresh(term)
        payload.update(
            **term.model_dump(),
            term_example_id=123,
            highlight=[[1, 4], [6, 8]],
        )

        response = client.post(
            self.create_example_translation_route, json=payload, headers=token_header
        )

        assert response.status_code == 404

    @parametrize_example_link
    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_create_example_translation_with_model_link_not_found(
        self, client, session, generate_payload, token_header, item
    ):
        example = TermExampleFactory()
        payload = generate_payload(TermExampleTranslationFactory)
        Factory, attr = item
        db_factory = Factory()
        linked_attr = self._get_linked_attributes(attr, db_factory)
        payload.update(
            linked_attr,
            highlight=[[1, 4], [6, 8]],
            term_example_id=example.id,
        )
        session.delete(db_factory)
        session.commit()

        response = client.post(
            self.create_example_translation_route, json=payload, headers=token_header
        )

        assert response.status_code == 404
        assert db_factory.__class__.__name__ in response.json()['detail']

    @parametrize_example_link
    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_create_example_translation_with_conflict(
        self, session, client, token_header, item
    ):
        example = TermExampleFactory()
        translation = TermExampleTranslationFactory(term_example_id=example.id)
        session.refresh(translation)
        payload = translation.model_dump()
        Factory, attr = item
        db_factory = Factory()
        linked_attr = self._get_linked_attributes(attr, db_factory)
        TermExampleLink.create(
            session,
            highlight=[[1, 4], [6, 8]],
            term_example_id=example.id,
            translation_language=payload['language'],
            **linked_attr,
        )
        payload.update(
            linked_attr,
            highlight=[[1, 4], [6, 8]],
        )

        response = client.post(
            self.create_example_translation_route, json=payload, headers=token_header
        )

        assert response.status_code == 409
        assert (
            response.json()['detail']
            == 'the example is already linked with this model.'
        )

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_create_example_translation_model_link_not_set(
        self, client, generate_payload, token_header
    ):
        example = TermExampleFactory()
        payload = generate_payload(TermExampleTranslationFactory)
        payload.update(
            term_example_id=example.id,
            highlight=[[1, 4], [6, 8]],
        )

        response = client.post(
            self.create_example_translation_route, json=payload, headers=token_header
        )

        assert response.status_code == 422
        assert 'at least one object to link' in response.json()['detail'][0]['msg']

    @pytest.mark.parametrize('term_attr', ['term', 'origin_language'])
    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_create_example_translation_model_link_term_not_right_setted(
        self, client, generate_payload, token_header, term_attr
    ):
        term = TermFactory()
        example = TermExampleFactory()
        payload = generate_payload(TermExampleTranslationFactory)
        payload.update(
            **{term_attr: getattr(term, term_attr)},
            highlight=[[1, 4], [6, 8]],
            term_example_id=example.id,
        )

        response = client.post(
            self.create_example_translation_route, json=payload, headers=token_header
        )

        assert response.status_code == 422
        assert (
            'you need to provide term and origin_language attributes'
            in response.json()['detail'][0]['msg']
        )

    @pytest.mark.parametrize(
        'link_attr',
        [
            {
                'term_definition_id': 123,
                'term': 'test',
                'origin_language': Language.PORTUGUESE,
            },
            {
                'term_definition_id': 123,
                'term_lexical_id': 400,
            },
        ],
    )
    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_create_example_translation_multiple_models(
        self, client, generate_payload, token_header, link_attr
    ):
        example = TermExampleFactory()
        payload = generate_payload(TermExampleTranslationFactory)
        payload.update(
            link_attr,
            highlight=[[1, 4], [6, 8]],
            term_example_id=example.id,
        )

        response = client.post(
            self.create_example_translation_route, json=payload, headers=token_header
        )

        assert response.status_code == 422
        assert 'reference two objects at once' in response.json()['detail'][0]['msg']

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_create_example_translation_invalid_num_highlight(
        self, client, session, generate_payload, token_header
    ):
        example = TermExampleFactory()
        payload = generate_payload(TermExampleTranslationFactory)
        term = TermFactory()
        session.refresh(term)
        payload.update(
            **term.model_dump(),
            term_example_id=example.id,
            highlight=[[1, 4, 5], [6, 8]],
        )

        response = client.post(
            self.create_example_translation_route, json=payload, headers=token_header
        )

        assert response.status_code == 422
        assert (
            'highlight must consist of pairs of numbers'
            in response.json()['detail'][0]['msg']
        )

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    @pytest.mark.parametrize(
        'highlight', [[[1, 4], [4, 6]], [[10, 14], [13, 16]], [[0, 3], [0, 9]]]
    )
    def test_create_example_translation_invalid_highlight_interval(
        self, client, session, generate_payload, token_header, highlight
    ):
        example = TermExampleFactory()
        payload = generate_payload(TermExampleTranslationFactory)
        term = TermFactory()
        session.refresh(term)
        payload.update(
            **term.model_dump(),
            term_example_id=example.id,
            highlight=highlight,
        )

        response = client.post(
            self.create_example_translation_route, json=payload, headers=token_header
        )

        assert response.status_code == 422
        assert (
            'highlight interval must not overlap' in response.json()['detail'][0]['msg']
        )

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    @pytest.mark.parametrize('highlight', [[[399, 5]], [[5, 699]]])
    def test_create_example_translation_invalid_highlight_len(
        self, client, session, generate_payload, token_header, highlight
    ):
        example = TermExampleFactory()
        payload = generate_payload(TermExampleTranslationFactory)
        term = TermFactory()
        session.refresh(term)
        payload.update(
            **term.model_dump(),
            term_example_id=example.id,
            highlight=highlight,
        )

        response = client.post(
            self.create_example_translation_route, json=payload, headers=token_header
        )

        assert response.status_code == 422
        assert (
            'highlight cannot be greater than the length of the example.'
            in response.json()['detail'][0]['msg']
        )

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    @pytest.mark.parametrize('highlight', [[[-1, 5]], [[-5, -1]]])
    def test_create_example_translation_invalid_highlight_values_lower_than_0(
        self, client, session, generate_payload, token_header, highlight
    ):
        example = TermExampleFactory()
        payload = generate_payload(TermExampleTranslationFactory)
        term = TermFactory()
        session.refresh(term)
        payload.update(
            **term.model_dump(),
            term_example_id=example.id,
            highlight=highlight,
        )

        response = client.post(
            self.create_example_translation_route, json=payload, headers=token_header
        )

        assert response.status_code == 422
        assert (
            'both highlight values must be greater than or equal to 0.'
            in response.json()['detail'][0]['msg']
        )

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_create_example_translation_invalid_highlight_value1_greater_than_value2(
        self, client, session, generate_payload, token_header
    ):
        example = TermExampleFactory()
        payload = generate_payload(TermExampleTranslationFactory)
        term = TermFactory()
        session.refresh(term)
        payload.update(
            **term.model_dump(),
            term_example_id=example.id,
            highlight=[[7, 1]],
        )

        response = client.post(
            self.create_example_translation_route, json=payload, headers=token_header
        )

        assert response.status_code == 422
        assert (
            'highlight beginning value cannot be greater than the ending value'
            in response.json()['detail'][0]['msg']
        )

    def test_list_example(self, client):
        term = TermFactory()
        examples = TermExampleFactory.create_batch(
            language=term.origin_language,
            size=5,
            link_obj=term,
        )

        response = client.get(
            self.list_example_route(
                term=term.term, origin_language=term.origin_language
            )
        )

        assert response.status_code == 200
        assert len(response.json()['items']) == 5
        assert [
            TermExampleTranslationView(**example)
            for example in response.json()['items']
        ] == [
            TermExampleTranslationView(
                **example.model_dump(),
                **example.link.model_dump(exclude={'term_example_id', 'id'}),
            )
            for example in examples
        ]

    def test_list_example_pagination(self, client, session):
        term = TermFactory()
        examples = TermExampleFactory.create_batch(
            language=term.origin_language,
            size=15,
            link_obj=term,
        )

        response = client.get(
            self.list_example_route(
                term=term.term,
                origin_language=term.origin_language,
                size=5,
                page=2,
            )
        )
        [session.refresh(example) for example in examples]
        [session.refresh(example.link) for example in examples]

        assert response.status_code == 200
        assert [
            TermExampleTranslationView(**example)
            for example in response.json()['items']
        ] == [
            TermExampleTranslationView(
                **example.model_dump(),
                **example.link.model_dump(exclude={'term_example_id', 'id'}),
            )
            for example in examples[5:10]
        ]
        assert response.json()['total'] == 15
        assert 'size=5' in response.json()['next_page']
        assert 'page=3' in response.json()['next_page']
        assert f'term={term.term.replace(" ", "+")}' in response.json()['next_page']
        assert (
            f'origin_language={term.origin_language.value}'
            in response.json()['next_page']
        )
        assert 'size=5' in response.json()['previous_page']
        assert 'page=1' in response.json()['previous_page']
        assert f'term={term.term.replace(" ", "+")}' in response.json()['previous_page']
        assert (
            f'origin_language={term.origin_language.value}'
            in response.json()['previous_page']
        )

    def test_list_example_passing_a_term_form_as_term(
        self,
        client,
    ):
        term = TermFactory()
        TermLexicalFactory(
            term=term.term,
            origin_language=term.origin_language,
            type=TermLexicalType.FORM,
            value='TÉstÎng',
        )
        examples = TermExampleFactory.create_batch(
            link_obj=term,
            language=term.origin_language,
            size=5,
        )
        TermExampleFactory.create_batch(size=5)

        response = client.get(
            self.list_example_route(
                term='testing', origin_language=term.origin_language
            )
        )

        assert response.status_code == 200
        assert len(response.json()['items']) == 5
        assert [
            TermExampleTranslationView(**example)
            for example in response.json()['items']
        ] == [
            TermExampleTranslationView(
                **example.model_dump(),
                **example.link.model_dump(exclude={'term_example_id', 'id'}),
            )
            for example in examples
        ]

    def test_list_example_term_special_character(self, client):
        term = TermFactory(term='TÉstê')
        examples = TermExampleFactory.create_batch(
            language=term.origin_language,
            size=5,
            link_obj=term,
        )
        TermExampleFactory.create_batch(size=5)

        response = client.get(
            self.list_example_route(term='teste', origin_language=term.origin_language)
        )

        assert response.status_code == 200
        assert len(response.json()['items']) == 5
        assert [
            TermExampleTranslationView(**example)
            for example in response.json()['items']
        ] == [
            TermExampleTranslationView(
                **example.model_dump(),
                **example.link.model_dump(exclude={'term_example_id', 'id'}),
            )
            for example in examples
        ]

    def test_list_example_translation(self, client):
        term = TermFactory()
        examples = TermExampleFactory.create_batch(
            link_obj=term, language=term.origin_language, size=5
        )
        translations = [
            TermExampleTranslationFactory(
                term_example_id=example.id, language=Language.RUSSIAN
            )
            for example in examples
        ]

        examples2 = TermExampleFactory.create_batch(
            term=term.term, origin_language=term.origin_language, size=5
        )
        for example in examples2:
            TermExampleTranslationFactory(
                term_example_id=example.id, language=Language.SPANISH
            )

        response = client.get(
            self.list_example_route(
                term=term.term,
                origin_language=term.origin_language,
                translation_language=Language.RUSSIAN,
            )
        )

        assert response.status_code == 200
        assert len(response.json()['items']) == 5
        assert [TermExampleView(**example) for example in response.json()['items']] == [
            TermExampleView(
                **example.model_dump(),
                **example.link.model_dump(
                    exclude={'term_example_id', 'id', 'translation_language'}
                ),
                translation_language=translation.language,  # pyright: ignore[reportArgumentType]
                translation_example=translation.translation,  # pyright: ignore[reportArgumentType]
            )
            for example, translation in zip(examples, translations)
        ]

    def test_list_example_translation_pagination(self, client):
        term = TermFactory()
        examples = TermExampleFactory.create_batch(
            link_obj=term, language=term.origin_language, size=15
        )
        translations = [
            TermExampleTranslationFactory(
                term_example_id=example.id, language=Language.RUSSIAN
            )
            for example in examples
        ]

        examples2 = TermExampleFactory.create_batch(
            term=term.term, origin_language=term.origin_language, size=5
        )
        for example in examples2:
            TermExampleTranslationFactory(
                term_example_id=example.id, language=Language.SPANISH
            )

        response = client.get(
            self.list_example_route(
                term=term.term,
                origin_language=term.origin_language,
                translation_language=Language.RUSSIAN,
                page=2,
                size=5,
            )
        )

        assert response.status_code == 200
        assert (
            [TermExampleView(**example) for example in response.json()['items']]
            == [
                TermExampleView(
                    **example.model_dump(),
                    **example.link.model_dump(
                        exclude={'term_example_id', 'id', 'translation_language'}
                    ),
                    translation_language=translation.language,  # pyright: ignore[reportArgumentType]
                    translation_example=translation.translation,  # pyright: ignore[reportArgumentType]
                )
                for example, translation in zip(examples[5:10], translations[5:10])
            ]
        )
        assert response.json()['total'] == 15
        assert 'size=5' in response.json()['next_page']
        assert 'page=3' in response.json()['next_page']
        assert f'term={term.term.replace(" ", "+")}' in response.json()['next_page']
        assert (
            f'origin_language={term.origin_language.value}'
            in response.json()['next_page']
        )
        assert 'size=5' in response.json()['previous_page']
        assert 'page=1' in response.json()['previous_page']
        assert f'term={term.term.replace(" ", "+")}' in response.json()['previous_page']
        assert (
            f'origin_language={term.origin_language.value}'
            in response.json()['previous_page']
        )

    def test_list_example_translation_passing_a_term_form_as_term(
        self,
        client,
        session,
    ):
        term = TermFactory()
        TermLexicalFactory(
            term=term.term,
            origin_language=term.origin_language,
            type=TermLexicalType.FORM,
            value='TÉstÎng',
        )
        examples = TermExampleFactory.create_batch(
            language=term.origin_language, size=5, link_obj=term
        )
        translations = [
            TermExampleTranslationFactory(
                term_example_id=example.id, language=Language.RUSSIAN
            )
            for example in examples
        ]

        examples2 = TermExampleFactory.create_batch(
            term=term.term, origin_language=term.origin_language, size=5
        )
        for example in examples2:
            TermExampleTranslationFactory(
                term_example_id=example.id, language=Language.SPANISH
            )

        response = client.get(
            self.list_example_route(
                term='testing',
                origin_language=term.origin_language,
                translation_language=Language.RUSSIAN,
            )
        )
        [session.refresh(example) for example in examples]
        [session.refresh(translation) for translation in translations]

        assert response.status_code == 200
        assert len(response.json()['items']) == 5
        assert [TermExampleView(**example) for example in response.json()['items']] == [
            TermExampleView(
                **example.model_dump(),
                **example.link.model_dump(
                    exclude={'term_example_id', 'id', 'translation_language'}
                ),
                translation_language=translation.language,  # pyright: ignore[reportArgumentType]
                translation_example=translation.translation,  # pyright: ignore[reportArgumentType]
            )
            for example, translation in zip(examples, translations)
        ]

    def test_list_example_empty(self, client):
        term = TermFactory()

        response = client.get(
            self.list_example_route(
                term=term.term, origin_language=term.origin_language
            )
        )

        assert response.status_code == 200
        assert len(response.json()['items']) == 0

    def test_list_example_empty_translation(self, client):
        term = TermFactory()
        TermExampleFactory.create_batch(
            size=5,
            term=term.term,
            highlight=[[1, 4], [6, 8]],
            origin_language=term.origin_language,
            language=Language.RUSSIAN,
        )

        response = client.get(
            self.list_example_route(
                term=term.term,
                origin_language=term.origin_language,
                translation_language=Language.PORTUGUESE,
            )
        )

        assert response.status_code == 200
        assert len(response.json()['items']) == 0

    def test_list_example_filter_definition_id(self, client):
        term = TermFactory()
        definition = TermDefinitionFactory(
            term=term.term, origin_language=term.origin_language
        )
        examples = TermExampleFactory.create_batch(
            size=5, language=term.origin_language, link_obj=definition
        )
        TermExampleFactory.create_batch(
            size=5,
            language=term.origin_language,
        )

        response = client.get(
            self.list_example_route(
                term_definition_id=definition.id,
            )
        )

        assert response.status_code == 200
        assert len(response.json()['items']) == 5
        assert [
            TermExampleTranslationView(**example)
            for example in response.json()['items']
        ] == [
            TermExampleTranslationView(
                **example.model_dump(),
                **example.link.model_dump(
                    exclude={'term_example_id', 'id', 'translation_language'}
                ),
            )
            for example in examples
        ]

    def test_list_example_translation_filter_definition_id(self, client):
        definition = TermDefinitionFactory()
        examples = TermExampleFactory.create_batch(
            size=5, language=definition.origin_language, link_obj=definition
        )
        translations = [
            TermExampleTranslationFactory(
                term_example_id=example.id, language=Language.PORTUGUESE
            )
            for example in examples
        ]

        examples2 = TermExampleFactory.create_batch(
            size=5,
            language=definition.origin_language,
        )
        for example in examples2:
            TermExampleTranslationFactory(term_example_id=example.id)

        response = client.get(
            self.list_example_route(
                translation_language=Language.PORTUGUESE,
                term_definition_id=definition.id,
            )
        )

        assert response.status_code == 200
        assert len(response.json()['items']) == 5
        assert [TermExampleView(**example) for example in response.json()['items']] == [
            TermExampleView(
                **example.model_dump(),
                **example.link.model_dump(
                    exclude={'term_example_id', 'id', 'translation_language'}
                ),
                translation_language=translation.language,  # pyright: ignore[reportArgumentType]
                translation_example=translation.translation,  # pyright: ignore[reportArgumentType]
            )
            for example, translation in zip(examples, translations)
        ]

    def test_list_example_filter_lexical_id(self, client):
        term = TermFactory()
        lexical = TermLexicalFactory(
            term=term.term, origin_language=term.origin_language
        )
        examples = TermExampleFactory.create_batch(
            size=5, language=term.origin_language, link_obj=lexical
        )
        TermExampleFactory.create_batch(
            size=5,
            language=term.origin_language,
        )

        response = client.get(
            self.list_example_route(
                term_lexical_id=lexical.id,
            )
        )

        assert response.status_code == 200
        assert len(response.json()['items']) == 5
        assert [
            TermExampleTranslationView(**example)
            for example in response.json()['items']
        ] == [
            TermExampleTranslationView(
                **example.model_dump(),
                **example.link.model_dump(exclude={'term_example_id', 'id'}),
            )
            for example in examples
        ]

    def test_list_example_translation_filter_lexical_id(self, client):
        term = TermFactory()
        lexical = TermLexicalFactory(
            term=term.term, origin_language=term.origin_language
        )
        examples = TermExampleFactory.create_batch(
            size=5, language=term.origin_language, link_obj=lexical
        )
        translations = [
            TermExampleTranslationFactory(
                term_example_id=example.id, language=Language.PORTUGUESE
            )
            for example in examples
        ]

        examples2 = TermExampleFactory.create_batch(
            size=5,
            language=term.origin_language,
        )
        for example in examples2:
            TermExampleTranslationFactory(term_example_id=example.id)

        response = client.get(
            self.list_example_route(
                term_lexical_id=lexical.id,
                translation_language=Language.PORTUGUESE,
            )
        )

        assert response.status_code == 200
        assert len(response.json()['items']) == 5
        assert [TermExampleView(**example) for example in response.json()['items']] == [
            TermExampleView(
                **example.model_dump(),
                **example.link.model_dump(
                    exclude={'term_example_id', 'id', 'translation_language'}
                ),
                translation_language=translation.language,  # pyright: ignore[reportArgumentType]
                translation_example=translation.translation,  # pyright: ignore[reportArgumentType]
            )
            for example, translation in zip(examples, translations)
        ]

    def test_list_example_model_link_not_set(self, client):
        response = client.get(self.list_example_route())

        assert response.status_code == 422
        assert 'at least one object to link' in response.json()['detail'][0]['msg']

    @pytest.mark.parametrize(
        'term_attr', [{'term': 'test'}, {'origin_language': Language.PORTUGUESE}]
    )
    def test_list_example_model_link_term_not_right_setted(self, client, term_attr):
        response = client.get(self.list_example_route(**term_attr))

        assert response.status_code == 422
        assert (
            'you need to provide term and origin_language attributes'
            in response.json()['detail'][0]['msg']
        )

    @pytest.mark.parametrize(
        'link_attr',
        [
            {
                'term_definition_id': 123,
                'term': 'test',
                'origin_language': Language.PORTUGUESE,
            },
            {
                'term_definition_id': 123,
                'term_lexical_id': 400,
            },
        ],
    )
    def test_list_example_multiple_models(self, client, link_attr):
        response = client.get(self.list_example_route(**link_attr))

        assert response.status_code == 422
        assert 'reference two objects at once' in response.json()['detail'][0]['msg']


class TestTermLexical:
    create_lexical_route = app.url_path_for('create_lexical')

    def list_lexical_route(
        self, term=None, origin_language=None, type=None, page=None, size=None
    ):
        url = app.url_path_for('list_lexical')
        return set_url_params(
            url,
            term=term,
            origin_language=origin_language,
            type=type,
            page=page,
            size=size,
        )

    def update_lexical_route(self, lexical_id):
        return app.url_path_for('update_lexical', lexical_id=lexical_id)

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_create_lexical(self, session, client, generate_payload, token_header):
        payload = generate_payload(TermLexicalFactory)
        TermFactory(term=payload['term'], origin_language=payload['origin_language'])

        response = client.post(
            self.create_lexical_route, json=payload, headers=token_header
        )

        assert response.status_code == 201
        assert_json_response(
            session, TermLexical, response.json(), id=response.json()['id']
        )

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_create_lexical_passing_a_term_form_as_term(
        self, session, client, generate_payload, token_header
    ):
        payload = generate_payload(TermLexicalFactory)
        term = TermFactory(
            term=payload['term'], origin_language=payload['origin_language']
        )
        TermLexicalFactory(
            term=term.term,
            origin_language=term.origin_language,
            type=TermLexicalType.FORM,
            value='TÉstÎng',
        )
        payload.update(term='testing', origin_language=term.origin_language)

        response = client.post(
            self.create_lexical_route, json=payload, headers=token_header
        )

        assert response.status_code == 201
        assert_json_response(
            session, TermLexical, response.json(), id=response.json()['id']
        )

    def test_create_lexical_user_is_not_authenticated(self, client, generate_payload):
        payload = generate_payload(TermLexicalFactory)

        response = client.post(self.create_lexical_route, json=payload)

        assert response.status_code == 401

    def test_create_lexical_user_does_not_have_permission(
        self, client, generate_payload, token_header
    ):
        payload = generate_payload(TermLexicalFactory)

        response = client.post(
            self.create_lexical_route, json=payload, headers=token_header
        )

        assert response.status_code == 403

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_create_lexical_term_does_not_exists(
        self, client, generate_payload, token_header
    ):
        payload = generate_payload(TermLexicalFactory)

        response = client.post(
            self.create_lexical_route, json=payload, headers=token_header
        )

        assert response.status_code == 404

    def test_list_lexical(self, client):
        term = TermFactory()
        term_lexicals = TermLexicalFactory.create_batch(
            term=term.term,
            origin_language=term.origin_language,
            type=TermLexicalType.ANTONYM,
            size=5,
        )

        response = client.get(
            self.list_lexical_route(
                term=term.term,
                origin_language=term.origin_language,
                type=TermLexicalType.ANTONYM,
            )
        )

        assert response.status_code == 200
        assert len(response.json()['items']) == 5
        assert [
            TermLexical(**lexical) for lexical in response.json()['items']
        ] == term_lexicals

    def test_list_lexical_pagination(self, client):
        term = TermFactory()
        lexicals = TermLexicalFactory.create_batch(
            term=term.term,
            origin_language=term.origin_language,
            type=TermLexicalType.ANTONYM,
            size=15,
        )

        response = client.get(
            self.list_lexical_route(
                term=term.term,
                origin_language=term.origin_language,
                type=TermLexicalType.ANTONYM,
                page=2,
                size=5,
            )
        )

        assert response.status_code == 200
        assert [
            TermLexical(**lexical) for lexical in response.json()['items']
        ] == lexicals[5:10]
        assert response.json()['total'] == 15
        assert 'size=5' in response.json()['next_page']
        assert 'page=3' in response.json()['next_page']
        assert f'term={term.term.replace(" ", "+")}' in response.json()['next_page']
        assert (
            f'origin_language={term.origin_language.value}'
            in response.json()['next_page']
        )
        assert TermLexicalType.ANTONYM.value in response.json()['next_page']
        assert 'size=5' in response.json()['previous_page']
        assert 'page=1' in response.json()['previous_page']
        assert f'term={term.term.replace(" ", "+")}' in response.json()['previous_page']
        assert (
            f'origin_language={term.origin_language.value}'
            in response.json()['previous_page']
        )
        assert TermLexicalType.ANTONYM.value in response.json()['previous_page']

    def test_list_lexical_passing_a_term_form_as_term(
        self,
        client,
    ):
        term = TermFactory()
        TermLexicalFactory(
            term=term.term,
            origin_language=term.origin_language,
            type=TermLexicalType.FORM,
            value='TÉstÎng',
        )
        term_lexicals = TermLexicalFactory.create_batch(
            term=term.term,
            origin_language=term.origin_language,
            type=TermLexicalType.ANTONYM,
            size=5,
        )

        response = client.get(
            self.list_lexical_route(
                term='testing',
                origin_language=term.origin_language,
                type=TermLexicalType.ANTONYM,
            )
        )

        assert response.status_code == 200
        assert len(response.json()['items']) == 5
        assert [
            TermLexical(**lexical) for lexical in response.json()['items']
        ] == term_lexicals

    def test_list_lexical_term_special_character(self, client):
        term = TermFactory(term='TésTÊ')
        term_lexicals = TermLexicalFactory.create_batch(
            term=term.term,
            origin_language=term.origin_language,
            type=TermLexicalType.ANTONYM,
            size=5,
        )

        response = client.get(
            self.list_lexical_route(
                term='teste',
                origin_language=term.origin_language,
                type=TermLexicalType.ANTONYM,
            )
        )

        assert response.status_code == 200
        assert len(response.json()['items']) == 5
        assert [
            TermLexical(**lexical) for lexical in response.json()['items']
        ] == term_lexicals

    def test_list_lexical_empty(self, client):
        response = client.get(
            self.list_lexical_route(term='test', origin_language='pt', type='antonym')
        )

        assert response.status_code == 200
        assert len(response.json()['items']) == 0

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_update_lexical(self, session, client, generate_payload, token_header):
        lexical = TermLexicalFactory(extra={'test1': 1})
        payload = generate_payload(TermLexicalFactory, include={'value'})
        payload.update(extra={'test2': 2})

        response = client.patch(
            self.update_lexical_route(lexical.id),
            json=payload,
            headers=token_header,
        )
        session.refresh(lexical)

        assert response.status_code == 200
        assert lexical.value == payload['value']
        assert lexical.extra == {'test1': 1, 'test2': 2}

    def test_update_lexical_user_not_authenticated(self, client, generate_payload):
        lexical = TermLexicalFactory(extra={'test1': 1})
        payload = generate_payload(TermLexicalFactory, include={'value'})

        response = client.patch(
            self.update_lexical_route(lexical.id),
            json=payload,
        )

        assert response.status_code == 401

    def test_update_lexical_user_not_enough_permission(
        self, client, generate_payload, token_header
    ):
        lexical = TermLexicalFactory(extra={'test1': 1})
        payload = generate_payload(TermLexicalFactory, include={'value'})

        response = client.patch(
            self.update_lexical_route(lexical.id), json=payload, headers=token_header
        )

        assert response.status_code == 403

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_update_lexical_not_found(self, client, generate_payload, token_header):
        payload = generate_payload(TermLexicalFactory, include={'value'})

        response = client.patch(
            self.update_lexical_route(123), json=payload, headers=token_header
        )

        assert response.status_code == 404
