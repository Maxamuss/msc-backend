from django.contrib import admin

from .models import Model, ModelSchema


@admin.register(Model)
class ModelAdmin(admin.ModelAdmin):
    pass


@admin.register(ModelSchema)
class ModelSchemaAdmin(admin.ModelAdmin):
    pass
