from django.db import models

from core.models import BaseModel


class Function(BaseModel):
    function_name = models.CharField(max_length=255, blank=False)
    is_standard = models.BooleanField(default=False)

    def __str__(self):
        return self.function_name
