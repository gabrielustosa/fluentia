from urllib.parse import parse_qs, urlencode, urlparse, urlunparse


def set_url_params(url, **params):
    params = dict(filter(lambda item: item[1] is not None, params.items()))
    parsed_url = urlparse(url)
    current_params = parse_qs(parsed_url.query)
    current_params.update(params)
    new_query = urlencode(current_params, doseq=True)
    return str(urlunparse(parsed_url._replace(query=new_query)))
