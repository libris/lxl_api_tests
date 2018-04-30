from lxml import html
from oauthlib.oauth2 import MobileApplicationClient
from requests_oauthlib import OAuth2Session
from urlparse import urlparse
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
OAUTH_CLIENT_ID = os.environ.get('LXLTESTING_OAUTH_CLIENT_ID')
OAUTH_SCOPES = ['read', 'write']

THING_ID_PLACEHOLDER = '_:TMPID#it'
ITEM_OF_TMP = 'ITEM_OF_TMP'
ITEM_OF_DEFAULT = 'http://libris.kb.se/resource/bib/816913'
XL_ACTIVE_SIGEL_HEADER = 'XL-Active-Sigel'
ACTIVE_SIGEL = 'Utb2'


@pytest.fixture(scope="module")
def session():
    session = requests.session()
    oauth = OAuth2Session(
        client=MobileApplicationClient(client_id=OAUTH_CLIENT_ID),
        scope=OAUTH_SCOPES)
    authorization_url, state = oauth.authorization_url(AUTH_URL)

    result = session.get(authorization_url)
    page = html.fromstring(result.text)
    csrf_token = _get_input_value(page, 'csrf_token')
    next = list(set(page.xpath("//input[@name='next_redirect']/@value")))[0]

    payload = {
        'username': USERNAME,
        'password': PASSWORD,
        'next_redirect': next,
        'csrf_token': csrf_token
    }

    result = session.post(LOGIN_URL, data=payload,
                          headers={'referer': result.url})

    assert result.status_code == 200

    page = html.fromstring(result.text)
    authorize_xpath = page.xpath("//form[@id='authorizeForm']")

    if authorize_xpath:
        csrf_token = _get_input_value(page, 'csrf_token')
        scope = _get_input_value(page, 'scope')

        payload = {
            'csrf_token': csrf_token,
            'scope': scope,
            'confirm': 'y'
        }

        result = session.post(result.url, data=payload,
                              headers={'Referer': result.url})
        token = _get_token_from_url(result.url)
        session.headers.update({'Authorization': 'Bearer {}'.format(token)})
        assert result.status_code == 200

    session.headers.update({'Accept': 'application/ld+json'})
    return session


def _get_input_value(page, name):
    xpath = page.xpath("//input[@name='{0}']/@value".format(name))
    return list(set(xpath))[0]


def _get_token_from_url(url):
    params = _get_params_from_url_fragment(url)
    return params['access_token']


def _get_params_from_url_fragment(url):
    parsed_url = urlparse(url)
    fragment = parsed_url.fragment
    params = {}
    for pair in fragment.split('&'):
        k, v = pair.split('=')
        params[k] = v
    return params


def _read_payload(filename):
    with open(filename, 'r') as f:
        payload = f.read()
        return payload


def create_holding(session, thing_id=None, item_of=None):
    return _do_post(session, HOLD_FILE, thing_id, item_of)


def create_bib(session, thing_id=None):
    return _do_post(session, BIB_FILE, thing_id, None)


def put_post(session, thing_id, **kwargs):
    headers = {XL_ACTIVE_SIGEL_HEADER: ACTIVE_SIGEL}
    return session.put(thing_id, headers=headers, **kwargs)


def delete_post(session, thing_id, **kwargs):
    headers = {XL_ACTIVE_SIGEL_HEADER: ACTIVE_SIGEL}
    return session.delete(thing_id, headers=headers, **kwargs)


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
    json_payload = json_payload.replace("/bib/999999",
                                        "/bib/" + str(fake_voyager_id))

    headers = {'Content-Type': 'application/ld+json',
               XL_ACTIVE_SIGEL_HEADER: ACTIVE_SIGEL}
    result = session.post(ROOT_URL + "/",
                          data=json_payload,
                          headers=headers)
    assert result.status_code == 201
    location = result.headers['Location']
    return location


def update_holding(session, holding_id, payload, etag):
    # Update a simple field
    payload['@graph'][1]['inventoryLevel'] = 2
    json_payload = json.dumps(payload)

    headers = {'Content-Type': 'application/ld+json',
               'If-Match': etag,
               XL_ACTIVE_SIGEL_HEADER: ACTIVE_SIGEL}

    result = session.put(holding_id,
                         data=json_payload,
                         headers=headers)
    return result
