#Description
#Count all Auto QC runs and print to screen

# Date = 12/02/25

#Use python manage.py shell < /export/home/webapps/auto_qc/auto_qc_queries/all_runs_counts.py (with env activated)

from qc_database.models import Run
from datetime import date
import datetime
from django.db.models import Q
import csv

# Getting coverage metrics for WGS runs
runs = Run.objects.all().count()
print(runs)

#first_5 = Run.objects.values('instrument_date').order_by('instrument_date')[0:5]
#print(first_5)

last_5 = Run.objects.values('instrument_date').order_by('-instrument_date')[0:5]
print(last_5)

