import uuid
from typing import List, Optional

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
    current_release = models.BooleanField(default=False, editable=False)

    parent = TreeForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, related_name='children'
    )

    # Stores the syntax for all models for this release.
    modelschemas = models.JSONField(default=list, blank=True)
    pages = models.JSONField(default=list, blank=True)
    packages = models.JSONField(default=list, blank=True)
    workflows = models.JSONField(default=list, blank=True)
    functions = models.JSONField(default=list, blank=True)

    field_mappings = {
        ModelSchema._meta.model_name: 'modelschemas',
        Page._meta.model_name: 'pages',
        Package._meta.model_name: 'packages',
        Workflow._meta.model_name: 'workflows',
        Function._meta.model_name: 'functions',
    }

    def __str__(self):
        return self.release_version

    def save(self, *args, **kwargs):
        """
        When a Release is created, we need to pull in all of the changes, merge it with the last
        parent Releases' syntax and add it to the model.
        """
        release_changes = None

        if self.parent:
            syntax = {
                ModelSchema._meta.model_name: self.parent.modelschemas,
                Page._meta.model_name: self.parent.pages,
                Package._meta.model_name: self.parent.packages,
                Workflow._meta.model_name: self.parent.workflows,
                Function._meta.model_name: self.parent.functions,
            }
            # ReleaseChanges without a release FK have not been merged into their own release yet.
            release_changes = self.parent.staged_changes.filter(release__isnull=True)

            # Merge the parent Release syntax with the current changes.
            merged_syntax = self._apply_changes(syntax, release_changes)

            # Add the merged syntax to the correct field on this model.
            for key, field in self.field_mappings.items():
                setattr(self, field, merged_syntax[key])

        # Use update to not call this save method on the other Releases.
        Release.objects.all().update(current_release=False)

        # Set this release as the current release. Ensures there is always only 1 current release.
        self.current_release = True

        super().save(*args, **kwargs)

        # For the ReleaseChanges that have been merged into this Release, set their release FK to
        # this Release so that they are marked are merged. This must be done after super so that it
        # is ensured that this model has been created.
        if release_changes:
            release_changes.update(release=self)

    def _apply_changes(self, syntax, changes):
        """
        For each ReleaseChange requiring to be merged, modify the parent Release's syntax.
        """
        for change in changes:
            # Validates incoming syntax from frontend and prevents storing of unnecessary data.
            if change.model_type in syntax.keys():
                object_id = str(change.object_id)

                if change.change_type == ReleaseChangeType.CREATE:
                    # Add resource to syntax.
                    syntax[change.model_type].append(change.syntax_json)
                elif change.change_type == ReleaseChangeType.UPDATE:
                    # Remove parent resource  syntax and add updated resource syntax.
                    syntax[change.model_type] = [
                        obj for obj in syntax[change.model_type] if obj['id'] != object_id
                    ]
                    syntax[change.model_type].append(change.syntax_json)
                elif change.change_type == ReleaseChangeType.DELETE:
                    # Remove parent resource from syntax.
                    syntax[change.model_type] = [
                        x for x in syntax[change.model_type] if x['id'] != object_id
                    ]

        return syntax

    def get_all_syntax_definitions(
        self, model_name: str, fields: Optional[List[str]] = None
    ) -> list:
        """
        This method returns the all of the syntax definitions for a given model. However, a release
        only contains the current committed changes to an application. This means there may exist
        updated to one of the syntaxes within a ReleaseChange model.
        """
        syntax = {model_name: getattr(self, self.field_mappings[model_name])}
        changes = self.staged_changes.all()

        merged_syntax = self._apply_changes(syntax, changes)[model_name]

        if fields:
            return [self._extract_fields(syntax_object, fields) for syntax_object in merged_syntax]
        return merged_syntax

    def get_syntax_definition(
        self, model_name: str, object_id: uuid.UUID, fields: Optional[List[str]] = None
    ) -> dict:
        found_syntaxes = [
            x for x in self.get_all_syntax_definitions(model_name) if x['id'] == str(object_id)
        ]

        if found_syntaxes:
            syntax = found_syntaxes[0]

            return self._extract_fields(syntax, fields)
        return {}

    def _extract_fields(self, syntax: dict, fields: Optional[List[str]]):
        if fields:
            if 'id' not in fields:
                fields.insert(0, 'id')

            return {field: syntax[field] for field in fields}
        return syntax

    @classmethod
    def get_current_release(cls):
        return cls.objects.get(current_release=True)


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

    In the case of a creation, there is no object_id. Therefore, the object_id is generated and
    added to the syntax.
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
    object_id = models.UUIDField(editable=False)

    syntax_json = models.JSONField()

    def __str__(self):
        return f'{self.change_type} {self.model_type} {self.object_id}'

    def save(self, *args, **kwargs):
        # self.full_clean()

        # Generate object_id (if required).
        if not self.object_id:
            # TODO: check unique.
            self.object_id = uuid.uuid4()

        if 'id' not in self.syntax_json:
            self.syntax_json['id'] = str(self.object_id)

        super().save(*args, **kwargs)

    # def clean(self, *args, **kwargs):
    #     # Validate the JSON syntax.

    #     super().clean(*args, **kwargs)
