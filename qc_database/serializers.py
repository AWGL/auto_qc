from rest_framework import serializers
from .models import RunAnalysis, SampleAnalysis

class RunAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = RunAnalysis
        fields = '__all__'

class SampleAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = SampleAnalysis
        fields = '__all__'