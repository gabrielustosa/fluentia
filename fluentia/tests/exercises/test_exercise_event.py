from sqlmodel import select

from fluentia.apps.exercises.constants import ExerciseType
from fluentia.apps.exercises.models import Exercise
from fluentia.apps.term.constants import TermLexicalType
from fluentia.apps.term.models import PronunciationLink
from fluentia.tests.factories.term import (
    PronunciationFactory,
    TermExampleFactory,
    TermFactory,
    TermLexicalFactory,
)


def test_write_exercise_event(session):
    example = TermExampleFactory()

    exercise = session.exec(
        select(Exercise).where(
            Exercise.term == example.term,
            Exercise.origin_language == example.origin_language,
            Exercise.term_example_id == example.id,
            Exercise.type == ExerciseType.WRITE_SENTENCE,
        )
    ).first()

    assert exercise is not None


def test_listen_exercise_term(session):
    term = TermFactory()
    pronunciation = PronunciationFactory()

    PronunciationLink.create(
        session,
        pronunciation_id=pronunciation.id,
        term=term.term,
        origin_language=term.origin_language,
    )

    exercise = session.exec(
        select(Exercise).where(
            Exercise.term == term.term,
            Exercise.origin_language == term.origin_language,
            Exercise.type == ExerciseType.LISTEN_TERM,
        )
    ).first()

    assert exercise is not None


def test_listen_exercise_audio_file_none(session):
    term = TermFactory()
    pronunciation = PronunciationFactory(audio_file=None)

    PronunciationLink.create(
        session,
        pronunciation_id=pronunciation.id,
        term=term.term,
        origin_language=term.origin_language,
    )

    exercise = session.exec(
        select(Exercise).where(
            Exercise.term == term.term,
            Exercise.origin_language == term.origin_language,
            Exercise.type == ExerciseType.LISTEN_TERM,
        )
    ).first()

    assert exercise is None


def test_listen_exercise_sentence(session):
    example = TermExampleFactory()
    pronunciation = PronunciationFactory()

    PronunciationLink.create(
        session,
        pronunciation_id=pronunciation.id,
        term_example_id=example.id,
    )

    exercise = session.exec(
        select(Exercise).where(
            Exercise.term == example.term,
            Exercise.origin_language == example.origin_language,
            Exercise.term_example_id == example.id,
            Exercise.type == ExerciseType.LISTEN_SENTENCE,
        )
    ).first()

    assert exercise is not None


def test_listen_exercise_lexical(session):
    lexical = TermLexicalFactory()
    pronunciation = PronunciationFactory()

    PronunciationLink.create(
        session,
        pronunciation_id=pronunciation.id,
        term_lexical_id=lexical.id,
    )

    exercise = session.exec(
        select(Exercise).where(
            Exercise.term == lexical.term,
            Exercise.origin_language == lexical.origin_language,
            Exercise.term_lexical_id == lexical.id,
            Exercise.type == ExerciseType.LISTEN_TERM,
        )
    ).first()

    assert exercise is not None


def test_update_listen_exercise_lexical(session):
    term = TermFactory()
    pronunciation = PronunciationFactory(audio_file=None)

    PronunciationLink.create(
        session,
        pronunciation_id=pronunciation.id,
        term=term.term,
        origin_language=term.origin_language,
    )

    pronunciation.audio_file = 'https://google.com'
    session.commit()

    exercise = session.exec(
        select(Exercise).where(
            Exercise.term == term.term,
            Exercise.origin_language == term.origin_language,
            Exercise.type == ExerciseType.LISTEN_TERM,
        )
    ).first()

    assert exercise is not None


def test_update_none_listen_exercise_lexical(session):
    term = TermFactory()
    pronunciation = PronunciationFactory()

    PronunciationLink.create(
        session,
        pronunciation_id=pronunciation.id,
        term=term.term,
        origin_language=term.origin_language,
    )

    pronunciation.audio_file = None
    session.commit()

    exercise = session.exec(
        select(Exercise).where(
            Exercise.term == term.term,
            Exercise.origin_language == term.origin_language,
            Exercise.type == ExerciseType.LISTEN_TERM,
        )
    ).first()

    assert exercise is None


def test_speak_exercise_term(session):
    term = TermFactory()

    exercise = session.exec(
        select(Exercise).where(
            Exercise.term == term.term,
            Exercise.origin_language == term.origin_language,
            Exercise.type == ExerciseType.SPEAK_TERM,
        )
    ).first()

    assert exercise is not None


def test_speak_exercise_sentence(session):
    example = TermExampleFactory()

    exercise = session.exec(
        select(Exercise).where(
            Exercise.term == example.term,
            Exercise.origin_language == example.origin_language,
            Exercise.term_example_id == example.id,
            Exercise.type == ExerciseType.SPEAK_SENTENCE,
        )
    ).first()

    assert exercise is not None


def test_mchoice_term_exercise(session):
    term = TermFactory()
    TermLexicalFactory.create_batch(
        3,
        term=term.term,
        origin_language=term.origin_language,
        type=TermLexicalType.ANTONYM,
    )

    exercise = session.exec(
        select(Exercise).where(
            Exercise.term == term.term,
            Exercise.origin_language == term.origin_language,
            Exercise.type == ExerciseType.MCHOICE_TERM,
        )
    ).first()

    assert exercise is not None


def test_mchoice_term_exercise_only_2_lexical(session):
    term = TermFactory()
    TermLexicalFactory.create_batch(
        2,
        term=term.term,
        origin_language=term.origin_language,
        type=TermLexicalType.ANTONYM,
    )

    exercise = session.exec(
        select(Exercise).where(
            Exercise.term == term.term,
            Exercise.origin_language == term.origin_language,
            Exercise.type == ExerciseType.MCHOICE_TERM,
        )
    ).first()

    assert exercise is None
