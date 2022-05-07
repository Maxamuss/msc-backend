from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from core.models import BaseModel


class Page(BaseModel):
    """
    Model to store the layout of a page for a given model.
    """

    class Meta:
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]

    # model = models.ForeignKey('db.ModelSchema', on_delete=models.CASCADE, related_name='pages')

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    page_name = models.CharField(max_length=255)
    layout = models.JSONField(default=list)

    def __str__(self):
        return self.page_name


class Navigation(BaseModel):
    """
    Model to store the navigation layout (i.e. sidebar links) for the application.
    """

    layout = models.JSONField(default=dict)

    def __str__(self):
        return str(self.id)


class Style(BaseModel):
    """
    Model to store the style schema for the application.
    """

    application_logo = models.ImageField()
    application_favicon = models.ImageField()
    primary_color = models.CharField(max_length=7)
    secondary_color = models.CharField(max_length=7)

    def __str__(self):
        return str(self.id)
