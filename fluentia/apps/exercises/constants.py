from enum import Enum


class ExerciseType(str, Enum):
    WRITE_SENTENCE = 'write-sentence'
    LISTEN_TERM = 'listen-term'
    LISTEN_SENTENCE = 'listen-sentence'
    SPEAK_TERM = 'speak-term'
    SPEAK_SENTENCE = 'speak-sentence'
    MCHOICE_TERM = 'mchoice-term'
    RANDOM = 'random'
