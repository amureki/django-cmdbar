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
    ("query", "expected"),
    [
        ("", {"head": "", "action": "list", "value": ""}),
        (" arti ", {"head": "arti", "action": "list", "value": ""}),
        ("arti#42", {"head": "arti", "action": "change", "value": "42"}),
        ("arti #42", {"head": "arti", "action": "change", "value": "42"}),
        ("arti# 42 ", {"head": "arti", "action": "change", "value": "42"}),
        ("arti#", {"head": "arti", "action": "change", "value": ""}),
        ("arti #", {"head": "arti", "action": "change", "value": ""}),
        ("arti# ", {"head": "arti", "action": "change", "value": ""}),
        ("arti alice", {"head": "arti", "action": "search", "value": "alice"}),
        ("arti\talice smith", {"head": "arti", "action": "search", "value": "alice smith"}),
        ("arti alice#42", {"head": "arti", "action": "search", "value": "alice#42"}),
        ("arti 42", {"head": "arti", "action": "search", "value": "42"}),
        ("arti +", {"head": "arti", "action": "add", "value": ""}),
        ("tests.Article#42", {"head": "tests.Article", "action": "change", "value": "42"}),
    ],
)
async def test_query_syntax(search_page, query, expected):
    result = await search_page.evaluate("query => searchModule.parseQuery(query)", query)
    assert result == expected


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


@pytest.mark.parametrize("query", ["Talk series", "Talk se", "k series"])
async def test_multiword_model_names_remain_navigation_queries(search, catalog, query):
    article = catalog["models"][0]
    catalog["models"] = [
        {**article, "name": "Talks", "key": "talks.talk", "keywords": ["Talk"]},
        {
            **article,
            "name": "Talk series",
            "key": "talks.series",
            "keywords": ["Series"],
            "list_url": "/admin/talks/series/",
        },
    ]
    results = await search(query)
    assert results[0]["url"] == "/admin/talks/series/"
    assert results[0]["detail"] == ""
    if query.startswith("Talk"):
        assert any("?q=" in result["url"] for result in results)


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("tal", ["talks.talk", "talks.series"]),
        ("Talk", ["talks.talk", "talks.series"]),
        ("talks.sub", ["talks.subscription"]),
    ],
)
async def test_app_names_only_match_explicitly_qualified_queries(search, catalog, query, expected):
    model = catalog["models"][0]
    catalog["models"] = [
        {
            **model,
            "name": "Subscriptions",
            "key": "talks.subscription",
            "keywords": ["Subscription"],
        },
        {**model, "name": "Talk series", "key": "talks.series", "keywords": ["Series"]},
        {**model, "name": "Talks", "key": "talks.talk", "keywords": ["Talk"]},
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
