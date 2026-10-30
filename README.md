# Django CmdBar

[![Build](https://img.shields.io/github/actions/workflow/status/amureki/django-cmdbar/tests.yml?branch=main)](https://github.com/amureki/django-cmdbar/actions/workflows/tests.yml)
[![Latest PyPI version](https://img.shields.io/pypi/v/django-cmdbar.svg)](https://pypi.org/project/django-cmdbar/)

A navigation palette for Django admin. Press Cmd+K or Ctrl+K to find models,
search records, or jump to a record by primary key.

Supports maintained [Python](https://devguide.python.org/versions/) and
[Django](https://www.djangoproject.com/download/#supported-versions) releases.
Uses plain JavaScript and CSS, with no frontend dependencies, build step,
middleware, or additional URLs.

**Start with your models:** press Cmd+K or Ctrl+K to browse the models you can access.

![Django CmdBar's empty search showing Articles, Departments, Groups, and Users.](https://raw.githubusercontent.com/amureki/django-cmdbar/main/docs/images/django-cmdbar-models.png)

**Search records:** `user alice` opens the Users list filtered by “alice”.

![Django CmdBar showing the query user alice and the result Search for alice.](https://raw.githubusercontent.com/amureki/django-cmdbar/main/docs/images/django-cmdbar-search.png)

**Jump to a record:** `user#42` opens the user with primary key 42.

![Django CmdBar showing the query user#42 and the result Open record #42.](https://raw.githubusercontent.com/amureki/django-cmdbar/main/docs/images/django-cmdbar-record.png)

<details>
<summary>Built-in query guide</summary>

![Django CmdBar's query guide showing commands to open model lists, find records, search, and add records.](https://raw.githubusercontent.com/amureki/django-cmdbar/main/docs/images/django-cmdbar.png)

</details>

## Install

**Install the package, add one app, and you're ready.**

```sh
uv pip install django-cmdbar
```

Add `django_cmdbar` **before** `django.contrib.admin` in `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ...
    "django_cmdbar",
    "django.contrib.admin",
    # ...
]
```

Open Django admin and press **Cmd+K** or **Ctrl+K**. That's it—no extra settings,
URLs, middleware, or migrations to configure.

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
of using Django CmdBar's template extension:

```django
{% extends "admin/base.html" %}
{% load static django_cmdbar %}

{% block extrastyle %}
  {{ block.super }}
  <link rel="stylesheet" href="{% static 'django_cmdbar/palette.css' %}">
{% endblock %}

{% block extrabody %}
  {{ block.super }}
  {% django_cmdbar %}
{% endblock %}
```

For a custom admin view that does not expose its site through Django's normal
view wrapper, put the `AdminSite` instance in the template context and pass it to
the tag:

```django
{% django_cmdbar site=admin_site %}
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

Django CmdBar is under development. Its integration and query syntax can change
before the first stable release.
