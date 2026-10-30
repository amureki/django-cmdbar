from django.contrib import admin
from django.http import HttpResponse
from django.urls import path

from .admin import backoffice

urlpatterns = [
    path("admin/", admin.site.urls),
    path("backoffice/", backoffice.urls),
    path("", lambda request: HttpResponse("<html><body>Public page</body></html>")),
]
