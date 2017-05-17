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
    limit = 1
    query_params = {'q': 'mumintrollet',
                    '_limit': limit}

    result = session.get(ROOT_URL + search_endpoint,
                         params=query_params,
                         headers={'Accept': 'application/ld+json'})
    assert result.status_code == 200

    es_result = result.json()
    assert es_result['totalItems'] == 4
    assert len(es_result['items']) == limit

    aggregations = es_result['stats']['sliceByDimension']
    assert len(aggregations['@type']['observation']) == 2

    search_details = es_result['search']
    search_mappings = search_details['mapping']
    assert len(search_mappings) == 1


def test_search_aggregates(session):
    search_endpoint = "/find"
    limit = 0
    query_params = {'q': '*',
                    '_limit': limit,
                    '_statsrepr': '{"publication.date":{"sort":"value","sortOrder":"desc","size":2}}'}
    result = session.get(ROOT_URL + search_endpoint,
                         params=query_params,
                         headers={'Accept': 'application/ld+json'})
    assert result.status_code == 200

    es_result = result.json()
    assert len(es_result['items']) == limit

    aggregations = es_result['stats']['sliceByDimension']
    assert len(aggregations['publication.date']['observation']) == 2

    items_first = aggregations['publication.date']['observation'][0]['totalItems']
    items_second = aggregations['publication.date']['observation'][1]['totalItems']
    assert items_first >= items_second

    query_params = {'q': '*',
                    '_limit': limit,
                    '_statsrepr': '{"publication.date":{"sort":"key","sortOrder":"desc","size":2}}'}
    result = session.get(ROOT_URL + search_endpoint,
                         params=query_params,
                         headers={'Accept': 'application/ld+json'})
    value_first = int(aggregations['publication.date']['observation'][0]['object']['label'])
    value_second = int(aggregations['publication.date']['observation'][1]['object']['label'])
    assert value_first >= value_second


def test_search_filtering(session):
    search_endpoint = "/find"
    limit = 2000
    only_instance = ['Instance']
    instance_and_type = ['Instance', 'Item']
    bad_type = ['NonExistantType']

    # single type
    query_params = {'q': '*',
                    '@type': only_instance,
                    '_limit': limit}

    result = session.get(ROOT_URL + search_endpoint,
                         params=query_params,
                         headers={'Accept': 'application/ld+json'})
    assert result.status_code == 200

    es_result = result.json()
    assert all(is_instance(item) for item in es_result['items'])

    # instance and type
    query_params = {'q': '*',
                    '@type': instance_and_type,
                    '_limit': limit}

    result = session.get(ROOT_URL + search_endpoint,
                         params=query_params,
                         headers={'Accept': 'application/ld+json'})
    assert result.status_code == 200

    es_result = result.json()
    assert all(is_instance(item) or is_item(item)
               for item in es_result['items'])

    # bad type
    query_params = {'q': '*',
                    '@type': bad_type,
                    '_limit': limit}

    result = session.get(ROOT_URL + search_endpoint,
                         params=query_params,
                         headers={'Accept': 'application/ld+json'})
    assert result.status_code == 200

    es_result = result.json()
    assert len(es_result['items']) == 0


def test_search_limit(session):
    search_endpoint = "/find"
    limit0 = 0
    limit1 = 1
    limit200 = 200

    # limit=0
    query_params = {'q': '*',
                    '_limit': limit0}

    result = session.get(ROOT_URL + search_endpoint,
                         params=query_params,
                         headers={'Accept': 'application/ld+json'})
    assert result.status_code == 200

    es_result = result.json()
    assert len(es_result['items']) == limit0

    # limit=1
    query_params = {'q': '*',
                    '_limit': limit1}

    result = session.get(ROOT_URL + search_endpoint,
                         params=query_params,
                         headers={'Accept': 'application/ld+json'})
    assert result.status_code == 200

    es_result = result.json()
    assert len(es_result['items']) == limit1

    # limit=200
    query_params = {'q': '*',
                    '_limit': limit200}

    result = session.get(ROOT_URL + search_endpoint,
                         params=query_params,
                         headers={'Accept': 'application/ld+json'})
    assert result.status_code == 200

    es_result = result.json()
    assert len(es_result['items']) == limit200


def test_search_isbn(session):
    search_endpoint = "/find"

    # good query
    query_params = {'identifiedBy.value': '91-1-895301-8',
                    'identifiedBy.@type': 'ISBN'}

    result = session.get(ROOT_URL + search_endpoint,
                         params=query_params,
                         headers={'Accept': 'application/ld+json'})
    assert result.status_code == 200

    es_result = result.json()
    assert len(es_result['items']) == 1

    # bad query
    query_params = {'identifiedBy.value': 'not_a_valid_isbn',
                    'identifiedBy.@type': 'ISBN'}

    result = session.get(ROOT_URL + search_endpoint,
                         params=query_params,
                         headers={'Accept': 'application/ld+json'})
    assert result.status_code == 200

    es_result = result.json()
    assert len(es_result['items']) == 0


def is_instance(doc):
    return doc['@type'] == 'Instance'


def is_item(doc):
    return doc['@type'] == 'Item'
