from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import CustomUserManager
from core.models import BaseModel


class User(BaseModel, AbstractUser):
    username = None
    email = models.EmailField('email address', unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email
