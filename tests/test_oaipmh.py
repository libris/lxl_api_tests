from conf_util import *
import os
import requests
from datetime import datetime, timedelta

OAIPMH_URL = os.environ.get('LXLTESTING_OAIPMH_URL')


def test_get_record(session, load_holding):
    holding_id = load_holding()
    result = requests.session().get(OAIPMH_URL +
                                    '?verb=GetRecord&metadataPrefix=oai_dc&identifier=' +
                                    holding_id)

    assert result.status_code == 200
    assert '<identifier>{}</identifier>'.format(holding_id) in result.text


def test_holding_for_sigel_is_exported_on_bib_datestamp_updated(session, load_holding, load_bib_for_module):
    bib_id = load_bib_for_module()
    holding_id = load_holding(item_of=bib_id)

    from_time = (datetime.utcnow() - timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    until_time = (datetime.utcnow() + timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%SZ")

    result = requests.session().get(OAIPMH_URL +
                                    '?metadataPrefix=marcxml_expanded&set=hold:{}&verb=ListRecords&from={}&until={}'.format(
                                        '%s' % ACTIVE_SIGEL, from_time, until_time))

    assert '<identifier>{}</identifier>'.format(holding_id) in result.text
    assert '<setSpec>hold</setSpec>' in result.text


@pytest.mark.skip(reason="broken on DEV")
def test_bib_expanded_includes_auth_information(session):
    bibexample = ITEM_OF_DEFAULT
    bibexample_auth_record_id = 'wt79bh6f2j46dtr'

    result = requests.session().get(OAIPMH_URL +
                                    '?verb=GetRecord&metadataPrefix=marcxml&identifier={}'.format(bibexample))

    assert bibexample_auth_record_id not in result.text

    result = requests.session().get(OAIPMH_URL +
                                    '?verb=GetRecord&metadataPrefix=marcxml_expanded&identifier={}'.format(bibexample))

    assert bibexample_auth_record_id in result.text

@pytest.mark.skip(reason="broken on DEV")
def test_bib_includehold_includes_holdings(session):
    bibexample = ITEM_OF_DEFAULT
    bibexample_hold_id_h = 'mrxbsl2s5tn09x3'
    bibexample_hold_id_jon = 'nszctm3t34v26t3'
    bibexample_hold_id_krh = 'pt0dvn4v0c9803t'

    result = requests.session().get(OAIPMH_URL +
                                    '?verb=GetRecord&metadataPrefix=marcxml_includehold&identifier={}'.format(bibexample))

    assert bibexample_hold_id_h  in result.text
    assert bibexample_hold_id_jon  in result.text
    assert bibexample_hold_id_krh  in result.text


def test_identify_should_contain_repository_name(session):
    result = requests.session().get(OAIPMH_URL + '?verb=Identify')
    assert 'Libris XL' in result.text


def test_sets_should_contain_example_set_specifications(session):
    result = requests.session().get(OAIPMH_URL + '?verb=ListSets')
    assert '<setSpec>auth</setSpec>' in result.text
    assert '<setSpec>bib</setSpec>' in result.text
    assert '<setSpec>hold</setSpec>' in result.text
    assert '<setSpec>hold:S</setSpec>' in result.text
    assert '<setSpec>hold:KVIN</setSpec>' in result.text
    assert '<setSpec>hold:Gbg</setSpec>' in result.text
