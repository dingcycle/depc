import json
import random

import pytest


def test_list_team_checks_authorization(client, create_team, create_user, create_grant):
    team_id = str(create_team('My team')['id'])

    resp = client.get('/v1/teams/{}/checks'.format(team_id))
    assert resp.status_code == 401

    client.login('depc')
    resp = client.get('/v1/teams/{}/checks'.format(team_id))
    assert resp.status_code == 403

    for role in ['member', 'editor', 'manager']:
        user_id = str(create_user(role)['id'])
        create_grant(team_id, user_id, role)
        client.login(role)
        resp = client.get('/v1/teams/{}/checks'.format(team_id))
        assert resp.status_code == 200


def test_list_checks_notfound(client, create_team, create_source, create_user, create_grant):
    team_id = str(create_team('My team')['id'])
    user_id = str(create_user('depc')['id'])
    create_grant(team_id, user_id, 'member')
    client.login('depc')

    resp = client.get('/v1/teams/notfound/checks')
    assert resp.status_code == 404


def test_list_checks(client, create_team, create_source, create_user, create_grant, create_check):
    team_id = str(create_team('My team')['id'])
    first_source = str(create_source('First', team_id)['id'])
    create_check('First', first_source, 'Threshold', {'metric': 'foo', 'threshold': "100"})

    second_source = str(create_source('Second', team_id)['id'])
    create_check('Second', second_source, 'Threshold', {'metric': 'foo', 'threshold': "100"})

    user_id = str(create_user('depc')['id'])
    create_grant(team_id, user_id, 'member')
    client.login('depc')

    resp = client.get('/v1/teams/{}/checks'.format(team_id))
    assert resp.status_code == 200
    assert [c["name"] for c in resp.json["checks"]] == ["First", "Second"]

    for i in range(8):
        create_check(
            'My check {}'.format(i), random.choice([first_source, second_source]),
            'Threshold', {'metric': 'foo', 'threshold': "100"}
        )
    resp = client.get('/v1/teams/{}/checks'.format(team_id))
    assert resp.status_code == 200
    assert len(resp.json['checks']) == 10


def test_list_source_checks_authorization(client, create_team, create_source, create_user, create_grant):
    team_id = str(create_team('My team')['id'])
    source_id = str(create_source('My source', team_id)['id'])

    resp = client.get('/v1/teams/{}/sources/{}/checks'.format(team_id, source_id))
    assert resp.status_code == 401

    client.login('depc')
    resp = client.get('/v1/teams/{}/sources/{}/checks'.format(team_id, source_id))
    assert resp.status_code == 403

    for role in ['member', 'editor', 'manager']:
        user_id = str(create_user(role)['id'])
        create_grant(team_id, user_id, role)
        client.login(role)
        resp = client.get('/v1/teams/{}/sources/{}/checks'.format(team_id, source_id))
        assert resp.status_code == 200


def test_list_source_checks_notfound(client, create_team, create_source, create_user, create_grant):
    team_id = str(create_team('My team')['id'])
    source_id = str(create_source('My source', team_id)['id'])
    user_id = str(create_user('depc')['id'])
    create_grant(team_id, user_id, 'member')

    client.login('depc')
    resp = client.get('/v1/teams/notfound/sources/{}/checks'.format(source_id))
    assert resp.status_code == 404

    resp = client.get('/v1/teams/{}/sources/notfound/checks'.format(team_id))
    assert resp.status_code == 404


def test_list_source_checks(client, create_team, create_source, create_user, create_grant, create_check):
    team_id = str(create_team('My team')['id'])
    source_id = str(create_source('My source', team_id)['id'])
    checks_id = [str(create_check('My check', source_id, 'Threshold', {'metric': 'foo', 'threshold': "100"})['id'])]

    user_id = str(create_user('depc')['id'])
    create_grant(team_id, user_id, 'member')
    client.login('depc')

    client.login('depc')
    resp = client.get('/v1/teams/{}/sources/{}/checks'.format(team_id, source_id))
    assert resp.status_code == 200
    assert resp.json == {
        'checks': [{
            'name': 'My check',
            'parameters': {'metric': 'foo', 'threshold': "100"},
            'type': 'Threshold'
        }]
    }

    for i in range(9):
        checks_id.append(str(create_check(
            'My check {}'.format(i), source_id,
            'Threshold', {'metric': 'foo', 'threshold': "100"})['id']
        ))
    resp = client.get('/v1/teams/{}/sources/{}/checks'.format(team_id, source_id))
    assert resp.status_code == 200
    assert len(resp.json['checks']) == 10


def test_post_source_check_authorization(client, create_team, create_user, create_source, create_grant):
    team_id = str(create_team('My team')['id'])
    source_id = str(create_source('My source', team_id)['id'])

    post_data = [
        {'name': 'My member check', 'type': 'Threshold', 'parameters': {'metric': 'foo', 'threshold': "100"}},
        {'name': 'My editor check', 'type': 'Threshold', 'parameters': {'metric': 'foo', 'threshold': "100"}},
        {'name': 'My manager check', 'type': 'Threshold', 'parameters': {'metric': 'foo', 'threshold': "100"}}
    ]

    resp = client.post('/v1/teams/{}/sources/{}/checks'.format(team_id, source_id), data=json.dumps(post_data[0]))
    assert resp.status_code == 401

    client.login('depc')
    resp = client.post('/v1/teams/{}/sources/{}/checks'.format(team_id, source_id), data=json.dumps(post_data[0]))
    assert resp.status_code == 403

    roles = {'member': 403, 'editor': 201, 'manager': 201}
    for i, (role, status) in enumerate(roles.items()):
        user_id = str(create_user(role)['id'])
        create_grant(team_id, user_id, role)
        client.login(role)
        resp = client.post('/v1/teams/{}/sources/{}/checks'.format(team_id, source_id), data=json.dumps(post_data[i]))
        assert resp.status_code == status


def test_post_source_check_notfound(client, create_team, create_source, create_user, create_grant):
    team_id = str(create_team('My team')['id'])
    source_id = str(create_source('My source', team_id)['id'])
    user_id = str(create_user('depc')['id'])
    create_grant(team_id, user_id, 'manager')
    client.login('depc')
    post_data = {'name': 'My check', 'type': 'Threshold', 'parameters': {'metric': 'foo', 'threshold': "100"}}

    resp = client.post('/v1/teams/notfound/sources/{}/checks'.format(source_id), data=json.dumps(post_data))
    assert resp.status_code == 404

    resp = client.post('/v1/teams/{}/sources/notfound/checks'.format(team_id), data=json.dumps(post_data))
    assert resp.status_code == 404


def test_post_source_check(client, create_team, create_source, create_user, create_grant):
    team_id = str(create_team('My team')['id'])
    source_id = str(create_source('My source', team_id)['id'])
    user_id = str(create_user('depc')['id'])
    create_grant(team_id, user_id, 'manager')
    client.login('depc')

    post_data = {'name': 'My check', 'type': 'Threshold'}
    resp = client.post('/v1/teams/{}/sources/{}/checks'.format(team_id, source_id), data=json.dumps(post_data))
    assert resp.raises_required_property('parameters')

    post_data = {'name': 'My check', 'parameters': {'metric': 'foo', 'threshold': "100"}}
    resp = client.post('/v1/teams/{}/sources/{}/checks'.format(team_id, source_id), data=json.dumps(post_data))
    assert resp.raises_required_property('type')

    post_data = {'type': 'Threshold', 'parameters': {'metric': 'foo', 'threshold': "100"}}
    resp = client.post('/v1/teams/{}/sources/{}/checks'.format(team_id, source_id), data=json.dumps(post_data))
    assert resp.raises_required_property('name')

    post_data = {'name': 'My check', 'type': 'Threshold', 'parameters': {'metric': 'foo', 'threshold': "100"}, 'additional': 'property'}
    resp = client.post('/v1/teams/{}/sources/{}/checks'.format(team_id, source_id), data=json.dumps(post_data))
    assert 'Additional properties are not allowed' in resp.json['message']

    post_data = {'name': 'My check', 'type': 'Threshold', 'parameters': {'metric': 'foo', 'threshold': "100"}}
    resp = client.post('/v1/teams/{}/sources/{}/checks'.format(team_id, source_id), data=json.dumps(post_data))
    assert resp.status_code == 201
    assert resp.json == {
        'name': 'My check',
        'parameters': {'metric': 'foo', 'threshold': "100"},
        'type': 'Threshold'
    }


def test_post_source_check_conflict(client, create_team, create_user, create_source, create_grant):
    team_id = str(create_team('My team')['id'])
    source_id = str(create_source('My source', team_id)['id'])

    role = 'editor'
    create_grant(team_id, str(create_user(role)['id']), role)
    client.login(role)

    post_data = {'name': 'My check', 'type': 'Threshold', 'parameters': {'metric': 'foo', 'threshold': "100"}}

    resp = client.post('/v1/teams/{}/sources/{}/checks'.format(team_id, source_id), data=json.dumps(post_data))
    assert resp.status_code == 201

    resp = client.post('/v1/teams/{}/sources/{}/checks'.format(team_id, source_id), data=json.dumps(post_data))
    assert resp.status_code == 409


@pytest.mark.parametrize("test_input", ["'Test", "Test'", "'Test'", '"Test', 'Test"', '"Test"'])
def test_post_source_check_prohibited_quotes(
        client, create_team, create_user, create_source, create_grant, test_input
):
    team_id = str(create_team('My team')['id'])
    source_id = str(create_source('My source', team_id)['id'])

    role = 'editor'
    create_grant(team_id, str(create_user(role)['id']), role)
    client.login(role)

    post_data = {'name': test_input, 'type': 'Threshold', 'parameters': {'metric': 'foo', 'threshold': "100"}}

    resp = client.post('/v1/teams/{}/sources/{}/checks'.format(team_id, source_id), data=json.dumps(post_data))
    assert resp.status_code == 400
