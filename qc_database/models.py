from django.db import models

# Create your models here.

class Instrument(models.Model):

	instrument_id = models.CharField(max_length=255, primary_key=True)
	instrument_type = models.CharField(max_length=255)

	def __str__(self):
		return self.instrument_id

class Run(models.Model):

	run_id = models.CharField(max_length=50, primary_key=True)
	demultiplexing_completed = models.BooleanField(default=False)
	demultiplexing_valid = models.BooleanField(default=False)

	instrument = models.OneToOneField('Instrument', on_delete=models.CASCADE, blank=True, null=True)
	instrument_date = models.DateField(blank=True, null=True)
	setup_date = models.DateField(blank=True, null=True)
	samplesheet_date = models.DateField(blank=True, null=True)
	lanes = models.IntegerField(blank=True, null=True)

	investigator = models.CharField(max_length=255, blank=True, null=True)
	experiment = models.CharField(max_length=255, blank=True, null=True)
	workflow = models.CharField(max_length=255, blank=True, null=True)
	chemistry = models.CharField(max_length=255, blank=True, null=True)

	num_reads = models.IntegerField(blank=True, null=True)
	length_read1 = models.IntegerField(blank=True, null=True)
	length_read2 = models.IntegerField(blank=True, null=True)
	num_indexes = models.IntegerField(blank=True, null=True)
	length_index1 = models.IntegerField(blank=True, null=True)
	length_index2 = models.IntegerField(blank=True, null=True)

	percent_q30 = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
	cluster_density = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
	percent_pf = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
	phasing = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
	prephasing = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
	error_rate = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
	aligned = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)

	def get_status(self):

		if self.demultiplexing_completed == False:

			return 'demultiplexing'

		elif self.demultiplexing_completed == True and self.demultiplexing_valid == True:

			return 'demultiplexing_complete'

		elif self.demultiplexing_completed == True and self.demultiplexing_valid == False:

			return 'demultiplexing_failed'

		else:

			return 'other'


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
	results_completed = models.BooleanField(default=False)
	results_valid = models.BooleanField(default=False)

	class Meta:
		unique_together = [['run', 'pipeline', 'analysis_type']]


class SampleAnalysis(models.Model):

	sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
	run = models.ForeignKey(Run, on_delete=models.CASCADE)
	pipeline = models.ForeignKey(Pipeline, on_delete=models.CASCADE)
	analysis_type = models.ForeignKey(AnalysisType, on_delete=models.CASCADE)
	worksheet = models.ForeignKey(WorkSheet, on_delete=models.CASCADE)
	results_completed = models.BooleanField(default = False)
	results_valid = models.BooleanField(default=False)


	class Meta:
		unique_together = [['sample', 'run', 'pipeline']]


class FastqcData(models.Model):
	"""
	Model to store data from the FastQC output, there will be one entry per fastq file.
	There is a fastq file made for each lane and each read, so a run will usually have 2-4.
	"""
	sample_analysis = models.ForeignKey(SampleAnalysis, on_delete=models.CASCADE)
	read_group = models.CharField(max_length=255, blank=True)
	lane = models.CharField(max_length=255, blank=True)
	basic_statistics = models.CharField(max_length=255, blank=True)
	per_base_sequence_quality = models.CharField(max_length=255, blank=True)
	Per_tile_sequence_quality = models.CharField(max_length=255, blank=True)
	per_sequence_quality_scores = models.CharField(max_length=255, blank=True)
	per_base_sequence_content = models.CharField(max_length=255, blank=True)
	per_sequence_qc_content = models.CharField(max_length=255, blank=True)
	per_base_n_content = models.CharField(max_length=255, blank=True)
	sequence_length_distribution = models.CharField(max_length=255, blank=True)
	sequence_duplication_levels = models.CharField(max_length=255, blank=True)
	overrepresented_sequences = models.CharField(max_length=255, blank=True)
	adapter_content = models.CharField(max_length=255, blank=True)
	kmer_content = models.CharField(max_length=255, blank=True)

	def __str__(self):
		return self.unique_id