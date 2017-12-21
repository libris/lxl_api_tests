from restapi import *
import sys # sys.stderr.write('hej\n')

merge_endpoint = "/_merge"

def test_merge_and_delete(session):
    # Create two records
    bib_id1 = create_bib(session)
    bib_id2 = create_bib(session)

    # Merge them
    query_params = {'id1': bib_id1, 'id2': bib_id2}
    result = session.post(ROOT_URL + merge_endpoint,
                         params=query_params)
    assert result.status_code == 200

    # Delete merged record
    result = delete_post(session, bib_id1)
    assert result.status_code == 204

    # Assert that the non-favored URI is also gone
    result = session.get(bib_id2)
    assert result.status_code == 404


def test_merge_with_holdings(session):
    # Create two records
    bib_id1 = create_bib(session)
    bib_id2 = create_bib(session)

    # Create a holding on each of them
    result = session.get(bib_id1)
    json_body = result.json()
    graph = json_body['@graph']
    record = graph[0]
    thing = graph[1]
    thing_id1 = thing['@id']

    result = session.get(bib_id2)
    json_body = result.json()
    graph = json_body['@graph']
    record = graph[0]
    thing = graph[1]
    thing_id2 = thing['@id']

    holding_id1 = create_holding(session, None, thing_id1.decode("utf-8").encode("ascii","ignore"))
    holding_id2 = create_holding(session, None, thing_id2.decode("utf-8").encode("ascii","ignore"))

    # Merge the bib records
    query_params = {'id1': bib_id1, 'id2': bib_id2}
    result = session.post(ROOT_URL + merge_endpoint,
                         params=query_params)
    assert result.status_code == 200

    # Assert holding2 now points to bib1
    result = session.get(holding_id2)
    json_body = result.json()
    graph = json_body['@graph']
    record = graph[0]
    thing = graph[1]
    item_of = thing['itemOf']['@id']
    assert item_of == thing_id1

    # Cleanup
    result = delete_post(session, holding_id1)
    assert result.status_code == 204

    result = delete_post(session, holding_id2)
    assert result.status_code == 204

    result = delete_post(session, bib_id1)
    assert result.status_code == 204
