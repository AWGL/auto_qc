#Description
# Get duplpication metrics for all AgilentOGTFH sample in the last year as a CSV

# Calculate the mean, std dev, min, max etc. for all values

# Print out sample name and run ID for each metric

# Date = 06/02/23

#Use python manage.py shell < /export/home/webapps/auto_qc/auto_qc_queries/fh_duplication_metrics.py (with env activated)

from qc_database.models import DuplicationMetrics, SampleAnalysis, RunAnalysis, Run, Sample
from datetime import date
import datetime
from django.db.models import Q
import csv 

# Getting duplication metrics for fh runs in the last year
date_fh = DuplicationMetrics.objects.filter(Q(sample_analysis__run__run_id__startswith='22')| Q(sample_analysis__run__run_id__icontains='23')).filter(Q(sample_analysis__analysis_type__analysis_type_id__icontains='agilent'))
#print(date_fh)

# Write to csv
with open('fh_duplication_metrics.txt', 'a') as fh_duplication_metrics:

	for metrics in date_fh:

		print(metrics, metrics.library, metrics.unpaired_reads_examined, metrics.read_pairs_examined, metrics.secondary_or_supplementary_rds, metrics.unmapped_reads, metrics.unpaired_read_duplicates, metrics.read_pair_duplicates,  metrics.read_pair_optical_duplicates, metrics.percent_duplication, metrics.estimated_library_size, file = fh_duplication_metrics)

				
