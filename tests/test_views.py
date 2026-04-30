import pytest
from django.contrib.auth import get_user_model
from django.test import Client

pytestmark = pytest.mark.django_db


def _login_staff(client, **kwargs):
    User = get_user_model()
    user = User.objects.create_user(username="staff", password="pw", is_staff=True, **kwargs)
    client.force_login(user)
    return user


def test_endpoint_requires_staff():
    c = Client()
    r = c.get("/djangonaut/commands/?q=user")
    assert r.status_code == 404


def test_endpoint_lists_models():
    c = Client()
    _login_staff(c, is_superuser=True)
    r = c.get("/djangonaut/commands/?q=user")
    assert r.status_code == 200
    labels = [x["label"] for x in r.json()["results"]]
    assert any("User" in lbl for lbl in labels)


def test_search_action_builds_q_param():
    c = Client()
    _login_staff(c, is_superuser=True)
    r = c.get("/djangonaut/commands/?q=user+rick")
    urls = [x["url"] for x in r.json()["results"]]
    assert any(u.endswith("?q=rick") for u in urls)


def test_add_action_returns_add_url():
    c = Client()
    _login_staff(c, is_superuser=True)
    r = c.get("/djangonaut/commands/", {"q": "user +"})
    urls = [x["url"] for x in r.json()["results"]]
    assert any(u.endswith("/add/") for u in urls)


def test_app_index():
    c = Client()
    _login_staff(c, is_superuser=True)
    r = c.get("/djangonaut/commands/", {"q": "@auth"})
    results = r.json()["results"]
    assert any("auth" in x["hint"] for x in results)


def test_middleware_injects_for_staff_on_html():
    c = Client()
    _login_staff(c, is_superuser=True)
    r = c.get("/admin/")
    assert r.status_code == 200
    assert b"palette.js" in r.content


def test_middleware_skips_for_anonymous():
    c = Client()
    r = c.get("/admin/login/")
    assert b"palette.js" not in r.content
