import factory
from factory import fuzzy

from fluentia.apps.term.constants import Language
from fluentia.apps.term.models import Term


class TermFactory(factory.alchemy.SQLAlchemyModelFactory):
    term = factory.Faker('sentence')
    origin_language = fuzzy.FuzzyChoice(Language)

    class Meta:
        model = Term
        sqlalchemy_session_persistence = 'commit'
