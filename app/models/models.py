from django.db import models

from dynamic_models.models import ModelSchema

from core.models import BaseModel


class Model(BaseModel):
    class Meta:
        indexes = [
            models.Index(fields=['model_name']),
        ]

    model_name = models.CharField(max_length=255)
    model_schema = models.OneToOneField(ModelSchema, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.model_name
