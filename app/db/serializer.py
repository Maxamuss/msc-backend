from rest_framework import serializers

from layout.models import Page
from syntax.utils import replace_syntax
from .constants import MODEL_DEFAULT_PAGES
from .models import FieldSchema, ModelSchema


class ModelSchemaSerializer(serializers.ModelSerializer):
    """
    Serializer for user defined models.
    """

    class Meta:
        model = ModelSchema
        fields = ['id', 'name']

    def create(self, validated_data):
        model_schema = ModelSchema.objects.create(name=validated_data['name'])

        for page_name, definition in MODEL_DEFAULT_PAGES.items():
            # Replace ${model} with name of this model.
            parsed_syntax = replace_syntax(definition, '${model}', model_schema.model_name_lower)

            Page.objects.create(
                page_name=page_name,
                layout=parsed_syntax,
                model_schema=model_schema,
            )

        return model_schema


class FieldSchemaSerializer(serializers.ModelSerializer):
    field_type = serializers.CharField(required=True, write_only=True)

    class Meta:
        model = FieldSchema
        fields = ['id', 'name', 'model_schema', 'field_type']

    def create(self, validated_data):
        if validated_data['field_type'] == 'text':
            class_name = 'django.db.models.TextField'
        else:
            class_name = 'django.db.models.TextField'

        field_schema = FieldSchema.objects.create(
            name=validated_data['name'],
            model_schema=validated_data['model_schema'],
            class_name=class_name,
        )

        return field_schema
