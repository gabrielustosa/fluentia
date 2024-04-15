from fluentia.core.model.shortcut import get_object_or_404


def assert_json_response(session, Model, response_json, **model_kwargs):
    db_model = get_object_or_404(Model, session=session, **model_kwargs)

    json_schema = Model(**response_json)

    assert json_schema == db_model
