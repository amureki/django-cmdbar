# djangonaut

Raycast-style command palette for Django. Press `Cmd+K` anywhere on your site while logged in as staff and jump to any admin page.

## Install

```sh
pip install djangonaut
```

```python
# settings.py
INSTALLED_APPS = [..., "djangonaut"]
MIDDLEWARE = [..., "djangonaut.middleware.PaletteMiddleware"]
```

```python
# urls.py
from django.urls import include, path

urlpatterns = [
    ...,
    path("djangonaut/", include("djangonaut.urls")),
]
```

## Syntax

- `User` — changelist for `auth.User`
- `User rick` — changelist filtered with `?q=rick`
- `User #42` — change page for pk 42
- `User +` — add page
- `@auth` — the `auth` app index

Fuzzy-matching on model names. `?rick` is accepted as an alias for ` rick`.

## Keys

- `Cmd+K` / `Ctrl+K` — toggle palette
- `Esc` — close
- `↑ / ↓` — move
- `Enter` — open
- `Cmd+Enter` — open in new tab
