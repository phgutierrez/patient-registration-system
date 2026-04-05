import pytest


@pytest.mark.anyio
async def test_auth_login_me_refresh_logout(client):
    login = await client.post('/api/auth/login', json={'username': 'admin', 'password': 'admin123'})
    assert login.status_code == 200
    access = login.json()['access_token']

    me = await client.get('/api/auth/me', headers={'Authorization': f'Bearer {access}'})
    assert me.status_code == 200
    assert me.json()['username'] == 'admin'

    csrf = login.cookies.get('csrf_token')
    refresh = await client.post('/api/auth/refresh', headers={'x-csrf-token': csrf})
    assert refresh.status_code == 200

    logout = await client.post('/api/auth/logout', headers={'x-csrf-token': refresh.cookies.get('csrf_token') or csrf})
    assert logout.status_code == 204
