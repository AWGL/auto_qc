from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from ...utils import import_worksheet_data

class Command(BaseCommand):
    help = 'test'

    def add_arguments(self, parser):
        parser.add_argument('--input', nargs=1, type=str, required=True)

    def handle(self, *args, **options):
        input_path = options['input'][0]
        with transaction.atomic():
            import_worksheet_data(input_path)
