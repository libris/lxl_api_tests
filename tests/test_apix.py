from restapi import *
import os
import sys # sys.stderr.write('hej\n')

APIX_URL = os.environ.get('LXLTESTING_APIX_URL')
if not APIX_URL.endswith("/"):
    APIX_URL += "/"

ROOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
HOLD_FILE = os.path.join(ROOT_DIR, "resources", "hold.marcxml")
BIB_FILE = os.path.join(ROOT_DIR, "resources", "bib.marcxml")
    
import requests

def test_get_nonexisting_record():
    result = requests.session().get(APIX_URL +
                                    '0.1/cat/libris/bib/a0a0a0a0a0a0a0a0')
    assert result.status_code == 404

def test_new_update_delete_bib():
    marcxml_payload = _read_file(BIB_FILE)

    # Write a new record
    result = requests.session().put(APIX_URL +
                                    '0.1/cat/libris/bib/new',
                                    data=marcxml_payload)
    assert result.status_code == 201
    location = result.headers['Location']
    xlid = location.split("/")[-1]

    # Get the record, confirm it's there
    result = requests.session().get(APIX_URL +
                                    '0.1/cat/libris/bib/' +
                                    xlid)
    assert result.status_code == 200

    # Update the record
    result = requests.session().put(APIX_URL +
                                    '0.1/cat/libris/bib/' + xlid,
                                    data=marcxml_payload,
                                    allow_redirects=False)
    assert result.status_code == 303

    # Get the record, confirm still there
    result = requests.session().get(APIX_URL +
                                    '0.1/cat/libris/bib/' +
                                    xlid)
    assert result.status_code == 200

    # Delete the record
    result = requests.session().delete(APIX_URL +
                                       '0.1/cat/libris/bib/' + xlid)
    assert result.status_code == 200

    # Get the record, confirm gone
    result = requests.session().get(APIX_URL +
                                    '0.1/cat/libris/bib/' +
                                    xlid)
    assert result.status_code == 404

    
def test_new_hold_on_voyager_id():
    marcxml_payload = _read_file(HOLD_FILE)

    # Write a new record
    result = requests.session().put(APIX_URL +
                                    '0.1/cat/libris/bib/12141831/newhold',
                                    data=marcxml_payload)
    
    assert result.status_code == 201
    location = result.headers['Location']
    xlid = location.split("/")[-1]

    # Get the record, confirm it's there
    result = requests.session().get(APIX_URL +
                                    '0.1/cat/libris/hold/' + xlid)
    assert result.status_code == 200

    # Delete the record
    result = requests.session().delete(APIX_URL +
                                       '0.1/cat/libris/hold/' + xlid)
    assert result.status_code == 200

    # Get the record, confirm gone
    result = requests.session().get(APIX_URL +
                                    '0.1/cat/libris/hold/' + xlid)
    assert result.status_code == 404

    
def test_new_hold_on_xl_id():
    marcxml_payload = _read_file(HOLD_FILE)

    # Write a new record
    result = requests.session().put(APIX_URL +
                                    '0.1/cat/libris/bib/cwpqbclp4x4n61k/newhold',
                                    data=marcxml_payload)
    
    assert result.status_code == 201
    location = result.headers['Location']
    xlid = location.split("/")[-1]

    # Get the record, confirm it's there
    result = requests.session().get(APIX_URL +
                                    '0.1/cat/libris/hold/' + xlid)
    assert result.status_code == 200

    # Delete the record
    result = requests.session().delete(APIX_URL +
                                       '0.1/cat/libris/hold/' + xlid)
    assert result.status_code == 200

    # Get the record, confirm gone
    result = requests.session().get(APIX_URL +
                                    '0.1/cat/libris/hold/' + xlid)
    assert result.status_code == 404

    
def test_search_isbn():
    result = requests.session().get(APIX_URL +
                                    '0.1/cat/libris/search?isbn=9780141330464')
    assert result.status_code == 200
    assert 'Alice, who falls down a rabbit hole' in result.text
    

def test_search_issn():
    result = requests.session().get(APIX_URL +
                                    '0.1/cat/libris/search?issn=0018-0327')
    assert result.status_code == 200
    assert 'Bilagor med varierande utseende och' in result.text


def test_search_urnnbn():
    result = requests.session().get(APIX_URL +
                                    '0.1/cat/libris/search?urnnbn=(OCoLC)964671537')
    assert result.status_code == 200
    assert 'Orig:s titel: Denna dagen, ett liv' in result.text

    
def _read_file(filename):
    with open(filename, 'r') as f:
        payload = f.read()
        return payload
