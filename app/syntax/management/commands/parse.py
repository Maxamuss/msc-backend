from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    def add_arguments(self, parser):
        parser.add_argument('layout_file_path', nargs=1, type=str)

    def handle(self, *args, **options):
        print(options['layout_file_path'])
        self.stdout.write(self.style.SUCCESS('Successfully'))
