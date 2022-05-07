from django.contrib import admin

from .models import Function


@admin.register(Function)
class FunctionAdmin(admin.ModelAdmin):
    pass
