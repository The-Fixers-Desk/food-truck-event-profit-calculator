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


def test_comparison_page_loads(client):
    """The Comparison screen should load successfully."""
    response = client.get("/comparison")

    assert response.status_code == 200
    assert b"Comparison" in response.data
