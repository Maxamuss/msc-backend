from django.contrib import admin

from .models import ModelSchema


@admin.register(ModelSchema)
class ModelSchemaAdmin(admin.ModelAdmin):
    pass
