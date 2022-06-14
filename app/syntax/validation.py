from django.core.exceptions import ValidationError

from db.models import ModelSchema
from layout.models import Page
from packages.models import Package
from workflows.models import Function, Workflow


def validate_str(value, max_length=None, regex=None):
    try:
        str(value)
    except TypeError:
        raise

    if max_length:
        if len(value) > max_length:
            raise ValidationError('max_length')


MODELSCHEMA = [
    {
        'key': 'model_name',
        'validation': {
            'function': validate_str,
            'args': {
                'max_length': 255,
            },
        },
    },
    {
        'key': 'fields',
        'type': list,
    },
]
PAGE = [
    {'key': 'page_name', 'type': str},
]
FUNCTION = [
    {'key': 'function_name', 'type': str},
]


validation_mappings = {
    ModelSchema._meta.model_name: MODELSCHEMA,
    Page._meta.model_name: 'pages',
    # Package._meta.model_name: 'packages',
    # Workflow._meta.model_name: 'workflows',
    Function._meta.model_name: FUNCTION,
}


def validate_release_change(release_change):
    model_validations = validation_mappings.get(release_change.model_type)

    if not model_validations:
        raise ValidationError('Invalid model_type')

    syntax = release_change.syntax_json

    for validation in model_validations:
        if validation['key'] not in syntax:
            raise ValidationError(f"Missing {validation['key']} key in syntax")

        value = syntax[validation['key']]

        if validation.get('required', False):
            if not value:
                raise ValidationError(f"{validation['key']} syntax key requires a valid value")
