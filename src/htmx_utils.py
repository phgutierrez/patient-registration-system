"""Apoio a respostas parciais HTMX sem alterar URLs nem endpoints.

A mesma rota atende navegação tradicional (página completa) e requisições
HTMX (somente o fragmento). Restaurações de histórico e navegação "boost"
recebem sempre a página completa.
"""
from flask import make_response, render_template, request


def is_htmx_partial_request() -> bool:
    headers = request.headers
    return (
        headers.get('HX-Request') == 'true'
        and headers.get('HX-History-Restore-Request') != 'true'
        and headers.get('HX-Boosted') != 'true'
    )


def render_page_or_partial(page_template: str, partial_template: str, status: int = 200, **context):
    partial = is_htmx_partial_request()
    template = partial_template if partial else page_template
    response = make_response(
        render_template(template, htmx_partial=partial, **context), status
    )
    response.vary.add('HX-Request')
    return response
