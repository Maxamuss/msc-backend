from django.core.management.base import BaseCommand

from ...utils import load_from_directory


class Command(BaseCommand):
    help = 'Load an application configuration'

    def add_arguments(self, parser):
        parser.add_argument('directory', type=str)

    def handle(self, *args, **options):
        load_from_directory(options['directory'])
        self.stdout.write(self.style.SUCCESS('Successfully'))
