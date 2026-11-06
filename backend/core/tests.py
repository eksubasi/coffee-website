from unittest import mock

import pytest
from django.db import OperationalError
from django.urls import reverse


@pytest.mark.django_db
def test_health_reports_database_reachable(client):
    response = client.get(reverse("health"))

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "db": True}


@pytest.mark.django_db
def test_health_reports_database_unreachable(client):
    with mock.patch(
        "core.views.connection.cursor",
        side_effect=OperationalError("database unavailable"),
    ):
        response = client.get(reverse("health"))

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "db": False}
