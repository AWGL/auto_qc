from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from core.models import Index, IndexSet, IndexToIndexSet

import csv



'''
example run command for script:

python manage.py import_indexes --vendor_name Illumina --index_tsv index_files/TSO500a_indexes_short.tsv --set_name WINGSa

'''

class Command(BaseCommand):
    help = 'index import TODO'

    def add_arguments(self, parser):
        parser.add_argument('--set_name', nargs=1, type=str, required=True, help='name of set to be displayed in dropdown eg: WINGSa')
        parser.add_argument('--vendor_name', nargs=1, type=str, required=True, help='name of vendor eg: Illumina')
        parser.add_argument('--index_tsv', nargs=1, type=str, required=True, help='path to tsv file of indexes to upload')



    def handle(self, *args, **options):

        ## only affect models if whole script runs OK
        with transaction.atomic():

            ## load args
            set_name = options['set_name'][0]
            vendor_name = options['vendor_name'][0]
            tsv_filepath = options['index_tsv'][0]

            print(set_name)
            print(vendor_name)
            print(tsv_filepath)

            ## create indexset object first. indexset name, vendor name, service/assay product
            ## query to see if exists first
            if IndexSet.objects.filter(set_name=set_name).exists():

                # raise ValueError('index set with this set name exists already')
                print('set name exists already as an index set')

                ## create indexset object with existing information
                IndexSet_object = IndexSet.objects.get(set_name=set_name)

            else:

                IndexSet_object = IndexSet.objects.create(
                    set_name = set_name,
                    vendor = vendor_name
                )
                print(f'new index set created: {set_name}')
                


            ## read file per line
            with open(tsv_filepath) as f:

                csv_file = csv.reader(f, delimiter='\t')

                for n, line in enumerate(csv_file):

                    ## skip header line
                    if n == 0:
                        print(line)

                    else:
                        print(n)
                        print(line)

                        ## create individual indexes
                        index_pos = line[0]
                        plate_well = line[1]
                        i7_index_name = line[2]
                        i7_index_seq = line[3]
                        i5_index_name = line[4]
                        i5_index_seq = line[5]

                        ##check if i7 exists in model, match to both i7 type and index name
                        if Index.objects.filter(index_name=i7_index_name, i7_or_i5="i7").exists():

                            print(f'i7 index name already exists: {i7_index_name}')

                            ## create i7 index object from existing information
                            i7_index_obj = Index.objects.get(index_name=i7_index_name, i7_or_i5="i7")

                        else:

                            ## create new i7 index object
                            i7_index_obj = Index.objects.create(
                                index_name = i7_index_name,
                                index_well = plate_well,
                                sequence = i7_index_seq,
                                i7_or_i5 = "i7"
                                )

                        ## check if i5 information exists in tsv file
                        if i5_index_seq == '' and i5_index_name == '':

                            ## no i5 info, create index to index set obj with only i7
                            if IndexToIndexSet.objects.filter(index1 = i7_index_obj, index_set = IndexSet_object).exists():
                                print('index to index set object already exists in models')
                            else:
                                ## doesn't exist already, create new object
                                IndexToIndexSet_object = IndexToIndexSet.objects.create(
                                    index1 = i7_index_obj,
                                    index_set = IndexSet_object,
                                    index_pos = index_pos
                                    )

                        else:

                            ## i5 info in tsv file, check if i5 exists in model
                            if Index.objects.filter(index_name=i5_index_name, i7_or_i5="i5").exists():

                                print(f'i5 index name already exists: {i5_index_name}')

                                ## create i5 index object from existing information
                                i5_index_obj = Index.objects.get(index_name=i5_index_name, i7_or_i5="i5")

                            else:

                                ## create new i5 index object
                                i5_index_obj = Index.objects.create(
                                    index_name = i5_index_name,
                                    index_well = plate_well,
                                    sequence = i5_index_seq,
                                    i7_or_i5 = "i5"
                                    )

                            ## create indextoindexset with i5 present
                            ## check if exists
                            if IndexToIndexSet.objects.filter(index1 = i7_index_obj, index2 = i5_index_obj, index_set = IndexSet_object).exists():
                                print('index to index set object already exists')
                            else:
                                ## create new index to index set object
                                IndexToIndexSet_object = IndexToIndexSet.objects.create(
                                    index1 = i7_index_obj,
                                    index2 = i5_index_obj,
                                    index_set = IndexSet_object,
                                    index_pos = index_pos
                                    )

                        print('done')