from rest_framework import serializers

from layout.models import Page
from .constants import MODEL_DEFAULT_PAGES
from .models import FieldSchema, ModelSchema


class ModelFieldSerializer(serializers.Serializer):
    DATA_TYPES = (
        ('character', 'character'),
        ('text', 'text'),
        ('integer', 'integer'),
        ('float', 'float'),
        ('boolean', 'boolean'),
        ('date', 'date'),
    )

    name = serializers.CharField(max_length=255, required=True)
    data_type = serializers.ChoiceField(DATA_TYPES, required=True)


class ModelSerializer(serializers.Serializer):
    """
    Serializer for user defined models.
    """

    model_name = serializers.CharField(max_length=255)
    fields = ModelFieldSerializer(many=True)

    def create(self, validated_data):
        # Check if model already exists or create.
        model_schema, created = ModelSchema.objects.get_or_create(
            name=validated_data['model_name']
        )

        if created:
            for field in validated_data['fields']:
                field_schema, created = FieldSchema.objects.get_or_create(
                    model_schema=model_schema,
                    name=field['name'],
                    data_type=field['data_type'],
                    max_length=255,
                )

            # Create Model object for this new model.
            model = Model.objects.create(
                model_name=validated_data['model_name'], model_schema=model_schema
            )

            for page_name, definition in MODEL_DEFAULT_PAGES.items():
                Page.objects.create(model=model, page_name=page_name, definition=definition)

        return model_schema


"""
{"model_name":"Test3", "fields": [{"name": "test", "data_type": "text"},{"name": "test2", "data_type": "boolean"}]}
"""
