from pathlib import Path
from urllib.parse import quote, urlencode

import pytest


@pytest.fixture
async def search_page(page):
    source = Path(__file__).parents[1] / "src/djangonaut/static/djangonaut/search.js"
    await page.evaluate(
        "async url => { window.searchModule = await import(url); }",
        "data:text/javascript," + quote(source.read_text()),
    )
    return page


@pytest.fixture
def catalog():
    return {
        "models": [
            {
                "name": "Articles",
                "singular": "article",
                "key": "tests.article",
                "keywords": ["Article", "article"],
                "list_url": "/admin/tests/article/",
                "change_url": "/admin/tests/article/__djangonaut_pk__/change/",
                "add_url": "/admin/tests/article/add/",
                "searchable": True,
            },
            {
                "name": "Departments",
                "singular": "department",
                "key": "tests.department",
                "keywords": ["Department", "department"],
                "list_url": "/admin/tests/department/",
                "change_url": "/admin/tests/department/__djangonaut_pk__/change/",
                "add_url": "/admin/tests/department/add/",
                "searchable": False,
            },
        ],
        "pk_placeholder": "__djangonaut_pk__",
        "quote_map": {},
        "labels": {
            "list": "",
            "search": "Search for %(value)s",
            "change": "Open record #%(value)s",
            "record_id": "Enter a record ID",
            "add": "Add %(value)s",
        },
    }


@pytest.fixture
def search(search_page, catalog):
    async def results(query):
        return await search_page.evaluate(
            "({query, catalog}) => searchModule.getResults(query, catalog)",
            {"query": query, "catalog": catalog},
        )

    return results


@pytest.mark.parametrize(
    ("query", "url", "detail"),
    [
        (" arti ", "/admin/tests/article/", ""),
        ("arti#42", "/admin/tests/article/42/change/", "Open record #42"),
        ("arti #42", "/admin/tests/article/42/change/", "Open record #42"),
        ("arti# 42 ", "/admin/tests/article/42/change/", "Open record #42"),
        ("arti#", None, "Enter a record ID"),
        ("arti #", None, "Enter a record ID"),
        ("arti# ", None, "Enter a record ID"),
        ("arti alice", "/admin/tests/article/?q=alice", "Search for alice"),
        ("arti\talice smith", "/admin/tests/article/?q=alice+smith", "Search for alice smith"),
        ("arti alice#42", "/admin/tests/article/?q=alice%2342", "Search for alice#42"),
        ("arti 42", "/admin/tests/article/?q=42", "Search for 42"),
        ("arti +", "/admin/tests/article/add/", "Add article"),
        ("tests.Article#42", "/admin/tests/article/42/change/", "Open record #42"),
    ],
)
async def test_query_syntax(search, query, url, detail):
    results = await search(query)
    assert [(result["key"], result["url"], result["detail"]) for result in results] == [
        ("tests.article", url, detail)
    ]


@pytest.mark.parametrize("query", ["", " \t "])
async def test_empty_query_lists_models(search, query):
    results = await search(query)
    assert [(result["key"], result["url"], result["detail"]) for result in results] == [
        ("tests.article", "/admin/tests/article/", ""),
        ("tests.department", "/admin/tests/department/", ""),
    ]


@pytest.mark.parametrize("query", ["arti", "ARTI", "ace", "tests.article", "árti"])
async def test_model_matching(search, query):
    assert (await search(query))[0]["url"] == "/admin/tests/article/"


async def test_exact_match_ranks_before_prefixes(search, catalog):
    article = catalog["models"][0]
    catalog["models"] = [
        {
            **article,
            "name": "Article notes",
            "key": "tests.articlenote",
            "keywords": ["ArticleNote"],
        },
        article,
    ]
    assert [result["key"] for result in await search("article")] == [
        "tests.article",
        "tests.articlenote",
    ]


async def test_all_model_lists_remain_available(search, catalog):
    model = catalog["models"][0]
    catalog["models"] = [
        {**model, "name": f"Model {i}", "key": f"app.model{i}", "keywords": [f"Model{i}"]}
        for i in range(30)
    ]
    assert len(await search("")) == 30


@pytest.mark.parametrize("query", ["Article groups", "Article gr", "e groups"])
async def test_multiword_model_names_remain_navigation_queries(search, catalog, query):
    article = catalog["models"][0]
    catalog["models"] = [
        {**article, "name": "Articles", "key": "content.article", "keywords": ["Article"]},
        {
            **article,
            "name": "Article groups",
            "key": "content.group",
            "keywords": ["Group"],
            "list_url": "/admin/content/group/",
        },
    ]
    results = await search(query)
    assert results[0]["url"] == "/admin/content/group/"
    assert results[0]["detail"] == ""
    if query == "Article gr":
        assert any("?q=" in result["url"] for result in results)


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("art", ["content.article", "content.group"]),
        ("Article", ["content.article", "content.group"]),
        ("content.sub", ["content.subscription"]),
    ],
)
async def test_app_names_only_match_explicitly_qualified_queries(search, catalog, query, expected):
    model = catalog["models"][0]
    catalog["models"] = [
        {
            **model,
            "name": "Subscriptions",
            "key": "content.subscription",
            "keywords": ["Subscription"],
        },
        {**model, "name": "Article groups", "key": "content.group", "keywords": ["Group"]},
        {**model, "name": "Articles", "key": "content.article", "keywords": ["Article"]},
    ]
    assert [result["key"] for result in await search(query)] == expected


@pytest.mark.parametrize("value", ["alice & bob + café/#42", "alice $& $' $` $$"])
async def test_search_url_encoding(search, value):
    result = (await search(f"arti {value}"))[0]
    assert result["url"] == f"/admin/tests/article/?{urlencode({'q': value})}"
    assert result["detail"] == f"Search for {value}"


async def test_add_and_unsupported_operations(search):
    assert (await search("arti +"))[0]["url"] == "/admin/tests/article/add/"
    assert await search("department alice") == []
    assert await search("zzzzzz") == []


async def test_space_qualified_model_name(search):
    assert (await search("tests article"))[0]["url"] == "/admin/tests/article/"


@pytest.mark.parametrize(
    ("query", "destination"),
    [
        ("Article groups#42", "/admin/content/group/42/change/"),
        ("Article groups #42", "/admin/content/group/42/change/"),
        ("árticle GROUPS#42", "/admin/content/group/42/change/"),
        ("Article groups +", "/admin/content/group/add/"),
        ("Article groups alice", "/admin/content/group/?q=alice"),
        ("Article groups alice#42", "/admin/content/group/?q=alice%2342"),
        ("content group#42", "/admin/content/group/42/change/"),
        ("Article groups archive#42", "/admin/content/archive/42/change/"),
    ],
)
async def test_longest_multiword_model_head(search, catalog, query, destination):
    article = catalog["models"][0]
    catalog["models"] = [
        {**article, "name": "Articles", "key": "content.article", "keywords": ["Article"]},
        *[
            {
                **article,
                "name": name,
                "key": f"content.{model}",
                "keywords": [model],
                "list_url": f"/admin/content/{model}/",
                "change_url": f"/admin/content/{model}/__djangonaut_pk__/change/",
                "add_url": f"/admin/content/{model}/add/",
            }
            for name, model in [("Article groups", "group"), ("Article groups archive", "archive")]
        ],
    ]
    results = await search(query)
    assert results[0]["url"] == destination
    assert all(result["key"] != "content.article" for result in results)


async def test_multiword_incomplete_pk_and_unavailable_actions(search, catalog):
    catalog["models"][0].update(
        name="Article groups", keywords=["Group"], searchable=False, add_url=None
    )
    result = (await search("Article groups#"))[0]
    assert result["url"] is None
    assert result["detail"] == "Enter a record ID"
    assert await search("Article groups alice") == []
    assert await search("Article groups +") == []
