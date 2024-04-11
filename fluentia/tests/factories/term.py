import factory
import faker
from factory import fuzzy

from fluentia.apps.term.constants import (
    Language,
    PartOfSpeech,
    TermLevel,
    TermLexicalType,
)
from fluentia.apps.term.models import (
    Pronunciation,
    Term,
    TermDefinition,
    TermDefinitionTranslation,
    TermExample,
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
    term_level = fuzzy.FuzzyChoice(TermLevel)
    part_of_speech = fuzzy.FuzzyChoice(PartOfSpeech)
    definition = factory.Faker('sentence')

    class Meta:
        model = TermDefinition
        sqlalchemy_session_persistence = 'commit'


class TermDefinitionTranslationFactory(factory.alchemy.SQLAlchemyModelFactory):
    language = fuzzy.FuzzyChoice(Language)
    translation = factory.Faker('sentence')
    meaning = factory.Faker('sentence')

    class Meta:
        model = TermDefinitionTranslation
        sqlalchemy_session_persistence = 'commit'


class TermExampleFactory(factory.alchemy.SQLAlchemyModelFactory):
    language = fuzzy.FuzzyChoice(Language)

    @factory.LazyAttribute
    def example(self):
        sentence = faker.Faker().sentence(nb_words=8)
        words = sentence.split()
        words[0] = '*' + words[0] + '*'
        return ' '.join(words)

    class Meta:
        model = TermExample
        sqlalchemy_session_persistence = 'commit'


class TermExampleTranslationFactory(TermExampleFactory):
    language = fuzzy.FuzzyChoice(Language)

    @factory.LazyAttribute
    def translation(self):
        return self.example

    class Meta:
        model = TermExampleTranslation
        sqlalchemy_session_persistence = 'commit'


class TermLexicalFactory(TermFactoryBase):
    value = factory.Faker('sentence')
    type = fuzzy.FuzzyChoice(TermLexicalType)
    description = factory.Faker('sentence')

    class Meta:
        model = TermLexical
        sqlalchemy_session_persistence = 'commit'
