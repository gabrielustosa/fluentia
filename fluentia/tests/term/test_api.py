import pytest

from fluentia.apps.term.constants import (
    Language,
    PartOfSpeech,
    TermLevel,
    TermLexicalType,
)
from fluentia.apps.term.models import (
    Pronunciation,
    PronunciationLink,
    Term,
    TermDefinition,
    TermDefinitionTranslation,
    TermExample,
    TermExampleTranslation,
    TermLexical,
)
from fluentia.apps.term.schema import (
    PronunciationView,
    TermDefinitionView,
    TermExampleView,
    TermLexicalSchema,
    TermSchema,
)
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
from fluentia.tests.utils import assert_json_response, set_url_params


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
    def test_create_term_alreaday_exists(self, client, token_header, generate_payload):
        payload = generate_payload(TermFactory)
        term = TermFactory(**payload)

        response = client.post(
            self.term_create_route,
            json=payload,
            headers=token_header,
        )

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
        term = TermFactory(term='TésTé.?')

        response = client.get(
            self.get_term_route(term='teste', origin_language=term.origin_language)
        )

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

    def test_search_term(self, client):
        terms = [
            TermFactory(term=f'test {i}', origin_language=Language.PORTUGUESE)
            for i in range(5)
        ]

        response = client.get(
            self.search_term_route(text='test', origin_language=Language.PORTUGUESE)
        )

        assert response.status_code == 200
        assert len(response.json()) == 5
        assert [Term(**term) for term in response.json()] == terms

    def test_search_term_special_character(self, client):
        terms = [
            TermFactory(term=f'tésté.!#! {i}', origin_language=Language.PORTUGUESE)
            for i in range(5)
        ]

        response = client.get(
            self.search_term_route(text='teste', origin_language=Language.PORTUGUESE)
        )

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
                meaning=f'tésté.!#!@-{i}',
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

    def get_pronunciation_route(
        self,
        term=None,
        origin_language=None,
        term_example_id=None,
        term_lexical_id=None,
    ):
        url = app.url_path_for('get_pronunciation')
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

    parmetrize_pronunciations = pytest.mark.parametrize(
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

    @parmetrize_pronunciations
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
    def test_create_pronunciation_model_attribute_not_set(
        self, client, generate_payload, token_header
    ):
        payload = generate_payload(PronunciationFactory)

        response = client.post(
            self.create_pronunciation_route, json=payload, headers=token_header
        )

        assert response.status_code == 422

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_create_pronunciation_multiple_models_with_term(
        self, client, generate_payload, token_header
    ):
        payload = generate_payload(PronunciationFactory)
        payload.update(
            {
                'term_example_id': 123,
                'term': 'test',
                'origin_language': Language.PORTUGUESE,
            }
        )

        response = client.post(
            self.create_pronunciation_route, json=payload, headers=token_header
        )

        assert response.status_code == 422

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_create_pronunciation_multiple_models(
        self, client, generate_payload, token_header
    ):
        payload = generate_payload(PronunciationFactory)
        payload.update(
            {
                'term_example_id': 123,
                'term_lexical_id': 400,
            }
        )

        response = client.post(
            self.create_pronunciation_route, json=payload, headers=token_header
        )

        assert response.status_code == 422

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

    @parmetrize_pronunciations
    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_create_pronunciation_model_not_found(
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

    @parmetrize_pronunciations
    def test_get_pronunciation(self, client, session, item):
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

        response = client.get(self.get_pronunciation_route(**linked_attr))

        assert response.status_code == 200
        assert len(response.json()) == 5
        assert [
            Pronunciation(**pronunciation) for pronunciation in response.json()
        ] == pronunciations

    def test_get_pronunciation_term_special_character(self, client, session):
        term = TermFactory(term='TésTé*&.')
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
            self.get_pronunciation_route(
                term='teste', origin_language=term.origin_language
            )
        )

        assert response.status_code == 200
        assert len(response.json()) == 5
        assert [
            Pronunciation(**pronunciation) for pronunciation in response.json()
        ] == pronunciations

    @parmetrize_pronunciations
    def test_get_pronunciation_empty(self, client, item):
        Factory, attr = item
        db_factory = Factory()
        linked_attr = self._get_linked_attributes(attr, db_factory)
        PronunciationFactory.create_batch(5)

        response = client.get(self.get_pronunciation_route(**linked_attr))

        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_get_pronunciation_model_not_set(self, client):
        response = client.get(self.get_pronunciation_route())

        assert response.status_code == 422

    def test_get_pronunciation_term_model_invalid(self, client):
        response = client.get(self.get_pronunciation_route(term='test'))

        assert response.status_code == 422

    def test_get_pronunciation_term_model_multiple_invalid(self, client):
        response = client.get(
            self.get_pronunciation_route(
                term='test', origin_language=Language.PORTUGUESE, term_example_id=1
            )
        )

        assert response.status_code == 422

    def test_get_pronunciation_multiple_models(self, client):
        response = client.get(
            self.get_pronunciation_route(term_example_id=1, term_lexical_id=2)
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

    def get_definition_route(
        self,
        term=None,
        origin_language=None,
        translation_language=None,
        part_of_speech=None,
        term_level=None,
    ):
        url = app.url_path_for('get_definition')
        return set_url_params(
            url,
            term=term,
            origin_language=origin_language,
            translation_language=translation_language,
            part_of_speech=part_of_speech,
            term_level=term_level,
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
    def test_create_definition(self, session, client, generate_payload, token_header):
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
    def test_create_definition_already_exists(
        self, client, generate_payload, session, token_header
    ):
        payload = generate_payload(
            TermDefinitionFactory,
            term_level=None,
            definition='Tésté#!#.',
            term='TésTê!#;',
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

    def test_get_definition(self, client):
        term = TermFactory()
        definitions = TermDefinitionFactory.create_batch(
            term=term.term, origin_language=term.origin_language, size=5
        )
        TermDefinitionFactory.create_batch(size=5)

        response = client.get(
            self.get_definition_route(
                term=term.term, origin_language=term.origin_language
            )
        )

        assert response.status_code == 200
        assert len(response.json()) == 5
        assert [
            TermDefinition(**definition) for definition in response.json()
        ] == definitions

    def test_get_definition_term_special_character(self, client):
        term = TermFactory(term='TéStÉ$!.')
        definitions = TermDefinitionFactory.create_batch(
            term=term.term, origin_language=term.origin_language, size=5
        )
        TermDefinitionFactory.create_batch(size=5)

        response = client.get(
            self.get_definition_route(
                term='teste!', origin_language=term.origin_language
            )
        )

        assert response.status_code == 200
        assert len(response.json()) == 5
        assert [
            TermDefinition(**definition) for definition in response.json()
        ] == definitions

    def test_get_definition_translation(self, client):
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
            self.get_definition_route(
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

    def test_get_definition_empty(self, client):
        term = TermFactory()
        TermDefinitionFactory.create_batch(size=5)

        response = client.get(
            self.get_definition_route(
                term=term.term, origin_language=term.origin_language
            )
        )

        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_get_definition_translation_empty(self, client):
        term = TermFactory()
        TermDefinitionFactory.create_batch(
            term=term.term, origin_language=term.origin_language, size=5
        )

        response = client.get(
            self.get_definition_route(
                term=term.term,
                origin_language=term.origin_language,
                translation_language=Language.ITALIAN,
            )
        )

        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_get_definition_filter_part_of_speech(self, client):
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
            self.get_definition_route(
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

    def test_get_definition_filter_term_level(self, client):
        term = TermFactory()
        definitions = TermDefinitionFactory.create_batch(
            term=term.term,
            origin_language=term.origin_language,
            size=5,
            term_level=TermLevel.ADVANCED,
        )
        TermDefinitionFactory.create_batch(
            term=term.term,
            origin_language=term.origin_language,
            size=5,
            term_level=TermLevel.BEGINNER,
        )

        response = client.get(
            self.get_definition_route(
                term=term.term,
                origin_language=term.origin_language,
                term_level=TermLevel.ADVANCED,
            )
        )

        assert response.status_code == 200
        assert len(response.json()) == 5
        assert [
            TermDefinition(**definition) for definition in response.json()
        ] == definitions

    def test_get_definition_translation_filter_part_of_speech(self, client):
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
            self.get_definition_route(
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

    def test_get_definition_translation_filter_term_level(self, client):
        term = TermFactory()
        definitions_with_translation = TermDefinitionFactory.create_batch(
            term=term.term,
            origin_language=term.origin_language,
            size=5,
            term_level=TermLevel.ADVANCED,
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
            term_level=TermLevel.BEGINNER,
        )
        for definition in definitions_with_translation2:
            TermDefinitionTranslationFactory(
                language=Language.ITALIAN, term_definition_id=definition.id
            )

        response = client.get(
            self.get_definition_route(
                term=term.term,
                origin_language=term.origin_language,
                term_level=TermLevel.ADVANCED,
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
        definition = TermDefinitionFactory()
        payload = generate_payload(
            TermDefinitionFactory, include={'definition', 'term_level'}
        )

        response = client.patch(
            self.update_definition_route(definition.id),
            json=payload,
            headers=token_header,
        )
        session.refresh(definition)

        assert response.status_code == 200
        assert definition.definition == payload['definition']
        assert definition.term_level == payload['term_level']

    def test_update_definition_user_not_authenticated(self, client, generate_payload):
        definition = TermDefinitionFactory()
        payload = generate_payload(
            TermDefinitionFactory, include={'definition', 'term_level'}
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
            TermDefinitionFactory, include={'definition', 'term_level'}
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
            TermDefinitionFactory, include={'definition', 'term_level'}
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

        assert response.status_code == 200
        assert definition_translation.meaning == payload['meaning']
        assert definition_translation.translation == payload['translation']

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

    def get_example_route(
        self,
        term=None,
        origin_language=None,
        translation_language=None,
        term_definition_id=None,
        term_lexical_id=None,
    ):
        url = app.url_path_for('get_example')
        return set_url_params(
            url,
            term=term,
            origin_language=origin_language,
            translation_language=translation_language,
            term_definition_id=term_definition_id,
            term_lexical_id=term_lexical_id,
        )

    def update_example_route(self, example_id):
        return app.url_path_for('update_example', example_id=example_id)

    def update_example_translation_route(self, example_id, language):
        return app.url_path_for(
            'update_example_translation',
            example_id=example_id,
            language=language.value,
        )

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_create_example(self, session, client, generate_payload, token_header):
        payload = generate_payload(TermExampleFactory)
        TermFactory(term=payload['term'], origin_language=payload['origin_language'])

        response = client.post(
            self.create_example_route, json=payload, headers=token_header
        )

        assert response.status_code == 201
        assert_json_response(
            session, TermExample, response.json(), id=response.json()['id']
        )

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_create_example_with_term_definition_id(
        self, session, client, generate_payload, token_header
    ):
        payload = generate_payload(TermExampleFactory)
        TermFactory(term=payload['term'], origin_language=payload['origin_language'])
        definition = TermDefinitionFactory(
            term=payload['term'], origin_language=payload['origin_language']
        )
        payload['term_definition_id'] = definition.id

        response = client.post(
            self.create_example_route, json=payload, headers=token_header
        )

        assert response.status_code == 201
        assert response.json()['term_definition_id'] == definition.id
        assert_json_response(
            session, TermExample, response.json(), id=response.json()['id']
        )

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_create_example_with_term_lexical_id(
        self, session, client, generate_payload, token_header
    ):
        payload = generate_payload(TermExampleFactory)
        TermFactory(term=payload['term'], origin_language=payload['origin_language'])
        lexical = TermLexicalFactory(
            term=payload['term'], origin_language=payload['origin_language']
        )
        payload['term_lexical_id'] = lexical.id

        response = client.post(
            self.create_example_route, json=payload, headers=token_header
        )

        assert response.status_code == 201
        assert response.json()['term_lexical_id'] == lexical.id
        assert_json_response(
            session, TermExample, response.json(), id=response.json()['id']
        )

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_create_example_already_exists(
        self, client, generate_payload, token_header
    ):
        payload = generate_payload(
            TermExampleFactory, example='*test* Têstè!#', term='TéStê!#!'
        )
        db_example = TermExampleFactory(**payload)
        payload.update({'example': '*test* teste', 'term': 'teste'})

        response = client.post(
            self.create_example_route, json=payload, headers=token_header
        )

        assert response.status_code == 200
        assert response.json()['id'] == db_example.id

    def test_create_example_user_is_authenticated(self, client, generate_payload):
        payload = generate_payload(TermExampleFactory)
        TermFactory(term=payload['term'], origin_language=payload['origin_language'])

        response = client.post(self.create_example_route, json=payload)

        assert response.status_code == 401

    def test_create_example_user_not_enough_permission(
        self, client, generate_payload, token_header
    ):
        payload = generate_payload(TermExampleFactory)
        TermFactory(term=payload['term'], origin_language=payload['origin_language'])

        response = client.post(
            self.create_example_route, json=payload, headers=token_header
        )

        assert response.status_code == 403

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_create_example_term_not_found(
        self, client, generate_payload, token_header
    ):
        payload = generate_payload(TermExampleFactory)

        response = client.post(
            self.create_example_route, json=payload, headers=token_header
        )

        assert response.status_code == 404

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_create_example_not_highlighted(
        self, client, generate_payload, token_header
    ):
        payload = generate_payload(TermExampleFactory, example='test test test')
        TermFactory(term=payload['term'], origin_language=payload['origin_language'])

        response = client.post(
            self.create_example_route, json=payload, headers=token_header
        )

        assert response.status_code == 422

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_create_example_translation(
        self, session, client, generate_payload, token_header
    ):
        example = TermExampleFactory()
        payload = generate_payload(TermExampleTranslationFactory)
        payload.update({'term_example_id': example.id})

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

    def test_create_example_translation_user_is_not_authenticated(
        self, client, generate_payload
    ):
        example = TermExampleFactory()
        payload = generate_payload(TermExampleTranslationFactory)
        payload.update({'term_example_id': example.id})

        response = client.post(self.create_example_translation_route, json=payload)

        assert response.status_code == 401

    def test_create_example_translation_user_not_enough_permission(
        self, client, generate_payload, token_header
    ):
        example = TermExampleFactory()
        payload = generate_payload(TermExampleTranslationFactory)
        payload.update({'term_example_id': example.id})

        response = client.post(
            self.create_example_translation_route, json=payload, headers=token_header
        )

        assert response.status_code == 403

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_create_example_translation_example_was_not_found(
        self, client, generate_payload, token_header
    ):
        payload = generate_payload(TermExampleTranslationFactory)
        payload.update({'term_example_id': 123})

        response = client.post(
            self.create_example_translation_route, json=payload, headers=token_header
        )

        assert response.status_code == 404

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_create_example_translation_conflict(
        self, client, generate_payload, token_header
    ):
        example = TermExampleFactory()
        payload = generate_payload(TermExampleTranslationFactory)
        payload.update({'term_example_id': example.id})
        TermExampleTranslationFactory(**payload)

        response = client.post(
            self.create_example_translation_route, json=payload, headers=token_header
        )

        assert response.status_code == 409

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_create_example_translation_not_highlighted(
        self, client, generate_payload, token_header
    ):
        example = TermExampleFactory()
        payload = generate_payload(TermExampleTranslationFactory, translation='test')
        payload.update({'term_example_id': example.id})

        response = client.post(
            self.create_example_translation_route, json=payload, headers=token_header
        )

        assert response.status_code == 422

    def test_get_example(self, client):
        term = TermFactory()
        examples = TermExampleFactory.create_batch(
            term=term.term, origin_language=term.origin_language, size=5
        )
        TermExampleFactory.create_batch(size=5)

        response = client.get(
            self.get_example_route(term=term.term, origin_language=term.origin_language)
        )

        assert response.status_code == 200
        assert [TermExample(**example) for example in response.json()] == examples

    def test_get_example_term_special_character(self, client):
        term = TermFactory(term='TÉstê$!@')
        examples = TermExampleFactory.create_batch(
            term=term.term, origin_language=term.origin_language, size=5
        )
        TermExampleFactory.create_batch(size=5)

        response = client.get(
            self.get_example_route(term='teste', origin_language=term.origin_language)
        )

        assert response.status_code == 200
        assert [TermExample(**example) for example in response.json()] == examples

    def test_get_example_with_translation(self, client):
        term = TermFactory()
        examples = TermExampleFactory.create_batch(
            term=term.term, origin_language=term.origin_language, size=5
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
            self.get_example_route(
                term=term.term,
                origin_language=term.origin_language,
                translation_language=Language.RUSSIAN,
            )
        )

        assert response.status_code == 200
        assert [TermExampleView(**example) for example in response.json()] == [
            TermExampleView(
                **example.model_dump(),
                translation_language=translation.language,  # pyright: ignore[reportArgumentType]
                translation_example=translation.translation,  # pyright: ignore[reportArgumentType]
            )
            for example, translation in zip(examples, translations)
        ]

    def test_get_example_empty(self, client):
        term = TermFactory()
        TermExampleFactory.create_batch(size=5)

        response = client.get(
            self.get_example_route(term=term.term, origin_language=term.origin_language)
        )

        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_get_example_empty_translation(self, client):
        term = TermFactory()
        TermExampleFactory.create_batch(
            size=5,
            term=term.term,
            origin_language=term.origin_language,
            language=Language.RUSSIAN,
        )

        response = client.get(
            self.get_example_route(
                term=term.term,
                origin_language=term.origin_language,
                translation_language=Language.PORTUGUESE,
            )
        )

        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_get_example_filter_definition_id(self, client):
        term = TermFactory()
        definition = TermDefinitionFactory(
            term=term.term, origin_language=term.origin_language
        )
        examples = TermExampleFactory.create_batch(
            size=5,
            term=term.term,
            origin_language=term.origin_language,
            term_definition_id=definition.id,
        )
        TermExampleFactory.create_batch(
            size=5,
            term=term.term,
            origin_language=term.origin_language,
        )

        response = client.get(
            self.get_example_route(
                term=term.term,
                origin_language=term.origin_language,
                term_definition_id=definition.id,
            )
        )

        assert response.status_code == 200
        assert [TermExample(**example) for example in response.json()] == examples

    def test_get_example_translation_filter_definition_id(self, client):
        term = TermFactory()
        definition = TermDefinitionFactory(
            term=term.term, origin_language=term.origin_language
        )
        examples = TermExampleFactory.create_batch(
            size=5,
            term=term.term,
            origin_language=term.origin_language,
            term_definition_id=definition.id,
        )
        translations = [
            TermExampleTranslationFactory(
                term_example_id=example.id, language=Language.PORTUGUESE
            )
            for example in examples
        ]
        examples2 = TermExampleFactory.create_batch(
            size=5,
            term=term.term,
            origin_language=term.origin_language,
        )
        for example in examples2:
            TermExampleTranslationFactory(term_example_id=example.id)

        response = client.get(
            self.get_example_route(
                term=term.term,
                origin_language=term.origin_language,
                translation_language=Language.PORTUGUESE,
                term_definition_id=definition.id,
            )
        )

        assert response.status_code == 200
        assert [TermExampleView(**example) for example in response.json()] == [
            TermExampleView(
                **example.model_dump(),
                translation_language=translation.language,  # pyright: ignore[reportArgumentType]
                translation_example=translation.translation,  # pyright: ignore[reportArgumentType]
            )
            for example, translation in zip(examples, translations)
        ]

    def test_get_example_filter_lexical_id(self, client):
        term = TermFactory()
        lexical = TermLexicalFactory(
            term=term.term, origin_language=term.origin_language
        )
        examples = TermExampleFactory.create_batch(
            size=5,
            term=term.term,
            origin_language=term.origin_language,
            term_lexical_id=lexical.id,
        )
        translations = [
            TermExampleTranslationFactory(
                term_example_id=example.id, language=Language.PORTUGUESE
            )
            for example in examples
        ]
        examples2 = TermExampleFactory.create_batch(
            size=5,
            term=term.term,
            origin_language=term.origin_language,
        )
        for example in examples2:
            TermExampleTranslationFactory(term_example_id=example.id)

        response = client.get(
            self.get_example_route(
                term=term.term,
                origin_language=term.origin_language,
                term_lexical_id=lexical.id,
                translation_language=Language.PORTUGUESE,
            )
        )

        assert response.status_code == 200
        assert [TermExampleView(**example) for example in response.json()] == [
            TermExampleView(
                **example.model_dump(),
                translation_language=translation.language,  # pyright: ignore[reportArgumentType]
                translation_example=translation.translation,  # pyright: ignore[reportArgumentType]
            )
            for example, translation in zip(examples, translations)
        ]

    def test_get_example_translation_filter_lexical_id(self, client):
        term = TermFactory()
        lexical = TermLexicalFactory(
            term=term.term, origin_language=term.origin_language
        )
        examples = TermExampleFactory.create_batch(
            size=5,
            term=term.term,
            origin_language=term.origin_language,
            term_lexical_id=lexical.id,
        )
        TermExampleFactory.create_batch(
            size=5,
            term=term.term,
            origin_language=term.origin_language,
        )

        response = client.get(
            self.get_example_route(
                term=term.term,
                origin_language=term.origin_language,
                term_lexical_id=lexical.id,
            )
        )

        assert response.status_code == 200
        assert [TermExample(**example) for example in response.json()] == examples

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_update_example(self, client, session, generate_payload, token_header):
        payload = generate_payload(TermExampleFactory, include={'example'})
        example = TermExampleFactory()

        response = client.patch(
            self.update_example_route(example.id),
            json=payload,
            headers=token_header,
        )
        session.refresh(example)

        assert response.status_code == 200
        assert example.example == payload['example']

    def test_update_example_user_not_authenticated(self, client, generate_payload):
        payload = generate_payload(TermExampleFactory, include={'example'})
        example = TermExampleFactory()

        response = client.patch(
            self.update_example_route(example.id),
            json=payload,
        )

        assert response.status_code == 401

    def test_update_example_user_not_enough_permissions(
        self, client, generate_payload, token_header
    ):
        payload = generate_payload(TermExampleFactory, include={'example'})
        example = TermExampleFactory()

        response = client.patch(
            self.update_example_route(example.id),
            json=payload,
            headers=token_header,
        )

        assert response.status_code == 403

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_update_example_does_not_exists(
        self, client, generate_payload, token_header
    ):
        payload = generate_payload(TermExampleFactory, include={'example'})

        response = client.patch(
            self.update_example_route(123),
            json=payload,
            headers=token_header,
        )

        assert response.status_code == 404

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_update_example_is_not_highlighted(self, client, token_header):
        payload = {'example': 'test test test'}
        example = TermExampleFactory()

        response = client.patch(
            self.update_example_route(example.id),
            json=payload,
            headers=token_header,
        )

        assert response.status_code == 422

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_update_example_translation(
        self, client, session, generate_payload, token_header
    ):
        payload = generate_payload(
            TermExampleTranslationFactory, include={'translation'}
        )
        example = TermExampleFactory()
        translation = TermExampleTranslationFactory(term_example_id=example.id)

        response = client.patch(
            self.update_example_translation_route(example.id, translation.language),
            json=payload,
            headers=token_header,
        )
        session.refresh(translation)

        assert response.status_code == 200
        assert translation.translation == payload['translation']

    def test_update_example_translation_user_not_authenticated(
        self, client, generate_payload
    ):
        payload = generate_payload(
            TermExampleTranslationFactory, include={'translation'}
        )
        example = TermExampleFactory()
        translation = TermExampleTranslationFactory(term_example_id=example.id)

        response = client.patch(
            self.update_example_translation_route(example.id, translation.language),
            json=payload,
        )

        assert response.status_code == 401

    def test_update_example_translation_user_not_enough_permission(
        self, client, generate_payload, token_header
    ):
        payload = generate_payload(
            TermExampleTranslationFactory, include={'translation'}
        )
        example = TermExampleFactory()
        translation = TermExampleTranslationFactory(term_example_id=example.id)

        response = client.patch(
            self.update_example_translation_route(example.id, translation.language),
            json=payload,
            headers=token_header,
        )

        assert response.status_code == 403

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_update_example_translation_example_does_not_exists(
        self, client, session, generate_payload, token_header
    ):
        payload = generate_payload(
            TermExampleTranslationFactory, include={'translation'}
        )

        response = client.patch(
            self.update_example_translation_route(123, Language.PORTUGUESE),
            json=payload,
            headers=token_header,
        )

        assert response.status_code == 404

    @pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
    def test_update_example_translation_is_not_highlighted(self, client, token_header):
        payload = {'translation': 'test test test'}
        example = TermExampleFactory()
        translation = TermExampleTranslationFactory(term_example_id=example.id)

        response = client.patch(
            self.update_example_translation_route(
                example.id,
                translation.language,
            ),
            json=payload,
            headers=token_header,
        )

        assert response.status_code == 422


class TestTermLexical:
    create_lexical_route = app.url_path_for('create_lexical')

    def get_lexical_route(self, term=None, origin_language=None, type=None):
        url = app.url_path_for('get_lexical')
        return set_url_params(
            url, term=term, origin_language=origin_language, type=type
        )

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

    def test_get_lexical(self, client):
        term = TermFactory()
        term_lexicals = TermLexicalFactory.create_batch(
            term=term.term,
            origin_language=term.origin_language,
            type=TermLexicalType.ANTONYM,
            size=5,
        )

        response = client.get(
            self.get_lexical_route(
                term=term.term,
                origin_language=term.origin_language,
                type=TermLexicalType.ANTONYM,
            )
        )

        assert response.status_code == 200
        assert len(response.json()) == 5
        assert [TermLexical(**lexical) for lexical in response.json()] == term_lexicals

    def test_get_lexical_term_special_character(self, client):
        term = TermFactory(term='TésTÊ!#!')
        term_lexicals = TermLexicalFactory.create_batch(
            term=term.term,
            origin_language=term.origin_language,
            type=TermLexicalType.ANTONYM,
            size=5,
        )

        response = client.get(
            self.get_lexical_route(
                term='teste',
                origin_language=term.origin_language,
                type=TermLexicalType.ANTONYM,
            )
        )

        assert response.status_code == 200
        assert len(response.json()) == 5
        assert [TermLexical(**lexical) for lexical in response.json()] == term_lexicals

    def test_get_lexical_empty(self, client):
        response = client.get(
            self.get_lexical_route(term='test', origin_language='pt', type='antonym')
        )

        assert response.status_code == 200
        assert len(response.json()) == 0
