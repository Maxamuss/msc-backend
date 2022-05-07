from uuid import uuid4

from django.db.models import UUIDField

from .apps import DBConfig


def dynamic_models_app_label():
    return DBConfig.name


def default_fields():
    return {
        'id': UUIDField(primary_key=True, default=uuid4, editable=False),
    }


def default_charfield_max_length():
    return 255


def cache_key_prefix():
    return 'models_schema_'


def cache_timeout():
    return 60 * 60 * 24  # 24 hours
