from restapi import *

def test_update_and_delete_holding(session):
    holding_id = create_holding(session)

    result = session.get(holding_id, headers={'Accept':'application/ld+json'})
    assert result.status_code == 200

    etag = result.headers['ETag']
    result = update_holding(session, holding_id, etag)
    assert result.status_code == 204

    result = session.delete(holding_id)
    assert result.status_code == 204

    result = session.get(holding_id)
    assert result.status_code == 404

    result = session.delete(holding_id)
    assert result.status_code == 410


def test_search(session):
    search_endpoint = "/find"
    query_params = {'q': 'mumintrollet',
                    '_limit': 1}

    result = session.get(ROOT_URL + search_endpoint,
                         params=query_params,
                         headers={'Accept': 'application/ld+json'})
    assert result.status_code == 200

    es_result = result.json()
    assert es_result['totalItems'] == 4
    assert len(es_result['items']) == 1

    aggregations = es_result['stats']['sliceByDimension']
    assert len(aggregations['@type']['observation']) == 2

    search_details = es_result['search']
    search_mappings = search_details['mapping']
    assert len(search_mappings) == 1

