import json
import re
from unittest.mock import patch

import pytest
from django.contrib.auth.models import Permission
from django.template import Context, RequestContext, Template
from django.urls import resolve

from django_cmdbar.templatetags.django_cmdbar import django_cmdbar

from .admin import ArticleAdmin, backoffice
from .models import Article

pytestmark = pytest.mark.django_db


def catalog(response):
    data = re.search(
        r'<script id="django_cmdbar-data" type="application/json">(.*?)</script>',
        response.content.decode(),
        re.S,
    )
    return json.loads(data[1]) if data else None


def test_admin_index_and_model_pages_include_palette(client, superuser):
    client.force_login(superuser)
    for path in (
        "/admin/",
        "/admin/tests/",
        "/admin/tests/article/",
        "/admin/tests/article/add/",
    ):
        response = client.get(path)
        assert response.status_code == 200
        models = catalog(response)["models"]
        article = next(model for model in models if model["key"] == "tests.article")
        assert article["list_url"] == "/admin/tests/article/"
        assert article["change_url"] == "/admin/tests/article/__django_cmdbar_pk__/change/"
        assert article["add_url"] == "/admin/tests/article/add/"
        assert article["searchable"] is True
        assert b"django_cmdbar/palette.css" in response.content
        assert b'type="module" src="/static/django_cmdbar/palette.js"' in response.content


def test_nonsearchable_models_do_not_offer_search(client, superuser):
    client.force_login(superuser)
    models = catalog(client.get("/admin/"))["models"]
    department = next(model for model in models if model["key"] == "tests.department")
    assert department["searchable"] is False


@pytest.mark.parametrize("permission", ["view_article", "change_article", "add_article"])
def test_catalog_respects_model_permissions(client, staff, permission):
    staff.user_permissions.add(Permission.objects.get(codename=permission))
    client.force_login(staff)
    models = catalog(client.get("/admin/"))["models"]
    assert len(models) == 1
    article = models[0]
    assert article["key"] == "tests.article"
    assert bool(article["list_url"]) is (permission != "add_article")
    assert bool(article["change_url"]) is (permission != "add_article")
    assert bool(article["add_url"]) is (permission == "add_article")


def test_module_permissions_are_respected(client, superuser):
    client.force_login(superuser)
    with patch.object(ArticleAdmin, "has_module_permission", return_value=False):
        models = catalog(client.get("/admin/"))["models"]
    assert all(model["key"] != "tests.article" for model in models)


def test_empty_permissions_do_not_render_palette(client, staff):
    client.force_login(staff)
    assert catalog(client.get("/admin/")) is None


def test_palette_is_not_in_public_pages_or_popups(client, superuser):
    client.force_login(superuser)
    for path in ("/", "/admin/tests/article/?_popup=1", "/admin/tests/article/add/?_popup=1"):
        response = client.get(path)
        assert catalog(response) is None
        assert b"django_cmdbar/palette.js" not in response.content


def test_palette_is_not_on_login_page(client):
    response = client.get("/admin/login/")
    assert catalog(response) is None
    assert b"django_cmdbar/palette.css" not in response.content


def test_custom_admin_site_is_isolated(client, superuser):
    client.force_login(superuser)
    response = client.get("/backoffice/")
    models = catalog(response)["models"]
    assert len(models) == 1
    assert models[0]["list_url"] == "/backoffice/tests/article/"
    assert models[0]["change_url"] == "/backoffice/tests/article/__django_cmdbar_pk__/change/"
    assert models[0]["add_url"] == "/backoffice/tests/article/add/"


def test_search_fields_can_depend_on_request(client, superuser):
    client.force_login(superuser)
    with patch.object(ArticleAdmin, "get_search_fields", return_value=()):
        models = catalog(client.get("/admin/"))["models"]
    article = next(model for model in models if model["key"] == "tests.article")
    assert article["searchable"] is False


def test_tag_outside_admin_is_empty(rf, superuser):
    request = rf.get("/")
    request.user = superuser
    request.resolver_match = resolve("/")
    assert django_cmdbar(RequestContext(request)) == {}
    assert django_cmdbar(Context()) == {}


def test_inactive_staff_cannot_render_palette(rf, superuser):
    request = rf.get("/backoffice/")
    superuser.is_active = False
    request.user = superuser
    assert django_cmdbar(RequestContext(request), site=backoffice) == {}


def test_model_labels_are_safe_in_json(client, superuser):
    client.force_login(superuser)
    label = '</script><script>alert("label")</script>'
    with patch.object(Article._meta, "verbose_name_plural", label):
        response = client.get("/admin/")
    assert label.encode() not in response.content
    models = catalog(response)["models"]
    assert next(model for model in models if model["key"] == "tests.article")["name"] == label


def test_explicit_template_integration_for_custom_admin_views(rf, superuser):
    request = rf.get("/custom-admin-view/")
    request.user = superuser
    output = Template("{% load django_cmdbar %}{% django_cmdbar site=site %}").render(
        RequestContext(request, {"site": backoffice})
    )
    assert 'id="django_cmdbar"' in output
    assert "/backoffice/tests/article/" in output
