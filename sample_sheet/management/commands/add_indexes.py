from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from ...utils import import_indexes_combined
from indexes.models import Index, IndexSet, IndexToIndexSet

import csv

class Command(BaseCommand):
    help = 'test'

    def add_arguments(self, parser):
        parser.add_argument('--input', nargs=1, type=str, required=True)

    def handle(self, *args, **options):
        input_path = options['input'][0]

        with transaction.atomic():
            
            vendor = input('input vendor: ')
            product = input('input product: ')
            combination = input('input set type: ')
            set_name = input('input set name: ')

            # TODO - check doesnt already exist

            # make vendorindexset
            index_set_object = IndexSet.objects.create(
                set_name = set_name,
                set_type = 'V',
                vendor = vendor,
                product = product,
                combination = combination
            )

            # add and link indexes
            # if index sets are combined
            if combination == 'combined':
                import_indexes_combined(input_path, index_set_object)

            # TODO - function to import when indexes arent combined
            elif combination == 'i7_only' or 'i5_only':
                pass

            # otherwise throw an error
            else:
                raise ValueError('Index combination not recognised - options are combined, i7_only or i5_only')
