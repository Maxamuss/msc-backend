from django.db import models

from core.models import BaseModel


class Package(BaseModel):
    package_name = models.CharField(max_length=255)

    def __str__(self):
        return self.package_name
