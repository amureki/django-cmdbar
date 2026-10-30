import mimetypes
import re
from urllib.parse import urlsplit

import pytest
from asgiref.sync import sync_to_async
from django.contrib.admin.utils import quote
from django.core.management import call_command
from django.urls import reverse
from playwright.async_api import expect

from .models import Article

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize(
    "pk", ["42", "a_b/c:d#e?f&g%", "名字", "id with spaces", "a\"b'c\\d", ".", ".."]
)
async def test_record_links_use_django_admin_quoting(admin_page, pk):
    expected = reverse("admin:tests_article_change", args=[quote(pk)])
    results = await admin_page.evaluate(
        """async query => {
            const { getResults } = await import('/static/djangonaut/search.js');
            const catalog = JSON.parse(document.getElementById('djangonaut-data').textContent);
            return getResults(query, catalog);
        }""",
        f"arti#{pk}",
    )
    assert results[0]["url"] == expected


async def test_keyboard_navigation_and_focus_restore(admin_page):
    previous = admin_page.get_by_role("link", name="View site")
    await previous.focus()
    await admin_page.keyboard.press("Control+k")
    dialog = admin_page.get_by_role("dialog", name="Go to")
    query = admin_page.get_by_role("combobox")
    await expect(dialog).to_be_visible()
    await expect(query).to_be_focused()
    options = admin_page.get_by_role("option")
    await expect(options.first).to_have_attribute("aria-selected", "true")
    await query.press("ArrowDown")
    await expect(options.nth(1)).to_have_attribute("aria-selected", "true")
    await expect(query).to_have_attribute(
        "aria-activedescendant", await options.nth(1).get_attribute("id")
    )
    await query.press("ArrowUp")
    await expect(options.first).to_have_attribute("aria-selected", "true")
    await query.press("ArrowUp")
    await expect(options.last).to_have_attribute("aria-selected", "true")
    await query.press("Tab")
    await expect(admin_page.get_by_role("button", name="Close navigation")).to_be_focused()
    await admin_page.keyboard.press("Tab")
    await expect(query).to_be_focused()
    await query.press("Escape")
    await expect(dialog).not_to_be_visible()
    await expect(previous).to_be_focused()


async def test_empty_results_and_reopening_are_safe(admin_page):
    errors = []
    admin_page.on("pageerror", lambda error: errors.append(str(error)))
    await admin_page.keyboard.press("Control+k")
    query = admin_page.get_by_role("combobox")
    await query.fill("zzzzzz")
    await expect(admin_page.get_by_role("status")).to_have_text("No matches. Try a model name.")
    await expect(query).not_to_have_attribute("aria-activedescendant", re.compile(".+"))
    for key in ("ArrowDown", "ArrowUp", "Enter"):
        await query.press(key)
    await expect(admin_page).to_have_url("http://testserver/admin/")
    await admin_page.keyboard.press("Control+k")
    await admin_page.keyboard.press("Control+k")
    await expect(query).to_have_value("")
    await expect(admin_page.get_by_role("option").first).to_have_attribute("aria-selected", "true")
    assert errors == []


async def test_typing_does_not_make_search_requests(admin_page):
    requests = []
    admin_page.on("request", lambda request: requests.append(request.url))
    await admin_page.keyboard.press("Control+k")
    await admin_page.get_by_role("combobox").fill("arti alice")
    await expect(admin_page.get_by_role("option")).to_contain_text("Search for alice")
    assert requests == []


async def test_enter_opens_filtered_changelist(admin_page):
    await Article.objects.acreate(id="42", name="Alice")
    await Article.objects.acreate(id="43", name="Bob")
    await admin_page.keyboard.press("Control+k")
    query = admin_page.get_by_role("combobox")
    await query.fill("arti Alice")
    await query.press("Enter")
    await expect(admin_page).to_have_url("http://testserver/admin/tests/article/?q=Alice")
    await expect(admin_page.locator("#result_list")).to_contain_text("Alice")
    await expect(admin_page.locator("#result_list")).not_to_contain_text("Bob")


async def test_enter_opens_record(admin_page):
    await Article.objects.acreate(id="42", name="Alice")
    await admin_page.keyboard.press("Control+k")
    query = admin_page.get_by_role("combobox")
    await query.fill("arti#42")
    await query.press("Enter")
    await expect(admin_page).to_have_url("http://testserver/admin/tests/article/42/change/")
    await expect(admin_page.locator("#id_name")).to_have_value("Alice")


async def test_incomplete_record_query_keeps_model_completions(admin_page):
    query_text = "arti#"
    await Article.objects.acreate(id="42", name="Alice")
    await admin_page.keyboard.press("Control+k")
    query = admin_page.get_by_role("combobox")
    await query.fill(query_text)
    option = admin_page.get_by_role("option")
    await expect(option).to_contain_text("Articles")
    await expect(option).to_contain_text("Enter a record ID")
    await expect(option).to_have_attribute("aria-disabled", "true")
    await expect(admin_page.get_by_role("status")).not_to_be_visible()

    for key in ("ArrowDown", "ArrowUp", "Enter", "Control+Enter"):
        await query.press(key)
    await option.click(force=True)
    await expect(admin_page).to_have_url("http://testserver/admin/")
    await expect(admin_page.get_by_role("dialog")).to_be_visible()
    await expect(query).to_be_focused()
    await expect(query).to_have_value(query_text)

    await query.press_sequentially("42")
    await expect(option).to_contain_text("Open record #42")
    await expect(option).to_have_attribute("aria-disabled", "false")
    await query.press("Enter")
    await expect(admin_page).to_have_url("http://testserver/admin/tests/article/42/change/")
    await expect(admin_page.locator("#id_name")).to_have_value("Alice")


async def test_click_opens_model_list(admin_page):
    await admin_page.keyboard.press("Control+k")
    await admin_page.get_by_role("combobox").fill("arti")
    await admin_page.get_by_role("option").click()
    await expect(admin_page).to_have_url("http://testserver/admin/tests/article/")


async def test_modified_enter_opens_new_tab(admin_page):
    await admin_page.keyboard.press("Control+k")
    query = admin_page.get_by_role("combobox")
    await query.fill("arti")
    async with admin_page.context.expect_page() as opened:
        await query.press("Control+Enter")
    new_tab = await opened.value
    await expect(new_tab).to_have_url("http://testserver/admin/tests/article/")
    assert await new_tab.evaluate("window.opener === null")
    await expect(admin_page.get_by_role("dialog")).not_to_be_visible()
    await expect(admin_page).to_have_url("http://testserver/admin/")


async def test_custom_site_navigation_stays_on_that_site(admin_page):
    await admin_page.goto("http://testserver/backoffice/")
    await admin_page.keyboard.press("Control+k")
    query = admin_page.get_by_role("combobox")
    await query.fill("arti")
    await query.press("Enter")
    await expect(admin_page).to_have_url("http://testserver/backoffice/tests/article/")


async def test_search_terms_are_rendered_as_text(admin_page):
    await admin_page.keyboard.press("Control+k")
    await admin_page.get_by_role("combobox").fill('arti <img src=x onerror="alert(1)">')
    await expect(admin_page.get_by_role("option")).to_contain_text('<img src=x onerror="alert(1)">')
    await expect(admin_page.locator("#djangonaut img")).to_have_count(0)


async def test_close_button_and_backdrop(admin_page):
    await admin_page.keyboard.press("Control+k")
    await admin_page.get_by_role("button", name="Close navigation").click()
    await expect(admin_page.get_by_role("dialog")).not_to_be_visible()
    await admin_page.keyboard.press("Control+k")
    await admin_page.mouse.click(2, 2)
    await expect(admin_page.get_by_role("dialog")).not_to_be_visible()


async def test_query_help_and_return_to_search(admin_page):
    await admin_page.keyboard.press("Control+k")
    query = admin_page.get_by_role("combobox")
    guide = admin_page.get_by_role("region", name="Query help")
    await expect(guide).not_to_be_visible()
    await query.fill("?")
    await expect(guide).to_be_visible()
    for syntax in ("model#id", "model text", "model +"):
        await expect(guide).to_contain_text(syntax)
    await expect(admin_page.get_by_role("listbox")).not_to_be_visible()
    await expect(admin_page.get_by_role("status")).not_to_be_visible()
    await expect(query).to_have_attribute("aria-expanded", "false")
    await expect(query).not_to_have_attribute("aria-activedescendant", re.compile(".+"))
    for key in ("ArrowDown", "ArrowUp", "Enter"):
        await query.press(key)
    await expect(admin_page).to_have_url("http://testserver/admin/")
    await expect(query).to_be_focused()

    await query.fill("arti alice?")
    await expect(guide).not_to_be_visible()
    await expect(admin_page.get_by_role("option")).to_contain_text("Search for alice?")
    await expect(query).to_have_attribute("aria-expanded", "true")
    await query.fill(" ? ")
    await expect(guide).to_be_visible()


@pytest.mark.parametrize("theme", ["light", "dark"])
async def test_mobile_layout_and_admin_theme(admin_page, theme):
    await admin_page.set_viewport_size({"width": 390, "height": 844})
    await admin_page.evaluate("theme => document.documentElement.dataset.theme = theme", theme)
    await admin_page.keyboard.press("Control+k")
    await admin_page.get_by_role("combobox").fill("arti " + "long name " * 30)
    box = await admin_page.get_by_role("dialog").bounding_box()
    assert box["x"] >= 0
    assert box["x"] + box["width"] <= 390
    assert box["y"] + box["height"] <= 844
    assert await admin_page.locator("#djangonaut").evaluate(
        "el => el.scrollWidth <= el.clientWidth"
    )
    assert await admin_page.locator("#djangonaut").evaluate(
        "el => getComputedStyle(el).backgroundColor === "
        "getComputedStyle(document.body).backgroundColor"
    )

    await admin_page.get_by_role("combobox").fill("?")
    await expect(admin_page.get_by_role("region", name="Query help")).to_be_visible()
    assert await admin_page.locator("#djangonaut").evaluate(
        "el => el.scrollWidth <= el.clientWidth"
    )


async def test_manifest_static_assets_without_unhashed_files(admin_page, settings, tmp_path):
    settings.STATIC_ROOT = tmp_path
    settings.STORAGES = {
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage",
        },
    }
    await sync_to_async(call_command)("collectstatic", interactive=False, verbosity=0)
    for name in ("palette.js", "search.js", "palette.css"):
        (tmp_path / "djangonaut" / name).unlink()

    async def static_response(route):
        name = urlsplit(route.request.url).path.removeprefix("/static/")
        path = tmp_path / name
        if path.is_file():
            await route.fulfill(path=path, content_type=mimetypes.guess_type(path)[0])
        else:
            await route.fulfill(status=404)

    await admin_page.context.route("http://testserver/static/**", static_response)
    await admin_page.goto("http://testserver/admin/")
    await admin_page.keyboard.press("Control+k")
    query = admin_page.get_by_role("combobox")
    await query.fill("arti#42")
    await expect(admin_page.get_by_role("option")).to_contain_text("Open record #42")
