from enum import Enum


class ExerciseType(str, Enum):
    ORDER_SENTENCE = 'order-sentence'
    LISTEN_TERM = 'listen-term'
    LISTEN_TERM_MCHOICE = 'listen-term-mchoice'
    LISTEN_SENTENCE = 'listen-sentence'
    SPEAK_TERM = 'speak-term'
    SPEAK_SENTENCE = 'speak-sentence'
    MCHOICE_TERM = 'mchoice-term'
    RANDOM = 'random'
