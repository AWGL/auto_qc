# Get the on target reads for NonacusFH

# NT 06/03/25

#Use python manage.py shell < /u01/apps/autoqc/auto_qc//auto_qc_queries/fh_on_target_reads.py (with env activated)

from qc_database.models import
from datetime import date
import datetime
from django.db.models import Q
import csv

nonacusfh = AnalysisType.objects.filter(


