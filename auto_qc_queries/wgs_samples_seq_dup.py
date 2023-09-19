#Description
#Extracts all samples that have undergone a WGS run of some kind and then extracted all samples that have been sequenced and analysed twice.

# Date = 04/04/23 - KM

#Use python manage.py shell < /export/home/webapps/auto_qc/auto_qc_queries/wgs_samples_seq_dup.py (with env activated)

from qc_database.models import SampleAnalysis, RunAnalysis, Run, Sample
from django.db.models import Q

wgs_samples = SampleAnalysis.objects.filter(Q(analysis_type__analysis_type_id = 'WGS'))
fast_wgs_samples = SampleAnalysis.objects.filter(Q(analysis_type__analysis_type_id = 'FastWGS'))
illumina_wgs_samples = SampleAnalysis.objects.filter(Q(analysis_type__analysis_type_id = 'IlluminaPCRFree38'))

total_list = [*wgs_samples, *fast_wgs_samples, *illumina_wgs_samples]

sample_count = {}

for sample in total_list:
	if sample.sample in sample_count:
		sample_count[sample.sample] = sample_count[sample.sample] + 1
	else:
		sample_count[sample.sample] = 1

#print(sample_count)

dup_samples = [k for k, v in sample_count.items() if v > 1]

for dup in dup_samples:
	print(dup)



