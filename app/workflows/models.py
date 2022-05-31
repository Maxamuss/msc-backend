from django.db import models

from core.models import BaseModel


class Workflow(BaseModel):
    model_schema = models.ForeignKey(
        'db.ModelSchema', on_delete=models.CASCADE, related_name='workflows'
    )
    workflow_name = models.CharField(max_length=255)
    definition = models.JSONField(default=dict)

    def __str__(self):
        return self.workflow_name


class Function(BaseModel):
    function_name = models.CharField(max_length=255, blank=False)
    is_standard = models.BooleanField(default=False)

    def __str__(self):
        return self.function_name
