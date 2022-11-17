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