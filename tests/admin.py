from django.contrib import admin

from .models import Article, Department


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    search_fields = ("name",)


admin.site.register(Department)

backoffice = admin.AdminSite(name="backoffice")
backoffice.register(Article, ArticleAdmin)
