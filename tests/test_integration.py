def test_main_pages_load(client):
    for path in ['/','/register','/login','/inventory','/requests','/assignments','/volunteers','/notifications','/alerts','/incidents','/reports']:
        response=client.get(path)
        assert response.status_code==200, path
