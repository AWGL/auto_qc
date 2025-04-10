#Description
# Get coverage metrics from DragenWGSCoverageMetrics from WGS Samples and export to CSV

# Extract uniformity_of_coverage_pct_02mean_over_genome, uniformity_of_coverage_pct_04mean_over_genome and
# insert_length_mean 

# Date = 06/03/23

#Use python manage.py shell < /export/home/webapps/auto_qc/auto_qc_queries/wgs_coverage_metrics.py (with env activated)

from qc_database.models import DragenWGSCoverageMetrics, DragenAlignmentMetrics, SampleAnalysis, RunAnalysis, Run, Sample
from datetime import date
import datetime
from django.db.models import Q
import csv

# Getting coverage metrics for WGS runs
wgs_samples = DragenWGSCoverageMetrics.objects.filter(Q(sample_analysis__analysis_type__analysis_type_id__icontains='WGS'))
align_samples = DragenAlignmentMetrics.objects.filter(Q(sample_analysis__analysis_type__analysis_type_id__icontains='WGS'))

final_male_list = []
final_female_list = []

count = 0

for sample in wgs_samples:

	if sample.sample_analysis.results_valid == True:
		if 'NTC' in sample.sample_analysis.sample.sample_id:
			pass
		else:
			if sample.sample_analysis.sex == '1':
				print(sample.sample_analysis.sample.sample_id, sample.uniformity_of_coverage_pct_02mean_over_genome, sample.sample_analysis.run)
#			elif sample.sample_analysis.sex == '2':
#				if sample.uniformity_of_coverage_pct_02mean_over_genome == '84.61':
#					print(sample.sample_analysis
#					final_female_list.append(sample.uniformity_of_coverage_pct_02mean_over_genome)	


for metric in final_male_list:

	print(metric)


