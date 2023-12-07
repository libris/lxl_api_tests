from conf_util import *
import re

pytestmark = pytest.mark.dev

def test_update_and_delete_holding(session, load_holding):
    holding_id = load_holding(session)

    result = session.get(holding_id, params={"embellished": "false"})
    assert result.status_code == 200

    payload = result.json()
    etag = result.headers['ETag']

    result = update_holding(session, holding_id, payload, etag)
    assert result.status_code == 204

    trigger_elastic_refresh(session)
    result = delete_record(session, holding_id)

    assert result.status_code == 204

    result = session.get(holding_id)
    assert result.status_code == 410

    result = delete_record(session, holding_id)
    assert result.status_code == 410

    trigger_elastic_refresh(session)


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
    thing_sameas = thing['sameAs'][0]['@id'].replace('http://libris.kb.se', ROOT_URL)
    expected_thing_location = thing_id

    # Record.sameAs
    result = session.get(API_URL + "/" + record_sameas,
                         allow_redirects=False)
    assert result.status_code == 302

    location = result.headers['Location']
    assert location == expected_record_location

    # Thing.@id
    result = session.get(thing_id)
    assert result.status_code == 200

    # Thing.sameAs
    result = session.get(thing_sameas,
                         allow_redirects=False)
    assert result.status_code == 302

    location = result.headers['Location']
    assert location == expected_thing_location

    # Cleanup
    result = delete_record(session, bib_id)
    assert result.status_code == 204

    result = session.get(bib_id)
    assert result.status_code == 410

    result = session.get(API_URL + "/" + record_sameas)
    assert result.status_code == 404

    result = session.get(thing_id)
    assert result.status_code == 410

    result = session.get(thing_sameas)
    assert result.status_code == 404

    trigger_elastic_refresh(session)


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
    thing_sameas = thing['sameAs'][0]['@id'].replace('http://libris.kb.se', ROOT_URL)
    thing_id = thing['@id']
    hold_id = create_holding(session, None, thing_id)

    # Delete A (should be blocked due to dependency)
    result = delete_record(session, bib_id,
                           allow_redirects=False)
    assert result.status_code == 403

    # Delete B (should be ok)
    result = delete_record(session, hold_id,
                           allow_redirects=False)
    assert result.status_code == 204

    # Delete A (should now be ok as dependency is gone)
    result = delete_record(session, bib_id,
                           allow_redirects=False)
    assert result.status_code == 204

    result = session.get(hold_id)
    assert result.status_code == 410

    result = session.get(bib_id)
    assert result.status_code == 410

    trigger_elastic_refresh(session)


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
    thing_sameas = thing['sameAs'][0]['@id'].replace('http://libris.kb.se', ROOT_URL)
    expected_thing_location = thing_id

    # Record.sameAs
    result = delete_record(session, API_URL + "/" + record_sameas,
                           allow_redirects=False)
    assert result.status_code == 302

    location = result.headers['Location']
    assert location == expected_record_location

    # Thing.sameAs
    result = delete_record(session, thing_sameas,
                           allow_redirects=False)
    assert result.status_code == 302

    location = result.headers['Location']
    assert location == expected_thing_location

    # Thing.@id
    result = delete_record(session, thing_id,
                           allow_redirects=False)
    assert result.status_code == 204

    result = session.get(bib_id)
    assert result.status_code == 410

    trigger_elastic_refresh(session)


def test_update_bib(session):
    bib_id = create_bib(session)

    result = session.get(bib_id, params={"embellished": "false"})
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
    thing_sameas = thing['sameAs'][0]['@id'].replace('http://libris.kb.se', ROOT_URL)
    expected_thing_location = thing_id

    # Update value in document
    json_body['@graph'][0]['dimensions'] = '18 x 230 cm'
    payload = json.dumps(json_body)

    # Record.sameAs
    result = put_record(session, API_URL + "/" + record_sameas,
                        data=payload, allow_redirects=False)
    assert result.status_code == 302

    location = result.headers['Location']
    assert location == expected_record_location

    # Thing.sameAs
    result = put_record(session, thing_sameas,
                        data=payload, allow_redirects=False)
    assert result.status_code == 302

    location = result.headers['Location']
    assert location == expected_thing_location

    # Thing.@id
    result = put_record(session, thing_id,
                        data=payload, allow_redirects=False)
    assert result.status_code == 204

    # cleanup
    result = delete_record(session, bib_id)
    assert result.status_code == 204

    result = session.get(bib_id)
    assert result.status_code == 410

    trigger_elastic_refresh(session)


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

    result = put_record(session, thing_id,
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
    result = delete_record(session, bib_id)
    assert result.status_code == 204

    result = session.get(bib_id)
    assert result.status_code == 410

    result = session.get(bib_id + '?version=0')
    assert result.status_code == 200

    result = session.get(bib_id + '?version=1')
    assert result.status_code == 200

    result = session.get(bib_id + '?version=2')
    assert result.status_code == 410

    trigger_elastic_refresh(session)


@pytest.mark.parametrize('view', ['/data'])
@pytest.mark.parametrize('suffix', ['', '.jsonld', '.json'])
@pytest.mark.parametrize('framed', [True, False])
@pytest.mark.parametrize('embellished', [True, False])
def test_get_view_with_parameters(session, view, suffix, framed, embellished):
    get_with_parameters(session, view + suffix, framed, embellished)


@pytest.mark.parametrize('framed', [True, False])
@pytest.mark.parametrize('embellished', [True, False])
def test_get_resource_with_parameters(session, framed, embellished):
    get_with_parameters(session, '', framed, embellished)


def get_with_parameters(session, view, framed, embellished):
    def is_framed(json):
        if '@id' not in json and '@graph' not in json:
            raise Exception('could not parse %s ' % json)
        return '@id' in json

    def is_embellished(json):
        if is_framed(json):
            return len(json['mainEntity']['illustrativeContent']) > 1
        else:
            return len(json['@graph']) > 3

    bib_id = find_id(session, '9789187745317+nya+konditionstest+cykel')
    url = API_URL + '/' + bib_id + view

    query = '?framed=%s&embellished=%s' % (framed, embellished)

    result = session.get(url + query)

    assert result.status_code == 200
    json = result.json()
    assert is_framed(json) == framed
    assert is_embellished(json) == embellished


@pytest.mark.parametrize('view', ['', '/data', '/data.json', '/data.jsonld'])
@pytest.mark.parametrize('lens', [None, 'chip', 'card'])
def test_get_with_lens(session, view, lens):
    def check_lens(json):
        if 'controlNumber' in json:
            return None
        if 'hasDimensions' in json:
            return 'card'
        if 'hasTitle' in json:
            return 'chip'
        raise Exception('could not identify lens')

    bib_id = find_id(session, '9789187745317+nya+konditionstest+cykel')
    url = API_URL + '/' + bib_id + view

    if lens:
        url = url + '?lens=' + lens
    else:
        url = url + '?framed=true'

    result = session.get(url)

    assert result.status_code == 200
    json = result.json()
    assert check_lens(json) == lens


cached_ids = {}
def find_id(session, q):
    if q in cached_ids:
        return cached_ids[q]

    url = ROOT_URL + '/find?q=' + q

    result = session.get(url)
    assert result.status_code == 200
    json = result.json()
    assert len(json['items']) == 1

    the_id = json['items'][0]['@id']
    the_id = re.sub('#.*', '', the_id)
    cached_ids[q] = the_id

    return the_id


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
    single_type = ['Manuscript']
    many_types = ['Manuscript', 'Map', 'VideoRecording']
    bad_type = ['NonExistantType']

    # single type
    query_params = {'q': '*',
                    '@type': single_type,
                    '_limit': limit}

    result = session.get(ROOT_URL + search_endpoint,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert(len(es_result['items']) != 0)
    assert all(item['@type'] == single_type[0] for item in es_result['items'])

    # many types
    query_params = {'q': '*',
                    '@type': many_types,
                    '_limit': limit}

    result = session.get(ROOT_URL + search_endpoint,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert(len(es_result['items']) != 0)
    assert all(item['@type'] in many_types
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


def test_search_with_or_count(session):
    # Given
    search_endpoint = "/find"
    limit = 2000

    query_params_s = {'q': '*',
                    '@type': ['SoundRecording'],
                    '_limit': limit}
    query_params_v = {'q': '*',
                    '@type': ['VideoRecording'],
                    '_limit': limit}
    query_params_sv = {'q': '*',
                    '@type': ['SoundRecording', 'VideoRecording'],
                    '_limit': limit}

    # When
    result_s = session.get(ROOT_URL + search_endpoint,
                         params=query_params_s)
    result_v = session.get(ROOT_URL + search_endpoint,
                           params=query_params_v)
    result_sv = session.get(ROOT_URL + search_endpoint,
                           params=query_params_sv)

    # Then
    assert result_s.status_code == 200
    assert result_v.status_code == 200
    assert result_sv.status_code == 200

    es_result_s = result_s.json()
    es_result_v = result_v.json()
    es_result_sv = result_sv.json()

    assert (len(es_result_s['items']) != 0)
    assert (len(es_result_v['items']) != 0)
    assert (len(es_result_sv['items']) != 0)

    assert (len(es_result_s['items']) + len(es_result_v['items']) == len(es_result_sv['items']) )

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


@pytest.mark.parametrize('bib_file, expected', [(BIB_FILE_ISBN10, 9789172530997),
                                                (BIB_FILE_ISBN13, 9172530995)])
def test_isbn_10_or_13_should_index_corresponding_form(session, bib_file, expected, load_bib):
    # Given
    load_bib(bib_file)

    # When
    query_params = {'identifiedBy.value': expected,
                    'identifiedBy.@type': 'ISBN'}
    search_endpoint = "/find"
    result = session.get(ROOT_URL + search_endpoint, params=query_params)
    assert result.status_code == 200

    # Then:
    es_result = result.json()
    assert len(es_result['items']) == 1


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
    holding_id = create_holding(session, None, thing_id)
    trigger_elastic_refresh(session)

    result = session.get(ROOT_URL + search_endpoint,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert len(es_result['items']) == num_items_before + 1

    aggregates = es_result['stats']['sliceByDimension']
    assert len(aggregates) == 1

    type_aggregate = aggregates['@type']
    observations = type_aggregate['observation']
    assert len(observations) == 1
    assert observations[0]['totalItems'] == num_items_before + 1

    # after delete - no hits
    result = delete_record(session, holding_id)
    assert result.status_code == 204
    trigger_elastic_refresh(session)

    result = session.get(holding_id)
    assert result.status_code == 410

    result = session.get(ROOT_URL + search_endpoint,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert len(es_result['items']) == num_items_before
    assert not 'stats' in es_result

    # cleanup
    result = delete_record(session, bib_id)
    assert result.status_code == 204

    result = session.get(bib_id)
    assert result.status_code == 410


def test_search_date(session, load_bib):
    import datetime

    def create(generationDate, pubYear, edition):
        load_bib(resource('bib_date.jsonld'), {'_:TMP_DATE': generationDate,
                                               '_:TMP_EDITION': edition,
                                               '_:TMP_YEAR': pubYear})

    def search(params):
        query_params = {'hasTitle.mainTitle': 'DATE_TEST_TITLE',
                        '_sort': 'meta.generationDate'}
        query_params.update(params)
        result = session.get(ROOT_URL + '/find', params=query_params)
        assert result.status_code == 200
        return [i['editionStatement'] for i in result.json()['items']]

    # Given
    # meta.generationDate, publication.year, editionStatement
    create('1983-12-07T11:12:00Z', '1968', 'A') # W49
    create('1990-01-02T10:10:10Z', '1971', 'B') # W01
    create('1992-01-02T10:10:10Z', '1975', 'C') # W01
    create('1995-10-10T09:09:09Z', '1980', 'D') # W41
    trigger_elastic_refresh(session)

    # Then:

    # Valid date formats
    # (one hour offset UTC vs Europe/Stockholm)
    assert search({'matches-meta.generationDate': '1983'}) == ['A']
    assert search({'matches-meta.generationDate': '1983-12'}) == ['A']
    assert search({'matches-meta.generationDate': '1983-12-07'}) == ['A']
    assert search({'matches-meta.generationDate': '1983-12-07T12'}) == ['A']
    assert search({'matches-meta.generationDate': '1983-12-07T12:12'}) == ['A']
    assert search({'matches-meta.generationDate': '1983-12-07T12:12:00'}) == ['A']
    assert search({'matches-meta.generationDate': '1983-W49'}) == ['A']

    # Inclusive/exclusive
    assert search({'min-meta.generationDate': '1983-12-07',
                   'max-meta.generationDate': '1995-10-10'}) == [
                       'A', 'B', 'C', 'D']
    assert search({'minEx-meta.generationDate': '1983-12-07',
                   'maxEx-meta.generationDate': '1995-10-10'}) == [
                       'B', 'C']
    assert search({'min-meta.generationDate': '1995-W41',
                   'max-meta.generationDate': '1995-W42'}) == ['D']
    assert search({'minEx-meta.generationDate': '1995-W41',
                   'max-meta.generationDate': '1995-W42'}) == []

    # Multiple fields - AND
    year_now = datetime.datetime.now().year
    assert search({'matches-meta.generationDate': '1983',
                   'matches-meta.created': year_now}) == ['A']

    assert search({'matches-meta.generationDate': '1983',
                   'matches-meta.created': '2000'}) == []

    # Same field, multiple ranges - OR
    assert search({'matches-meta.generationDate': ['1990-W01', '1992-W01']}) == ['B', 'C']
    assert search({'matches-meta.generationDate': '1990-W01, 1992-W01'}) == ['B', 'C']
    assert search({'matches-meta.generationDate': ['1983', '1990,1992', '1995']}) == [
        'A', 'B', 'C', 'D']
    assert search({'min-meta.generationDate': ['1982', '1989'],
                   'max-meta.generationDate': ['1984', '1991']}) == ['A', 'B']

    # Works on numeric fields, e.g. publication year
    assert search({'min-publication.year': '1970',
                   'maxEx-publication.year': '1980'}) == ['B', 'C']


def test_search_date_invalid(session, load_bib):
    def search(params):
        result = session.get(ROOT_URL + '/find', params=params)
        assert result.status_code == 400

    # bad date format
    search({'matches-meta.created': '12345'})
    search({'matches-meta.created': '2000-01-35'})

    # mixing week and other format
    search({'min-meta.created': '2000', 'max-meta.created': '2001-W05'})
    search({'max-meta.created': '2000-05-05', 'min-meta.created': '2001-W05'})


def test_search_o(session):
    o_id = 'https://id.kb.se/language/ger'

    def get_items(lens):
        limit = 50

        search_endpoint = "/find"
        query_params = {
            'o': o_id,
            '_limit': limit,
            '_lens': lens
        }

        result = session.get(ROOT_URL + search_endpoint,
                             params=query_params)

        assert result.status_code == 200

        json_body = result.json()
        items = json_body['items']

        assert json_body['totalItems'] > 45
        assert json_body['itemsPerPage'] == limit
        assert len(items) > 0 # TODO: what is correct? can be less than limit
        assert "_lens=%s" % lens in json_body['@id']

        return items

    card_only = ['https://id.kb.se/term/rda/Volume',
                 'https://id.kb.se/term/rda/Unmediated']

    items = get_items('cards')
    assert all([has_reference(item, o_id) for item in items])
    assert any([has_reference(item, c) for item in items for c in card_only])

    items = get_items('chips')
    assert all([has_reference(item, o_id) for item in items])
    assert all([not has_reference(item, c) for item in items for c in card_only])


@pytest.mark.skip(reason="investigate why broken")
@pytest.mark.parametrize("limit", [30, 20])
def test_search_o_navigation(limit, session):
    def fetch(url):
        result = session.get(ROOT_URL + url)
        return result.json()

    def next(body):
        return fetch(body['next']['@id'])

    def prev(body):
        return fetch(body['previous']['@id'])

    query = '/find?o=https://id.kb.se/language/ger&_limit=%s'
    first = fetch(query % limit)
    total = first['totalItems']
    all_items = fetch(query % total)['items']

    assert total > limit
    assert first['@id'] == first['first']['@id']
    assert first['itemsPerPage'] == limit

    num_steps = total // limit
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


def test_search_or_prefix(session):
    # Given
    search_endpoint = "/find"
    limit = 100
    tove_jansson = ROOT_URL + "/wt79bh6f2j46dtr#it"
    title = "Mumintrollet"

    query_params_a = {
        'instanceOf.contribution.agent.@id': tove_jansson,
        '_limit': limit
    }
    query_params_b = {
        'hasTitle.mainTitle': title,
        '_limit': limit
    }
    query_params_a_or_b = {
        'or-instanceOf.contribution.agent.@id': tove_jansson,
        'or-hasTitle.mainTitle': title,
        '_limit': limit
    }

    # When
    result_a = session.get(ROOT_URL + search_endpoint,
                         params=query_params_a)

    result_b = session.get(ROOT_URL + search_endpoint,
                         params=query_params_b)

    result_a_or_b = session.get(ROOT_URL + search_endpoint,
                         params=query_params_a_or_b)

    # Then
    assert result_a.status_code == 200
    assert result_b.status_code == 200
    assert result_a_or_b.status_code == 200

    es_result_a = result_a.json()
    es_result_b = result_b.json()
    es_result_a_or_b = result_a_or_b.json()

    assert (len(es_result_a['items']) != 0)
    assert (len(es_result_b['items']) != 0)
    assert (len(es_result_a_or_b['items']) != 0)

    deduplicated_a_and_b = set(map(tuple, es_result_a['items'] + es_result_b['items']))

    assert (len(deduplicated_a_and_b) == len(es_result_a_or_b['items']))


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


def _trigger_elastic_refresh(session):
    result = session.post(ES_REFRESH_URL, verify=False, auth=(ES_USER, ES_PASSWORD))
    assert result.status_code == 200
