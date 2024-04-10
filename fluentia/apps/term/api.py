from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session as SQLModelSession

from fluentia.apps.term import constants, models, schema
from fluentia.apps.user.models import User
from fluentia.apps.user.security import get_current_admin_user
from fluentia.core.api.constants import (
    NOT_ENOUGH_PERMISSION,
    TERM_NOT_FOUND,
    USER_NOT_AUTHORIZED,
)
from fluentia.core.model.shortcut import get_object_or_404
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
        200: {
            'description': 'O termo enviado já existe nesta linguagem, por esse motivo ele foi retornado.',
            'content': {
                'application/json': {
                    'example': {'term': 'Casa', 'origin_language': 'pt'}
                }
            },
        },
        401: USER_NOT_AUTHORIZED,
        403: NOT_ENOUGH_PERMISSION,
    },
    summary='Criação de um novo termo.',
    description="""
        <br> Endpoint utilizado para a criação de um termo, palavra ou expressão de um certo idioma.
        <br> A princípio, poderá existir somente um termo com o mesmo valor de expressão de texto para cada idioma.
        <br> É importante salientar que se o valor do termo enviado for igual a um termo existente no idioma ele será retornado.
        <br> Da mesma forma, se o valor do termo enviado for igual a uma forma idiomática (TermLexical - Type.Form) relacionada a um termo já existente no idioma, esse termo existente será retornado.
    """,
)
def create_term(
    user: AdminUser,
    session: Session,
    term_schema: schema.TermSchemaBase,
):
    db_term, created = models.Term.get_or_create(session, **term_schema.model_dump())
    return JSONResponse(
        status_code=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        content=db_term.model_dump(),
    )


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
    db_term = models.Term.get_or_404(
        session=session, term=term, origin_language=origin_language
    )

    meanings_list = []
    if translation_language:
        meanings_list = models.TermDefinitionTranslation.list_meaning(
            session,
            term,
            origin_language,
            translation_language,
        )

    lexical_list = []
    if lexical:
        lexical_list = [
            schema.TermLexicalSchema(**lexical.model_dump())
            for lexical in models.TermLexical.list(session, term, origin_language)
        ]

    pronunciation_list = []
    if pronunciation:
        pronunciation_list = [
            schema.PronunciationView(**db_pronunciation.model_dump())
            for db_pronunciation in models.Pronunciation.list(
                session, term=term, origin_language=origin_language
            )
        ]

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
    return models.Term.search(session, text, origin_language)


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
    return models.Term.search_term_meaning(
        session,
        text,
        origin_language,
        translation_language,
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
    db_pronuciation = models.Pronunciation.create(
        session, **pronunciation_schema.model_dump()
    )

    models.PronunciationLink.create(
        session,
        pronunciation_id=db_pronuciation.id,
        **pronunciation_schema.model_link_dump(),
    )

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
def list_pronunciation(
    session: Session,
    pronunciation_schema: schema.PronunciationLinkSchema = Depends(),
):
    return models.Pronunciation.list(session, **pronunciation_schema.model_dump())


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
        models.Pronunciation, session=session, id=pronunciation_id
    )

    return models.Pronunciation.update(
        session,
        db_pronunciation,
        **pronunciation_schema.model_dump(
            exclude_unset=True,
        ),
    )


@term_router.post(
    path='/definition',
    status_code=201,
    response_model=schema.TermDefinitionView,
    response_description='A criação da definição do termo especificado.',
    responses={
        200: {
            'description': 'A definição enviada já existe para esse termo, por esse motivo ele foi retornado.',
        },
        401: USER_NOT_AUTHORIZED,
        403: NOT_ENOUGH_PERMISSION,
        404: TERM_NOT_FOUND,
    },
    summary='Criação das definições de um termo.',
    description='Endpoint utilizado para criar uma definição de um certo termo de um determinado idioma.',
)
def create_definition(
    user: AdminUser,
    session: Session,
    definition_schema: schema.TermDefinitionSchema,
):
    db_definition, created = models.TermDefinition.get_or_create(
        session, definition_schema
    )
    return JSONResponse(
        status_code=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        content=db_definition.model_dump(),
    )


@term_router.post(
    path='/definition/translation',
    status_code=201,
    response_model=schema.TermDefinitionTranslationSchema,
    response_description='A criação da tradução para a definição do termo especificado.',
    responses={
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
    summary='Criação da tradução das definições de um termo.',
    description='Endpoint utilizado para criar uma tradução para uma definição de um certo termo de um determinado idioma.',
)
def create_definition_translation(
    user: AdminUser,
    session: Session,
    translation_schema: schema.TermDefinitionTranslationSchema,
):
    get_object_or_404(
        models.TermDefinition,
        session=session,
        id=translation_schema.term_definition_id,
    )

    try:
        return models.TermDefinitionTranslation.create(
            session=session, **translation_schema.model_dump()
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='translation language for this definition is already registered.',
        )


@term_router.get(
    path='/definition',
    status_code=200,
    response_model=list[schema.TermDefinitionView],
    response_description='A consulta das definições de um termo específicado.',
    summary='Consulta das definições de um termo.',
    description='Endpoint utilizado para consultar as definição de um certo termo de um determinado idioma, sendo possível escolher a linguagem de tradução.',
)
def list_definition(
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
        return models.TermDefinition.list(
            session,
            term,
            origin_language,
            part_of_speech,
            term_level,
        )

    definition_list = []
    for row in models.TermDefinitionTranslation.list(
        session,
        term,
        origin_language,
        part_of_speech,
        term_level,
        translation_language,
    ).all():
        db_definition, db_definition_translation = row
        definition_list.append(
            schema.TermDefinitionView(
                **db_definition.model_dump(),
                translation_language=db_definition_translation.language,
                translation_definition=db_definition_translation.translation,
                translation_meaning=db_definition_translation.meaning,
            )
        )
    return definition_list


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
):
    db_definition = get_object_or_404(models.TermDefinition, session, id=definition_id)

    return models.TermDefinition.update(
        session,
        db_definition,
        **definition_schema.model_dump(
            exclude_unset=True,
        ),
    )


@term_router.patch(
    path='/definition/translation/{definition_id}/{language}',
    status_code=200,
    response_model=schema.TermDefinitionTranslationSchema,
    response_description='Atualização das definições do termo.',
    responses={
        401: USER_NOT_AUTHORIZED,
        403: NOT_ENOUGH_PERMISSION,
        404: TERM_NOT_FOUND,
    },
    summary='Atualizar as definições de um termo.',
    description='Endpoint utilizado para atualizar as definição de um certo termo de um determinado idioma.',
)
def update_definition_translation(
    user: AdminUser,
    session: Session,
    definition_id: int,
    language: constants.Language,
    translation_schema: schema.TermDefinitionTranslationUpdate,
):
    db_definition_translation = get_object_or_404(
        models.TermDefinitionTranslation,
        session,
        term_definition_id=definition_id,
        language=language,
    )
    return models.TermDefinitionTranslation.update(
        session,
        db_definition_translation,
        **translation_schema.model_dump(exclude_unset=True),
    )


@term_router.post(
    path='/example',
    status_code=201,
    response_model=schema.TermExampleView,
    response_description='Criação de um exemplo para determinado termo ou definição.',
    responses={
        401: USER_NOT_AUTHORIZED,
        403: NOT_ENOUGH_PERMISSION,
        404: TERM_NOT_FOUND,
    },
    summary='Criação de exemplos sobre um termo.',
    description='Endpoint utilizado para criação de exemplos para termos ou definições.',
)
def create_example(
    user: AdminUser,
    session: Session,
    example_schema: schema.TermExampleSchema,
):
    db_example, created = models.TermExample.get_or_create(session, example_schema)
    return JSONResponse(
        status_code=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        content=db_example.model_dump(),
    )


@term_router.post(
    path='/example/translation',
    status_code=201,
    response_model=schema.TermExampleTranslationSchema,
    response_description='Criação de uma tradução para um exemplo para determinado termo ou definição.',
    responses={
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
    summary='Criação de traduções para exemplos sobre um termo.',
    description='Endpoint utilizado para criação tradução para exemplos de termos ou definições.',
)
def create_example_translation(
    user: AdminUser,
    session: Session,
    translation_schema: schema.TermExampleTranslationSchema,
):
    get_object_or_404(
        models.TermExample,
        session,
        id=translation_schema.term_example_id,
    )

    try:
        return models.TermExampleTranslation.create(
            session, **translation_schema.model_dump()
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='translation language for this example is already registered.',
        )


@term_router.get(
    path='/example',
    status_code=200,
    response_model=list[schema.TermExampleView],
    response_description='Consulta de um exemplo para determinado termo.',
    summary='Consulta de exemplos sobre um termo.',
    description='Endpoint utilizado para consultar exemplos de termos ou definições.',
)
def list_example(
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
    term_lexical_id: int | None = Query(
        default=None,
        description='Filtrar por lexical sobre um termo.',
    ),
):
    if translation_language is None:
        return models.TermExample.list(
            session,
            term,
            origin_language,
            term_definition_id,
            term_lexical_id,
        )

    example_list = []
    for row in models.TermExampleTranslation.list(
        session,
        term,
        origin_language,
        translation_language,
        term_definition_id,
        term_lexical_id,
    ):
        db_example, db_example_translation = row
        example_list.append(
            schema.TermExampleView(
                **db_example.model_dump(),
                translation_language=db_example_translation.language,
                translation_example=db_example_translation.translation,
            )
        )
    return example_list


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
):
    db_example = get_object_or_404(models.TermExample, session, id=example_id)

    return models.TermExample.update(
        session, db_example, example=example_schema.example
    )


@term_router.patch(
    path='/example/translation/{example_id}/{language}',
    status_code=200,
    response_model=schema.TermExampleTranslationSchema,
    response_description='Atualização da tradução do exemplo do termo ou definição.',
    responses={
        401: USER_NOT_AUTHORIZED,
        403: NOT_ENOUGH_PERMISSION,
        404: TERM_NOT_FOUND,
    },
    summary='Atualizar traduções de exemplos.',
    description='Endpoint para atualizar traduções de um exemplo ligado a um termo ou definição.',
)
def update_example_translation(
    user: AdminUser,
    session: Session,
    example_id: int,
    language: constants.Language,
    example_schema: schema.TermExampleTranslationUpdateSchema,
):
    db_example_translation = get_object_or_404(
        models.TermExampleTranslation,
        session,
        term_example_id=example_id,
        language=language,
    )
    return models.TermExampleTranslation.update(
        session, db_example_translation, **example_schema.model_dump()
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
    user: AdminUser,
    session: Session,
    lexical_schema: schema.TermLexicalSchema,
):
    return models.TermLexical.create(session, **lexical_schema.model_dump())


@term_router.get(
    path='/lexical',
    status_code=200,
    response_model=list[schema.TermLexicalView],
    summary='Consulta de relação de uma relação lexical.',
    description='Endpoint utilizado para consultar de relações lexicais entre termos, sendo elas sinônimos, antônimos e conjugações.',
)
def get_lexical(
    session: Session,
    term: str,
    origin_language: constants.Language,
    type: constants.TermLexicalType,
):
    return models.TermLexical.list(session, term, origin_language, type)
