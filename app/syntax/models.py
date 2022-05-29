from django.db import models

from core.models import BaseModel


class Syntax(BaseModel):
    """
    Model to store the syntax for a given model (e.g. ModelSchema, Page, Workflow etc.). This model
    makes it possible for the version controlling of syntax.
    """

    syntax_json = models.JSONField()
