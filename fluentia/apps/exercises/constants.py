from enum import Enum


class ExerciseType(str, Enum):
    ORDER_SENTENCE = 'order-sentence'
    LISTEN_TERM = 'listen-term'
    LISTEN_TERM_MCHOICE = 'listen-term-mchoice'
    LISTEN_SENTENCE = 'listen-sentence'
    SPEAK_TERM = 'speak-term'
    SPEAK_SENTENCE = 'speak-sentence'
    MCHOICE_TERM = 'mchoice-term'
    MCHOICE_TERM_TRANSLATION = 'mchoice-term-translation'
    RANDOM = 'random'

    @classmethod
    def is_term_exercise(cls, exercise_type):
        return exercise_type in (
            ExerciseType.LISTEN_TERM,
            ExerciseType.LISTEN_TERM_MCHOICE,
            ExerciseType.SPEAK_TERM,
            ExerciseType.MCHOICE_TERM,
            ExerciseType.RANDOM,
        )

    @classmethod
    def is_sentence_exercise(cls, exercise_type):
        return exercise_type in (
            ExerciseType.ORDER_SENTENCE,
            ExerciseType.LISTEN_SENTENCE,
            ExerciseType.SPEAK_SENTENCE,
            ExerciseType.RANDOM,
        )

    @classmethod
    def is_pronunciation_exercise(cls, exercise_type):
        return exercise_type in (
            ExerciseType.LISTEN_TERM,
            ExerciseType.LISTEN_SENTENCE,
            ExerciseType.RANDOM,
        )

    @classmethod
    def is_translation_exercise(cls, exercise_type):
        return exercise_type in (
            ExerciseType.ORDER_SENTENCE,
            ExerciseType.MCHOICE_TERM_TRANSLATION,
            ExerciseType.RANDOM,
        )
