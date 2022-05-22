from django.contrib.contenttypes.models import ContentType

from rest_framework import serializers

from layout.models import Page
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

        model_content_type = ContentType.objects.get(model=model_schema._meta.model_name)

        for page_name, definition in MODEL_DEFAULT_PAGES.items():
            Page.objects.create(
                page_name=page_name,
                layout=definition,
                model=model_content_type,
                model_schema=model_schema,
            )

        return model_schema


class FieldSchemaSerializer(serializers.ModelSerializer):
    field_type = serializers.CharField(required=True)

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
