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
    query_params = {'_q': 'workCategory:"saogf:Seriella%20publikationer"',
                    '_appConfig': json.dumps(DEFAULT_WORK_FILTER)}
    result = session.get(FIND_API,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert es_result['totalItems'] > 80 and es_result['totalItems'] < 100

def test_search_work_find_category_2(session):
    query_params = {'_q': 'workCategory:(seriella publikationer)',
                    '_appConfig': json.dumps(DEFAULT_WORK_FILTER)}
    result = session.get(FIND_API,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert es_result['totalItems'] > 80 and es_result['totalItems'] < 100

def test_search_work_identify_category(session):
    query_params = {'_q': 'workCategory:"saogf:Romaner"',
                    '_appConfig': json.dumps(DEFAULT_WORK_FILTER)}
    result = session.get(FIND_API,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert es_result['totalItems'] > 200 and es_result['totalItems'] < 300

def test_search_work_identify_category_2(session):
    query_params = {'_q': 'workCategory:(romaner)',
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

def test_search_work_none_category_2(session):
    query_params = {'_q': 'workCategory:(deckare)',
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

def test_search_instance_category_2(session):
    query_params = {'_q': 'instanceCategory:(tryck)',
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

def test_search_instance_record_created(session):
    query_params = {'_q': 'instanceRecordCreated:1900-2100',
                    '_appConfig': json.dumps(DEFAULT_WORK_FILTER)}
    result = session.get(FIND_API,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    num_works = es_result['totalItems']
    # Should match all works
    assert num_works > 17000

    query_params = {'_q': 'type:Instance instanceRecordCreated:1900-2100',
                    '_appConfig': json.dumps(DEFAULT_WORK_FILTER)}
    result = session.get(FIND_API,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    num_instances = es_result['totalItems']
    # Should match all instances
    assert num_instances > 17000

    # Assume some instances to share the same linked work
    assert num_instances > num_works

def test_search_encoding_level(session):
    query_params = {'_q': 'encodingLevel:"marc:fullLevel"',
                    '_appConfig': json.dumps(DEFAULT_WORK_FILTER)}
    result = session.get(FIND_API,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert es_result['totalItems'] > 9000 and es_result['totalItems'] < 10000

def test_search_dewey(session):
    # classification[DdcClassfication].code + additionalClassificationDdc.code
    query_params = {'_q': 'dewey:610.73707155 dewey:615.8207155',
                    '_appConfig': json.dumps(DEFAULT_WORK_FILTER)}
    result = session.get(FIND_API,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert es_result['totalItems'] == 1 # Matching ID: q82bfms20cgvmrm

def test_search_title(session):
    # hasTitle + relationship.entity.hasTitle + translationOf.hasTitle
    query_params = {'_q': 'titel:(Nonchalans sjabb och dödliga fräknar) titel:(The quality of sprawl) title:(A working forest)',
                    '_appConfig': json.dumps(DEFAULT_WORK_FILTER)}
    result = session.get(FIND_API,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert es_result['totalItems'] == 1 # Matching ID: vc55czd6447wmv1

def test_search_isxn(session):
    # identifiedBy[ISBN].value + identifiedBy[ISSN].value + identifiedBy[ISMN].value
    query_params = {'_q': 'isxn:(9789100118969 OR 0002-6204 OR M004211915)',
                    '_appConfig': json.dumps(DEFAULT_WORK_FILTER)}
    result = session.get(FIND_API,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert es_result['totalItems'] == 3 # Matching IDs: j19pfzdcgngtf8dh, btmjhgbn240st8h, l4x9b1mx41nsqc5

def test_search_control_number(session):
    query_params = {'_q': 'controlNumber:(197467)',
                    '_appConfig': json.dumps(DEFAULT_WORK_FILTER)}
    result = session.get(FIND_API,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert es_result['totalItems'] == 1 # wd6r4jm75f0xvk7

def test_search_control_number_2(session):
   query_params = {'_q': 'controlNumber:(wd6r4jm75f0xvk7)',
                   '_appConfig': json.dumps(DEFAULT_WORK_FILTER)}
   result = session.get(FIND_API,
                        params=query_params)
   assert result.status_code == 200

   es_result = result.json()
   assert es_result['totalItems'] == 1 # wd6r4jm75f0xvk7

def test_search_identifier(session):
    # identifiedBy[ISBN].value + indirectlyIdentifiedBy[ISBN].value
    query_params = {'_q': 'identifier:(9138223325)',
                    '_appConfig': json.dumps(DEFAULT_WORK_FILTER)}
    result = session.get(FIND_API,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert es_result['totalItems'] == 2 # Matching IDs: 4ngg73bg5k4wk0b, 6phgbg8j1rm7v6d

def test_search_identifier_2(session):
    # identifiedBy[ISSN].value + marc:incorrectIssn
    query_params = {'_q': 'identifier:(0375-250X) ',
                    '_appConfig': json.dumps(DEFAULT_WORK_FILTER)}
    result = session.get(FIND_API,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert es_result['totalItems'] == 4 # Matching IDs: dxq5tnbq5qjc20k, n5ztm3v03xf1cv7, 1jb60g8c0wbsj5q, zg84xdm90nck7zf

def test_search_identifier_3(session):
    # identifiedBy[ISSN].value + marc:canceledIssn
    query_params = {'_q': 'identifier:(0020-7292)',
                    '_appConfig': json.dumps(DEFAULT_WORK_FILTER)}
    result = session.get(FIND_API,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert es_result['totalItems'] == 2 # Matching IDs: 5ng5cz7h50swx3m, gzrplcts5twr5xg

def test_search_identifier_4(session):
   # meta.controlNumber + meta.identifiedBy[LibrisIIINumber].value + "fnurgel" ID
   query_params = {'_q': 'identifier:(197467 9138021854 wd6r4jm75f0xvk7)',
                   '_appConfig': json.dumps(DEFAULT_WORK_FILTER)}
   result = session.get(FIND_API,
                        params=query_params)
   assert result.status_code == 200

   es_result = result.json()
   assert es_result['totalItems'] == 1 # Matching IDs: wd6r4jm75f0xvk7

def test_search_linked_shelfmark(session):
    query_params = {'_q': 'placering:(Sv2021)',
                    '_appConfig': json.dumps(DEFAULT_WORK_FILTER)}
    result = session.get(FIND_API,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert es_result['totalItems'] > 0

def test_search_item_shelf(session):
    # shelfMark.label + shelfLabel + physicalLocation
    query_params = {'_q': 'placering:(Informatik och media Falkheimer Kurs)',
                    '_appConfig': json.dumps(DEFAULT_WORK_FILTER)}
    result = session.get(FIND_API,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert es_result['totalItems'] == 1 # Matching ID: bvntnvqn4bwtdjm

def test_search_item_subject(session):
    query_params = {'_q': 'itemSubject:(C++)',
                    '_appConfig': json.dumps(DEFAULT_WORK_FILTER)}
    result = session.get(FIND_API,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert es_result['totalItems'] > 5 # Matching for example: 7qj91s6k2r7trj1

def test_search_item_statement(session):
    # hasNote.label
    query_params = {'_q': 'beståndsuppgift:(Orig:s titel: Elverdronningens riddere - Den fortryllede skjold)',
                    '_appConfig': json.dumps(DEFAULT_WORK_FILTER)}
    result = session.get(FIND_API,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert es_result['totalItems'] == 1 # Matching ID: 4nggzhjg0b6hlkk

def test_search_internal_item_note(session):
    # cataloguersNote
    query_params = {'_q': 'hasInternalItemNote:(nb2009mon)',
                    '_appConfig': json.dumps(DEFAULT_WORK_FILTER)}
    result = session.get(FIND_API,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert es_result['totalItems'] > 10 # Matching for example: j19pfz0cg2xl1f2v

def test_search_additional_item_information(session):
    # immediateAcquisition.marc:sourceOfAcquisition
    query_params = {'_q': 'hasAdditionalItemInformation:(Pliktex)',
                    '_appConfig': json.dumps(DEFAULT_WORK_FILTER)}
    result = session.get(FIND_API,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert es_result['totalItems'] > 20 # Matching for example: h08ndxddfg5v2pjf

def test_search_item_information(session):
    # hasNote.label + shelfMark.label + cataloguersNote
    query_params = {'_q': 'bestånd:(Tryckningar finns Sv2009 nb2009mon)',
                    '_appConfig': json.dumps(DEFAULT_WORK_FILTER)}
    result = session.get(FIND_API,
                         params=query_params)
    assert result.status_code == 200

    es_result = result.json()
    assert es_result['totalItems'] == 2 # Matching IDs: j19pfz0cg2xl1f2v, h1ttdg7t1zfr2mk

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

def test_suggest_for_contributor_filter(session):
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

def test_suggest_for_bibliography_filter(session):
    query_params = {'_q': 'bibliography:(nation)',
                    '_suggest': True,
                    'cursor': 20,
                    '_limit': 5,
                    '_appConfig': json.dumps(DEFAULT_WORK_FILTER)}
    result = session.get(FIND_API,
                         params=query_params)
    assert result.status_code == 200
    es_result = result.json()
    nationalbibliografin = next((x for x in es_result['items'] if x['@id'] == 'https://libris.kb.se/library/NB'), False)
    assert nationalbibliografin and nationalbibliografin['_qualifiers']

def test_get_search_mappings(session):
    query_params = {'_q': 'hej',
                    '_r': 'library:"sigel:S"',
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
    assert q_mapping['up']['@id'] == '/find?_q=&_r=library:%22sigel:S%22'

    assert r_mapping['property']['@id'] == 'https://id.kb.se/ns/librissearch/library'
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

        lars_ahlstrom = find_observation(sbd, 'librissearch:contributor', ROOT_URL + '/sq47c3sb51r8z7b#it')
        assert_observation(lars_ahlstrom, 100)

        finansiering = find_observation(sbd, 'subject', 'https://id.kb.se/term/sao/Finansiering')
        assert_observation(finansiering, 50)

        nb = find_observation(sbd, 'librissearch:bibliography', 'https://libris.kb.se/library/NB')
        assert_observation(nb, 5000)

        monograph = find_observation(sbd, 'librissearch:workType', 'https://id.kb.se/vocab/Monograph')
        assert_observation(monograph, 10000)

