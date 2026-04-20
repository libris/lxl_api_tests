from conf_util import *

pytestmark = pytest.mark.dev

TYPE_WORK_FILTER={'filter': '"rdf:type":Work'}
DEFAULT_WORK_FILTER = {'defaultSiteFilters': [TYPE_WORK_FILTER]}
FIND_API = ROOT_URL + "/find"

def test_default_work_filter(session):
    query_params = {'_q': '', '_appConfig': json.dumps(DEFAULT_WORK_FILTER)}

    result = session.get(FIND_API,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert es_result['totalItems'] > 17000

def test_exists_embedded_single_vs_multiple_instances(session):
    query_params = {'_q': 'grisfesten', '_appConfig': json.dumps(DEFAULT_WORK_FILTER)}

    result = session.get(FIND_API,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    items = es_result['items']
    exists_work_with_multiple_instances = any([len(item['@reverse']['instanceOf']) > 1 for item in items])
    exists_work_with_single_instance = any([len(item['@reverse']['instanceOf']) == 1 for item in items])
    assert exists_work_with_multiple_instances and exists_work_with_single_instance

def test_search_with_configured_filter_aliases(session):
    query_params = {'_q': '', '_appConfig': json.dumps(DEFAULT_WORK_FILTER)}
    result = session.get(FIND_API,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    total_works = es_result['totalItems']

    def filtered_works(alias, filter):
        config = {'filterAliases': [{'alias': alias, 'filter': filter}],
                  'defaultSiteFilters': [TYPE_WORK_FILTER]}
        q_params = {'_q': alias,
                    '_appConfig': json.dumps(config)}
        res = session.get(FIND_API,
                          params=q_params)
        assert res.status_code == 200
        es_res = res.json()
        return es_res['totalItems']

    assert total_works > filtered_works('excludeEplikt',
                                         'NOT (bibliography:"sigel:EPLK" AND itemHeldBy:"sigel:APIS" AND reverseLinks.totalItemsByRelation.itemOf.instanceOf=1)')
    assert total_works == filtered_works('includeEplikt',
                                        'NOT excludeEplikt')
    assert total_works > filtered_works('excludePreliminary',
                                         'NOT encodingLevel:("marc:PartialPreliminaryLevel" OR "marc:PrepublicationLevel")')
    assert total_works == filtered_works('includePreliminary',
                                        'NOT excludePreliminary')
    assert total_works > filtered_works('existsImage',
                                         'image:*')
    # assert total_works > filtered_works('freeOnline',
    #                                      'instanceType:DigitalResource AND (usageAndAccessPolicy.label:gratis OR "associatedMedia.marc:publicNote":"fritt tillgänglig" OR usageAndAccessPolicy:("https://id.kb.se/policy/freely-available" OR "https://id.kb.se/policy/oa/gratis"))')

def test_search_my_libraries(session):
    query_params = {'_q': 'alias-myLibraries', '_alias-myLibraries': 'itemHeldByOrg:"sigel:org/KB"', '_appConfig': json.dumps(DEFAULT_WORK_FILTER)}
    result = session.get(FIND_API,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert es_result['totalItems'] > 300 and es_result['totalItems'] < 400

def test_search_instance_type(session):
    query_params = {'_q': 'instanceType:DigitalResource',
                    '_appConfig': json.dumps(DEFAULT_WORK_FILTER)}
    result = session.get(FIND_API,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert es_result['totalItems'] > 7000 and es_result['totalItems'] < 8000

def test_search_work_find_category(session):
    query_params = {'_q': 'workCategory:"saogf:Sk%C3%B6nlitteratur"',
                    '_appConfig': json.dumps(DEFAULT_WORK_FILTER)}
    result = session.get(FIND_API,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert es_result['totalItems'] > 300 and es_result['totalItems'] < 400

def test_search_work_identify_category(session):
    query_params = {'_q': 'workCategory:"saogf:Romaner"',
                    '_appConfig': json.dumps(DEFAULT_WORK_FILTER)}
    result = session.get(FIND_API,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert es_result['totalItems'] > 200 and es_result['totalItems'] < 300

def test_search_work_none_category(session):
    query_params = {'_q': 'workCategory:"saogf:Deckare"',
                    '_appConfig': json.dumps(DEFAULT_WORK_FILTER)}
    result = session.get(FIND_API,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert es_result['totalItems'] > 20 and es_result['totalItems'] < 30

def test_search_instance_category(session):
    query_params = {'_q': 'instanceCategory:"https://id.kb.se/term/saobf/Print"',
                    '_appConfig': json.dumps(DEFAULT_WORK_FILTER)}
    result = session.get(FIND_API,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert es_result['totalItems'] > 9000 and es_result['totalItems'] < 10000

def test_search_language(session):
    query_params = {'_q': 'language:"lang:swe"',
                    '_appConfig': json.dumps(DEFAULT_WORK_FILTER)}
    result = session.get(FIND_API,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert es_result['totalItems'] > 16000 and es_result['totalItems'] < 17000

def test_search_library(session):
    query_params = {'_q': 'itemHeldByOrg:"sigel:org/KB"',
                    '_appConfig': json.dumps(DEFAULT_WORK_FILTER)}
    result = session.get(FIND_API,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert es_result['totalItems'] > 300 and es_result['totalItems'] < 400

def test_search_year(session):
    query_params = {'_q': 'yearPublished:2014',
                    '_appConfig': json.dumps(DEFAULT_WORK_FILTER)}
    result = session.get(FIND_API,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert es_result['totalItems'] > 100 and es_result['totalItems'] < 200

def test_search_year_interval(session):
    query_params = {'_q': 'yearPublished:2000-2010',
                    '_appConfig': json.dumps(DEFAULT_WORK_FILTER)}
    result = session.get(FIND_API,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert es_result['totalItems'] > 2000 and es_result['totalItems'] < 4000

def test_search_contributor(session):
    query_params = {'_q': 'contributor:"libris:sq47c3sb51r8z7b%23it"',
                    '_appConfig': json.dumps(DEFAULT_WORK_FILTER)}
    result = session.get(FIND_API,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert es_result['totalItems'] > 100 and es_result['totalItems'] < 200

def test_search_subject(session):
    query_params = {'_q': 'subject:"sao:Arbetsmarknad"',
                    '_appConfig': json.dumps(DEFAULT_WORK_FILTER)}
    result = session.get(FIND_API,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert es_result['totalItems'] > 40 and es_result['totalItems'] < 60

def test_search_bibliography(session):
    query_params = {'_q': 'bibliography:"sigel:KVIN"',
                    '_appConfig': json.dumps(DEFAULT_WORK_FILTER)}
    result = session.get(FIND_API,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert es_result['totalItems'] > 100 and es_result['totalItems'] < 300

def test_search_work_type(session):
    query_params = {'_q': 'workType:Serial',
                    '_appConfig': json.dumps(DEFAULT_WORK_FILTER)}
    result = session.get(FIND_API,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert es_result['totalItems'] > 50 and es_result['totalItems'] < 200

def test_o_search_subject(session):
    app_config = {
        'defaultSiteFilters': [TYPE_WORK_FILTER],
        'relationFilters': [{'objectType': 'Concept', 'predicates': ['subject']}]
    }
    query_params = {'_o': 'https://id.kb.se/term/sao/Finansiering',
                    '_appConfig': json.dumps(app_config)}
    result = session.get(FIND_API,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert es_result['totalItems'] > 50
    assert es_result['stats']['_predicates'][0]['totalItems'] > 50

def test_o_search_instance_category(session):
    app_config = {
        'defaultSiteFilters': [TYPE_WORK_FILTER],
        'relationFilters': [{'objectType': 'Concept', 'predicates': ['librissearch:instanceCategory']}]
    }
    query_params = {'_o': 'https://id.kb.se/term/saobf/Print',
                    '_appConfig': json.dumps(app_config)}
    result = session.get(FIND_API,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert es_result['totalItems'] > 5000
    assert es_result['stats']['_predicates'][0]['totalItems'] > 5000

def test_o_search_work_category(session):
    app_config = {
        'defaultSiteFilters': [TYPE_WORK_FILTER],
        'relationFilters': [{'objectType': 'Concept', 'predicates': ['librissearch:workCategory']}]
    }
    query_params = {'_o': 'https://id.kb.se/term/saogf/Sk%C3%B6nlitteratur',
                    '_appConfig': json.dumps(app_config)}
    result = session.get(FIND_API,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert es_result['totalItems'] > 300
    assert es_result['stats']['_predicates'][0]['totalItems'] > 300

def test_o_p_search(session):
    query_params = {'_o': 'https://id.kb.se/term/sao/Finansiering',
                    '_p': 'fieldOfActivity',
                    '_appConfig': json.dumps(DEFAULT_WORK_FILTER)}
    result = session.get(FIND_API,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert es_result['totalItems'] > 0 and es_result['totalItems'] < 10

def test_r_search(session):
    query_params = {'_r': 'itemHeldBy:"sigel:S"',
                    '_appConfig': json.dumps(DEFAULT_WORK_FILTER)}
    result = session.get(FIND_API,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert es_result['totalItems'] > 300 and es_result['totalItems'] < 400

def test_q_r_search(session):
    query_params = {'_q': 'grisfesten',
                    '_r': 'itemHeldByOrg:"sigel:org/UUB"',
                    '_appConfig': json.dumps(DEFAULT_WORK_FILTER)}
    result = session.get(FIND_API,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert es_result['totalItems'] == 1

def test_like_search(session):
    query_params = {'_q': 'contributor:"libris:tr579gmc1g104f7#it"',
                    '_appConfig': json.dumps(DEFAULT_WORK_FILTER)}
    result = session.get(FIND_API,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    exact_total_items = es_result['totalItems']

    query_params = {'_q': 'contributor~"libris:tr579gmc1g104f7#it"',
                    '_appConfig': json.dumps(DEFAULT_WORK_FILTER)}
    result = session.get(FIND_API,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    like_total_items = es_result['totalItems']

    assert like_total_items > exact_total_items

def test_and_search(session):
    query_params = {'_q': 'language:"lang:nor" yearPublished:1989',
                    '_appConfig': json.dumps(DEFAULT_WORK_FILTER)}
    result = session.get(FIND_API,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert es_result['totalItems'] > 5 and es_result['totalItems'] < 10

def test_or_search(session):
    query_params = {'_q': 'language:"lang:nor" OR yearPublished:1989',
                    '_appConfig': json.dumps(DEFAULT_WORK_FILTER)}
    result = session.get(FIND_API,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert es_result['totalItems'] > 300 and es_result['totalItems'] < 400

def test_not_search(session):
    def total_items(q):
        query_params = {'_q': q,
                        '_appConfig': json.dumps(DEFAULT_WORK_FILTER)}
        result = session.get(FIND_API,
                             params=query_params)
        assert result.status_code == 200
        es_result = result.json()
        return es_result['totalItems']

    assert total_items('') - total_items('NOT language:"lang:nor"') == total_items('language:"lang:nor"')

def test_suggest(session):
    query_params = {'_q': 'grisf',
                    '_suggest': True,
                    'cursor': 5,
                    '_limit': 5,
                    '_appConfig': json.dumps(DEFAULT_WORK_FILTER)}
    result = session.get(FIND_API,
                         params=query_params)
    assert result.status_code == 200
    es_result = result.json()
    assert next((x for x in es_result['items'] if x['hasTitle'][0]['mainTitle'] == 'Grisfesten'), False)

def test_suggest_for_filter(session):
    query_params = {'_q': 'contributor:(astrid li)',
                    '_suggest': True,
                    'cursor': 21,
                    '_limit': 5,
                    '_appConfig': json.dumps(DEFAULT_WORK_FILTER)}
    result = session.get(FIND_API,
                         params=query_params)
    assert result.status_code == 200
    es_result = result.json()
    astrid_lindgren = next((x for x in es_result['items'] if x['@id'] == ROOT_URL + '/fcrtpljz1qp2bdv#it'), False)
    assert astrid_lindgren and astrid_lindgren['_qualifiers']

def test_get_search_mappings(session):
    query_params = {'_q': 'hej',
                    '_r': 'itemHeldBy:"sigel:S"',
                    '_mappingOnly': True,
                    '_appConfig': json.dumps(DEFAULT_WORK_FILTER)}
    result = session.get(FIND_API,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()

    q_mapping = next((x for x in es_result['search']['mapping'] if x['variable'] == '_q'), False)
    r_mapping = next((x for x in es_result['search']['mapping'] if x['variable'] == '_r'), False)
    default_site_filter_mapping = next((x for x in es_result['search']['mapping'] if x['variable'] == 'defaultSiteFilters'), False)

    assert q_mapping
    assert r_mapping
    assert default_site_filter_mapping

    assert q_mapping['property']['@id'] == 'https://id.kb.se/vocab/textQuery'
    assert q_mapping['equals'] == 'hej'
    assert q_mapping['up']['@id'] == '/find?_q=&_r=itemHeldBy:%22sigel:S%22'

    assert r_mapping['property']['@id'] == 'https://id.kb.se/ns/librissearch/itemHeldBy'
    assert r_mapping['equals']['@id'] == 'https://libris.kb.se/library/S'
    assert r_mapping['up']['@id'] == '/find?_q=hej&_r=' # TODO: Should not include empty _r?

    assert default_site_filter_mapping['property']['@id'] == 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type'
    assert default_site_filter_mapping['equals']['@id'] == 'https://id.kb.se/vocab/Work'

def test_get_stats(session):
    for type in ['Instance', 'Work']:
        statistics = {
            "sliceList": [
                {"dimensionChain": ["rdf:type"], "itemLimit": 100},
                {"dimensionChain": ["instanceType"], "itemLimit": 100},
                {"dimensionChain": ["findCategory"], "itemLimit": 20,
                 "slice": {"dimensionChain": ["identifyCategory"], "itemLimit": 50}
                 },
                {"dimensionChain": ["instanceCategory"], "itemLimit": 100},
                {"dimensionChain": ["language"], "itemLimit": 100, "connective": "OR"},
                {"dimensionChain": ["itemHeldByOrg"], "itemLimit": 1000, "connective": "OR", "countTopLevelDocs": True},
                {"dimensionChain": ["yearPublished"], "itemLimit": 500, "range": True},
                {"dimensionChain": ["contributor"], "itemLimit": 20},
                {"dimensionChain": ["subject"], "itemLimit": 100},
                {"dimensionChain": ["bibliography"], "itemLimit": 200},
                {"dimensionChain": ["workType"], "itemLimit": 100}
            ]
        }
        app_config = {
            'statistics': statistics,
        }
        query_params = {'_q': 'type:' + type,
                        '_appConfig': json.dumps(app_config)}
        result = session.get(FIND_API,
                             params=query_params)
        assert result.status_code == 200

        es_result = result.json()

        def find_observation(slice_by_dimension, property, value):
            slice = slice_by_dimension[property]
            assert slice
            return next((x for x in slice['observation'] if x['object']['@id'] == value), False)

        def assert_observation(observation, min_items):
            assert observation and observation['totalItems'] > min_items

        sbd = es_result['stats']['sliceByDimension']

        assert sbd

        physical_resource = find_observation(sbd, 'librissearch:instanceType', 'https://id.kb.se/vocab/PhysicalResource')
        assert_observation(physical_resource, 5000)

        facklitteratur = find_observation(sbd, 'librissearch:findCategory','https://id.kb.se/term/saogf/Facklitteratur')
        assert_observation(facklitteratur, 5000)

        offentligt_tryck = find_observation(facklitteratur['sliceByDimension'], 'librissearch:identifyCategory','https://id.kb.se/term/saogf/Offentligt%20tryck')
        assert_observation(offentligt_tryck, 5000)

        print = find_observation(sbd, 'librissearch:instanceCategory', 'https://id.kb.se/term/saobf/Print')
        assert_observation(print, 5000)

        language = find_observation(sbd, 'language', 'https://id.kb.se/language/swe')
        assert_observation(language, 10000)

        kb = find_observation(sbd, 'librissearch:itemHeldByOrg', 'https://libris.kb.se/library/org/KB')
        assert_observation(kb, 300)

        year_published_slice = sbd['librissearch:yearPublished']
        assert year_published_slice
        year_1997 = next((x for x in year_published_slice['observation'] if x['object'] == '1997'), False)
        assert_observation(year_1997, 500)
        assert year_published_slice['search'] == {
          "mapping": {
            "greaterThanOrEquals": "",
            "lessThanOrEquals": "",
            "variable": "yearPublished"
          },
          "template": f"/find?_q=type:{type}+%7B%3FyearPublished%7D"
        }

        lars_ahlstrom = find_observation(sbd, 'contributor', ROOT_URL + '/sq47c3sb51r8z7b#it')
        assert_observation(lars_ahlstrom, 100)

        finansiering = find_observation(sbd, 'subject', 'https://id.kb.se/term/sao/Finansiering')
        assert_observation(finansiering, 50)

        nb = find_observation(sbd, 'bibliography', 'https://libris.kb.se/library/NB')
        assert_observation(nb, 5000)

        monograph = find_observation(sbd, 'librissearch:workType', 'https://id.kb.se/vocab/Monograph')
        assert_observation(monograph, 10000)

