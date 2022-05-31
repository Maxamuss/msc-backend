from django.contrib import admin

from .models import Function, Workflow


@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    pass


@admin.register(Function)
class FunctionAdmin(admin.ModelAdmin):
    pass
