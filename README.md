# Djangonaut

Keyboard navigation for Django admin. Press Cmd+K or Ctrl+K to open model lists,
filtered searches, and individual records.

Requires Python 3.14 or 3.15 and Django 6.1. Uses plain JavaScript and CSS, with no
frontend dependencies, build step, middleware, or additional URLs.

## Install

```sh
uv pip install djangonaut
```

Put `djangonaut` **before** `django.contrib.admin` in `INSTALLED_APPS` so Django
loads its admin template extension:

```python
INSTALLED_APPS = [
    # ...
    "djangonaut",
    "django.contrib.admin",
    # ...
]
```

Keep the project's existing admin URL configuration.

## Queries

For Django's built-in User model:

| Query | Result |
| --- | --- |
| `user` | User list |
| `user#42` | User with primary key 42 |
| `user #42` | Same record |
| `user alice` | User list filtered with `?q=alice` |
| `user +` | User creation form |
| `auth.User` | User list in the auth app |

Type `?` or click the **?** button to show a short syntax guide.

Matching ignores case and accents and supports abbreviations. Use `auth.User` or
`auth User` to distinguish models from different apps.

Names containing spaces use the same syntax, such as `Article groups#42`.

Search requires configured admin search fields. Use `#` for an exact primary key;
`user 42` performs a text search. String and UUID primary keys are supported.

The palette shows models and actions allowed by your admin permissions. Record
names are not previewed; Django checks access when you open a destination.

## Keyboard

- Cmd+K or Ctrl+K opens or closes the palette.
- Up and Down select a destination.
- Enter opens the selected destination.
- Cmd+Enter or Ctrl+Enter opens it in a new tab.
- Escape closes the palette.

The palette follows Django admin's light or dark theme.

## Custom admin sites and templates

Custom admin sites and URL prefixes are supported. Each palette lists its site's
models.

If your project overrides `admin/base_site.html`, extend `admin/base_site.html`
and preserve `block.super` in the `extrastyle` and `extrabody` blocks.

For templates that bypass that chain, add the assets and tag explicitly instead
of using Djangonaut's template extension:

```django
{% extends "admin/base.html" %}
{% load static djangonaut %}

{% block extrastyle %}
  {{ block.super }}
  <link rel="stylesheet" href="{% static 'djangonaut/palette.css' %}">
{% endblock %}

{% block extrabody %}
  {{ block.super }}
  {% djangonaut %}
{% endblock %}
```

For a custom admin view that does not expose its site through Django's normal
view wrapper, put the `AdminSite` instance in the template context and pass it to
the tag:

```django
{% djangonaut site=admin_site %}
```

## Development

```sh
uv sync --python 3.14
uv run playwright install chromium
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv build
```

Djangonaut is under development. Its integration and query syntax can change
before the first stable release.
