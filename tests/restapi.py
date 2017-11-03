from lxml import html
import json
import os
import pytest
import requests


ROOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
HOLD_FILE = os.path.join(ROOT_DIR, "resources", "hold.jsonld")
BIB_FILE = os.path.join(ROOT_DIR, "resources", "bib.jsonld")

DEFAULT_AUTH_URL = 'http://127.0.0.1:5000/login/authorize'
DEFAULT_AUTH_COOKIE_DOMAIN = 'localhost'
DEFAULT_LXL_LOGIN_URL = 'http://127.0.0.1:5000/login'
DEFAULT_ROOT_URL = 'http://127.0.0.1:5000'
DEFAULT_ES_REFRESH_URL = 'http://127.0.0.1:9200/_refresh'

AUTH_URL = os.environ.get('LXLTESTING_AUTH_URL', DEFAULT_AUTH_URL)
LXL_LOGIN_URL = os.environ.get('LXLTESTING_LXL_LOGIN_URL',
                               DEFAULT_LXL_LOGIN_URL)
ROOT_URL = os.environ.get('LXLTESTING_ROOT_URL', DEFAULT_ROOT_URL)
ES_REFRESH_URL = os.environ.get('LXLTESTING_ES_REFRESH_URL',
                                DEFAULT_ES_REFRESH_URL)
AUTH_COOKIE_DOMAIN = os.environ.get('LXLTESTING_AUTH_COOKIE_DOMAIN',
                                    DEFAULT_AUTH_COOKIE_DOMAIN)

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
    csrf_token = _get_input_value(page, 'csrf_token')
    next = list(set(page.xpath("//input[@name='next_redirect']/@value")))[0]

    payload = {
        'username': USERNAME,
        'password': PASSWORD,
        'next_redirect': next,
        'csrf_token': csrf_token
    }

    result = session.post(LOGIN_URL, data=payload,
                          cookies=_get_session_cookie(session),
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
                              cookies=_get_session_cookie(session),
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


def _get_session_cookie(session):
    cookies = requests.utils.dict_from_cookiejar(session.cookies)
    return cookies


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
    json_payload = json_payload.replace("/bib/999999",
                                        "/bib/" + str(fake_voyager_id))

    result = session.post(ROOT_URL + "/",
                          cookies=_get_session_cookie(session),
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
                         cookies=_get_session_cookie(session),
                         data=json_payload,
                         headers={'Content-Type': 'application/ld+json',
                                  'If-Match': etag})
    return result
