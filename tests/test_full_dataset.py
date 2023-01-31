from conf_util import *

pytestmark = pytest.mark.qa

def test_free_text_relevance(session):
    search_endpoint = "/find"
    limit = 10
    query_params = {'q': 'röda rummet',
                    '_limit': limit,
                    '@type': 'Instance'}

    result = session.get(ROOT_URL + search_endpoint,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert len(es_result['items']) == limit
    for item in es_result['items']:
        assert 'hasTitle' in item
        assert item['hasTitle']
        assert item['hasTitle'][0]['mainTitle'].lower().startswith('röda rummet')


def test_not_operator(session):
    search_endpoint = "/find"
    limit = 50
    query_params = {'q': 'röda rummet',
                    '_limit': limit,
                    '@type': 'Instance',
                    'not-instanceOf.language.@id': 'https://id.kb.se/language/swe'
                    }

    result = session.get(ROOT_URL + search_endpoint,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert len(es_result['items']) == limit
    for item in es_result['items']:
        assert not any(language.get('@id') == 'https://id.kb.se/language/swe' for language in item['instanceOf'].get('language', []))


def test_and_operator(session):
    search_endpoint = "/find"
    limit = 50

    # First do an OR query
    query_params_or = {'q': '*',
                    '_limit': limit,
                    '@type': 'Instance',
                    'instanceOf.subject.@id': ['https://id.kb.se/term/sao/Historia', 'https://id.kb.se/term/sao/1300-talet']
                    }
    result = session.get(ROOT_URL + search_endpoint,
                         params=query_params_or)
    assert result.status_code == 200
    es_result_or = result.json()
    assert len(es_result_or['items']) == limit

    # And then AND (should be fewer hits)
    query_params_and = {
                    '_limit': limit,
                    '@type': 'Instance',
                    'and-instanceOf.subject.@id': ['https://id.kb.se/term/sao/Historia', 'https://id.kb.se/term/sao/1300-talet']
                    }
    result = session.get(ROOT_URL + search_endpoint,
                         params=query_params_and)
    assert result.status_code == 200
    es_result_and = result.json()
    assert len(es_result_and['items']) == limit

    assert es_result_or["totalItems"] > es_result_and["totalItems"]
    for item in es_result_and['items']:
        assert any(subject.get('@id') == 'https://id.kb.se/term/sao/Historia' for subject in item['instanceOf']['subject'])
        assert any(subject.get('@id') == 'https://id.kb.se/term/sao/1300-talet' for subject in item['instanceOf']['subject'])


def test_and_and_multiple_not(session):
    search_endpoint = "/find"
    limit = 100
    query_params = {'q': '*',
                    '_limit': limit,
                    '@type': 'Instance',
                    'and-instanceOf.subject.@id': ['https://id.kb.se/term/sao/Historia', 'https://id.kb.se/term/sao/Sverige'],
                    'not-instanceOf.language.@id': ['https://id.kb.se/language/swe', 'https://id.kb.se/language/eng']
                    }

    result = session.get(ROOT_URL + search_endpoint,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert len(es_result['items']) == limit

    for item in es_result['items']:
        assert any(subject.get('@id') == 'https://id.kb.se/term/sao/Historia' for subject in item['instanceOf']['subject'])
        assert any(subject.get('@id') == 'https://id.kb.se/term/sao/Sverige' for subject in item['instanceOf']['subject'])
        assert not any(language.get('@id') == 'https://id.kb.se/language/eng' for language in item['instanceOf'].get('language', []))
        assert not any(language.get('@id') == 'https://id.kb.se/language/swe' for language in item['instanceOf'].get('language', []))
