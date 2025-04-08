#Description
#List TSC runs where all samples are female or male

# Date = 12/03/25

## run the following : ##

# cd /u01/apps/autoqc/auto_qc/
# conda activate auto_qc
# python manage.py shell < /u01/apps/autoqc/auto_qc/auto_qc_queries/list_TSC_all_female.py | sort -u

from qc_database.models import Run, RunAnalysis, SampleAnalysis
from django.db.models import Q

# get all TSC runs
all_TSC = RunAnalysis.objects.filter(analysis_type='IlluminaTruSightCancer')

# for each TSC run
for tsc in all_TSC:
    # get all samples in the run
    samples = SampleAnalysis.objects.filter(run = tsc.run)
    # create empty set to store sex
    sex_set = set()
    # for each sample in run
    for sample in samples:
        if "NTC" not in sample.sample.sample_id:
            # add sex to set if not an NTC
            sex_set.add(sample.sex)
    print(sex_set)
    # list runs with only female samples
    if sex_set == {'2'} :
        print(f"run {tsc.run} has only female samples")
    # list runs with only male samples
    elif sex_set == {'1'} :
        print(f"run {tsc.run} has only male samples")
