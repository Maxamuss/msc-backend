from django.apps import apps
from django.core.cache import cache

from ..models import FieldSchema, ModelSchema
from ..utils import ModelRegistry

TEST_APP_LABEL = 'db'


def cleanup_cache():
    try:
        yield
    finally:
        cache.clear()


def cleanup_registry():
    """
    The app registry bleeds between tests. This fixture removes all dynamically
    declared models after each test.
    """
    try:
        yield
    finally:
        apps.all_models[TEST_APP_LABEL].clear()
        apps.register_model(TEST_APP_LABEL, ModelSchema)
        apps.register_model(TEST_APP_LABEL, FieldSchema)


def model_registry(model_schema):
    return ModelRegistry(model_schema.app_label)


def unsaved_model_schema():
    return ModelSchema(name='unsaved model')


def model_schema():
    return ModelSchema.objects.get_or_create(name='simple model')[0]


def another_model_schema():
    return ModelSchema.objects.get_or_create(name='another model')[0]


def field_schema(model_schema_=None):
    model_schema_ = model_schema_ or model_schema()

    return FieldSchema.objects.create(
        name='field', class_name='django.db.models.IntegerField', model_schema=model_schema_
    )
