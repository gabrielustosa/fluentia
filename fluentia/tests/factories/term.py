import factory
from factory import fuzzy

from fluentia.apps.term.constants import Language, Level, PartOfSpeech, TermLexicalType
from fluentia.apps.term.models import (
    Pronunciation,
    Term,
    TermDefinition,
    TermDefinitionTranslation,
    TermExample,
    TermExampleLink,
    TermExampleTranslation,
    TermLexical,
)
from fluentia.core.model.shortcut import get_or_create_object


class TermFactoryBase(factory.alchemy.SQLAlchemyModelFactory):
    term = factory.Faker('sentence')
    origin_language = fuzzy.FuzzyChoice(Language)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        get_or_create_object(
            Term,
            session=cls._meta.sqlalchemy_session,
            term=kwargs.get('term'),
            origin_language=kwargs.get('origin_language'),
        )
        return super()._create(model_class, *args, **kwargs)

    class Meta:
        abstract = True


class TermFactory(factory.alchemy.SQLAlchemyModelFactory):
    term = factory.Faker('sentence')
    origin_language = fuzzy.FuzzyChoice(Language)

    class Meta:
        model = Term
        sqlalchemy_session_persistence = 'commit'


class PronunciationFactory(factory.alchemy.SQLAlchemyModelFactory):
    audio_file = factory.Faker('url')
    description = factory.Faker('sentence')
    language = fuzzy.FuzzyChoice(Language)
    phonetic = factory.Faker('name')
    text = factory.Faker('sentence')

    class Meta:
        model = Pronunciation
        sqlalchemy_session_persistence = 'commit'


class TermDefinitionFactory(TermFactoryBase):
    level = fuzzy.FuzzyChoice(Level)
    part_of_speech = fuzzy.FuzzyChoice(PartOfSpeech)
    definition = factory.Faker('sentence')
    extra = {'test': '123', 'test_2': '234'}

    class Meta:
        model = TermDefinition
        sqlalchemy_session_persistence = 'commit'


class TermDefinitionTranslationFactory(factory.alchemy.SQLAlchemyModelFactory):
    language = fuzzy.FuzzyChoice(Language)
    translation = factory.Faker('sentence')
    meaning = factory.Faker('sentence')
    extra = {'test': '123', 'test_2': '234'}

    class Meta:
        model = TermDefinitionTranslation
        sqlalchemy_session_persistence = 'commit'


class TermExampleFactory(factory.alchemy.SQLAlchemyModelFactory):
    language = fuzzy.FuzzyChoice(Language)
    example = factory.Faker('sentence', nb_words=8)
    level = fuzzy.FuzzyChoice(Level)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        link_obj = kwargs.pop('link_obj', None)
        if link_obj is None:
            link_obj = TermFactory()
        link_attr = {}
        if isinstance(link_obj, Term):
            link_attr.update(
                term=link_obj.term, origin_language=link_obj.origin_language
            )
        elif isinstance(link_obj, TermDefinition):
            link_attr.update(term_definition_id=link_obj.id)
        elif isinstance(link_obj, TermLexical):
            link_attr.update(term_lexical_id=link_obj.id)

        db_example = super()._create(model_class, *args, **kwargs)

        link = TermExampleLink.create(
            cls._meta.sqlalchemy_session,
            highlight=[[1, 4], [6, 8]],
            term_example_id=db_example.id,
            **link_attr,
        )
        db_example.__dict__['link'] = link

        return db_example

    class Meta:
        model = TermExample
        sqlalchemy_session_persistence = 'commit'


class TermExampleTranslationFactory(factory.alchemy.SQLAlchemyModelFactory):
    language = fuzzy.FuzzyChoice(Language)
    highlight = [[1, 4], [6, 8]]
    translation = factory.Faker('sentence')

    class Meta:
        model = TermExampleTranslation
        sqlalchemy_session_persistence = 'commit'


class TermLexicalFactory(TermFactoryBase):
    value = factory.Faker('sentence')
    type = fuzzy.FuzzyChoice(TermLexicalType)
    extra = {'test': '123', 'test_2': '234'}

    class Meta:
        model = TermLexical
        sqlalchemy_session_persistence = 'commit'
