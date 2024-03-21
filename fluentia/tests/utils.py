from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from fluentia.core.model.shortcut import get_object_or_404


def assert_json_response(session, Model, response_json, **model_kwargs):
    db_model = get_object_or_404(Model, session=session, **model_kwargs)

    json_schema = Model(**response_json)

    assert json_schema == db_model


def set_url_params(url, **params):
    params = dict(filter(lambda item: item[1] is not None, params.items()))
    parsed_url = urlparse(url)
    current_params = parse_qs(parsed_url.query)
    current_params.update(params)
    new_query = urlencode(current_params, doseq=True)
    return urlunparse(parsed_url._replace(query=new_query))
