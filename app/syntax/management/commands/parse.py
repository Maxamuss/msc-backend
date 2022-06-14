import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from ..._old.parser import SyntaxParser


class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    def add_arguments(self, parser):
        parser.add_argument('layout_file_path', nargs=1, type=str)

    def handle(self, *args, **options):
        file_path = options['layout_file_path'][0]
        layout_path_input = os.path.join(settings.BASE_DIR, '..', file_path)
        layout_path_output = os.path.join(settings.BASE_DIR, '..', file_path.replace('.min', ''))

        with open(layout_path_input) as f:
            layouts = json.loads(f.read())

        for page_name, page_config in layouts.items():
            SyntaxParser().parse_layout(page_config)
            print(page_name)

        with open(layout_path_output, 'w') as f:
            f.write(json.dumps(layouts))

        self.stdout.write(self.style.SUCCESS('Successfully'))
