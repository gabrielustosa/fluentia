import factory

from fluentia.apps.card.models import Card, CardSet
from fluentia.apps.term.constants import Language
from fluentia.tests.factories.term import TermFactoryBase
from fluentia.tests.factories.user import UserFactory


class CardSetFactory(factory.alchemy.SQLAlchemyModelFactory):
    name = factory.Faker('name')
    description = factory.Faker('sentence')
    language = factory.fuzzy.FuzzyChoice(Language)
    user_id = factory.LazyAttribute(lambda o: UserFactory().id)

    class Meta:
        model = CardSet
        sqlalchemy_session_persistence = 'commit'


class CardFactory(TermFactoryBase):
    cardset_id = factory.LazyAttribute(lambda o: CardSetFactory().id)
    note = factory.Faker('sentence')

    class Meta:
        model = Card
        sqlalchemy_session_persistence = 'commit'
