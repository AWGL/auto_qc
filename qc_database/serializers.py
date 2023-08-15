from rest_framework import serializers
from qc_database.models import RunAnalysis, SampleAnalysis

class RunAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = RunAnalysis
        fields = ['run', 'start_date', 'pipeline', 'analysis_type', 'results_completed', 'results_valid', 'demultiplexing_completed',
                  'demultiplexing_valid', 'manual_approval', 'comment', 'signoff_user', 'signoff_date']

class SampleAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = SampleAnalysis
        fields = ['sample', 'run', 'pipeline', 'analysis_type', 'worksheet', 'results_completed', 'results_valid',
                  'sex', 'contamination_cutoff', 'ntc_contamination_cutoff', 'min_cnvs_called_cutoff', 'max_cnvs_called_cutoff',
                  'min_average_coverage_cutoff', 'sample_status']
        