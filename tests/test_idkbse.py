from conf_util import *
import json

pytestmark = pytest.mark.dev

urls_to_test_always = [
    f"{ID_URL}/sys/context/kbv",
    f"{ID_URL}/term/sao/Konstnärer i utlandet",
    f"{ID_URL}/term/sao/R%26B%20%28musik%29",
    f"{ID_URL}/term/saogf/Handb%C3%B6cker%2C%20manualer%20etc.",
    f"{ID_URL}/term/gmgpc%2F%2Fswe/Kartor",
]


def test_get_urls(session):
    urls = urls_to_test_always + [
        f"{ID_URL}/",
        f"{ID_URL}/vocab/",
    ]

    for url in urls:
        for content_type in HTML_CONTENT_TYPES:
            result = session.get(url, headers={"accept": content_type})
            _check_html_response(result, url)

        for content_type in NON_HTML_CONTENT_TYPES:
            result = session.get(url, headers={"accept": content_type})
            _check_nonhtml_response(result, content_type, url)


def test_get_data_urls(session):
    urls = urls_to_test_always + [
        f"{ID_URL}/vocab",
        f"{ID_URL}/vocab/display",
    ]

    for url in urls:
        for content_type, extension in FILE_TYPES.items():
            result = session.get(f"{url}/data.{extension}")
            _check_nonhtml_response(result, content_type, url)


def test_context(session):
    context_url = f"{ID_URL}/context.jsonld"

    result = session.get(context_url, allow_redirects=False)
    assert result.status_code == 302, context_url

    # Note: allow_redirects=True is default behavior
    result = session.get(context_url, allow_redirects=True)
    assert result.status_code == 200, context_url
    assert json.loads(result.content), context_url


def _check_html_response(result, url):
    assert result.status_code == 200, url
    assert "text/html" in result.headers["content-type"]
    assert len(result.content) > 100, url


def _check_nonhtml_response(result, content_type, url):
    assert result.status_code == 200, url
    # Note: result.headers is a case-insensitive dict so the header casing
    # in the response doesn't matter
    assert content_type in result.headers["content-type"], url
    assert result.headers.get("content-profile"), url
    assert result.headers.get("content-location"), url
    assert result.headers.get("document"), url
    assert result.headers.get("link"), url

    # Basic sanity checks
    assert len(result.content) > 100, url
    if content_type in ["application/ld+json", "application/json"]:
        assert json.loads(result.content), url
