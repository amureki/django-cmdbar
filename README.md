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

Keep the project's existing admin URL configuration. Run `collectstatic` as usual
when deploying.

## Queries

For Django's built-in User model:

| Query | Destination |
| --- | --- |
| `user` | User list |
| `user#42` | User with primary key 42 |
| `user #42` | Same record |
| `user alice` | User list filtered with `?q=alice` |
| `user +` | User creation form |
| `auth.User` | User list in the accounts app |

Type `?` to show a short syntax guide. Clear it to return to model navigation.

Matching ignores case and accents. Exact model names rank first, followed by
prefixes, substrings, and abbreviated character sequences. Results include the
app and model name to distinguish models with similar names. App names only match
when the query includes a dot, such as `auth.User`. Shorter model-name
prefix matches rank ahead of longer ones. An empty query shows all available
model lists.

Names containing spaces, such as `Talk series`, remain model navigation queries.
When the same input can also mean a filtered search, model-name matches appear
before search suggestions.

Search is available for models whose `ModelAdmin.get_search_fields(request)`
returns fields. Numeric text without `#`, such as `user 42`, is a search term.
String and UUID primary keys work with `#` too. Djangonaut applies Django admin's
primary-key quoting before URL encoding.
Typing `#` keeps matching models visible and prompts for a record ID. Navigation
waits until the ID is present.

The palette does not fetch records or preview names. It builds links locally from
model metadata. Django's destination views check record existence, queryset
restrictions, and object permissions. The palette uses the active admin site's
model and module permissions, omits unavailable operations, and stays out of
login pages and related-object popups.

## Keyboard

- Cmd+K or Ctrl+K opens or closes the palette.
- Up and Down select a destination.
- Enter opens the selected destination.
- Cmd+Enter or Ctrl+Enter opens it in a new tab.
- Escape or the Close button closes the palette and restores focus.

The palette uses a native modal dialog and Django admin's theme variables. It
follows the admin's selected light or dark theme, including manual theme changes.

## Custom admin sites and templates

Standard `AdminSite` and `ModelAdmin` views work with custom site names and URL
prefixes. Each palette lists only models registered with its active site.

If your project overrides `admin/base_site.html`, extend `admin/base_site.html`
and preserve `block.super` in the `extrastyle` and `extrabody` blocks. Django will
include Djangonaut's template through the normal template inheritance chain.

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

Include the tag once per page. It renders nothing for users without access to the
site or when no model navigation is available.

## Development

```sh
uv sync --python 3.14
uv run playwright install chromium
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv build
```

The browser tests use Chromium and route requests through Django's test client.
They do not need a running development server. CI tests Python 3.14 and 3.15.

Djangonaut is under development. Its integration and query syntax can change
before the first stable release.
