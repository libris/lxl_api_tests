from restapi import *
import os

OAIPMH_URL = os.environ.get('LXLTESTING_OAIPMH_URL')

import requests

def test_get_record(session):
    holding_id = create_holding(session)

    result = requests.session().get(OAIPMH_URL +
                                  '?verb=GetRecord&metadataPrefix=oai_dc&identifier=' +
                                  holding_id)
    assert '<record>' in result.text
    assert result.status_code == 200

    result = delete_post(session, holding_id)
    assert result.status_code == 204
