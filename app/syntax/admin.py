from django.contrib import admin

from .models import Release, ReleaseChange


class ReleaseChangeInline(admin.TabularInline):
    model = ReleaseChange
    fk_name = 'parent_release'
    extra = 0


@admin.register(Release)
class ReleaseAdmin(admin.ModelAdmin):
    inlines = [ReleaseChangeInline]
    list_display = ['release_version', 'current_release']
