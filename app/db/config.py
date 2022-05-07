from uuid import uuid4

from django.db import models

from .apps import DBConfig


def dynamic_models_app_label():
    return DBConfig.name


def default_fields():
    return {
        'id': models.UUIDField(primary_key=True, default=uuid4, editable=False),
        'created_at': models.DateTimeField(auto_now_add=True),
        'updated_at': models.DateTimeField(auto_now=True),
    }


def default_charfield_max_length():
    return 255


def cache_key_prefix():
    return 'db_schema_'


def cache_timeout():
    return 60 * 60 * 24  # 24 hours
