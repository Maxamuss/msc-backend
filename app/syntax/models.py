import uuid

from django.db import models
from django.db.models import F, Value

from mptt.models import MPTTModel, TreeForeignKey

from accounts.models import User
from core.models import BaseModel
from db.models import ModelSchema
from layout.models import Page
from packages.models import Package
from workflows.models import Function, Workflow

MODEL_TYPES = [
    ModelSchema._meta.model_name,
    Page._meta.model_name,
    Package._meta.model_name,
    Workflow._meta.model_name,
    Function._meta.model_name,
]


class ReleaseChangeType(models.TextChoices):
    CREATE = 'create'
    UPDATE = 'update'
    DELETE = 'delete'


class ReleaseSyntax(BaseModel):
    """
    Rather than store the each syntax JSON as a unique field on the Release model, it is stored
    here instead. This model stores the syntax for a single model object.

    The ReleaseSyntax holds the merged syntax at the time of the release. ReleaseChanges can be
    merged with these objects for a working branch.

    Always in the format:
    {
        "id": uuid,
        "model_id", uuid | null,
        ...[unique data for each model type]
    }

    Indexes are made on the id and model_id keys for faster lookups.
    """

    release = models.ForeignKey(
        'syntax.Release',
        on_delete=models.CASCADE,
        related_name='syntax',
    )

    model_type = models.CharField(max_length=30)
    syntax_json = models.JSONField()

    @classmethod
    def get_modelschema_id_from_name(cls, release, model_name):
        """
        Return the id of a modelschema by its model_name field.
        """
        print(
            cls.objects.filter(
                release=release, model_type='modelschema', syntax_json__model_name=model_name
            )
        )
        release_syntax = cls.objects.filter(
            release=release, model_type='modelschema', syntax_json__model_name=model_name
        ).first()

        if release_syntax:
            return release_syntax.syntax_json['id']
        return

    @classmethod
    def get_page(cls, release, modelschema_id, page_name):
        return cls.objects.filter(
            release=release,
            model_type='page',
            syntax_json__modelschema_id=modelschema_id,
            syntax_json__page_name=page_name,
        ).first()


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

    def __str__(self):
        return self.release_version

    @classmethod
    def get_current_release(cls):
        return cls.objects.get(current_release=True)

    def save(self, *args, **kwargs):
        """
        When a Release is created, we need to pull in all of the changes, merge it with the last
        parent Releases' syntax and add it to the model.

        Then, the changes are applied to the models.
        """
        is_new = self.pk is None

        super().save(*args, **kwargs)

        if is_new:
            Release.objects.all().update(current_release=False)
            Release.objects.filter(id=self.id).update(current_release=True)

            if self.parent:
                release_syntax_models = []

                for model_type in MODEL_TYPES:
                    syntaxes = self.get_syntax_definitions(model_type, release=self.parent)

                    for syntax_json in syntaxes:
                        if syntax_json:
                            release_syntax_models.append(
                                ReleaseSyntax(
                                    release=self,
                                    model_type=model_type,
                                    syntax_json=syntax_json,
                                )
                            )

                ReleaseSyntax.objects.bulk_create(release_syntax_models)

            ReleaseChange.objects.filter(parent_release=self.parent).delete()

    def get_syntax_definitions(
        self, model_type, object_id=None, modelschema_id=None, release=None, ordering=None
    ):
        """
        This method returns the all of the syntax definitions for a given model. However, a release
        only contains the current committed changes to an application. This means there may exist
        updated to one of the syntaxes within a ReleaseChange model.
        """
        release_syntaxes = list(
            self._get_release_syntax(
                model_type, object_id=object_id, modelschema_id=modelschema_id, release=release
            ).values_list('syntax_json', flat=True)
        )
        release_changes = self._get_release_changes(
            model_type, object_id=object_id, modelschema_id=modelschema_id, release=release
        )

        if release_changes.exists():
            syntax = self._merge_changes(release_syntaxes, release_changes)
        else:
            syntax = release_syntaxes

        if ordering:
            syntax = sorted(syntax, key=lambda x: x[ordering])

        if object_id:
            if len(syntax) == 1:
                return syntax[0]
            return {}
        return syntax

    def _get_release_syntax(self, model_type, object_id=None, modelschema_id=None, release=None):
        if release is None:
            release = self

        syntax = release.syntax.filter(model_type=model_type)

        if object_id:
            syntax = syntax.filter(syntax_json__id=object_id)

        if modelschema_id:
            syntax = syntax.filter(syntax_json__modelschema_id=modelschema_id)

        return syntax

    def _get_release_changes(self, model_type, object_id=None, modelschema_id=None, release=None):
        if release is None:
            release = self

        syntax = release.release_changes.filter(model_type=model_type)

        if object_id:
            syntax = syntax.filter(syntax_json__id=object_id)

        if modelschema_id:
            syntax = syntax.filter(syntax_json__modelschema_id=modelschema_id)

        return syntax

    def _merge_changes(self, current_syntax, release_changes):
        """
        For each ReleaseChange requiring to be merged, modify the parent Release's syntax.
        """
        for change in release_changes:
            object_id = change.syntax_json['id']

            if change.change_type == ReleaseChangeType.CREATE:
                # Add change syntax to current_syntax.
                current_syntax.append(change.syntax_json)
            elif change.change_type == ReleaseChangeType.UPDATE:
                # Remove parent resource  syntax and add updated resource syntax.
                current_syntax = [x for x in current_syntax if x['id'] != object_id]
                current_syntax.append(change.syntax_json)
            elif change.change_type == ReleaseChangeType.DELETE:
                # Remove parent resource from syntax.
                current_syntax = [x for x in current_syntax if x['id'] != object_id]

        return current_syntax


class ReleaseChange(BaseModel):
    """
    Model to store the syntax for a given model (e.g. ModelSchema, Page, Workflow etc.) object.
    Syntax for a model object is always related to a branch. This model stores the complex syntax
    for a model object and thus there can be at most 1 ReleaseChange for each model object.

    CREATE: creates a new model object.
        - model object primary field must be unique
        -
    UPDATE: updates the syntax of an existing model object.
    DELETE: removes a model object from the release.
    """

    parent_release = models.ForeignKey(
        Release,
        on_delete=models.CASCADE,
        related_name='release_changes',
        help_text='Release this change is being made against.',
    )

    change_type = models.CharField(max_length=10, choices=ReleaseChangeType.choices)
    model_type = models.CharField(max_length=30)
    syntax_json = models.JSONField()

    def __str__(self):
        return f'{self.change_type} {self.model_type} {self.syntax_json["id"]}'

    def save(self, *args, object_id=None, **kwargs):
        # self.full_clean()
        if change := self.get_existing_release_change(object_id):
            existing_syntax = change.syntax_json
            change.delete()
        elif change := self._get_existing_release_syntax(object_id):
            existing_syntax = change.syntax_json
        else:
            existing_syntax = None

        if existing_syntax:
            self.syntax_json['id'] = existing_syntax['id']
            self.syntax_json['modelschema_id'] = existing_syntax['modelschema_id']
        else:
            self._generate_id()

            if 'modelschema_id' not in self.syntax_json:
                self.syntax_json['modelschema_id'] = None

        super().save(*args, **kwargs)

    def _get_existing_release_syntax(self, object_id):
        """
        There is at most 1 object that matches with both the ReleaseChange and ReleaseSyntax
        models.
        """
        if not object_id:
            return

        return (
            ReleaseSyntax.objects.filter(
                release=self.parent_release,
                model_type=self.model_type,
            )
            .annotate(
                object_id=F('syntax_json__id'),
                change_type=Value(None, output_field=models.CharField()),
            )
            .filter(object_id=object_id)
            .first()
        )

    def get_existing_release_change(self, object_id):
        if not object_id:
            return

        return (
            ReleaseChange.objects.filter(
                parent_release=self.parent_release,
                model_type=self.model_type,
            )
            .annotate(object_id=F('syntax_json__id'))
            .filter(object_id=object_id)
            .first()
        )

    def _generate_id(self):
        # Get all existing ids in the parent release as well as other change creations.
        release_syntax_ids = list(
            ReleaseSyntax.objects.filter(
                release=self.parent_release,
                model_type=self.model_type,
            )
            .annotate(object_id=F('syntax_json__id'))
            .values_list('object_id', flat=True)
        )
        release_change_ids = list(
            ReleaseChange.objects.filter(
                parent_release=self.parent_release,
                model_type=self.model_type,
                change_type=ReleaseChangeType.CREATE,
            )
            .annotate(object_id=F('syntax_json__id'))
            .values_list('object_id', flat=True)
        )

        existing_ids = release_syntax_ids + release_change_ids

        object_id = uuid.uuid4()
        while object_id in existing_ids:
            object_id = uuid.uuid4()

        self.syntax_json['id'] = str(object_id)
