import sqlmodel as sm
from fastapi import HTTPException, status
from sqlalchemy.event import listens_for
from sqlalchemy.exc import IntegrityError

from fluentia.apps.exercises.constants import ExerciseType
from fluentia.apps.exercises.models import Exercise
from fluentia.apps.term import constants, schema
from fluentia.core.api.query import set_url_params
from fluentia.core.api.schema import Page
from fluentia.core.model.shortcut import (
    create,
    get_object_or_404,
    get_or_create_object,
    update,
)


class Term(sm.SQLModel, table=True):
    term: str = sm.Field(primary_key=True)
    origin_language: constants.Language = sm.Field(primary_key=True)

    __table_args__ = (sm.UniqueConstraint('term', 'origin_language'),)

    @staticmethod
    def get(session, term, origin_language):
        term_query = (
            sm.select(Term)
            .where(
                Term.origin_language == origin_language,
                sm.func.clean_text(Term.term) == sm.func.clean_text(term),
            )
            .union(
                sm.select(Term).where(
                    sm.tuple_(Term.term, Term.origin_language).in_(
                        sm.select(TermLexical.term, TermLexical.origin_language).where(
                            sm.func.clean_text(TermLexical.value)
                            == sm.func.clean_text(term),
                            TermLexical.origin_language == origin_language,
                            TermLexical.type == constants.TermLexicalType.FORM,
                        )
                    ),
                )
            )
        )
        obj = session.exec(term_query).first()
        if obj is not None:
            obj = Term(**obj._mapping)
        return obj

    @staticmethod
    def get_or_404(session, term, origin_language):
        obj = Term.get(session, term, origin_language)
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail='Term does not exists.'
            )
        return obj

    @staticmethod
    def get_or_create(session, **data):
        obj = Term.get(session, **data)
        if obj is not None:
            return obj, False
        return create(Term, session, **data), True

    @staticmethod
    def search(session, text, origin_language):
        return session.exec(
            sm.select(Term)
            .where(
                Term.origin_language == origin_language,
                sm.func.clean_text(Term.term).like(
                    '%' + sm.func.clean_text(text) + '%'
                ),
            )
            .union(
                sm.select(Term).where(
                    sm.tuple_(Term.term, Term.origin_language).in_(
                        sm.select(TermLexical.term, TermLexical.origin_language).where(
                            sm.func.clean_text(TermLexical.value).like(
                                '%' + sm.func.clean_text(text) + '%'
                            ),
                            TermLexical.origin_language == origin_language,
                            TermLexical.type == constants.TermLexicalType.FORM,
                        )
                    ),
                )
            )
        )

    @staticmethod
    def search_term_meaning(session, text, origin_language, translation_language):
        translation_query = (
            sm.select(
                TermDefinition.term,
                TermDefinition.origin_language,
            )
            .where(
                sm.func.clean_text(TermDefinitionTranslation.meaning).like(
                    '%' + sm.func.clean_text(text) + '%'
                ),
                TermDefinition.origin_language == origin_language,
                TermDefinitionTranslation.language == translation_language,
            )
            .join(
                TermDefinitionTranslation,
                TermDefinition.id == TermDefinitionTranslation.term_definition_id,  # pyright: ignore[reportArgumentType]
            )
        )
        return session.exec(
            sm.select(Term).where(
                sm.tuple_(Term.term, Term.origin_language).in_(translation_query)
            )
        )


class Pronunciation(sm.SQLModel, table=True):
    id: int = sm.Field(primary_key=True)
    audio_file: str | None = None
    description: str | None = None
    language: constants.Language
    phonetic: str
    text: str

    @staticmethod
    def create(session, **data):
        return create(Pronunciation, session, **data)

    @staticmethod
    def update(session, db_pronuciation, **data):
        return update(session, db_pronuciation, **data)

    @staticmethod
    def list(session, **link_attributes):
        filters = set()
        if 'term' in link_attributes:
            term = link_attributes.pop('term')
            db_term = Term.get(session, term, link_attributes['origin_language'])
            if db_term:
                term = db_term.term
            filters.add(
                sm.func.clean_text(PronunciationLink.term) == sm.func.clean_text(term)
            )
        return session.exec(
            sm.select(Pronunciation)
            .join(
                PronunciationLink,
                Pronunciation.id == PronunciationLink.pronunciation_id,  # pyright: ignore[reportArgumentType]
            )
            .filter_by(**link_attributes)
            .filter(*filters)
        ).all()


class PronunciationLink(sm.SQLModel, table=True):
    pronunciation_id: int = sm.Field(primary_key=True)
    term: str | None = None
    origin_language: constants.Language | None = None
    term_example_id: int | None = None
    term_lexical_id: int | None = None

    __table_args__ = (
        sm.ForeignKeyConstraint(
            ['pronunciation_id'],
            ['pronunciation.id'],
            ondelete='CASCADE',
        ),
        sm.ForeignKeyConstraint(
            ['term', 'origin_language'],
            ['term.term', 'term.origin_language'],
            ondelete='CASCADE',
        ),
        sm.ForeignKeyConstraint(
            ['term_example_id'],
            ['termexample.id'],
            ondelete='CASCADE',
        ),
        sm.ForeignKeyConstraint(
            ['term_lexical_id'],
            ['termlexical.id'],
            ondelete='CASCADE',
        ),
    )

    @staticmethod
    def create(session, **data):
        try:
            if 'term' in data:
                db_term = Term.get_or_404(
                    session,
                    data['term'],
                    data['origin_language'],
                )
                data['term'] = db_term.term
            elif 'term_example_id' in data:
                get_object_or_404(TermExample, session, id=data['term_example_id'])
            elif 'term_lexical_id' in data:
                get_object_or_404(TermLexical, session, id=data['term_lexical_id'])
        except HTTPException as err:
            session.rollback()
            session.exec(
                sm.delete(Pronunciation).where(
                    Pronunciation.id == data['pronunciation_id']
                )
            )
            raise err
        return create(PronunciationLink, session, **data)


class TermDefinition(sm.SQLModel, table=True):
    id: int = sm.Field(primary_key=True)
    term: str
    origin_language: constants.Language
    part_of_speech: constants.PartOfSpeech
    definition: str
    extra: sm.JSON | None = sm.Field(sa_column=sm.Column(sm.JSON))
    level: constants.Level | None = None
    term_lexical_id: int | None = None

    class Config:
        arbitrary_types_allowed = True

    __table_args__ = (
        sm.ForeignKeyConstraint(
            ['term', 'origin_language'],
            ['term.term', 'term.origin_language'],
            ondelete='CASCADE',
        ),
        sm.ForeignKeyConstraint(
            ['term_lexical_id'],
            ['termlexical.id'],
            ondelete='CASCADE',
        ),
    )

    @staticmethod
    def list(
        session,
        term,
        origin_language,
        part_of_speech=None,
        level=None,
    ):
        filters = set()
        if level:
            filters.add(TermDefinition.level == level)
        if part_of_speech:
            filters.add(TermDefinition.part_of_speech == part_of_speech)
        db_term = Term.get(session, term, origin_language)
        if db_term:
            term = db_term.term

        query_definition = sm.select(TermDefinition).where(
            sm.func.clean_text(TermDefinition.term) == sm.func.clean_text(term),
            TermDefinition.origin_language == origin_language,
            *filters,
        )
        return session.exec(query_definition)

    @staticmethod
    def get_or_create(session, **data):
        db_definition = session.exec(
            sm.select(TermDefinition).where(
                sm.func.clean_text(TermDefinition.term)
                == sm.func.clean_text(data['term']),
                sm.func.clean_text(TermDefinition.definition)
                == sm.func.clean_text(data['definition']),
                TermDefinition.origin_language == data['origin_language'],
                TermDefinition.part_of_speech == data['part_of_speech'],
            )
        ).first()
        if db_definition is not None:
            return db_definition, False
        return TermDefinition.create(session, **data), True

    @staticmethod
    def create(session, **data):
        db_term = Term.get_or_404(
            session,
            term=data['term'],
            origin_language=data['origin_language'],
        )
        data['term'] = db_term.term

        return create(TermDefinition, session, **data)

    @staticmethod
    def update(session, db_definition, **data):
        extra = data.pop('extra', None)
        if extra:
            db_definition.extra = {**db_definition.extra, **extra}

        for key, value in data.items():
            setattr(db_definition, key, value)

        session.commit()
        session.refresh(db_definition)

        return db_definition


class TermDefinitionTranslation(sm.SQLModel, table=True):
    language: constants.Language = sm.Field(primary_key=True)
    term_definition_id: int = sm.Field(primary_key=True)
    extra: sm.JSON | None = sm.Field(sa_column=sm.Column(sm.JSON))
    translation: str
    meaning: str

    class Config:
        arbitrary_types_allowed = True

    __table_args__ = (
        sm.ForeignKeyConstraint(
            ['term_definition_id'],
            ['termdefinition.id'],
            ondelete='CASCADE',
        ),
    )

    @staticmethod
    def create(session, **data):
        return create(TermDefinitionTranslation, session, **data)

    @staticmethod
    def update(session, db_definition_translation, **data):
        return TermDefinition.update(session, db_definition_translation, **data)

    @staticmethod
    def list(
        session,
        term,
        origin_language,
        part_of_speech=None,
        level=None,
        translation_language=None,
    ):
        filters = set()
        if level:
            filters.add(TermDefinition.level == level)
        if part_of_speech:
            filters.add(TermDefinition.part_of_speech == part_of_speech)
        db_term = Term.get(session, term, origin_language)
        if db_term:
            term = db_term.term

        query_translation = (
            sm.select(
                TermDefinition,
                TermDefinitionTranslation,
            )
            .where(
                sm.func.clean_text(TermDefinition.term) == sm.func.clean_text(term),
                TermDefinition.origin_language == origin_language,
                TermDefinitionTranslation.language == translation_language,
                *filters,
            )
            .join(
                TermDefinitionTranslation,
                TermDefinition.id == TermDefinitionTranslation.term_definition_id,  # pyright: ignore[reportArgumentType]
            )
        )
        rows = session.exec(query_translation)

        result_list = []
        for row in rows:
            db_definition, db_definition_translation = row
            result_list.append(
                schema.TermDefinitionView(
                    **db_definition.model_dump(),
                    translation_language=db_definition_translation.language,
                    translation_definition=db_definition_translation.translation,
                    translation_meaning=db_definition_translation.meaning,
                )
            )
        return result_list

    @staticmethod
    def list_meaning(session, term, origin_language, translation_language):
        translation_query = (
            sm.select(
                TermDefinitionTranslation.meaning,
            )
            .join(
                TermDefinition,
                TermDefinition.id == TermDefinitionTranslation.term_definition_id,  # pyright: ignore[reportArgumentType]
            )
            .where(
                TermDefinition.term == term,
                TermDefinition.origin_language == origin_language,
                TermDefinitionTranslation.language == translation_language,
            )
        )
        return session.exec(translation_query)


class TermExample(sm.SQLModel, table=True):
    id: int = sm.Field(primary_key=True)
    language: constants.Language
    example: str
    level: constants.Level | None = None

    @staticmethod
    def get_or_create(session, **data):
        db_example = session.exec(
            sm.select(TermExample).where(
                sm.func.clean_text(TermExample.example)
                == sm.func.clean_text(data['example']),
                TermExample.language == data['language'],
            )
        ).first()

        if db_example is not None:
            return db_example, False
        return TermExample.create(session, **data), True

    @staticmethod
    def create(session, **data):
        return create(TermExample, session, **data)

    @staticmethod
    def list(session, page=1, size=50, **link_attributes):
        from fluentia.main import app

        filters = set()
        term = link_attributes.pop('term', None)
        if term:
            db_term = Term.get(session, term, link_attributes['origin_language'])
            if db_term:
                term = db_term.term
            filters.add(
                sm.func.clean_text(TermExampleLink.term) == sm.func.clean_text(term)
            )

        example_list_query = (
            sm.select(
                TermExample,
                TermExampleLink,
                sm.func.count().over().label('total_count'),
            )
            .join(TermExampleLink, TermExample.id == TermExampleLink.term_example_id)  # pyright: ignore[reportArgumentType]
            .filter_by(**link_attributes)
            .where(*filters)
            .offset((page - 1) * size)
            .limit(size)
        )

        rows = session.exec(example_list_query).all()

        result_list = []
        for row in rows:
            db_example, db_example_link, _ = row
            result_list.append(
                schema.TermExampleTranslationView(
                    **db_example.model_dump(),
                    **db_example_link.model_dump(exclude={'term_example_id', 'id'}),
                )
            )

        if term:
            link_attributes['term'] = term
        url = app.url_path_for('list_example')
        return Page(
            items=result_list,
            total=0 if len(rows) == 0 else rows[0][2],
            next_page=set_url_params(url, **link_attributes, page=page + 1, size=size),
            previous_page=None
            if page == 1
            else set_url_params(url, **link_attributes, page=page - 1, size=size),
        )


class TermExampleLink(sm.SQLModel, table=True):
    id: int = sm.Field(primary_key=True)
    term_example_id: int
    highlight: list[list[int]] = sm.Field(
        sa_column=sm.Column(sm.ARRAY(sm.Integer, dimensions=2), nullable=False)
    )
    term: str | None = None
    origin_language: constants.Language | None = None
    term_definition_id: int | None = None
    term_lexical_id: int | None = None
    translation_language: constants.Language | None = None

    __table_args__ = (
        sm.ForeignKeyConstraint(
            ['term', 'origin_language'],
            ['term.term', 'term.origin_language'],
            ondelete='CASCADE',
        ),
        sm.ForeignKeyConstraint(
            ['term_example_id'],
            ['termexample.id'],
            ondelete='CASCADE',
        ),
        sm.ForeignKeyConstraint(
            ['term_definition_id'],
            ['termdefinition.id'],
            ondelete='CASCADE',
        ),
        sm.ForeignKeyConstraint(
            ['term_lexical_id'],
            ['termlexical.id'],
            ondelete='CASCADE',
        ),
        sm.UniqueConstraint('term', 'origin_language', 'term_example_id'),
        sm.UniqueConstraint('term_definition_id', 'term_example_id'),
        sm.UniqueConstraint('term_lexical_id', 'term_example_id'),
        # translation
        sm.UniqueConstraint(
            'term',
            'origin_language',
            'term_example_id',
            'translation_language',
        ),
        sm.UniqueConstraint(
            'term_definition_id',
            'term_example_id',
            'translation_language',
        ),
        sm.UniqueConstraint(
            'term_lexical_id',
            'term_example_id',
            'translation_language',
        ),
    )

    @staticmethod
    def create(session, **data):
        if 'translation_language' in data:
            get_object_or_404(
                TermExampleTranslation,
                session=session,
                term_example_id=data['term_example_id'],
                language=data['translation_language'],
            )
        if 'term' in data:
            db_term = Term.get_or_404(
                session,
                data['term'],
                data['origin_language'],
            )
            data['term'] = db_term.term
        elif 'term_definition_id' in data:
            get_object_or_404(TermDefinition, session, id=data['term_definition_id'])
        elif 'term_lexical_id' in data:
            get_object_or_404(TermLexical, session, id=data['term_lexical_id'])

        try:
            return create(TermExampleLink, session, **data)
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail='the example is already linked with this model.',
            )


class TermExampleTranslation(sm.SQLModel, table=True):
    language: constants.Language = sm.Field(primary_key=True)
    term_example_id: int = sm.Field(foreign_key='termexample.id', primary_key=True)
    translation: str

    @staticmethod
    def get_or_create(session, **data):
        query = sm.select(TermExampleTranslation).where(
            TermExampleTranslation.language == data['language'],
            TermExampleTranslation.term_example_id == data['term_example_id'],
            sm.func.clean_text(TermExampleTranslation.translation)
            == sm.func.clean_text(data['translation']),
        )
        db_translation = session.exec(query).first()
        if db_translation:
            return db_translation, False
        return create(TermExampleTranslation, session, **data), True

    @staticmethod
    def list(session, translation_language, page=1, size=50, **link_attributes):
        from fluentia.main import app

        filters = set()
        term = link_attributes.pop('term', None)
        if term:
            db_term = Term.get(session, term, link_attributes['origin_language'])
            if db_term:
                term = db_term.term
            filters.add(
                sm.func.clean_text(TermExampleLink.term) == sm.func.clean_text(term)
            )

        example_list_query = (
            sm.select(
                TermExample,
                TermExampleTranslation,
                TermExampleLink,
                sm.func.count().over().label('total_count'),
            )
            .join(
                TermExampleTranslation,
                TermExample.id == TermExampleTranslation.term_example_id,  # pyright: ignore[reportArgumentType]
            )
            .join(
                TermExampleLink,
                TermExample.id == TermExampleLink.term_example_id,  # pyright: ignore[reportArgumentType]
            )
            .where(TermExampleTranslation.language == translation_language, *filters)
            .filter_by(**link_attributes)
            .offset((page - 1) * size)
            .limit(size)
        )

        rows = session.exec(example_list_query).all()

        result_list = []
        for row in rows:
            db_example, db_example_translation, db_example_link, _ = row
            result_list.append(
                schema.TermExampleTranslationView(
                    **db_example.model_dump(),
                    **db_example_link.model_dump(
                        exclude={'term_example_id', 'id', 'translation_language'}
                    ),
                    translation_language=db_example_translation.language,
                    translation_example=db_example_translation.translation,
                )
            )

        if term:
            link_attributes['term'] = term
        url = app.url_path_for('list_example')
        return Page(
            items=result_list,
            total=0 if len(rows) == 0 else rows[0][3],
            next_page=set_url_params(
                url,
                **link_attributes,
                translation_language=translation_language,
                page=page + 1,
                size=size,
            ),
            previous_page=None
            if page == 1
            else set_url_params(
                url,
                **link_attributes,
                translation_language=translation_language,
                page=page - 1,
                size=size,
            ),
        )

    __table_args__ = (
        sm.ForeignKeyConstraint(
            ['term_example_id'],
            ['termexample.id'],
            ondelete='CASCADE',
        ),
    )


class TermLexical(sm.SQLModel, table=True):
    id: int = sm.Field(primary_key=True)
    term: str
    origin_language: constants.Language
    value: str
    type: constants.TermLexicalType
    extra: sm.JSON | None = sm.Field(sa_column=sm.Column(sm.JSON))

    class Config:
        arbitrary_types_allowed = True

    __table_args__ = (
        sm.ForeignKeyConstraint(
            ['term', 'origin_language'],
            ['term.term', 'term.origin_language'],
            ondelete='CASCADE',
        ),
    )

    @staticmethod
    def create(session, **data):
        db_term = Term.get_or_404(
            session,
            term=data['term'],
            origin_language=data['origin_language'],
        )
        data['term'] = db_term.term

        return create(TermLexical, session, **data)

    @staticmethod
    def list(session, term, origin_language, page=1, size=50, type=None):
        from fluentia.main import app

        db_term = Term.get(session, term, origin_language)
        if db_term:
            term = db_term.term
        lexical_query = (
            sm.select(
                TermLexical,
                sm.func.count().over().label('total_count'),
            )
            .where(
                sm.func.clean_text(TermLexical.term) == sm.func.clean_text(term),
                TermLexical.origin_language == origin_language,
            )
            .offset((page - 1) * size)
            .limit(size)
        )
        if type is not None:
            lexical_query = lexical_query.where(TermLexical.type == type.lower())

        rows = session.exec(lexical_query).all()

        result_list = []
        for row in rows:
            db_lexical, _ = row
            result_list.append(db_lexical)

        url = app.url_path_for('list_lexical')
        return Page(
            items=result_list,
            total=0 if len(rows) == 0 else rows[0][1],
            next_page=set_url_params(
                url,
                term=term,
                origin_language=origin_language,
                type=type,
                page=page + 1,
                size=size,
            ),
            previous_page=None
            if page == 1
            else set_url_params(
                url,
                term=term,
                origin_language=origin_language,
                type=type,
                page=page - 1,
                size=size,
            ),
        )

    @staticmethod
    def update(session, db_lexical, **data):
        extra = data.pop('extra', None)
        if extra:
            db_lexical.extra = {**db_lexical.extra, **extra}

        for key, value in data.items():
            setattr(db_lexical, key, value)

        session.commit()
        session.refresh(db_lexical)

        return db_lexical


@listens_for(TermExampleTranslation, 'after_insert')
def insert_order_exercise(_, connection, target):
    session = sm.Session(connection)

    db_example = session.exec(
        sm.select(TermExample).where(TermExample.id == target.term_example_id)
    ).one()

    get_or_create_object(
        Exercise,
        session,
        language=db_example.language,
        term_example_id=target.term_example_id,
        translation_language=target.language,
        type=ExerciseType.ORDER_SENTENCE,
    )


@listens_for(PronunciationLink, 'after_insert')
def insert_listen_exercise(_, connection, target):
    session = sm.Session(connection)

    pronunciation = session.exec(
        sm.select(Pronunciation).where(Pronunciation.id == target.pronunciation_id)
    ).one()
    if pronunciation.audio_file is None:
        return

    exercise_attr = {}
    if target.term:
        exercise_attr.update(
            {
                'term': target.term,
                'origin_language': target.origin_language,
                'language': target.origin_language,
                'type': ExerciseType.LISTEN_TERM,
            }
        )
    elif target.term_example_id:
        db_example = session.exec(
            sm.select(TermExample).where(TermExample.id == target.term_example_id)
        ).one()

        exercise_attr.update(
            {
                'language': db_example.language,
                'term_example_id': target.term_example_id,
                'type': ExerciseType.LISTEN_SENTENCE,
            }
        )
    elif target.term_lexical_id:
        db_lexical = session.exec(
            sm.select(TermLexical).where(TermLexical.id == target.term_lexical_id)
        ).one()

        exercise_attr.update(
            {
                'language': db_lexical.origin_language,
                'term_lexical_id': target.term_lexical_id,
                'type': ExerciseType.LISTEN_TERM,
            }
        )

    get_or_create_object(
        Exercise,
        session,
        pronunciation_id=target.pronunciation_id,
        **exercise_attr,
    )


@listens_for(Pronunciation, 'after_update')
def update_listen_exercise(_, connection, target):
    session = sm.Session(connection)

    if not target.audio_file:
        db_exercise = session.exec(
            sm.select(Exercise).where(
                Exercise.pronunciation_id == target.id,
                Exercise.type.in_(
                    (ExerciseType.LISTEN_SENTENCE, ExerciseType.LISTEN_TERM)
                ),
            )
        ).first()
        if db_exercise:
            session.delete(db_exercise)
            session.commit()
    else:
        link = session.exec(
            sm.select(PronunciationLink).where(
                PronunciationLink.pronunciation_id == target.id
            )
        ).first()
        if link:
            insert_listen_exercise(None, connection, link)


@listens_for(Term, 'after_insert')
def insert_speak_term_exercise(_, connection, target):
    session = sm.Session(connection)

    get_or_create_object(
        Exercise,
        session,
        term=target.term,
        origin_language=target.origin_language,
        language=target.origin_language,
        type=ExerciseType.SPEAK_TERM,
    )


@listens_for(TermExample, 'after_insert')
def insert_speak_sentence_exercise(_, connection, target):
    session = sm.Session(connection)

    get_or_create_object(
        Exercise,
        session,
        term_example_id=target.id,
        type=ExerciseType.SPEAK_SENTENCE,
        language=target.language,
    )


@listens_for(TermLexical, 'after_insert')
def insert_mchoice_term_exercise(_, connection, target):
    if target.type != constants.TermLexicalType.ANTONYM:
        return

    session = sm.Session(connection)

    count = session.exec(
        sm.select(
            sm.func.count(TermLexical.id),  # pyright: ignore[reportArgumentType]
        ).where(
            TermLexical.term == target.term,
            TermLexical.origin_language == target.origin_language,
            TermLexical.type == constants.TermLexicalType.ANTONYM,
        )
    ).all()[0]
    if count >= 3:
        get_or_create_object(
            Exercise,
            session,
            term=target.term,
            origin_language=target.origin_language,
            type=ExerciseType.MCHOICE_TERM,
            language=target.origin_language,
        )


@listens_for(TermDefinitionTranslation, 'after_insert')
def insert_mchoice_term_translation_exercise(_, connection, target):
    session = sm.Session(connection)

    definition = session.exec(
        sm.select(TermDefinition).where(TermDefinition.id == target.term_definition_id)
    ).one()

    count = session.exec(
        sm.select(
            sm.func.count(TermLexical.id),  # pyright: ignore[reportArgumentType]
        ).where(
            TermLexical.term == definition.term,
            TermLexical.origin_language == definition.origin_language,
            TermLexical.type == constants.TermLexicalType.ANTONYM,
        )
    ).all()[0]

    if count >= 3:
        get_or_create_object(
            Exercise,
            session,
            translation_language=target.language,
            language=definition.origin_language,
            term_definition_id=definition.id,
            type=ExerciseType.MCHOICE_TERM_TRANSLATION,
        )
