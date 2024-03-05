from enum import Enum


class TermLexicalType(str, Enum):
    SYNONYM = 'synonym'
    ANTONYM = 'antonym'
    FORMS = 'forms'


class TermLevel(str, Enum):
    BEGINNER = 'A1'
    ELEMENTARY = 'A2'
    INTERMEDIATE = 'B1'
    UPPER_INTERMEDIATE = 'B2'
    ADVANCED = 'C1'
    MASTER = 'C2'


class PartOfSpeech(str, Enum):
    ADJECTIVE = 'adjective'
    NOUN = 'noun'
    VERB = 'verb'
    ADVERB = 'adverb'
    CONJUNCTION = 'conjunction'
    PREPOSITION = 'preposition'
    PRONOUN = 'pronoun'
    DETERMINER = 'determiner'
    NUMBER = 'number'
    PREDETERMINER = 'predeterminer'
    PREFIX = 'prefix'
    SUFFIX = 'suffix'


class Language(str, Enum):
    PORTUGUES_BRASIL = 'pt-BR'
    ENGLISH = 'en'
    DEUTSCH = 'de'
    FRANÇAIS = 'fr'
    ESPAÑOL = 'es'
    ITALIANO = 'it'


class PronunciationModel(str, Enum):
    TERM = 'term'
    LEXICAL = 'lexical'
    EXAMPLE = 'example'