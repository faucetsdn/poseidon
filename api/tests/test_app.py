import falcon
from falcon import testing
import pytest

from app.app import api


@pytest.fixture
def client():
    return testing.TestClient(api)


def test_list_data(client):
    response = client.simulate_get('/v1/network')

    assert len(response.json) == 2
    assert response.status == falcon.HTTP_OK
