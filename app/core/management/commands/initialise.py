import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from syntax.models import Release


class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    def handle(self, *args, **options):
        initial_release = Release.objects.create(
            release_version='0.1.0',
            release_notes='Initial release',
        )
