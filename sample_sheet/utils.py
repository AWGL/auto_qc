import csv

from django.shortcuts import get_object_or_404
from sample_sheet.models import *

def import_worksheet_data(filepath):
    """
    input:
        filepath: path to a file containing the output of a shire query

    output:
        if successful:
        - returns True, worksheet id value, assay referral, '' message
        - samples, referrals, worksheets and sample-worksheet relations will be imported to the database
        if fails for referral type, column formatting, or ws already in database:
        - returns False, '' worksheet, '' referral, failure message of what happened
        if fails for other reason (uncoded):
        - fails and triggers exception in view code
    """

    ## sort/translate via hardcoded dict (shire test: assay instance - see model data)
    ## Add more here when adding assays/tests
    assay_translate_dict = {
                        'TSO500RNA panel' : 'TSO500RNA',
                        'TSO500DNA panel' : 'TSO500DNA',
                        'WGS - Nextera DNA Flex' : 'WINGS',
                        'CRM panel' : 'CRM',
                        'BRCA panel' : 'BRCA',
                        'haem NGS' : 'Myeloid',
                        'TruSight Cancer' : 'TruSightCancer',
                        'TruSight One CES panel' : 'TruSightOne',
                        'FH NGS Panel v1' : 'FH'
    }



    ## this returns a dictionary per sample as a list of dicts.
    ## input file must be saved using MS excel as commadelimited.csv (not utf-8 csv)
    shire_query = list(csv.DictReader(filepath))
    print('full shire query is:')
    print(shire_query)

    ## LOGIC CHECK for formatting to prevent partial failures/uploads
    ## check all columns are present and correctly named
    if list(dict.keys(shire_query[0])) != ['LABNO', 'POSITION', 'WORKSHEET', 'TEST', 'COMMENTS', 'UPDATEDDATE', 'REASON_FOR_REFERRAL', 'FIRSTNAME', 'LASTNAME', 'SEX']:
        message = 'Worksheet not uploaded. Column formatting is not as expected, please check the input file'
        print(message)
        worksheet = ''
        assay = ''
        return False, message, worksheet, assay
    else:
        print('column formatting checked: OK')


    # make dictionary sorted by worksheet
    # LIMITATION: only handles one ws at a time for returning ws_id to view
    query_dict = {}
    for sample_dict in shire_query:
        ws = sample_dict['WORKSHEET']
        if ws in query_dict:
            query_dict[ws].append(sample_dict)
        else:
            query_dict[ws] = [sample_dict]

    # add NTC to each worksheet
    for key, value in query_dict.items():
        ntc_pos = str(len(value) + 1)
        ntc_name = f'NTC-{key}'
        ntc_test = value[0]['TEST']
        value.append({
            'LABNO': ntc_name,
            'REASON_FOR_REFERRAL': 'null',
            'SEX': '0',
            'POSITION': ntc_pos,
            'TEST': ntc_test
        })


    ## LOGIC CHECK for formatting to prevent partial failures/uploads
    ## pull assay type from first sampleline in uploaded file dict
    assay_type = shire_query[0]['TEST']
    print(f'assay type is: {assay_type}')

    ## check is dependent on assay type. Don't check for overwritten values below
    if assay_translate_dict[assay_type] not in ['Myeloid','TruSightOne','TruSightCancer']:

        # get list of referral types from models
        expected_referral_list = list(ReferralType.objects.all().values_list('shire_name', flat = True))

        # check referral types are all expected values
        for key, value in query_dict.items():

            for item in value:


                if item['REASON_FOR_REFERRAL'] not in expected_referral_list:
                    print(item['REASON_FOR_REFERRAL'])
                    message = 'Worksheet not uploaded. Unexpected referral type found, please check the input file'
                    print(message)
                    worksheet = ''
                    assay = ''
                    return False, message, worksheet, assay

                else:
                    print('Referral types check: OK')



    ## skip upload if worksheet ID already exists in worksheet model
    ## get list of all worksheets in database
    worksheet_list = list(Worksheet.objects.all().values_list('worksheet_id', flat = True))

    ## check if new worksheet in list on database
    if ws in worksheet_list:

        message = f'Worksheet not uploaded as the worksheet ID {ws} already exists in database'
        print(message)
        worksheet = ''
        assay = ''
        return False, message, worksheet, assay

    else:
        print('worksheet is not already on database')

    
    ## upload data
    for ws, samples in query_dict.items():

        assay_name = assay_translate_dict[samples[0]['TEST']]
        assay = get_object_or_404(Assay, assay_name = assay_name)
        worksheet_obj, created = Worksheet.objects.get_or_create(
            worksheet_id = ws,
            worksheet_test = assay
        )
        print(worksheet_obj, created)

        for sample in samples:
            print(sample)

            ## create lowercase no blank referral
            referral_formatted = sample['REASON_FOR_REFERRAL'].lower().replace(' ', '')
            print(referral_formatted)

            ## add overwrite for some of the referral types
            ## rewrite myeloid NGS referral from shire to just be myeloid on DB
            if referral_formatted == 'myeloidngs':
                referral_name = 'myeloid'
                shire_referral_name = sample['REASON_FOR_REFERRAL']

            ## add ws level overwrite for some assays (except NTC)
            elif not sample['LABNO'].startswith('NTC'):
                ## overwrite all Trusightcancer referrals on DB
                if assay_name == 'TruSightCancer':
                    referral_name = 'TSC'
                    shire_referral_name = 'TSC' # N/A

                ## overwrite all TruSightOne referrals on DB
                elif assay_name == 'TruSightOne':
                    referral_name = 'TS1'
                    shire_referral_name = 'TS1' # N/A

                ## overwrite all FH referral types on DB
                elif assay_name == 'FH':
                    referral_name = 'fh'
                    shire_referral_name = 'FH' # N/A

                ## no overwrite, default to lowercase no blankspace
                else:
                    referral_name = referral_formatted
                    shire_referral_name = sample['REASON_FOR_REFERRAL']

            ## keep NTC as null
            else:
                referral_name = 'null'
                shire_referral_name = 'null'

            ## get or create referral object
            referral_obj, created = ReferralType.objects.get_or_create(
                name = referral_name, 
                shire_name = shire_referral_name
            )
            print(referral_obj, created)


            ## handle unknown or missing sex
            try:
                if sample['SEX'] == 'M':
                    sex = '1'
                elif sample['SEX'] == 'F':
                    sex = '2'
                else:
                    sex = '0'
            except:
                sex='0'
            print('sex handled')

            ## get or create sample object
            sample_obj, created = Sample.objects.get_or_create(
                sampleid = sample['LABNO'],
                sex = sex
                )
            print(sample_obj, created)


            ## get or create sample to worksheet link object
            sample_ws_obj, created = SampleToWorksheet.objects.get_or_create(
                sample = sample_obj,
                referral = referral_obj,
                worksheet = worksheet_obj,
                pos = sample['POSITION']
            )
            print(sample_ws_obj, created)


        # all import script ran ok, create blank message
        message = ''
        
    return True, message, ws, assay_name


def import_indexes_combined(filepath, index_set_object):
    """
    input:
      filepath: path to a file containing vendor index sequences
      index_set_object: a django object of the vendor index set being added

    output:
      indexes and index-vendor index set relations will be imported to the database
    """
    with open(filepath) as f:
        csv_file = csv.reader(f, delimiter='\t')
        for n, line in enumerate(csv_file):
            index_name = line[0]
            i7_sequence = line[1]
            i5_sequence = line[2]

            # add i7 index
            i7_obj = Index.objects.create(
                index_name = index_name,
                sequence = i7_sequence,
                i7_or_i5 = 'i7'
            )

            # add i5 index
            i5_obj = Index.objects.create(
                index_name = index_name,
                sequence = i5_sequence,
                i7_or_i5 = 'i5'
            )

            # make m2m relationships
            index_to_index_set_obj = IndexToIndexSet.objects.create(
                index1 = i7_obj,
                index2 = i5_obj,
                index_set = index_set_object,
                index_pos = n + 1,
            )


def generate_ss_data_dict(worksheet, position_offset=0):

    ## get worksheet data
    worksheet_obj = Worksheet.objects.get(worksheet_id=worksheet) 
    sample_dict = worksheet_obj.get_samples_from_ws()

    ## create dictionary of values. These are hardcoded to match samplesheet column headers
    export_dict = {}
    for pos, values in sample_dict.items():

        ## allow for multiple worksheets positioning
        adjusted_position = int(pos) + int(position_offset)

        ## query indextoindexset for index position for TSO500
        # index_pos = IndexToIndexSet.objects.filter(index1 = values['sample_obj'].index1.index_name)
        export_dict[adjusted_position] = {
                            'Sample_ID' : values['sample'],
                            'Sample_Name' : values['sample'],
                            'Sample_Plate' : worksheet,
                            'Sample_Well' : str(adjusted_position),
                            'I7_Index_ID' : values['sample_obj'].index1.index_name,
                            'Index_ID' : values['sample_obj'].index1.index_name,
                            'index' : values['sample_obj'].index1.sequence,
                            'Pair_ID' : values['sample'],
                            'Sample_Project' : '',
                            'Sex' : values['sex'],
                            'Referral' : values['referral'],
                            'Familyid' : values['familyid'],
                            'Affected' : values['affected'],
                            'FamilyPos' : values['familypos'],
                            'Index_Well' : values['sample_obj'].index1.index_well,
        }
        ## if second index exists add values to dictionary, else make ''
        if values['index2']:
            export_dict[adjusted_position]['I5_Index_ID'] = values['sample_obj'].index2.index_name
            export_dict[adjusted_position]['index2'] = values['sample_obj'].index2.sequence

        else:

            export_dict[adjusted_position]['index2'] = ''
            export_dict[adjusted_position]['I5_Index_ID'] = ''

        # TODO sample_well field is different for TSO500
        # TODO sample type is specific to TSO500, uses index position on plate so need to query indextoindexset


    return export_dict


def combine_ss_data_dict(worksheets):
    """
    inputs:
      worksheets (list): a list of worksheet IDs (e.g. ['20-123', '20-456'])
      index_sets (list): a list of custom indexes sets (e.g. ['set1', 'set2'])
      reverse_complement (boolean): if True, i5 index will be the reverse complement

    output:
      ss_data_fields: list of lists of each row from the samplesheet [Data] section, for multiple worksheets
    """
    # make offset variable to ensure sample_well is incremental
    offset = 0
    ss_data_dict = {}

    # loop through worksheets
    for ws in worksheets:
        # generate samplesheet
        ss_data_dict.update(generate_ss_data_dict(ws, offset))
        offset += len(ss_data_dict.keys())

    return ss_data_dict