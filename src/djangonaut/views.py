from difflib import SequenceMatcher

from django.contrib import admin
from django.http import Http404, JsonResponse
from django.urls import NoReverseMatch, reverse
from django.views.decorators.http import require_GET

from .parser import parse

MAX_RESULTS = 20


def _score(query: str, candidate: str) -> float:
    if not query:
        return 0.5
    c = candidate.lower()
    if c == query:
        return 1.0
    if c.startswith(query):
        return 0.9
    if query in c:
        return 0.75
    return SequenceMatcher(None, query, c).ratio()


def _iter_models(request):
    for app in admin.site.get_app_list(request):
        for m in app["models"]:
            yield app, m


def _change_url(model_cls, pk: str) -> str:
    meta = model_cls._meta
    return reverse(f"admin:{meta.app_label}_{meta.model_name}_change", args=[pk])


def _results_for_model(request, parsed):
    head = parsed.head
    scored = []
    for app, m in _iter_models(request):
        model_cls = m.get("model")
        perms = m.get("perms", {})
        if not perms.get("view") and not perms.get("change"):
            continue

        object_name = m["object_name"].lower()
        verbose_name = str(m["name"]).lower()
        s = max(_score(head, object_name), _score(head, verbose_name))
        if head and s < 0.4:
            continue

        scored.append((s, app, m, model_cls))

    scored.sort(key=lambda x: x[0], reverse=True)

    results = []
    for score, app, m, model_cls in scored[:MAX_RESULTS]:
        app_label = app["app_label"]
        name = m["name"]
        object_name = m["object_name"]
        changelist = m["admin_url"]
        add_url = m.get("add_url")
        perms = m.get("perms", {})

        if parsed.action == "list":
            results.append({
                "label": str(name),
                "hint": f"{app_label}.{object_name} — list",
                "url": changelist,
                "icon": "list",
            })
        elif parsed.action == "search":
            results.append({
                "label": f"{name}: “{parsed.term}”",
                "hint": f"{app_label}.{object_name} — search",
                "url": f"{changelist}?q={parsed.term}",
                "icon": "search",
            })
        elif parsed.action == "add" and perms.get("add") and add_url:
            results.append({
                "label": f"Add {name}",
                "hint": f"{app_label}.{object_name} — new",
                "url": add_url,
                "icon": "plus",
            })
        elif parsed.action == "change" and model_cls is not None and perms.get("change"):
            try:
                url = _change_url(model_cls, parsed.pk)
            except NoReverseMatch:
                continue
            results.append({
                "label": f"{name} #{parsed.pk}",
                "hint": f"{app_label}.{object_name} — edit",
                "url": url,
                "icon": "edit",
            })
    return results


def _results_for_app(request, parsed):
    head = parsed.head
    scored = []
    for app in admin.site.get_app_list(request):
        label = app["app_label"].lower()
        name = str(app["name"]).lower()
        s = max(_score(head, label), _score(head, name))
        if head and s < 0.4:
            continue
        scored.append((s, app))

    scored.sort(key=lambda x: x[0], reverse=True)

    results = []
    for _score_val, app in scored[:MAX_RESULTS]:
        try:
            url = reverse("admin:app_list", args=[app["app_label"]])
        except NoReverseMatch:
            url = app.get("app_url") or ""
        results.append({
            "label": str(app["name"]),
            "hint": f"@{app['app_label']} — app index",
            "url": url,
            "icon": "folder",
        })
    return results


@require_GET
def commands(request):
    user = getattr(request, "user", None)
    if not (user and user.is_authenticated and user.is_staff):
        raise Http404

    parsed = parse(request.GET.get("q", ""))

    if parsed.kind == "app":
        results = _results_for_app(request, parsed)
    else:
        results = _results_for_model(request, parsed)

    return JsonResponse({"results": results})
