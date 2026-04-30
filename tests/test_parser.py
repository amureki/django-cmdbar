from djangonaut.parser import parse


def test_empty():
    p = parse("")
    assert p.kind == "empty"
    assert p.action == "list"


def test_model_only():
    p = parse("User")
    assert p.kind == "model" and p.head == "user" and p.action == "list"


def test_model_search_space():
    p = parse("User rick")
    assert p.kind == "model" and p.action == "search" and p.term == "rick"


def test_model_search_querystring():
    p = parse("User?rick")
    assert p.action == "search" and p.term == "rick"


def test_model_add():
    p = parse("User +")
    assert p.action == "add"


def test_model_change():
    p = parse("User #42")
    assert p.action == "change" and p.pk == "42"


def test_app_index():
    p = parse("@auth")
    assert p.kind == "app" and p.head == "auth" and p.action == "index"
