import uuid

from django.db import models

from mptt.models import MPTTModel, TreeForeignKey

from accounts.models import User
from core.models import BaseModel


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

    parent = TreeForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, related_name='children'
    )

    def __str__(self):
        return self.release_version


class ReleaseChange(BaseModel):
    """
    Model to store the syntax for a given model (e.g. ModelSchema, Page, Workflow etc.) object.
    Syntax for a model object is always related to a branch. Each model object can only ever has a
    single syntax definition. Multiple changes to the syntax for an object result in the updating
    of the syntax definition.

    The frontend is responsible for generating the syntax for a model. The syntax json in then
    passed to this model where all validation and model creating is handled.
    """

    release = models.ForeignKey(Release, on_delete=models.CASCADE, related_name='changes')

    # syntax_type = models.CharField(max_length=10, choices=BaseModel.SyntaxType.choices)
    syntax_json = models.JSONField()
    release_version = models.PositiveIntegerField()
    object_id = models.UUIDField(default=uuid.uuid4, editable=False, null=True)

    def clean(self, *args, **kwargs):
        # Validate the JSON syntax.

        super().clean(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
