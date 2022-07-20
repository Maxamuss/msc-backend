import uuid

from django.db import models
from django.db.models import F, Value

from mptt.models import MPTTModel, TreeForeignKey

from accounts.models import User
from core.models import BaseModel
from db.models import FieldSchema, ModelSchema
from layout.models import Page
from packages.models import Package
from workflows.models import Function, Workflow
from .constants import CREATE_PAGE_LAYOUT, DELETE_PAGE_LAYOUT, EDIT_PAGE_LAYOUT, LIST_PAGE_LAYOUT

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
        is_new = self.pk is None

        super().save(*args, **kwargs)

        if is_new:
            self._create_release()

    def _create_release(self):
        """
        This method is called when the release is first created. When a Release is created, we need
        to pull in all of the changes, merge it with the last parent Releases' syntax and add it to
        the model.
        """
        Release.objects.all().update(current_release=False)
        Release.objects.filter(id=self.id).update(current_release=True)

        if self.parent:
            # Create the new syntax from the existing and changes and add to ReleaseSyntax model.
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

            # Apply database changes.
            model_schema_changes = self._get_release_changes(
                ModelSchema._meta.model_name, release=self.parent
            )
            self._apply_database_migrations(model_schema_changes)

        ReleaseChange.objects.filter(parent_release=self.parent).delete()

    def _apply_database_migrations(self, release_changes):
        """
        Given the ReleaseChanges for modelschemas, applying the updates to the database. Models are
        tracked using the ModelSchema model (within the db app):
         - CREATE: create a new model with all fields.
        """

        def get_class_name(field_type):
            if field_type == 'float':
                return 'django.db.models.FloatField'
            elif field_type == 'datetime':
                return 'django.db.models.DateTimeField'
            elif field_type == 'fk':
                return 'django.db.models.ForeignKey'
            else:
                return 'django.db.models.TextField'

        def get_kwargs(field):
            if field['field_type'] == 'fk':
                return {
                    'on_delete': models.CASCADE,
                    'to': ModelSchema.objects.get(id=field["modelschema_id"]).name,
                    'null': not field['required'],
                }
            else:
                return {
                    'null': not field['required'],
                }

        def create_field(model_schema, field):
            FieldSchema.objects.create(
                model_schema=model_schema,
                name=field['field_name'],
                class_name=get_class_name(field['field_type']),
                kwargs=get_kwargs(field),
            )
            print(field['field_name'])

        for release_change in release_changes:
            if release_change.change_type == ReleaseChangeType.CREATE:
                print('CREATE')
                # Create model schema and fields.
                model_schema = ModelSchema.objects.create(
                    id=release_change.syntax_json['id'],
                    name=release_change.syntax_json['model_name'],
                )
                print(model_schema.name)
                for field in release_change.syntax_json.get('fields', []):
                    create_field(model_schema, field)

            elif release_change.change_type == ReleaseChangeType.UPDATE:
                print('UPDATE')
                model_schema = ModelSchema.objects.get(id=release_change.syntax_json['id'])

                existing_fields = model_schema.fields.all().values_list('name', flat=True)

                for field in release_change.syntax_json.get('fields', []):
                    if field['field_name'] not in existing_fields:
                        create_field(model_schema, field)

            elif release_change.change_type == ReleaseChangeType.DELETE:
                print('DELETE')
                # Delete model schema (and fields by cascade).
                model_schema = ModelSchema.objects.filter(
                    id=release_change.syntax_json['id'],
                ).first()

                if model_schema:
                    model_schema.delete()

    def get_syntax_definitions(
        self, model_type, object_id=None, release=None, include_changes=True, **kwargs
    ):
        """
        modelschema_id=None,
        This method returns the all of the syntax definitions for a given model. However, a release
        only contains the current committed changes to an application. This means there may exist
        updated to one of the syntaxes within a ReleaseChange model.
        """
        if kwargs:
            for key in list(kwargs):
                kwargs[f'syntax_json__{key}'] = kwargs.pop(key)

        release_syntaxes = list(
            self._get_release_syntax(
                model_type, object_id=object_id, release=release, **kwargs
            ).values_list('syntax_json', flat=True)
        )

        syntax = release_syntaxes

        if include_changes:
            release_changes = self._get_release_changes(
                model_type, object_id=object_id, release=release, **kwargs
            )

            if release_changes.exists():
                syntax = self._merge_changes(release_syntaxes, release_changes)

        if object_id:
            if len(syntax) == 1:
                return syntax[0]
            return {}
        return syntax

    def _get_release_syntax(self, model_type, object_id=None, release=None, **kwargs):
        if release is None:
            release = self

        syntax = release.syntax.filter(model_type=model_type)

        if object_id:
            syntax = syntax.filter(syntax_json__id=object_id)

        if kwargs:
            syntax = syntax.filter(**kwargs)

        return syntax

    def _get_release_changes(self, model_type, object_id=None, release=None, **kwargs):
        if release is None:
            release = self

        syntax = release.release_changes.filter(model_type=model_type)

        if object_id:
            syntax = syntax.filter(syntax_json__id=object_id)

        if kwargs:
            syntax = syntax.filter(**kwargs)

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
        if release_change := self.get_existing_release_change(object_id):
            existing_syntax = dict(release_change.syntax_json)
            release_change.delete()
            previous_change_type = release_change.change_type
        elif release_syntax := self._get_existing_release_syntax(object_id):
            existing_syntax = dict(release_syntax.syntax_json)
            previous_change_type = None
        else:
            existing_syntax = None
            previous_change_type = None

        self.syntax_json = dict(self.syntax_json)

        if existing_syntax:
            self.syntax_json['id'] = existing_syntax['id']

            if 'modelschema_id' in existing_syntax:
                self.syntax_json['modelschema_id'] = existing_syntax['modelschema_id']

            # If the resource does not exist in the db yet, and prev change was create, make sure
            # this is also a create.
            if (
                previous_change_type == ReleaseChangeType.CREATE
                and self.change_type == ReleaseChangeType.UPDATE
            ):
                self.change_type = ReleaseChangeType.CREATE

            # If the resource does not exist in the db yet, don't create change and delete related
            # changes.
            if (
                previous_change_type == ReleaseChangeType.CREATE
                and self.change_type == ReleaseChangeType.DELETE
            ):
                (
                    ReleaseChange.objects.annotate(modelschema_id=F('syntax_json__modelschema_id'))
                    .filter(modelschema_id=self.syntax_json['id'])
                    .delete()
                )
                return

            create_pages = False
        else:
            self._generate_id()

            if (
                self.model_type != ModelSchema._meta.model_name
                and 'modelschema_id' not in self.syntax_json
            ):
                self.syntax_json['modelschema_id'] = None

            create_pages = True

        super().save(*args, **kwargs)

        if create_pages and self.model_type == ModelSchema._meta.model_name:
            self._create_default_pages()

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

    def _create_default_pages(self):
        """
        Create the default pages for a model.
        """
        pages = [
            ('list', LIST_PAGE_LAYOUT),
            ('create', CREATE_PAGE_LAYOUT),
            ('edit', EDIT_PAGE_LAYOUT),
            ('delete', DELETE_PAGE_LAYOUT),
        ]

        for page_name, layout in pages:
            syntax_json = {
                'page_name': page_name,
                'modelschema_id': self.syntax_json['id'],
                'layout': layout,
            }

            ReleaseChange.objects.create(
                parent_release=self.parent_release,
                change_type=ReleaseChangeType.CREATE,
                model_type='page',
                syntax_json=syntax_json,
            )
