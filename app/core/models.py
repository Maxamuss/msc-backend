import uuid

from django.db import models


class BaseModel(models.Model):
    """
    Base model in which all application defined models inherit from.

    Provides the functionality to query syntax for the model.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
