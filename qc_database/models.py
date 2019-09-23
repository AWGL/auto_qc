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


class SampleFastqcData(models.Model):
	"""
	Model to store data from the FastQC output, there will be one entry per fastq file.
	There is a fastq file made for each lane and each read, so a run will usually have 2-4.
	"""
	sample_analysis = models.ForeignKey(SampleAnalysis, on_delete=models.CASCADE)
	read_number = models.CharField(max_length=10)
	lane = models.CharField(max_length=10)
	basic_statistics = models.CharField(max_length=10)
	per_base_sequencing_quality = models.CharField(max_length=10)
	per_tile_sequence_quality = models.CharField(max_length=10)
	per_sequence_quality_scores = models.CharField(max_length=10)
	per_base_sequence_content = models.CharField(max_length=10)
	per_sequence_gc_content = models.CharField(max_length=10)
	per_base_n_content = models.CharField(max_length=10)
	sequence_length_distribution = models.CharField(max_length=10)
	sequence_duplication_levels = models.CharField(max_length=10)
	overrepresented_sequences = models.CharField(max_length=10)
	adapter_content = models.CharField(max_length=10)
	kmer_content = models.CharField(max_length=10)



class SampleHsMetrics(models.Model):
	"""
	Model to store output from the Picard HS metrics program.
	One per sample.
	"""

	sample_analysis = models.ForeignKey(SampleAnalysis, on_delete=models.CASCADE)

	bait_set = models.CharField(max_length=255)
	genome_size = models.BigIntegerField(null=True)
	bait_territory = models.BigIntegerField(null=True) 
	target_territory = models.BigIntegerField(null=True)
	bait_design_efficiency = models.BigIntegerField(null=True)
	total_reads = models.IntegerField(null=True)
	pf_reads = models.IntegerField(null=True)
	pf_unique_reads = models.IntegerField(null=True)
	pct_pf_reads = models.IntegerField(null=True)
	pct_pf_uq_reads = models.DecimalField(max_digits=20, decimal_places=4, null=True)
	pf_uq_reads_aligned = models.IntegerField(null=True)
	pct_pf_uq_reads_aligned = models.DecimalField(max_digits=20, decimal_places=4, null=True) 
	pf_bases_aligned = models.IntegerField(null=True)
	pf_uq_bases_aligned = models.IntegerField(null=True)
	on_bait_bases = models.IntegerField(null=True) 
	near_bait_bases = models.IntegerField(null=True)
	off_bait_bases = models.IntegerField(null=True)
	on_target_bases = models.IntegerField(null=True)
	pct_selected_bases = models.DecimalField(max_digits=20, decimal_places=4, null=True)
	pct_off_bait = models.DecimalField(max_digits=20, decimal_places=4, null=True)
	on_bait_vs_selected = models.DecimalField(max_digits=20, decimal_places=4, null=True)
	mean_bait_coverage = models.DecimalField(max_digits=20, decimal_places=4, null=True)
	mean_target_coverage = models.DecimalField(max_digits=20, decimal_places=4, null=True)
	median_target_coverage = models.DecimalField(max_digits=20, decimal_places=4, null=True)
	max_target_coverage = models.DecimalField(max_digits=20, decimal_places=4, null=True)
	pct_usable_bases_on_bait = models.DecimalField(max_digits=20, decimal_places=4, null=True)
	pct_usable_bases_on_target = models.DecimalField(max_digits=20, decimal_places=4, null=True)
	fold_enrichment = models.DecimalField(max_digits=20, decimal_places=4, null=True)
	zero_cvg_targets_pct = models.DecimalField(max_digits=20, decimal_places=4, null=True)
	pct_exc_dupe = models.DecimalField(max_digits=20, decimal_places=4, null=True)
	pct_exc_mapq = models.DecimalField(max_digits=20, decimal_places=4, null=True)
	pct_exc_baseq = models.DecimalField(max_digits=20, decimal_places=4, null=True)
	pct_exc_overlap = models.DecimalField(max_digits=20, decimal_places=4, null=True)
	pct_exc_off_target = models.DecimalField(max_digits=20, decimal_places=4, null=True)
	fold_80_base_penalty = models.DecimalField(max_digits=20, decimal_places=4, null=True)
	pct_target_bases_1x =  models.DecimalField(max_digits=20, decimal_places=4, null=True)
	pct_target_bases_2x = models.DecimalField(max_digits=20, decimal_places=4, null=True)
	pct_target_bases_10x = models.DecimalField(max_digits=20, decimal_places=4, null=True)
	pct_target_bases_20x = models.DecimalField(max_digits=20, decimal_places=4, null=True)
	pct_target_bases_30x = models.DecimalField(max_digits=20, decimal_places=4, null=True)
	pct_target_bases_40x = models.DecimalField(max_digits=20, decimal_places=4, null=True)
	pct_target_bases_50x = models.DecimalField(max_digits=20, decimal_places=4, null=True)
	pct_target_bases_100x = models.DecimalField(max_digits=20, decimal_places=4, null=True)
	hs_library_size = models.DecimalField(max_digits=20, decimal_places=4, null=True)
	hs_penalty_10x = models.DecimalField(max_digits=20, decimal_places=4, null=True) 
	hs_penalty_20x = models.DecimalField(max_digits=20, decimal_places=4, null=True)
	hs_penalty_30x = models.DecimalField(max_digits=20, decimal_places=4, null=True)
	hs_penalty_40x = models.DecimalField(max_digits=20, decimal_places=4, null=True)
	hs_penalty_50x = models.DecimalField(max_digits=20, decimal_places=4, null=True)
	hs_penalty_100x = models.DecimalField(max_digits=20, decimal_places=4, null=True)
	at_dropout = models.DecimalField(max_digits=20, decimal_places=4, null=True)
	gc_dropout = models.DecimalField(max_digits=20, decimal_places=4, null=True)
	het_snp_sensitivity = models.DecimalField(max_digits=20, decimal_places=4, null=True)
	het_snp_q = models.IntegerField(null=True) 


class SampleDepthofCoverageMetrics(models.Model):

	sample_analysis = models.ForeignKey(SampleAnalysis, on_delete=models.CASCADE)
	total = models.BigIntegerField()
	mean = models.DecimalField(max_digits=20, decimal_places=4, null=True)
	granular_first_quartile = models.IntegerField()
	granular_median = models.IntegerField()
	granular_third_quartile = models.IntegerField()
	pct_bases_above_20  = models.DecimalField(max_digits=20, decimal_places=4)


class DuplicationMetrics(models.Model):

	sample_analysis = models.ForeignKey(SampleAnalysis, on_delete=models.CASCADE)
	library = models.CharField(max_length=255)
	unpaired_reads_examined = models.IntegerField()
	read_pairs_examined = models.BigIntegerField()
	secondary_or_supplementary_rds = models.IntegerField()
	unmapped_reads = models.IntegerField()
	unpaired_read_duplicates = models.IntegerField()
	read_pair_duplicates = models.IntegerField()
	read_pair_optical_duplicates = models.IntegerField()
	percent_duplication = models.DecimalField(max_digits=20, decimal_places=4, null=True)
	estimated_library_size = models.BigIntegerField(null=True)

class ContaminationMetrics(models.Model):

	sample_analysis = models.ForeignKey(SampleAnalysis, on_delete=models.CASCADE)
	num_snps = models.IntegerField()
	num_reads = models.IntegerField()
	avg_dp = models.DecimalField(max_digits=20, decimal_places=4)
	freemix = models.DecimalField(max_digits=20, decimal_places=4)
	freelk1 = models.DecimalField(max_digits=20, decimal_places=4)
	freelk0 = models.DecimalField(max_digits=20, decimal_places=4)