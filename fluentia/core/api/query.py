def filter_query(fields, params):
    return {
        field: value
        for field, value in params.items()
        if field in fields and value is not None
    }
