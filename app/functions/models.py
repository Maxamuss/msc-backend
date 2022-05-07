from django.db import models

from core.models import BaseModel


class Function(BaseModel):
    function_name = models.CharField(max_length=255)
    is_standard = models.BooleanField(default=False)
