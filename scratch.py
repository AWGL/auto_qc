from pipeline_monitoring.pipelines import GermlineEnrichment, IlluminaQC, SomaticEnrichment, SomaticAmplicon
from pipeline_monitoring.send_email import send_email_via_api
from qc_analysis.parsers import sample_sheet_parser

"""
germline = GermlineEnrichment(results_dir = '/home/joseph/Documents/auto_qc/data/results/190520_M02641_0219_000000000-CGJT6/IlluminaTruSightCancer',
								sample_names = ['19M06586'],
								run_id = '190520_M02641_0219_000000000-CGJT6')

"""
#print (germline.sample_is_complete('19M06586'))

#print (germline.sample_is_valid('19M06586'))

#print (germline.run_is_complete())

#print (germline.run_is_valid())

#print (germline.run_complete_and_valid())

#send_email_via_api('bioinformatics.team@wales.nhs.uk', 'hello world', 'ahoy world', '/home/joseph/Documents/auto_qc/pipeline_monitoring/credentials.json')

#sample_sheet_parser('/home/joseph/Documents/auto_qc/data/archive/miseq/190520_M02641_0219_000000000-CGJT6/SampleSheet.csv')
"""
illumina_qc = IlluminaQC(fastq_dir = '/home/joseph/Documents/auto_qc/data/archive/fastq/190520_M02641_0219_000000000-CGJT6',
						results_dir ='/home/joseph/Documents/auto_qc/data/results/190520_M02641_0219_000000000-CGJT6/IlluminaTruSightCancer',
						sample_names=['19M06586', 'NTC'],
						n_lanes =1,
						run_id = '190520_M02641_0219_000000000-CGJT6')

"""
#print (illumina_qc.demultiplex_run_is_complete())

#print ('The result of is valid is', illumina_qc.demultiplex_run_is_valid())

#print ('The result of is copied is', illumina_qc.pipeline_copy_complete())

#print(germline.get_fastqc_data())

#print (germline.get_hs_metrics())

#print (germline.get_depth_metrics())

#print (germline.get_contamination())

somatic_amplicon = SomaticAmplicon(results_dir = '/media/joseph/Storage/data/results/190906_M00766_0250_000000000-CJN92/NGHS-101X',
									sample_names = ['19M13120', 'NTC-19-6091-FOCUS4'],
									run_id = '190906_M00766_0250_000000000-CJN92'
									)

print (somatic_amplicon.sample_is_complete('19M13120'))
print (somatic_amplicon.sample_is_valid('19M13120'))
print (somatic_amplicon.run_is_complete())
print (somatic_amplicon.run_is_valid())

print (somatic_amplicon.get_depth_metrics())