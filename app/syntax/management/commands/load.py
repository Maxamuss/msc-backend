from django.core.management.base import BaseCommand
from django.db import DEFAULT_DB_ALIAS, connections
from django.db.backends.postgresql.introspection import DatabaseIntrospection

from ..._old.utils import load_from_directory


class Command(BaseCommand):
    help = 'Load an application configuration'

    # def add_arguments(self, parser):
    # parser.add_argument('directory', type=str)

    def handle(self, *args, **options):
        connection = connections['default']
        introspection = DatabaseIntrospection(connection)
        print(introspection)
