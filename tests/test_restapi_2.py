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
    assert total_works > filtered_works('freeOnline',
                                         'instanceType:DigitalResource AND (usageAndAccessPolicy.label:gratis OR "associatedMedia.marc:publicNote":"fritt tillgänglig" OR usageAndAccessPolicy:("https://id.kb.se/policy/freely-available" OR "https://id.kb.se/policy/oa/gratis"))')

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


