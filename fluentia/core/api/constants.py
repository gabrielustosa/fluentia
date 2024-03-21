USER_NOT_AUTHORIZED = {
    'description': 'Usuário não autorizado.',
    'content': {
        'application/json': {'example': {'detail': 'credentials do not match.'}}
    },
}
NOT_ENOUGH_PERMISSION = {
    'description': 'Usuário não possui permissão para executar.',
    'content': {'application/json': {'example': {'detail': 'not enough permission.'}}},
}
TERM_NOT_FOUND = {
    'description': 'Termo especificado não foi encontrado.',
    'content': {'application/json': {'example': {'detail': 'term does not exists.'}}},
}
CARDSET_NOT_FOUND = {
    'description': 'Conjuto de cartas especificado não foi encontrado.',
    'content': {
        'application/json': {'example': {'detail': 'cardset does not exists.'}}
    },
}
CARD_NOT_FOUND = {
    'description': 'Cartão de aprendizado especificado não foi encontrado.',
    'content': {'application/json': {'example': {'detail': 'card does not exists.'}}},
}
