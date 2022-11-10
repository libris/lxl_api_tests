from conf_util import *
import os
import sys # sys.stderr.write('hej\n')
import xml.etree.ElementTree as ET

pytestmark = pytest.mark.dev

APIX_URL = os.environ.get('LXLTESTING_APIX_URL')
if not APIX_URL.endswith("/"):
    APIX_URL += "/"

ROOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
HOLD_FILE = os.path.join(ROOT_DIR, "resources", "hold.marcxml")
BIB_FILE = os.path.join(ROOT_DIR, "resources", "bib.marcxml")


def test_get_nonexisting_record(apix_session):
    result = apix_session.get(APIX_URL + '0.1/cat/libris/bib/a0a0a0a0a0a0a0a0')
    assert result.status_code == 404


def test_readonly_bib(session, apix_readonly_session, apix_session):
    marcxml_payload = _read_file(BIB_FILE)

    # Try to write a new record
    result = session.put(APIX_URL + '0.1/cat/libris/bib/new',
                         data=marcxml_payload)
    assert result.status_code == 401
    result = apix_readonly_session.put(APIX_URL + '0.1/cat/libris/bib/new',
                                       data=marcxml_payload)
    assert result.status_code == 403

    # Write a new record
    result = apix_session.put(APIX_URL + '0.1/cat/libris/bib/new',
                              data=marcxml_payload)
    assert result.status_code == 201
    location = result.headers['Location']
    xlid = location.split("/")[-1]
    bib_url = APIX_URL + '0.1/cat/libris/bib/' + xlid

    # Get the record, confirm it's there
    result = apix_readonly_session.get(bib_url)
    assert result.status_code == 200
    result = apix_session.get(bib_url)
    assert result.status_code == 200

    # Modify marc_xml payload to have the new 001 (the assigned controlNumber)
    xmlRecord = ET.fromstring(marcxml_payload)
    xmlRecord.findall("controlfield[@tag='001']")[0].text = xlid
    marcxml_payload = ET.tostring(xmlRecord, encoding='utf-8', method='xml')

    # Update the record
    result = apix_readonly_session.put(bib_url, data=marcxml_payload,
                                       allow_redirects=False)
    assert result.status_code == 403
    result = apix_session.put(bib_url, data=marcxml_payload,
                              allow_redirects=False)
    assert result.status_code == 303

    # Get the record, confirm still there
    result = apix_readonly_session.get(bib_url)
    assert result.status_code == 200
    result = apix_session.get(bib_url)
    assert result.status_code == 200

    # Delete the record
    result = apix_readonly_session.delete(bib_url)
    assert result.status_code == 403
    result = apix_session.delete(bib_url)
    assert result.status_code == 200

    # Get the record, confirm gone
    result = apix_readonly_session.get(bib_url)
    assert result.status_code == 404
    result = apix_session.get(bib_url)
    assert result.status_code == 404


def test_new_update_delete_bib(apix_session):
    marcxml_payload = _read_file(BIB_FILE)

    # Write a new record
    result = apix_session.put(APIX_URL + '0.1/cat/libris/bib/new',
                              data=marcxml_payload)
    assert result.status_code == 201
    location = result.headers['Location']
    xlid = location.split("/")[-1]

    # Get the record, confirm it's there
    result = apix_session.get(APIX_URL + '0.1/cat/libris/bib/' + xlid)
    assert result.status_code == 200

    # Modify marc_xml payload to have the new 001 (the assigned controlNumber)
    xmlRecord = ET.fromstring(marcxml_payload)
    xmlRecord.findall("controlfield[@tag='001']")[0].text = xlid
    marcxml_payload = ET.tostring(xmlRecord, encoding='utf-8', method='xml')

    # Update the record
    result = apix_session.put(APIX_URL + '0.1/cat/libris/bib/' + xlid,
                              data=marcxml_payload, allow_redirects=False)
    assert result.status_code == 303

    # Get the record, confirm still there
    result = apix_session.get(APIX_URL + '0.1/cat/libris/bib/' + xlid)
    assert result.status_code == 200

    # Delete the record
    result = apix_session.delete(APIX_URL + '0.1/cat/libris/bib/' + xlid)
    assert result.status_code == 200

    # Get the record, confirm gone
    result = apix_session.get(APIX_URL + '0.1/cat/libris/bib/' + xlid)
    assert result.status_code == 404

def test_update_on_voyager_id(apix_session):
    marcxml_payload = _read_file(BIB_FILE)
    
    # Update the record
    result = apix_session.put(APIX_URL +
                                    '0.1/cat/libris/bib/1783264',
                                    data=marcxml_payload,
                                    allow_redirects=False)
    assert result.status_code == 303

    # Get the record, confirm still there
    result = apix_session.get(APIX_URL +
                                    '0.1/cat/libris/bib/1783264')
    assert result.status_code == 200

def test_new_hold_on_voyager_id(apix_session):
    marcxml_payload = _read_file(HOLD_FILE)

    # Write a new record
    result = apix_session.put(APIX_URL + '0.1/cat/libris/bib/12141831/newhold',
                              data=marcxml_payload)

    assert result.status_code == 201
    location = result.headers['Location']
    xlid = location.split("/")[-1]

    # Get the record, confirm it's there
    result = apix_session.get(APIX_URL + '0.1/cat/libris/hold/' + xlid)
    assert result.status_code == 200

    # Delete the record
    result = apix_session.delete(APIX_URL + '0.1/cat/libris/hold/' + xlid)
    assert result.status_code == 200

    # Get the record, confirm gone
    result = apix_session.get(APIX_URL + '0.1/cat/libris/hold/' + xlid)
    assert result.status_code == 404


def test_new_hold_on_xl_id(apix_session):
    marcxml_payload = _read_file(HOLD_FILE)

    # Write a new record
    result = apix_session.put(APIX_URL +
                              '0.1/cat/libris/bib/cwpqbclp4x4n61k/newhold',
                              data=marcxml_payload)

    assert result.status_code == 201
    location = result.headers['Location']
    xlid = location.split("/")[-1]

    # Get the record, confirm it's there
    result = apix_session.get(APIX_URL + '0.1/cat/libris/hold/' + xlid)
    assert result.status_code == 200

    # Delete the record
    result = apix_session.delete(APIX_URL + '0.1/cat/libris/hold/' + xlid)
    assert result.status_code == 200

    # Get the record, confirm gone
    result = apix_session.get(APIX_URL + '0.1/cat/libris/hold/' + xlid)
    assert result.status_code == 404


def test_search_isbn(apix_session):
    result = apix_session.get(APIX_URL +
                              '0.1/cat/libris/search?isbn=9780141330464')
    assert result.status_code == 200
    assert 'Alice, who falls down a rabbit hole' in result.text


def test_search_issn(apix_session):
    result = apix_session.get(APIX_URL +
                              '0.1/cat/libris/search?issn=0018-0327')
    assert result.status_code == 200
    assert 'Bilagor med varierande utseende och' in result.text


def test_search_urnnbn(apix_session):
    result = apix_session.get(APIX_URL +
                              '0.1/cat/libris/search?urnnbn=(OCoLC)964671537')
    assert result.status_code == 200
    assert 'Denne dag, et liv.' in result.text


def _read_file(filename):
    with open(filename, 'r') as f:
        payload = f.read()
        return payload
