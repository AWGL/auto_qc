from django.core.management.base import BaseCommand, CommandError
from ...utils import generate_ss_data_dict, combine_ss_data_dict
from ...models import Worksheet

from datetime import date

class Command(BaseCommand):

    help = 'Generate samplesheet from an input of a list of completed worksheets and a list of assay types'

    def add_arguments(self, parser):

        parser.add_argument('--worksheets', nargs=1, type=str, required=True, help='List of worksheets')
        parser.add_argument('--assays', nargs=1, type=str, required=True, help='list of assays in worksheets order')


    def handle(self, *args, **options):

        ## load args
        worksheets = options['worksheets'][0].split(',')
        assays = options['assays'][0].split(',')

        ## use main/first assay for majority of formatting purposes. Can fail if wrong samplesheets are paired
        assay = assays[0]

        ## hardcoded description column dictionary. added to and edited before writing csv file
        description_dict = {
                        'WGS' : 'pipelineName=DragenWGS;pipelineVersion=master;panel=WGS;',
                        'FastWGS': 'pipelineName=DragenWGS;pipelineVersion=master;panel=FastWGS;',
                        'TSO500RNA' : 'pipelineName=TSO500;pipelineVersion=master;',
                        'TSO500DNA' : 'pipelineName=TSO500;pipelineVersion=master;',
                        'Myeloid' : 'pipelineName=SomaticAmplicon;pipelineVersion=master;panel=TruSightMyeloid;',
                        'FH' : 'pipelineName=germline_enrichment_nextflow;pipelineVersion=master;panel=AgilentOGTFH;',
                        'TruSightCancer' : 'pipelineName=germline_enrichment_nextflow;pipelineVersion=master;panel=IlluminaTruSightCancer;',
                        'TruSightOne' : 'pipelineName=DragenGE;pipelineVersion=master;panel=IlluminaTruSightOne;',
                        'BRCA' : 'pipelineName=SomaticAmplicon;pipelineVersion=master;panel=NGHS-102X;',
                        'CRM' : 'pipelineName=SomaticAmplicon;pipelineVersion=master;panel=NGHS-101X;',
                        'WES' : 'pipelineName=DragenGE;pipelineVersion=master;panel=NonocusWES38;',
			'ctDNA' : 'pipelineName=tso500_ctdna;pipelineVersion=master;'
        }


        ## import header from file (reads as a list of lines)
        with open(f'sample_sheet/samplesheet_headers/{assay}_header.csv', newline='') as header_file:
            samplesheet_header = header_file.readlines()


        ## create data header list from last line of samplesheet header file
        data_headers = samplesheet_header[(len(samplesheet_header)-1)].strip('\n').split(',')


        ## create experiment id
        experiment_id = "_".join(worksheets)


        ## create samplesheet list of lines ready to add and export
        samplesheet_output = samplesheet_header


        ## generate data section for single worksheet. returned as dictionary against position
        if len(worksheets) == 1:
            ss_data_dict = generate_ss_data_dict(worksheets[0])
            
        ## generate data section for combined worksheets (essentially a second script to run one after the other while changing offset value)
        else:
            ss_data_dict = combine_ss_data_dict(worksheets)


        '''
        ## process dict for family information to generate paternal/maternal IDs
        aim is to create:
        familydict = {
                    'FAM001' : {
                            'paternalid' : '11M11111',
                            'maternalid' : '11M11112',
                            'probandid' : '11M11113'
                    },
                    'FAM002' : {
                            'paternalid' : '11M11114',
                            'maternalid' : '11M11115',
                            'probandid' : '11M11116'
                    },
        }
        '''
        familydict = {}
        for pos, values in ss_data_dict.items():

            ## if wings or WES assays as only ones that uses family at the moment
            if assay in ["WGS","WES"]:

                ## if familyid is populated
                if values['Familyid']:

                    ## check if familyid is already a key in family dict
                    if values['Familyid'] not in familydict.keys():
                        ## add blank dict to familydict with familyid as key
                        familydict[values['Familyid']] = {}

                    ## check for father info
                    if values['FamilyPos'] == 'Father':
                        familydict[values['Familyid']]['paternalid'] = values['Sample_ID']

                    ## check for mother info
                    if values['FamilyPos'] == 'Mother':
                        familydict[values['Familyid']]['maternalid'] = values['Sample_ID']

                    ## check for proband info
                    if values['FamilyPos'] == 'Proband':
                        familydict[values['Familyid']]['probandid'] = values['Sample_ID']


        ## process dict again to create fields
        for pos, values in ss_data_dict.items():


            '''
            1 {'Sample_ID': '20M55555', 'Sample_Name': '20M55555',
            'Sample_Plate': '21-678', 'Sample_Well': 1, 'I7_Index_ID': 'A05',
            'Index_ID': 'A05', 'index': 'ATTCAGAA', 'Pair_ID': '20M55555', 
            'Sample_Project': '', 'Sex': 'Male', 'Referral': 'GIST', 'Familyid': None, 
            'Affected': False, 'FamilyPos': None, 'I5_Index_ID': 'A03', 'index2': 'AGGCTATA'}
            '''

            ## generate description field
            ## if wings generate sex and family info then add to description field
            if assay == "WGS":

                ## if sample is urgent update panel to FastWGS
                sample_assay = assay
                if values['Urgent']:
                    sample_assay = 'FastWGS'

                ## format sex part. no semicolon in case its on a singleton/NTC
                if values['Sex'] == 'Male':
                    sex_desc = 'sex=1'
                elif values['Sex'] == 'Female':
                    sex_desc = 'sex=2'
                else:
                    sex_desc = 'sex=0'


                #generate referral data
                if values["Referral"].startswith('wgs~'):
                    referral_formatted = values["Referral"].replace('wgs~','')
                elif values['Referral'] == "null":
                    referral_formatted = "None"
                else:
                    referral_formatted = values["Referral"]

                referral_desc = f';referral={referral_formatted}'

                # generate hpo data
                if values['hpo_ids'] != None:
                    hpo_formatted = values['hpo_ids'].replace(',','|')
                    hpo_desc = f';hpoId={hpo_formatted}'
                else:
                    hpo_desc = ';hpoId=None'

                ## if familyid is populated then generate paternal/maternal ids from familydict
                if values['Familyid']:
                    familyid = values["Familyid"]
                    fam_desc = f';familyId={familyid}'
                    
                    ## if proband then add data: family, maternal, paternal
                    if values['FamilyPos'] == 'Proband':

                        # try get paternal info and add to family desc
                        try:
                            paternal = familydict[familyid]['paternalid']
                            fam_desc += f';paternalId={paternal}'
                        except:
                            pass
                        
                        # try to get maternal and add to family desc
                        try:
                            maternal = familydict[familyid]['maternalid']
                            fam_desc += f';maternalId={maternal}'
                        except:
                            pass

                    ## if not proband only inclue family ID
                    else:
                        fam_desc = f';familyId={familyid}'

                    ## format phenotype/affected part. no semicolon needed as at the end of the description.
                    ## only present in the event of a family id
                    if values['Affected']:
                        affected_desc = ';phenotype=2'
                    else:
                        affected_desc = ';phenotype=1'

                else:
                    ## fixes bug where if singleton processed after a family member it kept fam_desc and affected value
                    fam_desc = ''
                    affected_desc = ''


                ## build description field for WINGS
                description_field = f'{description_dict[sample_assay]}{sex_desc}{referral_desc}{hpo_desc}{fam_desc}{affected_desc}'


            ## if TSO500RNA or DNA is main assay, add DNA/RNA field to dict for relevant samples. Then deal with description field
            elif assay == 'TSO500RNA' or assay == 'TSO500DNA':

                type_dict = {
                            'TSO500RNA' : 'RNA',
                            'TSO500DNA' : 'DNA',
                }

                ## match values wsid with type_dict for sample type column. add to data dict
                '''
                output example:
                {'20-6582': 'DNA', '21-1971': 'RNA'}

                '''
                worksheet_type_dict = {}
                for a, b in zip(worksheets, assays):
                    worksheet_type_dict[a] = type_dict[b]

                ## copy whole of values and change
                changed_values = values
                changed_values['Sample_Type'] = worksheet_type_dict[values['Sample_Plate']]
                changed_values['Sample_Well'] = values['Index_Well']

                ## update main dict
                ss_data_dict[pos].update(changed_values)

                ## create description field
                description_field = f'{description_dict[assay]}referral={values["Referral"]}'


            ## if Myeloid assay then create description field using referral type for the samples
            elif assay == 'Myeloid':

                description_field = f'{description_dict[assay]}referral={values["Referral"]}'


            ## if FH then create description field using gender.
            elif assay == 'FH':

                ## format sex part. no semicolon in case its on a singleton/NTC
                if values['Sex'] == 'Male':
                    sex_desc = 'sex=1'
                elif values['Sex'] == 'Female':
                    sex_desc = 'sex=2'
                else:
                    sex_desc = 'sex=0'

                description_field = f'{description_dict[assay]}{sex_desc}'

            ## if TSC then description field plus order
            elif assay == 'TruSightCancer':

                ## format sex part. no semicolon in case its on a singleton/NTC
                if values['Sex'] == 'Male':
                    sex_desc = 'sex=1'
                elif values['Sex'] == 'Female':
                    sex_desc = 'sex=2'
                else:
                    sex_desc = 'sex=0'

                description_field = f'{description_dict[assay]}{sex_desc};order={pos}'


            ## if TS1 then create description field plus sex
            elif assay == 'TruSightOne':
                if values['Sex'] == 'Male':
                    sex_desc = 'sex=1'
                elif values['Sex'] == 'Female':
                    sex_desc = 'sex=2'
                else:
                    sex_desc = 'sex=0'

                description_field = f'{description_dict[assay]}{sex_desc}'


            ## CRM/BRCA loop. checks for first assay only then enters this loop
            elif assay == 'BRCA' or assay == 'CRM':

                ## check if multiple worksheets submitted
                if len(worksheets) >1:

                    ## check which is first worksheet
                    ## if worksheet in sample data is same as worksheet one, assay type is first assay
                    if values['Sample_Plate'] == worksheets[0]:
                        assay_type = assays[0]

                    ## if not first worksheet then assay is second assay
                    else:
                        assay_type = assays[1]

                    ## create description field from assay_type
                    description_field = f'{description_dict[assay_type]}referral={values["Referral"]}'

                ## one worksheet submitted so use main assay
                else:
                    description_field = f'{description_dict[assay]}referral={values["Referral"]}'


            elif assay == 'WES':

                ## check sequencer type of primary worksheet, create app_id 
                worksheet_obj = Worksheet.objects.get(worksheet_id = worksheets[0])
                sequencer_type = worksheet_obj.sequencer

                if sequencer_type == 'NextSeq':
                    app_id = 'NextSeqFASTQOnly'
                    override_id = 'Y145;I8U9;I8;Y145'
                elif sequencer_type == "NovaSeq":
                    app_id = 'NovaSeqFASTQOnly'
                    override_id = 'Y151;I8U9;I8;Y151'
                else:
                    app_id = 'WARNING INVALID SEQUENCER SELECTED'
                    override_id = 'WARNING INVALID SEQUENCER SELECTED'

                ## change position to well identifier
                changed_values = values
                changed_values['Sample_Well'] = values['Index_Well']

                ## update main dict
                ss_data_dict[pos].update(changed_values)


                ## format sex part. no semicolon in case its on a singleton/NTC
                if values['Sex'] == 'Male':
                    sex_desc = 'sex=1'
                elif values['Sex'] == 'Female':
                    sex_desc = 'sex=2'
                else:
                    sex_desc = 'sex=0'

                #generate referral data
                if values["Referral"].startswith('wes~'):
                    referral_formatted = values["Referral"].replace('wes~','')
                elif values['Referral'] == "null":
                    referral_formatted = "None"
                else:
                    referral_formatted = values["Referral"]

                referral_desc = f';referral={referral_formatted}'

                # generate hpo data
                if values['hpo_ids'] != None:
                    hpo_formatted = values['hpo_ids'].replace(',','|')
                    hpo_desc = f';hpoId={hpo_formatted}'
                else:
                    hpo_desc = ';hpoId=None'

                ## if familyid is populated then generate paternal/maternal ids from familydict
                if values['Familyid']:
                    familyid = values['Familyid']
                    fam_desc = f';familyId={familyid}'
                    
                    ## if proband then add data: family, maternal, paternal
                    if values['FamilyPos'] == 'Proband':

                        # try get paternal info and add to family desc
                        try:
                            paternal = familydict[familyid]['paternalid']
                            fam_desc += f';paternalId={paternal}'
                        except:
                            pass
                        
                        # try to get maternal and add to family desc
                        try:
                            maternal = familydict[familyid]['maternalid']
                            fam_desc += f';maternalId={maternal}'
                        except:
                            pass

                    ## if not proband only inclue family ID
                    else:
                        fam_desc = f';familyId={familyid}'

                    ## format phenotype/affected part. no semicolon needed as at the end of the description.
                    ## only present in the event of a family id
                    if values['Affected']:
                        affected_desc = ';phenotype=2'
                    else:
                        affected_desc = ';phenotype=1'

                else:
                    ## fixes bug where if singleton processed after a family member it kept fam_desc and affected value
                    fam_desc = ''
                    affected_desc = ''


                ## build description field for WINGS
                description_field = f'{description_dict[assay]}{sex_desc}{referral_desc}{hpo_desc}{fam_desc}{affected_desc}'


            ## if TSO500RNA or DNA is main assay, add DNA/RNA field to dict for relevant samples.
            elif assay == 'ctDNA':

                type_dict = {
                            'ctDNA' : 'DNA',
                }

                ## match values wsid with type_dict for sample type column. add to data dict
                '''
                output example:
                {'20-6582': 'DNA'}

                '''
                worksheet_type_dict = {}
                for a, b in zip(worksheets, assays):
                    worksheet_type_dict[a] = type_dict[b]

                ## copy whole of values and change
                changed_values = values
                changed_values['Sample_Type'] = worksheet_type_dict[values['Sample_Plate']]
                changed_values['Sample_Well'] = values['Index_Well']

                ## update main dict
                ss_data_dict[pos].update(changed_values)


                description_field = f'{description_dict[assay]}referral={values["Referral"]}'


            ## have a capture to create a warning description field if not picked up as an assay
            else:
                description_field = 'WARNING: Description not defined'


            ## add to export list for each sample
            ## create blank list to add values to
            samplesheet_row_list = []

            ## iterate through header list and create a line per sample
            for col_header in data_headers:

                if col_header == 'Description':
                    samplesheet_row_list.append(description_field)
                else:
                    samplesheet_row_list.append(values[col_header])

            ## for each sample, turn list of data into a csv delimited line and add to samplesheet header
            samplesheet_line = ','.join(samplesheet_row_list)

            ## for each sample, append the joined line to samplesheet output
            samplesheet_output.append(samplesheet_line)


        # output - print to screen as CSV
        # must be self.stdout.write, not print - print adds extra newlines when launched from call_command within app
        for line in samplesheet_output:

            ## replace keyword EXPID from headers file with experiment id
            if "EXPID" in line:
                line = line.replace("EXPID",experiment_id)

            ## replace keyword DDMMYYY with formatted date
            if "DDMMYYYY" in line:
                download_date = date.today().strftime('%d/%m/%Y')
                line = line.replace("DDMMYYYY", download_date)

            ## WES specific: replace appid and override id with specifics based off sequencer type
            if "APP_ID" in line:
                line = line.replace("APP_ID",app_id)
            if "OVERRIDE_ID" in line:
                line = line.replace("OVERRIDE_ID", override_id)

            self.stdout.write(line)
