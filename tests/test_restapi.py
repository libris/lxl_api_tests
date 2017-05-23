from restapi import *

def test_update_and_delete_holding(session):
    holding_id = create_holding(session)

    result = session.get(holding_id, headers={'Accept':'application/ld+json'})
    assert result.status_code == 200

    etag = result.headers['ETag']
    result = update_holding(session, holding_id, etag)
    assert result.status_code == 204

    result = session.delete(holding_id)
    assert result.status_code == 204

    result = session.get(holding_id)
    assert result.status_code == 404

    result = session.delete(holding_id)
    assert result.status_code == 410

