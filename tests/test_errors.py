def test_not_found_page(client):
    """Unknown routes should show the custom 404 page."""
    response = client.get("/this-page-does-not-exist")

    assert response.status_code == 404
    assert b"Page Not Found" in response.data


def test_internal_server_error_page(client):
    """Unhandled exceptions should show the custom 500 page."""
    response = client.get("/test-error")

    assert response.status_code == 500
    assert b"Something went wrong." in response.data