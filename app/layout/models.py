from django.db import models

from core.models import BaseModel


class Page(BaseModel):
    """
    Model to store the layout of a page for a given model.
    """

    model = models.ForeignKey(
        'models.Model', on_delete=models.CASCADE, related_name='pages'
    )
    page_name = models.CharField(max_length=255)
    layout = models.JSONField(default=list)


class Navigation(BaseModel):
    """
    Model to store the navigation layout (i.e. sidebar links) for the application.
    """

    layout = models.JSONField(default=dict)


class Style(BaseModel):
    """
    Model to store the style schema for the application.
    """

    application_logo = models.ImageField()
    application_favicon = models.ImageField()
    primary_color = models.CharField(max_length=7)
    secondary_color = models.CharField(max_length=7)
