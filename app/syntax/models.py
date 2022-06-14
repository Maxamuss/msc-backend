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


class ReleaseSyntax(BaseModel):
    """
    Rather than store the each syntax JSON as a unique field on the Release model, it is stored
    here instead.
    """

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['release', 'model_type'], name='unique_release_syntax_type'
            )
        ]

    release = models.ForeignKey(
        'syntax.Release',
        on_delete=models.CASCADE,
        related_name='syntax',
    )
    model_type = models.CharField(max_length=30)
    syntax_json = models.JSONField(default=list, blank=True)


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
    # modelschemas = models.JSONField(default=list, blank=True)
    # pages = models.JSONField(default=list, blank=True)
    # packages = models.JSONField(default=list, blank=True)
    # workflows = models.JSONField(default=list, blank=True)
    # functions = models.JSONField(default=list, blank=True)

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

        Then, the changes are applied to the models.
        """
        is_new = self.pk is None

        super().save(*args, **kwargs)

        if self.parent and is_new:
            # ReleaseChanges without a release FK have not been merged into their own release yet.
            release_changes = self.parent.staged_changes.filter(release__isnull=True)

            syntax = {
                model_type: self._get_release_syntax(model_type, release=self.parent)
                for model_type in self.field_mappings.keys()
            }

            # Merge the parent Release syntax with the current changes.
            merged_syntax = self._merge_changes(syntax, release_changes)

            # Set this release as current all other releases as no current. Use update to not call
            # the model save method on the other Releases. Ensures there is always only 1 current
            # release at a time.
            Release.objects.all().update(current_release=False)
            Release.objects.filter(id=self.id).update(current_release=True)

            # For the ReleaseChanges that have been merged into this Release, set their release FK
            # to this Release so that they are marked are merged. Also create a ReleaseSyntax for
            # the merged syntax.
            if release_changes:
                for model_type, syntax_json in merged_syntax.items():
                    ReleaseSyntax.objects.create(
                        release=self, model_type=model_type, syntax_json=syntax_json
                    )

                release_changes.update(release=self)

    def _get_release_syntax(self, model_type, release=None):
        """
        Return the syntax for the model model type and given release. There is only ever 1
        model_type syntax for a given release.

        The filter argument is for the filtering the json for a given key. This could be used to
        return a single object or to only return an objects related keys.
        """
        if release is None:
            release = self

        syntax = release.syntax.filter(model_type=model_type).first()

        if syntax:
            return syntax.syntax_json
        return []

    def _merge_changes(self, syntax, changes):
        """
        For each ReleaseChange requiring to be merged, modify the parent Release's syntax.
        """
        for change in changes:
            # Validates incoming syntax from frontend and prevents storing of unnecessary data.
            if change.model_type in syntax.keys():
                object_id = str(change.object_id)

                print(object_id)

                if change.change_type == ReleaseChangeType.CREATE:
                    # Add resource to syntax.
                    syntax[change.model_type].append(change.syntax_json)
                elif change.change_type == ReleaseChangeType.UPDATE:
                    # Remove parent resource  syntax and add updated resource syntax.
                    objs = [obj for obj in syntax[change.model_type] if obj['id'] != object_id]
                    if objs:
                        obj = objs[0]
                        obj.update(change.syntax_json)
                elif change.change_type == ReleaseChangeType.DELETE:
                    # Remove parent resource from syntax.
                    syntax[change.model_type] = [
                        x for x in syntax[change.model_type] if x['id'] != object_id
                    ]

        return syntax

    def _filter_syntax(self, syntax, filters):
        def filter_syntax(obj):
            for filter_dict in filters:
                if obj[filter_dict['key']] != filter_dict['value']:
                    return False
            return True

        return [obj for obj in syntax if filter_syntax(obj)]

    def get_all_syntax_definitions(
        self, model_type: str, parent_id: Optional[uuid.UUID] = None
    ) -> list:
        """
        This method returns the all of the syntax definitions for a given model. However, a release
        only contains the current committed changes to an application. This means there may exist
        updated to one of the syntaxes within a ReleaseChange model.
        """
        current_syntax = self._get_release_syntax(model_type)
        staged_changes = self.staged_changes.filter(model_type=model_type)

        if staged_changes.exists():
            merged_syntax = self._merge_changes({model_type: current_syntax}, staged_changes)
            merged_syntax = merged_syntax[model_type]
        else:
            merged_syntax = current_syntax

        if parent_id:
            return [x for x in merged_syntax if x['model_id'] == str(parent_id)]

        return merged_syntax

    def get_syntax_definition(self, model_name: str, object_id: uuid.UUID, filters: List) -> dict:
        found_syntaxes = [
            x
            for x in self.get_all_syntax_definitions(model_name, filters)
            if x['id'] == str(object_id)
        ]

        if found_syntaxes:
            syntax = found_syntaxes[0]

            return syntax
        return {}

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
        blank=True,
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
