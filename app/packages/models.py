from django.db import models

from core.models import BaseModel


class Package(BaseModel):
    package_name = models.CharField(max_length=255)
