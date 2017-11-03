from lxml import html
import json
import os
import pytest
import requests


ROOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
HOLD_FILE = os.path.join(ROOT_DIR, "resources", "hold.jsonld")
BIB_FILE = os.path.join(ROOT_DIR, "resources", "bib.jsonld")

DEFAULT_AUTH_URL = 'http://127.0.0.1:5000/login/authorize'
DEFAULT_LXL_LOGIN_URL = 'http://127.0.0.1:5000/login'
DEFAULT_ROOT_URL = 'http://127.0.0.1:5000'
DEFAULT_ES_REFRESH_URL = 'http://127.0.0.1:9200/_refresh'

AUTH_URL = os.environ.get('LXLTESTING_AUTH_URL', DEFAULT_AUTH_URL)
LXL_LOGIN_URL = os.environ.get('LXLTESTING_LXL_LOGIN_URL',
                               DEFAULT_LXL_LOGIN_URL)
ROOT_URL = os.environ.get('LXLTESTING_ROOT_URL', DEFAULT_ROOT_URL)
ES_REFRESH_URL = os.environ.get('LXLTESTING_ES_REFRESH_URL',
                                DEFAULT_ES_REFRESH_URL)

LOGIN_URL = os.environ.get('LXLTESTING_LOGIN_URL')
USERNAME = os.environ.get('LXLTESTING_USERNAME')
PASSWORD = os.environ.get('LXLTESTING_PASSWORD')

THING_ID_PLACEHOLDER = '_:TMPID#it'
ITEM_OF_TMP = 'ITEM_OF_TMP'
ITEM_OF_DEFAULT = 'http://libris.kb.se/resource/bib/816913'

@pytest.fixture(scope="module")
def session():
    session = requests.session()

    result = session.get(AUTH_URL)
    page = html.fromstring(result.text)
    csrf_token = _get_input_value(page, 'csrfmiddlewaretoken')
    next = list(set(page.xpath("//input[@name='next']/@value")))[0]

    payload = {
        'username': USERNAME,
        'password': PASSWORD,
        'next': next,
        'csrfmiddlewaretoken': csrf_token
    }

    result = session.post(LOGIN_URL, data=payload,
                          headers={'referer': result.url})

    assert result.status_code == 200

    page = html.fromstring(result.text)
    authorize_xpath = page.xpath("//form[@id='authorizationForm']")

    if authorize_xpath:
        csrf_token = _get_input_value(page, 'csrfmiddlewaretoken')
        redirect_uri = _get_input_value(page, 'redirect_uri')
        scope = _get_input_value(page, 'scope')
        client_id = _get_input_value(page, 'client_id')
        state = _get_input_value(page, 'state')
        response_type = _get_input_value(page, 'response_type')

        payload = {
            'csrfmiddlewaretoken': csrf_token,
            'redirect_uri': redirect_uri,
            'scope': scope,
            'client_id': client_id,
            'state': state,
            'response_type': response_type,
            'allow': 'true'
        }

        result = session.post(result.url, data=payload,
                              headers={'Referer': result.url})
        assert result.status_code == 200

    session.headers.update({'Accept': 'application/ld+json'})
    return session


def _get_input_value(page, name):
    xpath = page.xpath("//input[@name='{0}']/@value".format(name))
    return list(set(xpath))[0]


def _read_payload(filename):
    with open(filename, 'r') as f:
        payload = f.read()
        return payload


def create_holding(session, thing_id=None, item_of=None):
    return _do_post(session, HOLD_FILE, thing_id, item_of)


def create_bib(session, thing_id=None):
    return _do_post(session, BIB_FILE, thing_id, None)

fake_voyager_id = int(999999)
def _do_post(session, filename, thing_id, item_of):
    json_payload = _read_payload(filename)
    if thing_id:
        json_payload = json_payload.replace(THING_ID_PLACEHOLDER,
                                            thing_id)
    if item_of:
        json_payload = json_payload.replace(ITEM_OF_TMP,
                                            item_of)
    else:
        json_payload = json_payload.replace(ITEM_OF_TMP,
                                            ITEM_OF_DEFAULT)

    global fake_voyager_id
    fake_voyager_id = fake_voyager_id + 1
    json_payload = json_payload.replace("/bib/999999", "/bib/" + str(fake_voyager_id))
                
    result = session.post(ROOT_URL + "/",
                          data=json_payload,
                          headers={'Content-Type': 'application/ld+json'})
    assert result.status_code == 201
    location = result.headers['Location']
    return location


def update_holding(session, holding_id, payload, etag):
    # Update a simple field
    payload['@graph'][1]['inventoryLevel'] = 2
    json_payload = json.dumps(payload)

    result = session.put(holding_id,
                         data=json_payload,
                         headers={'Content-Type': 'application/ld+json',
                                  'If-Match': etag})
    return result
