from conf_util import *
import os
import re
import requests
from datetime import datetime, timedelta

pytestmark = pytest.mark.dev

OAIPMH_URL = os.environ.get('LXLTESTING_OAIPMH_URL')


def test_get_record(session, load_holding):
    holding_id = load_holding(session)
    result = requests.session().get(OAIPMH_URL +
                                    '?verb=GetRecord&metadataPrefix=oai_dc&identifier=' +
                                    holding_id)

    assert result.status_code == 200
    assert '<identifier>{}</identifier>'.format(holding_id) in result.text


def test_holding_for_sigel_is_exported_on_bib_datestamp_updated(session, load_holding, load_bib_for_module):
    bib_id = load_bib_for_module()
    holding_id = load_holding(session, item_of=bib_id)

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


def test_bib_includehold_includes_holdings(session, load_holding):
    bibexample = ITEM_OF_DEFAULT
    holding_id = load_holding(session, item_of=ITEM_OF_DEFAULT)

    result = requests.session().get(OAIPMH_URL +
                                    '?verb=GetRecord&metadataPrefix=marcxml_includehold&identifier={}'.format(bibexample))

    short_hold_id = holding_id.rsplit('/', 1)[0]
    assert short_hold_id in result.text


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


def _resumption_token(text):
    match = re.search(r'<resumptionToken[^>]*>([^<]+)</resumptionToken>', text)
    return match.group(1) if match else None


def test_listrecords_jsonld_returns_resumption_token(session):
    result = requests.session().get(OAIPMH_URL +
                                    '?verb=ListRecords&metadataPrefix=jsonld')

    assert result.status_code == 200
    assert '<ListRecords>' in result.text
    token = _resumption_token(result.text)
    assert token, 'expected a resumptionToken in a paged ListRecords response'


def test_listrecords_jsonld_resumption_token_returns_more_records(session):
    first = requests.session().get(OAIPMH_URL +
                                   '?verb=ListRecords&metadataPrefix=jsonld')
    token = _resumption_token(first.text)
    assert token, 'expected a resumptionToken in a paged ListRecords response'

    second = requests.session().get(OAIPMH_URL +
                                    '?verb=ListRecords&resumptionToken=' + token)

    assert second.status_code == 200
    assert '<ListRecords>' in second.text
    assert '<record>' in second.text

    first_identifiers = set(re.findall(r'<identifier>([^<]+)</identifier>', first.text))
    second_identifiers = set(re.findall(r'<identifier>([^<]+)</identifier>', second.text))
    assert second_identifiers, 'expected records in the resumed response'
    assert second_identifiers != first_identifiers, \
        'resumed response should return a different page of records'


def test_listrecords_jsonld_resumption_token_excludes_other_arguments(session):
    first = requests.session().get(OAIPMH_URL +
                                   '?verb=ListRecords&metadataPrefix=jsonld')
    token = _resumption_token(first.text)
    assert token, 'expected a resumptionToken in a paged ListRecords response'

    result = requests.session().get(
        OAIPMH_URL +
        '?verb=ListRecords&metadataPrefix=jsonld&resumptionToken=' + token)

    assert '<error code="badArgument">' in result.text


def test_listrecords_jsonld_invalid_resumption_token_returns_error(session):
    result = requests.session().get(
        OAIPMH_URL +
        '?verb=ListRecords&resumptionToken=this-is-not-a-valid-token')

    assert '<error code="badResumptionToken">' in result.text


def test_listrecords_jsonld_resumption_token_preserves_set(session):
    # The set (and other) parameters of the original request must be encoded in the
    # token, so that a resumed page stays scoped to the same selection.
    first = requests.session().get(OAIPMH_URL +
                                   '?verb=ListRecords&metadataPrefix=jsonld&set=bib')
    token = _resumption_token(first.text)
    assert token, 'expected a resumptionToken in a paged ListRecords response'

    second = requests.session().get(OAIPMH_URL +
                                    '?verb=ListRecords&resumptionToken=' + token)

    assert '<record>' in second.text
    assert '<setSpec>bib</setSpec>' in second.text
    # Records from other root sets should not leak into a bib-scoped harvest.
    assert '<setSpec>auth</setSpec>' not in second.text


def test_listrecords_jsonld_resumption_ends_with_empty_token(session):
    # A harvest that was started via a (non-empty) resumptionToken must, per the
    # OAI-PMH spec, terminate with an empty resumptionToken on the final page.
    # We pick a comparatively small set (hold:S) and walk the token chain to the end.
    result = requests.session().get(OAIPMH_URL +
                                    '?verb=ListRecords&metadataPrefix=jsonld&set=hold:S')
    token = _resumption_token(result.text)
    assert token, 'expected hold:S to span more than one page for this test to be meaningful'

    saw_empty_closing_token = False
    for _ in range(100):  # safety bound against an infinite loop
        result = requests.session().get(OAIPMH_URL +
                                        '?verb=ListRecords&resumptionToken=' + token)
        token = _resumption_token(result.text)
        if token is None:
            # Final page: a resumptionToken element is still present, but empty.
            assert '<resumptionToken' in result.text
            saw_empty_closing_token = True
            break

    assert saw_empty_closing_token, 'token chain did not terminate with an empty resumptionToken'


def test_listidentifiers_is_paged_and_omits_metadata(session):
    # ListIdentifiers shares the ListRecords code path but emits headers only.
    result = requests.session().get(OAIPMH_URL +
                                    '?verb=ListIdentifiers&metadataPrefix=jsonld&set=bib')

    assert result.status_code == 200
    assert '<ListIdentifiers>' in result.text
    assert '<identifier>' in result.text
    assert '<metadata>' not in result.text
    token = _resumption_token(result.text)
    assert token, 'expected a resumptionToken in a paged ListIdentifiers response'


def test_listidentifiers_resumption_token_returns_more_identifiers(session):
    first = requests.session().get(OAIPMH_URL +
                                   '?verb=ListIdentifiers&metadataPrefix=jsonld&set=bib')
    token = _resumption_token(first.text)
    assert token, 'expected a resumptionToken in a paged ListIdentifiers response'

    second = requests.session().get(OAIPMH_URL +
                                    '?verb=ListIdentifiers&resumptionToken=' + token)

    assert '<identifier>' in second.text
    first_identifiers = set(re.findall(r'<identifier>([^<]+)</identifier>', first.text))
    second_identifiers = set(re.findall(r'<identifier>([^<]+)</identifier>', second.text))
    assert second_identifiers and second_identifiers != first_identifiers


def test_bad_verb_returns_error(session):
    result = requests.session().get(OAIPMH_URL + '?verb=NoSuchVerb')
    assert '<error code="badVerb">' in result.text


def test_missing_verb_returns_bad_verb_error(session):
    result = requests.session().get(OAIPMH_URL + '?metadataPrefix=jsonld')
    assert '<error code="badVerb">' in result.text


def test_bad_verb_does_not_echo_request_parameters(session):
    # Per the OAI-PMH spec, the request element must not echo the supplied
    # parameters for badVerb/badArgument errors.
    result = requests.session().get(OAIPMH_URL + '?verb=NoSuchVerb&metadataPrefix=jsonld')
    assert '<error code="badVerb">' in result.text
    assert 'verb="NoSuchVerb"' not in result.text
    assert 'metadataPrefix="jsonld"' not in result.text


def test_listrecords_without_metadata_prefix_returns_bad_argument(session):
    result = requests.session().get(OAIPMH_URL + '?verb=ListRecords&set=bib')
    assert '<error code="badArgument">' in result.text


def test_getrecord_without_metadata_prefix_returns_bad_argument(session):
    result = requests.session().get(
        OAIPMH_URL + '?verb=GetRecord&identifier=' + ITEM_OF_DEFAULT)
    assert '<error code="badArgument">' in result.text


def test_getrecord_without_identifier_returns_bad_argument(session):
    result = requests.session().get(
        OAIPMH_URL + '?verb=GetRecord&metadataPrefix=jsonld')
    assert '<error code="badArgument">' in result.text


def test_unknown_parameter_returns_bad_argument(session):
    result = requests.session().get(
        OAIPMH_URL + '?verb=ListRecords&metadataPrefix=jsonld&bogusParam=x')
    assert '<error code="badArgument">' in result.text


def test_invalid_set_returns_bad_argument(session):
    result = requests.session().get(
        OAIPMH_URL + '?verb=ListRecords&metadataPrefix=jsonld&set=notaset')
    assert '<error code="badArgument">' in result.text


def test_invalid_subset_returns_bad_argument(session):
    # Sub-sets are only allowed for the hold and bib root sets (see SetSpec).
    result = requests.session().get(
        OAIPMH_URL + '?verb=ListRecords&metadataPrefix=jsonld&set=auth:sub')
    assert '<error code="badArgument">' in result.text


def test_malformed_date_returns_bad_argument(session):
    result = requests.session().get(
        OAIPMH_URL + '?verb=ListRecords&metadataPrefix=jsonld&from=notadate')
    assert '<error code="badArgument">' in result.text


def test_unsupported_format_returns_cannot_disseminate_format(session):
    result = requests.session().get(
        OAIPMH_URL +
        '?verb=GetRecord&metadataPrefix=bogus&identifier=' + ITEM_OF_DEFAULT)
    assert '<error code="cannotDisseminateFormat">' in result.text


def test_getrecord_unknown_identifier_returns_no_records_match(session):
    result = requests.session().get(
        OAIPMH_URL +
        '?verb=GetRecord&metadataPrefix=jsonld&identifier=http://example.org/doesnotexist')
    assert '<error code="noRecordsMatch">' in result.text


def test_listrecords_future_from_returns_no_records_match(session):
    result = requests.session().get(
        OAIPMH_URL +
        '?verb=ListRecords&metadataPrefix=jsonld&set=bib&from=2099-01-01T00:00:00Z')
    assert '<error code="noRecordsMatch">' in result.text


def test_listmetadataformats_lists_supported_formats(session):
    result = requests.session().get(OAIPMH_URL + '?verb=ListMetadataFormats')

    assert result.status_code == 200
    assert '<metadataPrefix>jsonld</metadataPrefix>' in result.text
    assert '<metadataPrefix>marcxml</metadataPrefix>' in result.text
    assert '<metadataPrefix>oai_dc</metadataPrefix>' in result.text


def test_listmetadataformats_unknown_identifier_returns_id_does_not_exist(session):
    result = requests.session().get(
        OAIPMH_URL +
        '?verb=ListMetadataFormats&identifier=http://example.org/doesnotexist')

    assert result.status_code == 200
    assert '<error code="idDoesNotExist">' in result.text
