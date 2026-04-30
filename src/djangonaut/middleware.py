from django.template.loader import render_to_string
from django.urls import NoReverseMatch, reverse


class PaletteMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        user = getattr(request, "user", None)
        if not (user and user.is_authenticated and user.is_staff):
            return response

        ctype = response.get("Content-Type", "")
        if "text/html" not in ctype:
            return response

        if getattr(response, "streaming", False) or not hasattr(response, "content"):
            return response

        try:
            commands_url = reverse("djangonaut:commands")
        except NoReverseMatch:
            return response

        body = response.content
        marker = b"</body>"
        idx = body.rfind(marker)
        if idx == -1:
            return response

        snippet = render_to_string(
            "djangonaut/inject.html",
            {"commands_url": commands_url},
        ).encode("utf-8")

        response.content = body[:idx] + snippet + body[idx:]
        if response.has_header("Content-Length"):
            response["Content-Length"] = str(len(response.content))
        return response
