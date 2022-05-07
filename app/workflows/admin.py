from django.contrib import admin

from .models import Workflow


@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    pass
