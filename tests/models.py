from django.db import models


class Article(models.Model):
    id = models.CharField(primary_key=True, max_length=120)
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Department(models.Model):
    name = models.CharField(max_length=200)
