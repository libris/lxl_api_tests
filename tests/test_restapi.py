from lxml import html
import os
import pytest
import requests

ROOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
HOLD_FILE = os.path.join(ROOT_DIR, "resources", "hold.jsonld")

DEFAULT_AUTH_URL = 'http://127.0.0.1:5000/login/authorize'
DEFAULT_LXL_LOGIN_URL = 'http://127.0.0.1:5000/login'
DEFAULT_ROOT_URL = 'http://127.0.0.1:5000'

AUTH_URL = os.environ.get('LXLTESTING_AUTH_URL', DEFAULT_AUTH_URL)
LXL_LOGIN_URL = os.environ.get('LXLTESTING_LXL_LOGIN_URL',
                               DEFAULT_LXL_LOGIN_URL)
ROOT_URL = os.environ.get('LXLTESTING_ROOT_URL', DEFAULT_ROOT_URL)

LOGIN_URL = os.environ.get('LXLTESTING_LOGIN_URL')
USERNAME = os.environ.get('LXLTESTING_USERNAME')
PASSWORD = os.environ.get('LXLTESTING_PASSWORD')


@pytest.fixture(scope="module")
def session():
    session = requests.session()

    result = session.get(AUTH_URL)
    page = html.fromstring(result.text)
    csrf_xpath = page.xpath("//input[@name='csrfmiddlewaretoken']/@value")
    csrf_token = list(set(csrf_xpath))[0]
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

    return session


def setup_DELETE_tests(session):
    _create_holding(session)
    pass


def _create_holding(session):
    # 1. POST hold.jsonld and grab Location header in response
    json_payload = _read_payload(HOLD_FILE)
    result = session.post(ROOT_URL + "/create?collection=xl",
                          data=json_payload,
                          headers={'Content-Type': 'application/ld+json'})
    assert result.status_code == 201
    location = result.headers['Location']
    return location


def _read_payload(filename):
    with open(filename, 'r') as f:
        payload = f.read()
        return payload


def test_delete_holding(session):
    holding_id = _create_holding(session)

    result = session.get(holding_id)
    assert result.status_code == 200

    result = session.delete(holding_id)
    assert result.status_code == 204

    result = session.get(holding_id)
    assert result.status_code == 404

    result = session.delete(holding_id)
    assert result.status_code == 410

