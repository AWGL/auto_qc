from pipeline_monitoring.pipelines import GermlineEnrichment
from pipeline_monitoring.send_email import send_email_via_api



germline = GermlineEnrichment(results_dir = '/home/joseph/Documents/auto_qc/data/results/190520_M02641_0219_000000000-CGJT6/IlluminaTruSightCancer',
								sample_names = ['19M06586'],
								run_id = '190520_M02641_0219_000000000-CGJT6')


print (germline.sample_is_complete('19M06586'))

print (germline.sample_is_valid('19M06586'))

print (germline.run_is_complete())

print (germline.run_is_valid())

print (germline.run_complete_and_valid())

send_email_via_api('bioinformatics.team@wales.nhs.uk', 'hello world', 'ahoy world', '/home/joseph/Documents/auto_qc/pipeline_monitoring/credentials.json')