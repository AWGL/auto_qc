from django.db import models

# Create your models here.

class Run(models.Model):

	run_id = models.CharField(max_length=50, primary_key=True)

class WorkSheet(models.Model):

	worksheet_id = models.CharField(max_length=50, primary_key=True)

class Sample(models.Model):

	sample_id = models.CharField(max_length=50, primary_key=True)

class Pipeline(models.Model):

	pipeline_id = models.CharField(max_length=50, primary_key=True)

class AnalysisType(models.Model):

	analysis_type_id = models.CharField(max_length=50, primary_key=True)

class RunAnalysis(models.Model):

	run = models.ForeignKey(Run, on_delete=models.CASCADE)
	pipeline = models.ForeignKey(Pipeline, on_delete=models.CASCADE)
	analysis_type = models.ForeignKey(AnalysisType, on_delete=models.CASCADE)

	class Meta:
		unique_together = [['run', 'pipeline', 'analysis_type']]


class SampleAnalysis(models.Model):

	sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
	run = models.ForeignKey(Run, on_delete=models.CASCADE)
	pipeline = models.ForeignKey(Pipeline, on_delete=models.CASCADE)
	analysis_type = models.ForeignKey(AnalysisType, on_delete=models.CASCADE)
	worksheet = models.ForeignKey(WorkSheet, on_delete=models.CASCADE)

	class Meta:
		unique_together = [['sample', 'run', 'pipeline']]


