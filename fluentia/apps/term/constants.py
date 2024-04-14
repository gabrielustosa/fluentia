from enum import Enum


class TermLexicalType(str, Enum):
    SYNONYM = 'synonym'
    ANTONYM = 'antonym'
    FORM = 'form'
    IDIOM = 'idiom'


class Level(str, Enum):
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
    SLANG = 'slang'
    LEXICAL = 'lexical'


class Language(str, Enum):
    PORTUGUESE = 'pt'
    ENGLISH = 'en'
    DEUTSCH = 'de'
    FRENCH = 'fr'
    SPANISH = 'es'
    ITALIAN = 'it'
    CHINESE = 'zh'
    JAPONESE = 'ja'
    RUSSIAN = 'ru'
