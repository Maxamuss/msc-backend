from django.contrib import admin

from dynamic_models.models import ModelSchema

from .models import Model


@admin.register(Model)
class ModelAdmin(admin.ModelAdmin):
    pass


@admin.register(ModelSchema)
class ModelSchemaAdmin(admin.ModelAdmin):
    pass
