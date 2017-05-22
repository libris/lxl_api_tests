from restapi import *


def test_update_and_delete_holding(session):
    holding_id = create_holding(session)

    result = session.get(holding_id,
                         headers={'Accept': 'application/ld+json'})
    assert result.status_code == 200

    etag = result.headers['ETag']
    result = update_holding(session, holding_id, etag)
    assert result.status_code == 204

    _trigger_elastic_refresh(session)
    result = session.delete(holding_id)

    assert result.status_code == 204

    result = session.get(holding_id)
    assert result.status_code == 404

    result = session.delete(holding_id)
    assert result.status_code == 410

    _trigger_elastic_refresh(session)


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
    aggs_by_value = {"publication.date":
                     {"sort": "value", "sortOrder": "desc", "size": 2}}
    aggs_by_key = {"publication.date":
                   {"sort": "key", "sortOrder": "desc", "size": 2}}

    query_params = {'q': '*',
                    '_limit': limit,
                    '_statsrepr': json.dumps(aggs_by_value)}
    result = session.get(ROOT_URL + search_endpoint,
                         params=query_params,
                         headers={'Accept': 'application/ld+json'})
    assert result.status_code == 200

    es_result = result.json()
    assert len(es_result['items']) == limit

    aggregations = es_result['stats']['sliceByDimension']
    assert len(aggregations) == 1
    assert len(aggregations['publication.date']['observation']) == 2

    observations = aggregations['publication.date']['observation']
    items_first = observations[0]['totalItems']
    items_second = observations[1]['totalItems']
    assert items_first >= items_second

    query_params = {'q': '*',
                    '_limit': limit,
                    '_statsrepr': json.dumps(aggs_by_key)}
    result = session.get(ROOT_URL + search_endpoint,
                         params=query_params,
                         headers={'Accept': 'application/ld+json'})

    es_result = result.json()
    assert len(es_result['items']) == limit

    aggregations = es_result['stats']['sliceByDimension']
    assert len(aggregations) == 1
    assert len(aggregations['publication.date']['observation']) == 2

    observations = aggregations['publication.date']['observation']
    value_first = int(observations[0]['object']['label'])
    value_second = int(observations[1]['object']['label'])
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
    assert all(is_type_instance(item) for item in es_result['items'])

    # instance and type
    query_params = {'q': '*',
                    '@type': instance_and_type,
                    '_limit': limit}

    result = session.get(ROOT_URL + search_endpoint,
                         params=query_params,
                         headers={'Accept': 'application/ld+json'})
    assert result.status_code == 200

    es_result = result.json()
    assert all(is_type_instance(item) or is_type_item(item)
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


def test_search_indexing(session):
    search_endpoint = "/find"

    query_params = {'itemOf.@id': 'http://libris.kb.se/resource/bib/816913'}

    # before create - no hits
    result = session.get(ROOT_URL + search_endpoint,
                         params=query_params,
                         headers={'Accept': 'application/ld+json'})
    assert result.status_code == 200

    es_result = result.json()
    assert len(es_result['items']) == 12

    aggregates = es_result['stats']['sliceByDimension']
    assert len(aggregates) == 1

    type_aggregate = aggregates['@type']
    observations = type_aggregate['observation']
    assert len(observations) == 1
    assert observations[0]['totalItems'] == 12

    # after create - one hit
    holding_id = _create_holding(session)
    _trigger_elastic_refresh(session)

    result = session.get(ROOT_URL + search_endpoint,
                         params=query_params,
                         headers={'Accept': 'application/ld+json'})
    assert result.status_code == 200

    es_result = result.json()
    assert len(es_result['items']) == 13

    aggregates = es_result['stats']['sliceByDimension']
    assert len(aggregates) == 1

    type_aggregate = aggregates['@type']
    observations = type_aggregate['observation']
    assert len(observations) == 1
    assert observations[0]['totalItems'] == 13

    # after delete - no hits
    result = session.delete(holding_id)
    assert result.status_code == 204
    _trigger_elastic_refresh(session)

    result = session.get(holding_id)
    assert result.status_code == 404

    result = session.get(ROOT_URL + search_endpoint,
                         params=query_params,
                         headers={'Accept': 'application/ld+json'})
    assert result.status_code == 200

    es_result = result.json()
    assert len(es_result['items']) == 12

    aggregates = es_result['stats']['sliceByDimension']
    assert len(aggregates) == 1

    type_aggregate = aggregates['@type']
    observations = type_aggregate['observation']
    assert len(observations) == 1
    assert observations[0]['totalItems'] == 12


def is_type_instance(doc):
    return doc['@type'] == 'Instance'


def is_type_item(doc):
    return doc['@type'] == 'Item'


def _trigger_elastic_refresh(session):
    result = session.post(ES_REFRESH_URL)
    assert result.status_code == 200
