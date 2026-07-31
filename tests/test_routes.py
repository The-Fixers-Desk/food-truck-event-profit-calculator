def test_calculator_page_loads(client):
    """The Event Inputs screen should load successfully."""
    response = client.get("/")

    assert response.status_code == 200
    assert b"Event Inputs" in response.data


def test_defaults_page_loads(client):
    """The Defaults screen should load successfully."""
    response = client.get("/defaults")

    assert response.status_code == 200
    assert b"Defaults" in response.data


def test_saved_events_page_loads(client):
    """The Saved Events screen should load successfully."""
    response = client.get("/saved-events")

    assert response.status_code == 200
    assert b"Saved Events" in response.data


def test_former_comparison_url_redirects_to_saved_events(client):
    response = client.get("/comparison")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/saved-events")
