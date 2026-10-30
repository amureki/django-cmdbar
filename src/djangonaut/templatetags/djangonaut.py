from string import punctuation

from django import template
from django.contrib.admin import AdminSite
from django.contrib.admin.utils import quote
from django.urls import NoReverseMatch, reverse
from django.utils.translation import gettext as _

register = template.Library()
PK_PLACEHOLDER = "__djangonaut_pk__"


@register.inclusion_tag("djangonaut/palette.html", takes_context=True)
def djangonaut(context, site: AdminSite | None = None):
    request = getattr(context, "request", None)
    if request is None or context.get("is_popup"):
        return {}

    if site is None:
        view = request.resolver_match.func if request.resolver_match else None
        model_admin = getattr(view, "model_admin", None)
        site = getattr(view, "admin_site", None) or getattr(model_admin, "admin_site", None)

    if site is None or not site.has_permission(request):
        return {}

    models = []
    for app in site.get_app_list(request):
        for item in app["models"]:
            model = item["model"]
            opts = model._meta
            model_admin = site.get_model_admin(model)
            list_url = item.get("admin_url")
            add_url = item.get("add_url")
            if not list_url and not add_url:
                continue

            change_url = None
            if list_url:
                try:
                    change_url = reverse(
                        f"admin:{opts.app_label}_{opts.model_name}_change",
                        args=[PK_PLACEHOLDER],
                        current_app=site.name,
                    )
                except NoReverseMatch:
                    pass

            models.append(
                {
                    "name": str(item["name"]),
                    "singular": str(opts.verbose_name),
                    "key": opts.label_lower,
                    "keywords": [opts.object_name, opts.model_name, str(opts.verbose_name)],
                    "list_url": list_url,
                    "add_url": add_url,
                    "change_url": change_url,
                    "searchable": bool(list_url and model_admin.get_search_fields(request)),
                }
            )

    if not models:
        return {}

    return {
        "palette": {
            "models": models,
            "pk_placeholder": PK_PLACEHOLDER,
            "quote_map": {char: quote(char) for char in punctuation + "\n" if quote(char) != char},
            "labels": {
                "list": "",
                "search": _("Search for %(value)s"),
                "change": _("Open record #%(value)s"),
                "record_id": _("Enter a record ID"),
                "add": _("Add %(value)s"),
            },
        },
    }
