from restapi import *
import sys

def test_update_and_delete_holding(session):
    holding_id = create_holding(session)

    result = session.get(holding_id)
    assert result.status_code == 200

    payload = result.json()
    etag = result.headers['ETag']

    result = update_holding(session, holding_id, payload, etag)
    assert result.status_code == 204

    _trigger_elastic_refresh(session)
    result = delete_post(session, holding_id)

    assert result.status_code == 204

    result = session.get(holding_id)
    assert result.status_code == 410

    result = delete_post(session, holding_id)
    assert result.status_code == 410

    _trigger_elastic_refresh(session)


def test_get_bib(session):
    bib_id = create_bib(session)
    
    expected_record_location = bib_id
    expected_content_location = "{0}/data.jsonld".format(bib_id)
    expected_document_header = "{0}".format(bib_id)
    expected_link_header = "<{0}>; rel=describedby".format(bib_id)

    result = session.get(bib_id)
    assert result.status_code == 200

    json_body = result.json()
    graph = json_body['@graph']
    record = graph[0]
    thing = graph[1]
    record_sameas = record['sameAs'][0]['@id']
    thing_id = thing['@id']
    thing_sameas = thing['sameAs'][0]['@id']
    expected_thing_location = thing_id

    # Record.sameAs
    result = session.get(ROOT_URL + "/" + record_sameas,
                         allow_redirects=False)
    assert result.status_code == 302

    location = result.headers['Location']
    assert location == expected_record_location

    # Thing.@id
    result = session.get(ROOT_URL + "/" + thing_id)
    assert result.status_code == 200

    # Thing.sameAs
    result = session.get(ROOT_URL + "/" + thing_sameas,
                         allow_redirects=False)
    assert result.status_code == 302

    location = result.headers['Location']
    assert location == expected_thing_location

    # Cleanup
    result = delete_post(session, bib_id)
    assert result.status_code == 204

    result = session.get(bib_id)
    assert result.status_code == 410

    result = session.get(ROOT_URL + "/" + record_sameas)
    assert result.status_code == 404

    result = session.get(ROOT_URL + "/" + thing_id)
    assert result.status_code == 410

    result = session.get(ROOT_URL + "/" + thing_sameas)
    assert result.status_code == 404

    _trigger_elastic_refresh(session)

    
# Create bib A, and holding B depending on A.
# Delete A (should be blocked due to dependency)
# Delete B (should be ok)
# Delete A (should now be ok as dependency is gone)
def test_delete_dependency(session):
    bib_id = create_bib(session)

    result = session.get(bib_id)
    assert result.status_code == 200

    expected_record_location = bib_id
    json_body = result.json()
    graph = json_body['@graph']
    record = graph[0]
    record_id = record['@id']
    thing = graph[1]
    thing_sameas = thing['sameAs'][0]['@id']
    thing_id = thing['@id']
    hold_id = create_holding(session, None, thing_id.decode("utf-8").encode("ascii","ignore"))

    # Delete A (should be blocked due to dependency)
    result = delete_post(session, ROOT_URL + "/" + bib_id,
                         allow_redirects=False)
    assert result.status_code == 403

    # Delete B (should be ok)
    result = delete_post(session, ROOT_URL + "/" + hold_id,
                         allow_redirects=False)
    assert result.status_code == 204

    # Delete A (should now be ok as dependency is gone)
    result = delete_post(session, ROOT_URL + "/" + bib_id,
                         allow_redirects=False)
    assert result.status_code == 204

    result = session.get(hold_id)
    assert result.status_code == 410

    result = session.get(bib_id)
    assert result.status_code == 410

    _trigger_elastic_refresh(session)


def test_delete_bib(session):
    bib_id = create_bib(session)

    result = session.get(bib_id)
    assert result.status_code == 200

    expected_record_location = bib_id
    json_body = result.json()
    graph = json_body['@graph']
    record = graph[0]
    thing = graph[1]
    record_sameas = record['sameAs'][0]['@id']
    thing_id = thing['@id']
    thing_sameas = thing['sameAs'][0]['@id']
    expected_thing_location = thing_id

    # Record.sameAs
    result = delete_post(session, ROOT_URL + "/" + record_sameas,
                         allow_redirects=False)
    assert result.status_code == 302

    location = result.headers['Location']
    assert location == expected_record_location

    # Thing.sameAs
    result = delete_post(session, ROOT_URL + "/" + thing_sameas,
                         allow_redirects=False)
    assert result.status_code == 302

    location = result.headers['Location']
    assert location == expected_thing_location

    # Thing.@id
    result = delete_post(session, ROOT_URL + "/" + thing_id,
                         allow_redirects=False)
    assert result.status_code == 204

    result = session.get(bib_id)
    assert result.status_code == 410

    _trigger_elastic_refresh(session)


def test_update_bib(session):
    bib_id = create_bib(session)

    result = session.get(bib_id)
    assert result.status_code == 200

    expected_record_location = bib_id
    etag = result.headers['ETag']
    session.headers.update({'If-Match': etag})
    session.headers.update({'Content-Type': 'application/ld+json'})

    json_body = result.json()
    graph = json_body['@graph']
    record = graph[0]
    thing = graph[1]
    record_sameas = record['sameAs'][0]['@id']
    thing_id = thing['@id']
    thing_sameas = thing['sameAs'][0]['@id']
    expected_thing_location = thing_id

    # Update value in document
    json_body['@graph'][0]['dimensions'] = '18 x 230 cm'
    payload = json.dumps(json_body)

    # Record.sameAs
    result = put_post(session, ROOT_URL + "/" + record_sameas,
                      data=payload, allow_redirects=False)
    assert result.status_code == 302

    location = result.headers['Location']
    assert location == expected_record_location

    # Thing.sameAs
    result = put_post(session, ROOT_URL + "/" + thing_sameas,
                      data=payload, allow_redirects=False)
    assert result.status_code == 302

    location = result.headers['Location']
    assert location == expected_thing_location

    # Thing.@id
    result = put_post(session, ROOT_URL + "/" + thing_id,
                      data=payload, allow_redirects=False)
    assert result.status_code == 204

    # cleanup
    result = delete_post(session, bib_id)
    assert result.status_code == 204

    result = session.get(bib_id)
    assert result.status_code == 410

    _trigger_elastic_refresh(session)


def test_get_bib_version(session):
    bib_id = create_bib(session)

    result = session.get(bib_id)
    assert result.status_code == 200

    result = session.get(bib_id + '?version=0')
    assert result.status_code == 200

    etag = result.headers['ETag']
    session.headers.update({'If-Match': etag})
    session.headers.update({'Content-Type': 'application/ld+json'})

    json_body = result.json()
    graph = json_body['@graph']
    thing = graph[1]
    thing_id = thing['@id']

    # Update value in document
    json_body['@graph'][1]['dimensions'] = '18 x 230 cm'
    payload = json.dumps(json_body)

    result = put_post(session, ROOT_URL + "/" + thing_id,
                      data=payload, allow_redirects=False)
    assert result.status_code == 204

    old_version = session.get(bib_id + '?version=0')
    assert old_version.status_code == 200

    old_json = old_version.json()
    assert old_json['@graph'][1]['dimensions'] != '18 x 230 cm'

    new_version = session.get(bib_id + '?version=1')
    assert new_version.status_code == 200

    new_json = new_version.json()
    assert new_json['@graph'][1]['dimensions'] == '18 x 230 cm'

    # cleanup
    result = delete_post(session, bib_id)
    assert result.status_code == 204

    result = session.get(bib_id)
    assert result.status_code == 410

    result = session.get(bib_id + '?version=0')
    assert result.status_code == 200

    result = session.get(bib_id + '?version=1')
    assert result.status_code == 200

    result = session.get(bib_id + '?version=2')
    assert result.status_code == 410

    _trigger_elastic_refresh(session)


def test_search(session):
    search_endpoint = "/find"
    limit = 1
    query_params = {'q': 'mumintrollet',
                    '_limit': limit}

    result = session.get(ROOT_URL + search_endpoint,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert es_result['totalItems'] > 0
    assert len(es_result['items']) == limit

    aggregations = es_result['stats']['sliceByDimension']
    assert len(aggregations['@type']['observation']) > 0

    search_details = es_result['search']
    search_mappings = search_details['mapping']
    assert len(search_mappings) > 0


def test_search_empty_sort_param(session):
    search_endpoint = "/find"
    limit = 1
    query_params = {'q': 'mumintrollet',
                    '_limit': limit,
                    '_sort': ''}

    result = session.get(ROOT_URL + search_endpoint,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert es_result['totalItems'] > 0
    assert len(es_result['items']) == limit

    aggregations = es_result['stats']['sliceByDimension']
    assert len(aggregations['@type']['observation']) > 0

    search_details = es_result['search']
    search_mappings = search_details['mapping']
    assert len(search_mappings) > 0


def test_search_aggregates(session):
    search_endpoint = "/find"
    limit = 0
    aggs_by_value = {"publication.year":
                     {"sort": "value", "sortOrder": "desc", "size": 2}}
    aggs_by_key = {"publication.year":
                   {"sort": "key", "sortOrder": "desc", "size": 2}}

    query_params = {'q': '*',
                    '_limit': limit,
                    '_statsrepr': json.dumps(aggs_by_value)}
    result = session.get(ROOT_URL + search_endpoint,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert len(es_result['items']) == limit

    aggregations = es_result['stats']['sliceByDimension']
    assert len(aggregations) == 1
    assert len(aggregations['publication.year']['observation']) == 2

    observations = aggregations['publication.year']['observation']
    items_first = observations[0]['totalItems']
    items_second = observations[1]['totalItems']
    assert items_first >= items_second

    query_params = {'q': '*',
                    '_limit': limit,
                    '_statsrepr': json.dumps(aggs_by_key)}
    result = session.get(ROOT_URL + search_endpoint,
                         params=query_params)

    es_result = result.json()
    assert len(es_result['items']) == limit

    aggregations = es_result['stats']['sliceByDimension']
    assert len(aggregations) == 1
    assert len(aggregations['publication.year']['observation']) == 2


def test_search_filtering(session):
    search_endpoint = "/find"
    limit = 2000
    only_instance = ['Manuscript']
    instance_and_type = ['Manuscript', 'MovingImage']
    bad_type = ['NonExistantType']

    # single type
    query_params = {'q': '*',
                    '@type': only_instance,
                    '_limit': limit}

    result = session.get(ROOT_URL + search_endpoint,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert all(is_type_instance(item) for item in es_result['items'])

    # instance and type
    query_params = {'q': '*',
                    '@type': instance_and_type,
                    '_limit': limit}

    result = session.get(ROOT_URL + search_endpoint,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert all(is_type_instance(item) or is_type_item(item)
               for item in es_result['items'])

    # bad type
    query_params = {'q': '*',
                    '@type': bad_type,
                    '_limit': limit}

    result = session.get(ROOT_URL + search_endpoint,
                         params=query_params)
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
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert len(es_result['items']) == limit0

    # limit=1
    query_params = {'q': '*',
                    '_limit': limit1}

    result = session.get(ROOT_URL + search_endpoint,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert len(es_result['items']) == limit1

    # limit=200
    query_params = {'q': '*',
                    '_limit': limit200}

    result = session.get(ROOT_URL + search_endpoint,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert len(es_result['items']) == limit200


def test_search_isbn(session):
    search_endpoint = "/find"

    # good query
    query_params = {'identifiedBy.value': '91-1-895301-8',
                    'identifiedBy.@type': 'ISBN'}

    result = session.get(ROOT_URL + search_endpoint,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert len(es_result['items']) == 1

    # bad query
    query_params = {'identifiedBy.value': 'not_a_valid_isbn',
                    'identifiedBy.@type': 'ISBN'}

    result = session.get(ROOT_URL + search_endpoint,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert len(es_result['items']) == 0


def test_search_indexing(session):
    search_endpoint = "/find"
    
    bib_id = create_bib(session)
    result = session.get(bib_id)
    json_body = result.json()
    graph = json_body['@graph']
    record = graph[0]
    thing = graph[1]
    thing_id = thing['@id']

    query_params = {'itemOf.@id': thing_id}

    # before create - no hits
    result = session.get(ROOT_URL + search_endpoint,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    num_items_before = len(es_result['items'])
    assert not 'stats' in es_result

    # after create - one hit
    holding_id = create_holding(session, None, thing_id.decode("utf-8").encode("ascii","ignore"))
    _trigger_elastic_refresh(session)

    result = session.get(ROOT_URL + search_endpoint,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert len(es_result['items']) == num_items_before + 1

    aggregates = es_result['stats']['sliceByDimension']
    assert len(aggregates) == 2

    type_aggregate = aggregates['@type']
    observations = type_aggregate['observation']
    assert len(observations) == 1
    assert observations[0]['totalItems'] == num_items_before + 1

    # after delete - no hits
    result = delete_post(session, holding_id)
    assert result.status_code == 204
    _trigger_elastic_refresh(session)

    result = session.get(holding_id)
    assert result.status_code == 410

    result = session.get(ROOT_URL + search_endpoint,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert len(es_result['items']) == num_items_before
    assert not 'stats' in es_result

    # cleanup
    result = delete_post(session, bib_id)
    assert result.status_code == 204

    result = session.get(bib_id)
    assert result.status_code == 410


def test_search_cannot_use_rev_and_q(session):
    search_endpoint = "/find"
    query_params = {'q': 'mumintrollet',
                    '_rev': 'id'}

    result = session.get(ROOT_URL + search_endpoint,
                         params=query_params)
    assert result.status_code == 400


def test_search_rev(session):
    rev_id = 'https://id.kb.se/language/swe'

    def get_items(lens):
        limit = 100

        search_endpoint = "/find"
        query_params = {
            '_rev': rev_id,
            '_limit': limit,
            '_lens': lens
        }

        result = session.get(ROOT_URL + search_endpoint,
                             params=query_params)

        assert result.status_code == 200

        json_body = result.json()
        items = json_body['items']

        assert json_body['totalItems'] > 400
        assert json_body['itemsPerPage'] == limit
        assert len(items) == limit
        assert "_lens=%s" % lens in json_body['@id']

        return items

    card_only = ['https://id.kb.se/term/rda/Volume',
                 'https://id.kb.se/term/rda/Unmediated']

    items = get_items('cards')
    assert all([has_reference(item, rev_id) for item in items])
    assert any([has_reference(item, c) for item in items for c in card_only])

    items = get_items('chips')
    assert all([has_reference(item, rev_id) for item in items])
    assert all([not has_reference(item, c) for item in items for c in card_only])


def test_search_rev_default_lens(session):
    search_endpoint = "/find"
    query_params = {
        '_rev': 'abc',
    }

    result = session.get(ROOT_URL + search_endpoint,
                         params=query_params)

    assert "_lens=cards" in result.json()['@id']


@pytest.mark.parametrize("limit", [30, 20])
def test_search_rev_navigation(limit, session):
    def fetch(url):
        result = session.get(ROOT_URL + url)
        return result.json()

    def next(body):
        return fetch(body['next']['@id'])

    def prev(body):
        return fetch(body['previous']['@id'])

    query = '/find?_rev=https://id.kb.se/language/swe&_limit=%s'
    first = fetch(query % limit)
    total = first['totalItems']
    all_items = fetch(query % total)['items']

    assert total > limit
    assert first['@id'] == first['first']['@id']
    assert first['itemsPerPage'] == limit

    num_steps = total / limit
    num_steps = num_steps -1 if total % limit == 0 else num_steps

    # forward to last
    offset = 0
    page = first
    items = page['items']
    for i in range(num_steps):
        page = next(page)
        items = items + page['items']
        offset = offset + limit
        assert page['itemOffset'] == offset
        assert page['itemsPerPage'] == limit
        assert first['last'] == page['last']
        assert first['first'] == page['first']

    assert page['@id'] == page['last']['@id']
    assert items == all_items

    # backward to first
    items = page['items']
    for i in range(num_steps):
        page = prev(page)
        items = page['items'] + items

    assert page == first
    assert items == all_items


def has_reference(x, ref, key=None):
    if isinstance(x, dict):
        return any([has_reference(x[key], ref, key=key) for key in x])
    elif isinstance(x, list):
        return any([has_reference(val, ref) for val in x])
    else:
        return key == "@id" and x == ref


def _assert_link_header(link_header, expected):
    link_headers = link_header.split(',')
    assert expected in link_headers


def is_type_instance(doc):
    return doc['@type'] == 'Instance'


def is_type_item(doc):
    return doc['@type'] == 'Item'


def _trigger_elastic_refresh(session):
    result = session.post(ES_REFRESH_URL)
    assert result.status_code == 200
