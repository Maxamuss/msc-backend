import uuid

from django.db import models

from mptt.models import MPTTModel, TreeForeignKey

from accounts.models import User
from core.models import BaseModel
from db.models import ModelSchema
from layout.models import Page
from packages.models import Package
from workflows.models import Function, Workflow


class ReleaseChangeType(models.TextChoices):
    CREATE = 'create'
    UPDATE = 'update'
    DELETE = 'delete'


class Release(MPTTModel):
    """
    This model stores an application version release. When a developer makes changes to their
    site, changes are applied to the staging area. They are not immediately applied to the site.
    When they are happy with the changes they have made, they can publish the changes by issuing a
    release. Each release holds a version of the site at a point in time and allows for releases to
    be restored from.
    """

    class MPTTMeta:
        order_insertion_by = ['release_version']

    release_version = models.CharField(max_length=10, unique=True)
    release_notes = models.TextField()
    released_at = models.DateTimeField(auto_now_add=True)
    released_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True)
    current_release = models.BooleanField(default=False)

    parent = TreeForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, related_name='children'
    )

    # Stores the syntax for all models for this release.
    modelschemas = models.JSONField(default=list)
    pages = models.JSONField(default=list)
    packages = models.JSONField(default=list)
    workflows = models.JSONField(default=list)
    functions = models.JSONField(default=list)

    field_mappings = {
        ModelSchema._meta.model_name: 'modelschemas',
        Page._meta.model_name: 'pages',
        Package._meta.model_name: 'packages',
        Workflow._meta.model_name: 'workflows',
        Function._meta.model_name: 'functions',
    }

    def __str__(self):
        return self.release_version

    def _apply_changes(self, syntax, changes):
        for change in changes:
            if change.model_type in syntax.keys():
                model_syntax = syntax[change.model_type]

                # Add id if does not already have one.
                if not change.object_id:
                    model_ids = [x['id'] for x in syntax[change.model_type]]
                    object_id = str(uuid.uuid4())
                    while object_id in model_ids or not object_id:
                        object_id = str(uuid.uuid4())
                    change.syntax_json['id'] = object_id

                if change.change_type == ReleaseChangeType.CREATE:
                    syntax[change.model_type].append(change.syntax_json)
                elif change.change_type == ReleaseChangeType.UPDATE:
                    syntax[change.model_type] = [
                        x for x in syntax[change.model_type] if x['id'] != str(change.object_id)
                    ]
                    change.syntax_json['id'] = str(change.object_id)
                    syntax[change.model_type].append(change.syntax_json)
                elif change.change_type == ReleaseChangeType.DELETE:
                    syntax[change.model_type] = [
                        x for x in syntax[change.model_type] if x['id'] != str(change.object_id)
                    ]
        return syntax

    def save(self, *args, **kwargs):
        changes = None

        if self.parent:
            syntax = {
                ModelSchema._meta.model_name: self.parent.modelschemas,
                Page._meta.model_name: self.parent.pages,
                Package._meta.model_name: self.parent.packages,
                Workflow._meta.model_name: self.parent.workflows,
                Function._meta.model_name: self.parent.functions,
            }
            changes = self.parent.staged_changes.filter(release__isnull=True)

            merged_syntax = self._apply_changes(syntax, changes)

            for key, field in self.field_mappings.items():
                setattr(self, field, merged_syntax[key])

        Release.objects.all().update(current_release=False)
        self.current_release = True

        super().save(*args, **kwargs)

        if changes:
            changes.update(release=self)

    def get_all_syntax_definitions(self, model_name: str) -> list:
        """
        This method returns the all of the syntax definitions for a given model. However, a release
        only contains the current committed changes to an application. This means there may exist
        updated to one of the syntaxes within a ReleaseChange model.
        """
        syntax = {model_name: getattr(self, self.field_mappings[model_name])}
        changes = self.staged_changes.all()

        merged_syntax = self._apply_changes(syntax, changes)

        return merged_syntax[model_name]

    def get_syntax_definition(self, model_name: str, object_id: uuid.UUID) -> dict:
        found_syntaxes = [
            x for x in self.get_all_syntax_definitions(model_name) if x['id'] == str(object_id)
        ]

        if found_syntaxes:
            return found_syntaxes[0]
        return {}


class ReleaseChange(BaseModel):
    """
    Model to store the syntax for a given model (e.g. ModelSchema, Page, Workflow etc.) object.
    Syntax for a model object is always related to a branch. Each model object can only ever has a
    ReleaseChange syntax definition. Multiple changes to the syntax for an object result in the
    updating ReleaseChange for it.

    When a new release is issued, the data contained within all ReleaseChange instances are added
    to the release model and all ReleaseChange instances are deleted. This means that the
    ReleaseChange model only stores the current changes being made to the application.

    This model only stores the change to a particular part of the model. Therefore, it specifies
    the action (create, update or delete) that is being made to that section of the syntax.
    """

    parent_release = models.ForeignKey(
        Release,
        on_delete=models.CASCADE,
        related_name='staged_changes',
    )
    release = models.ForeignKey(
        Release,
        on_delete=models.CASCADE,
        related_name='committed_changed',
        null=True,
    )
    change_type = models.CharField(max_length=10, choices=ReleaseChangeType.choices)

    model_type = models.CharField(max_length=30)
    object_id = models.UUIDField(editable=False, null=True)

    syntax_json = models.JSONField()

    def __str__(self):
        return f'{self.change_type} {self.model_type} {self.object_id}'

    # def clean(self, *args, **kwargs):
    #     # Validate the JSON syntax.

    #     super().clean(*args, **kwargs)

    # def save(self, *args, **kwargs):
    #     self.full_clean()
    #     super().save(*args, **kwargs)
