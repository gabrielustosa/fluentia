from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session as SQLModelSession
from sqlmodel import select, tuple_

from fluentia.apps.term import constants, schema
from fluentia.apps.term.models import (
    Pronunciation,
    PronunciationLink,
    Term,
    TermDefinition,
    TermDefinitionTranslation,
    TermExample,
    TermExampleTranslation,
    TermLexical,
)
from fluentia.apps.user.models import User
from fluentia.apps.user.security import get_current_admin_user
from fluentia.core.api.constants import (
    NOT_ENOUGH_PERMISSION,
    TERM_NOT_FOUND,
    USER_NOT_AUTHORIZED,
)
from fluentia.core.api.query import filter_query
from fluentia.core.model.shortcut import get_object_or_404, get_or_create_object
from fluentia.database import get_session

term_router = APIRouter(prefix='/term', tags=['term'])

Session = Annotated[SQLModelSession, Depends(get_session)]
AdminUser = Annotated[User, Depends(get_current_admin_user)]


@term_router.post(
    path='/',
    status_code=201,
    response_model=schema.TermSchemaBase,
    response_description='O termo criado é retornado.',
    responses={
        401: USER_NOT_AUTHORIZED,
        403: NOT_ENOUGH_PERMISSION,
        409: {
            'description': 'O termo enviado já existe nesta linguagem.',
            'content': {
                'application/json': {
                    'example': {'detail': 'term already registered in this language.'}
                }
            },
        },
    },
    summary='Criação de um novo termo.',
    description="""
        <br> Endpoint utilizado para a criação de um termo, palavra ou expressão de um certo idioma.
        <br> A princípio, poderá existir somente um termo com o mesmo valor de expressão de texto para cada idioma.
    """,
)
def create_term(
    term_schema: schema.TermSchemaBase,
    user: AdminUser,
    session: Session,
):
    db_term = Term(**term_schema.model_dump())

    try:
        session.add(db_term)
        session.commit()
        session.refresh(db_term)
    except IntegrityError:
        raise HTTPException(
            status_code=409, detail='term already registered in this language.'
        )

    return db_term


@term_router.get(
    path='/',
    status_code=200,
    response_model=schema.TermSchema,
    response_description='O resultado da consulta do termo especificado.',
    responses={404: TERM_NOT_FOUND},
    summary='Consulta de um termo existente.',
    description='Endpoint utilizado para a consultar um termo, palavra ou expressão específica de um certo idioma.',
)
def get_term(
    session: Session,
    term: str,
    origin_language: constants.Language,
    translation_language: constants.Language | None = Query(
        default=None,
        description='Se existir tradução para tal linguagem, virá os significados do termo no idioma referido.',
    ),
    lexical: bool | None = Query(
        default=None,
        description='Caso seja verdadeiro, informações como sinônimos, antônimos, pronúncias e conjugações relacionados ao termo serão incluídos na resposta.',
    ),
    pronunciation: bool | None = Query(
        default=None,
        description='Caso seja verdadeiro, as pronúncias do termo serão incluídos na resposta.',
    ),
):
    db_term = get_object_or_404(
        Term, session=session, term=term, origin_language=origin_language
    )
    if not translation_language and not lexical and not pronunciation:
        return db_term

    meanings_list = []
    if translation_language:
        translation_query = (
            select(
                TermDefinition,
                TermDefinitionTranslation.meaning,
            )
            .where(
                TermDefinition.term == term,
                TermDefinition.origin_language == origin_language,
                TermDefinitionTranslation.language == translation_language,
            )
            .join(
                TermDefinitionTranslation,
                TermDefinition.id == TermDefinitionTranslation.term_definition_id,
            )
        )
        result_query = session.exec(translation_query)

        for row in result_query.all():
            for key, value in row._mapping.items():
                if key == 'meaning':
                    meanings_list.append(value)

    lexical_list = []
    if lexical:
        lexical_query = select(TermLexical).where(
            TermLexical.term == term,
            TermLexical.origin_language == origin_language,
        )
        result_query = session.exec(lexical_query).all()
        lexical_list.extend(
            [
                schema.TermLexicalSchema(**lexical.model_dump())
                for lexical in result_query
            ]
        )

    pronunciation_list = []
    if pronunciation:
        pronunciation_query = select(Pronunciation).where(
            Pronunciation.id.in_(
                select(PronunciationLink.pronunciation_id).where(
                    PronunciationLink.term == term,
                    PronunciationLink.origin_language == origin_language,
                )
            )
        )
        result_query = session.exec(pronunciation_query).all()
        pronunciation_list.extend(
            [
                schema.PronunciationSchema(
                    **db_term.model_dump(), **pronunciation.model_dump()
                )
                for pronunciation in result_query
            ]
        )

    return schema.TermSchema(
        **db_term.model_dump(),
        meanings=meanings_list,
        lexical=lexical_list,
        pronunciations=pronunciation_list,
    )


@term_router.get(
    path='/search',
    status_code=200,
    response_model=list[schema.TermSchemaBase],
    response_description='O resultado da consulta dos termos que batem com o termo.',
    summary='Procura de termos.',
    description='Endpoint utilizado para procurar um termo, palavra ou expressão específica de um certo idioma de acordo com o valor enviado.',
)
def search_term(
    session: Session,
    text: str,
    origin_language: constants.Language,
):
    return session.exec(
        select(Term).where(
            Term.origin_language == origin_language,
            Term.term.ilike(f'%{text}%'),
        )
    )


@term_router.get(
    path='/search/meanings',
    status_code=200,
    response_model=list[schema.TermSchemaBase],
    response_description='O resultado da consulta dos significados dos termos que batem com o texto.',
    summary='Procura de termos por significados.',
    description='Endpoint utilizado para procurar um termo, palavra ou expressão de um certo idioma pelo seu significado na linguagem de tradução e termo especificados.',
)
def search_term_meaning(
    session: Session,
    text: str,
    origin_language: constants.Language,
    translation_language: constants.Language,
):
    translation_query = (
        select(
            TermDefinition.term,
            TermDefinition.origin_language,
        )
        .where(
            TermDefinitionTranslation.meaning.ilike(f'%{text}%'),
            TermDefinition.origin_language == origin_language,
            TermDefinitionTranslation.language == translation_language,
        )
        .join(
            TermDefinitionTranslation,
            TermDefinition.id == TermDefinitionTranslation.term_definition_id,
        )
    )
    return session.exec(
        select(Term).where(
            tuple_(Term.term, Term.origin_language).in_(translation_query)
        )
    )


@term_router.post(
    path='/pronunciation',
    status_code=201,
    response_model=schema.PronunciationView,
    response_description='A pronúncia para o modelo referenciado é criada.',
    responses={
        401: USER_NOT_AUTHORIZED,
        403: NOT_ENOUGH_PERMISSION,
        404: TERM_NOT_FOUND,
    },
    summary='Criação de pronúncia.',
    description="""
    <br> Endpoint utilizado para criar pronúncias com áudio, fonemas e descrição sobre um determinado objeto.
    <br> Só poderá ser enviado um dos 3 objetos para ligação com a pronúncia específica.
    <br> origin_language, term - Pronúncia para termos
    <br> term_example_id - Pronúncia para exemplos
    <br> term_lexical_id - Pronúncia para lexical
    """,
)
def create_pronunciation(
    user: AdminUser,
    session: Session,
    pronunciation_schema: schema.PronunciationSchema,
):
    link_values = pronunciation_schema.model_link_dump()
    if 'term' in link_values:
        get_object_or_404(
            Term,
            session=session,
            term=link_values['term'],
            origin_language=link_values['origin_language'],
        )
    elif 'term_example_id' in link_values:
        get_object_or_404(
            TermExample, session=session, id=link_values['term_example_id']
        )
    elif 'term_lexical_id' in link_values:
        get_object_or_404(
            TermLexical, session=session, id=link_values['term_lexical_id']
        )

    db_pronuciation = Pronunciation(**pronunciation_schema.model_dump())

    session.add(db_pronuciation)
    session.commit()

    db_link = PronunciationLink(
        pronunciation_id=db_pronuciation.id,
        **link_values,
    )
    session.add(db_link)
    session.commit()

    session.refresh(db_pronuciation)
    return schema.PronunciationView(**db_pronuciation.model_dump())


@term_router.get(
    path='/pronunciation',
    status_code=200,
    response_model=list[schema.PronunciationView],
    response_description='A consulta das pronúncias do modelo especificado.',
    summary='Consulta das pronúncias.',
    description='Endpoint utilizado para consultar pronúncias com áudio, fonemas e descrição sobre um determinado modelo.',
)
def get_pronunciation(
    session: Session,
    pronunciation_schema: schema.PronunciationLinkSchema = Depends(),
):
    return session.exec(
        select(Pronunciation).where(
            Pronunciation.id.in_(
                select(PronunciationLink.pronunciation_id).filter_by(
                    **pronunciation_schema.model_link_dump()
                )
            )
        )
    )


@term_router.patch(
    path='/pronunciation/{pronunciation_id}',
    status_code=200,
    response_model=schema.PronunciationView,
    response_description='Atualizar a pronúncia do modelo especificado.',
    responses={
        401: USER_NOT_AUTHORIZED,
        403: NOT_ENOUGH_PERMISSION,
        404: TERM_NOT_FOUND,
    },
    summary='Atualização das pronúncias.',
    description='Endpoint utilizado para atualizar o áudio, fonemas ou descrição de uma pronúncia sobre um determinado modelo.',
)
def update_pronunciation(
    user: AdminUser,
    session: Session,
    pronunciation_id: int,
    pronunciation_schema: schema.TermPronunciationUpdate,
):
    db_pronunciation = get_object_or_404(
        Pronunciation, session=session, id=pronunciation_id
    )

    for key, value in pronunciation_schema.model_dump(
        exclude_unset=True,
    ).items():
        setattr(db_pronunciation, key, value)

    session.commit()
    session.refresh(db_pronunciation)

    return db_pronunciation


@term_router.post(
    path='/definition',
    status_code=201,
    response_model=schema.TermDefinitionView,
    response_description='A criação da definição do termo especificado.',
    responses={
        400: {
            'description': 'Todos os atributos da tradução precisam estar setados.',
            'content': {
                'application/json': {
                    'example': {
                        'detail': 'all translation attributes need to be setup.'
                    }
                }
            },
        },
        401: USER_NOT_AUTHORIZED,
        403: NOT_ENOUGH_PERMISSION,
        404: TERM_NOT_FOUND,
        409: {
            'description': 'A tradução nesse idioma enviada para essa definição já existe.',
            'content': {
                'application/json': {
                    'example': {
                        'detail': 'translation language for this definition is already registered.'
                    }
                }
            },
        },
    },
    summary='Criação das definições de um termo.',
    description='Endpoint utilizado para criar uma definição de um certo termo de um determinado idioma.',
)
def create_definition(
    session: Session,
    user: AdminUser,
    definition_schema: schema.TermDefinitionSchema,
):
    get_object_or_404(
        Term,
        session=session,
        term=definition_schema.term,
        origin_language=definition_schema.origin_language,
    )

    db_definition, _ = get_or_create_object(
        TermDefinition,
        session=session,
        defaults=definition_schema.model_dump(
            include={'term_level'}, exclude_unset=True
        ),
        **definition_schema.model_dump(exclude={'term_level'}),
    )

    translation_values = definition_schema.model_dump_translation().values()
    if not any(translation_values):
        return db_definition

    if not all(translation_values):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='all translation attributes need to be setup.',
        )

    db_definition_translation = TermDefinitionTranslation(
        translation=definition_schema.translation_definition,
        language=definition_schema.translation_language,
        meaning=definition_schema.translation_meaning,
        term_definition_id=db_definition.id,
    )

    try:
        session.add(db_definition_translation)
        session.commit()
        session.refresh(db_definition_translation)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='translation language for this definition is already registered.',
        )

    session.refresh(db_definition)
    return schema.TermDefinitionView(
        **db_definition.model_dump(),
        translation_definition=db_definition_translation.translation,
        translation_language=db_definition_translation.language,
        translation_meaning=db_definition_translation.meaning,
    )


@term_router.get(
    path='/definition',
    status_code=200,
    response_model=list[schema.TermDefinitionView],
    response_description='A consulta das definições de um termo específicado.',
    summary='Consulta das definições de um termo.',
    description='Endpoint utilizado para consultar as definição de um certo termo de um determinado idioma, sendo possível escolher a linguagem de tradução.',
)
def get_definition(
    session: Session,
    term: str,
    origin_language: constants.Language,
    translation_language: constants.Language | None = Query(
        default=None,
        description='Caso houver definições para a tradução requirida ela será retornada.',
    ),
    part_of_speech: constants.PartOfSpeech | None = Query(
        default=None, description='Filtrar por classe gramatical.'
    ),
    term_level: constants.TermLevel | None = Query(
        default=None, description='Filtrar por level do termo.'
    ),
):
    if translation_language is None:
        query_definition = (
            select(TermDefinition).where(
                TermDefinition.term == term,
                TermDefinition.origin_language == origin_language,
            )
        ).filter_by(**filter_query(['part_of_speech', 'term_level'], locals()))
        return session.exec(query_definition)

    query_definition = (
        select(
            TermDefinition,
            TermDefinitionTranslation.language,
            TermDefinitionTranslation.translation,
            TermDefinitionTranslation.meaning,
        )
        .where(
            TermDefinition.term == term,
            TermDefinition.origin_language == origin_language,
            TermDefinitionTranslation.language == translation_language,
        )
        .filter_by(**filter_query(['part_of_speech', 'term_level'], locals()))
        .join(
            TermDefinitionTranslation,
            TermDefinition.id == TermDefinitionTranslation.term_definition_id,
        )
    )

    result_query = session.exec(query_definition)

    result_list = []
    for row in result_query.all():
        schema_dict = {}
        for key, value in row._mapping.items():
            if key == 'TermDefinition':
                schema_dict.update(**value.model_dump())
            elif key == 'language':
                schema_dict.update(translation_language=value)
            elif key == 'translation':
                schema_dict.update(translation_definition=value)
            elif key == 'meaning':
                schema_dict.update(translation_meaning=value)
        result_list.append(schema_dict)
    return [schema.TermDefinitionView(**result) for result in result_list]


@term_router.patch(
    path='/definition/{definition_id}',
    status_code=200,
    response_model=schema.TermDefinitionView,
    response_description='Atualização das definições do termo.',
    responses={
        401: USER_NOT_AUTHORIZED,
        403: NOT_ENOUGH_PERMISSION,
        404: TERM_NOT_FOUND,
    },
    summary='Atualizar as definições de um termo.',
    description='Endpoint utilizado para atualizar as definição de um certo termo de um determinado idioma.',
)
def update_definition(
    user: AdminUser,
    session: Session,
    definition_id: int,
    definition_schema: schema.TermDefinitionSchemaUpdate,
    translation_language: constants.Language | None = Query(
        default=None,
        description='Irá modificar a definição para a tradução especificada',
    ),
):
    db_definition = get_object_or_404(TermDefinition, session, id=definition_id)

    if translation_language is None:
        for key, value in definition_schema.model_dump(
            exclude_unset=True,
        ).items():
            setattr(db_definition, key, value)

        session.commit()
        session.refresh(db_definition)

        return db_definition

    db_definition_translation = get_object_or_404(
        TermDefinitionTranslation,
        session,
        term_definition_id=db_definition.id,
        language=translation_language,
    )
    translation_meaning = getattr(definition_schema, 'translation_meaning', None)
    translation_definition = getattr(definition_schema, 'translation_definition', None)
    if translation_meaning:
        db_definition_translation.meaning = translation_meaning
    if translation_definition:
        db_definition_translation.translation = translation_definition

    session.commit()
    session.refresh(db_definition_translation)

    session.refresh(db_definition)
    return schema.TermDefinitionView(
        **db_definition.model_dump(),
        translation_definition=db_definition_translation.translation,
        translation_language=db_definition_translation.language,
        translation_meaning=db_definition_translation.meaning,
    )


@term_router.post(
    path='/example',
    status_code=201,
    response_model=schema.TermExampleView,
    response_description='Criação de um exemplo para determinado termo ou definição.',
    responses={
        400: {
            'description': 'Todos os atributos da tradução precisam estar setados.',
            'content': {
                'application/json': {
                    'example': {
                        'detail': 'all translation attributes need to be setup.'
                    }
                }
            },
        },
        401: USER_NOT_AUTHORIZED,
        403: NOT_ENOUGH_PERMISSION,
        404: TERM_NOT_FOUND,
        409: {
            'description': 'A tradução nesse idioma enviada para esse exemplo já existe.',
            'content': {
                'application/json': {
                    'example': {
                        'detail': 'translation language for this example is already registered.'
                    }
                }
            },
        },
    },
    summary='Criação de exemplos sobre um termo.',
    description='Endpoint utilizado para criação de exemplos para termos ou definições.',
)
def create_example(
    user: AdminUser, session: Session, example_schema: schema.TermExampleSchema
):
    get_object_or_404(
        Term,
        session=session,
        term=example_schema.term,
        origin_language=example_schema.origin_language,
    )

    db_example, _ = get_or_create_object(
        TermExample,
        session=session,
        defaults=example_schema.model_dump(
            include={'term_definition_id'}, exclude_unset=True
        ),
        **example_schema.model_dump(exclude={'term_definition_id'}),
    )

    translation_attributes = example_schema.model_dump_translation().values()
    if not any(translation_attributes):
        return db_example

    if not all(translation_attributes):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='all translation attributes need to be setup.',
        )

    db_example_translation = TermExampleTranslation(
        translation=example_schema.translation_example,
        language=example_schema.translation_language,
        term_example_id=db_example.id,
    )

    try:
        session.add(db_example_translation)
        session.commit()
        session.refresh(db_example_translation)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='translation language for this example is already registered.',
        )

    session.refresh(db_example)
    return schema.TermExampleView(
        **db_example.model_dump(),
        translation_language=db_example_translation.language,
        translation_example=db_example.example,
    )


@term_router.get(
    path='/example',
    status_code=200,
    response_model=list[schema.TermExampleView],
    response_description='Consulta de um exemplo para determinado termo.',
    summary='Consulta de exemplos sobre um termo.',
    description='Endpoint utilizado para consultar exemplos de termos ou definições.',
)
def get_example(
    session: Session,
    term: str,
    origin_language: constants.Language,
    translation_language: constants.Language | None = Query(
        default=None,
        description='Caso houver exemplos para a tradução requirida ela será retornada.',
    ),
    term_definition_id: int | None = Query(
        default=None,
        description='Filtrar por exemplos sobre a definição de um termo.',
    ),
):
    if translation_language is None:
        query_example = select(TermExample).where(
            TermExample.term == term,
            TermExample.origin_language == origin_language,
            TermExample.term_definition_id == term_definition_id,
        )
        return session.exec(query_example)

    query_example = (
        select(
            TermExample,
            TermExampleTranslation.language,
            TermExampleTranslation.translation,
        )
        .join(
            TermExampleTranslation,
            TermExample.id == TermExampleTranslation.term_example_id,
        )
        .where(
            TermExampleTranslation.language == translation_language,
            TermExample.term == term,
            TermExample.origin_language == origin_language,
            TermExample.term_definition_id == term_definition_id,
        )
    )
    result_query = session.exec(query_example)

    result_list = []
    for row in result_query.all():
        schema_dict = {}
        for key, value in row._mapping.items():
            if key == 'TermExample':
                schema_dict.update(**value.model_dump())
            elif key == 'language':
                schema_dict.update(translation_language=value)
            elif key == 'translation':
                schema_dict.update(translation_example=value)
        result_list.append(schema_dict)
    return [schema.TermExampleView(**result) for result in result_list]


@term_router.patch(
    path='/example/{example_id}',
    status_code=200,
    response_model=schema.TermExampleView,
    response_description='Atualização do exemplo do termo ou definição.',
    responses={
        401: USER_NOT_AUTHORIZED,
        403: NOT_ENOUGH_PERMISSION,
        404: TERM_NOT_FOUND,
    },
    summary='Atualizar exemplos.',
    description='Endpoint para atualizar um exemplo ligado a um termo ou definição.',
)
def update_example(
    user: AdminUser,
    session: Session,
    example_id: int,
    example_schema: schema.TermExampleSchemaUpdate,
    translation_language: constants.Language | None = Query(
        default=None,
        description='Irá modificar o exemplo para a tradução especificada',
    ),
):
    db_example = get_object_or_404(TermExample, session, id=example_id)

    if translation_language is None:
        example = getattr(example_schema, 'example', None)
        if example:
            db_example.example = example

        session.commit()
        session.refresh(db_example)

        return db_example

    db_example_translation = get_object_or_404(
        TermExampleTranslation,
        session,
        term_example_id=db_example.id,
        language=translation_language,
    )
    translation_example = getattr(example_schema, 'translation_example', None)
    if translation_example:
        db_example_translation.translation = translation_example

    session.commit()
    session.refresh(db_example_translation)

    session.refresh(db_example)
    return schema.TermExampleView(
        **db_example.model_dump(),
        translation_language=db_example_translation.language,
        translation_example=db_example.example,
    )


@term_router.post(
    path='/lexical',
    status_code=201,
    response_model=schema.TermLexicalView,
    response_description='Criação de uma relação lexical',
    responses={
        401: USER_NOT_AUTHORIZED,
        403: NOT_ENOUGH_PERMISSION,
        404: TERM_NOT_FOUND,
    },
    summary='Criação de relação de uma relação lexical.',
    description='Endpoint utilizado para criação de relações lexicais entre termos, sendo elas sinônimos, antônimos e conjugações.',
)
def create_lexical(
    lexical_schema: schema.TermLexicalSchema, session: Session, user: AdminUser
):
    get_object_or_404(
        Term,
        session=session,
        term=lexical_schema.term,
        origin_language=lexical_schema.origin_language,
    )

    db_lexical = TermLexical(**lexical_schema.model_dump())

    session.add(db_lexical)
    session.commit()
    session.refresh(db_lexical)

    return db_lexical


@term_router.get(
    path='/lexical',
    status_code=200,
    response_model=list[schema.TermLexicalView],
    summary='Consulta de relação de uma relação lexical.',
    description='Endpoint utilizado para consultar de relações lexicais entre termos, sendo elas sinônimos, antônimos e conjugações.',
)
def get_lexical(
    term: str,
    origin_language: constants.Language,
    type: constants.TermLexicalType,
    session: Session,
):
    return session.exec(
        select(TermLexical).where(
            TermLexical.term == term,
            TermLexical.origin_language == origin_language,
            TermLexical.type == type.lower(),
        )
    )
