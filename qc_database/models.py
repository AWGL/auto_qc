from django.db import models
from django.conf import settings
from auditlog.registry import auditlog
from auditlog.models import AuditlogHistoryField

class Instrument(models.Model):
	"""
	Model to hold a sequencer

	"""

	instrument_id = models.CharField(max_length=255, primary_key=True)
	instrument_type = models.CharField(max_length=255)

	def __str__(self):
		return self.instrument_id

class Run(models.Model):
	"""
	A run from a sequencer e.g 190927_D00501_0360_AH5JTVBCX3

	Populated with information from the RunParams and Runinfo files.

	"""

	run_id = models.CharField(max_length=50, primary_key=True)

	instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE, blank=True, null=True)
	instrument_date = models.DateField(blank=True, null=True)
	setup_date = models.DateField(blank=True, null=True)
	samplesheet_date = models.DateField(blank=True, null=True)
	lanes = models.IntegerField(blank=True, null=True)

	investigator = models.CharField(max_length=255, blank=True, null=True)
	experiment = models.CharField(max_length=255, blank=True, null=True)
	chemistry = models.CharField(max_length=255, blank=True, null=True)

	num_reads = models.IntegerField(blank=True, null=True)
	length_read1 = models.IntegerField(blank=True, null=True)
	length_read2 = models.IntegerField(blank=True, null=True)
	num_indexes = models.IntegerField(blank=True, null=True)
	length_index1 = models.IntegerField(blank=True, null=True)
	length_index2 = models.IntegerField(blank=True, null=True)
	
	def __str__(self):
		return str(self.run_id)
	

class InteropRunQuality(models.Model):
	"""
	An interop summary file for Illumina 

	"""

	run = models.ForeignKey(Run, on_delete=models.CASCADE)
	read_number = models.IntegerField()
	lane_number = models.IntegerField()
	percent_q30 = models.DecimalField(max_digits=6, decimal_places=3)
	density = models.IntegerField()
	density_pf = models.IntegerField()
	cluster_count = models.IntegerField()
	cluster_count_pf = models.IntegerField()
	error_rate = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
	percent_aligned = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
	percent_pf = models.DecimalField(max_digits=6, decimal_places=3)
	phasing = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
	prephasing = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
	reads = models.BigIntegerField()
	reads_pf = models.BigIntegerField()
	yield_g = models.DecimalField(max_digits=10, decimal_places=3)

	def __str__(self):
		return str(self.run.run_id) + '_' + str(self.read_number) + '_' + str(self.lane_number)

	def display_cluster_density(self):

		return round(self.density / 1000)


class WorkSheet(models.Model):
	"""	
	A worksheet from Shire e.g. 19-5648
	"""

	worksheet_id = models.CharField(max_length=50, primary_key=True)

	def __str__(self):
		return self.worksheet_id


class Sample(models.Model):
	"""
	A sample e.g. 18M13236

	"""

	sample_id = models.CharField(max_length=50, primary_key=True)

	def __str__(self):
		return self.sample_id

	def is_ntc(self):
		"""
		Does the sample name match an ntc pattern.
		"""

		for ntc_marker in ['NTC', 'ntc']:

			if ntc_marker in self.sample_id:

				return True

		return False


class Pipeline(models.Model):
	"""
	A pipeline - should be pipelinename + version

	"""

	pipeline_id = models.CharField(max_length=50, primary_key=True)

	def __str__(self):
		return self.pipeline_id


class AnalysisType(models.Model):
	"""
	An analysis type e.g. IlluminaTruSightCancer

	"""

	analysis_type_id = models.CharField(max_length=50, primary_key=True)

	def __str__(self):
		return self.analysis_type_id


class RunAnalysis(models.Model):
	"""
	A run analysis is a Run object which has been analysed with \
	specific Pipeline and a specific AnalysisType.

	For example 190927_D00501_0360_AH5JTVBCX3 analysed with GermlineEnrichment-2.5.3 on IlluminaTruSightCancer

	"""

	run = models.ForeignKey(Run, on_delete=models.CASCADE)
	start_date = models.DateField(null=True, blank=True)
	pipeline = models.ForeignKey(Pipeline, on_delete=models.CASCADE)
	analysis_type = models.ForeignKey(AnalysisType, on_delete=models.CASCADE)
	results_completed = models.BooleanField(default=False)
	results_valid = models.BooleanField(default=False)
	demultiplexing_completed = models.BooleanField(default=False)
	demultiplexing_valid = models.BooleanField(default=False)
	min_q30_score = models.DecimalField(max_digits=6, decimal_places=3, default=0.8, null=True, blank=True)
	watching = models.BooleanField(default=True)
	manual_approval = models.BooleanField(default=False)
	comment = models.TextField(null=True, blank=True)
	signoff_user = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True, blank=True, related_name='signoff_user')
	signoff_date = models.DateField(blank=True, null=True)
	sensitivity = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
	sensitivity_lower_ci = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
	sensitivity_higher_ci = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
	sensitivity_user = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True, blank=True, related_name='sensitivity_user')
	auto_qc_checks = models.TextField(null=True, blank=True)
	min_variants = models.IntegerField(null=True, blank=True)
	max_variants = models.IntegerField(null=True, blank=True)
	min_titv = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
	max_titv = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
	min_coverage = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
	min_sensitivity = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
	min_fusion_aligned_reads_unique = models.IntegerField(null=True, blank=True)
	min_relatedness_parents = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
	max_relatedness_unrelated = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
	max_relatedness_between_parents = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
	max_child_parent_relatedness = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
	min_on_target_reads=models.IntegerField(null=True, blank=True)

	#for TSO500 only- ntc contamination for other runs in sampleAnalysis object
	max_ntc_contamination = models.IntegerField(null=True, blank=True)

	history = AuditlogHistoryField()

	class Meta:
		unique_together = [['run', 'pipeline', 'analysis_type']]

	def __str__(self):
		return self.run.run_id + '_' + self.pipeline.pipeline_id + '_' + self.analysis_type.analysis_type_id

	def get_n_samples_completed(self):

		count = 0

		sample_analyses = SampleAnalysis.objects.filter(run = self.run,
														pipeline = self.pipeline,
														analysis_type = self.analysis_type
														)

		completed = [x.results_completed for x in sample_analyses]

		return completed.count(True), len(completed)


	def get_n_samples_valid(self):

		count = 0

		sample_analyses = SampleAnalysis.objects.filter(run = self.run,
														pipeline = self.pipeline,
														analysis_type = self.analysis_type
														)

		completed = [x.results_valid for x in sample_analyses]

		return completed.count(True), len(completed)


	def passes_run_level_qc(self):

		interop_qualities = InteropRunQuality.objects.filter(run = self.run)

		for interop_quality in interop_qualities:

			if interop_quality.percent_q30 < (self.min_q30_score*100):

				return False

		return True

	def get_ntc_sample(self, worksheet):
		"""
		Get the NTC sample
		"""
		# DragenWGS NTC may be split across two assays e.g. WGS and FastWGS
		if 'DragenWGS' in self.pipeline.pipeline_id:

			samples = SampleAnalysis.objects.filter(run = self.run,
												pipeline = self.pipeline,
												worksheet = worksheet
												)
		else:

			samples = SampleAnalysis.objects.filter(run = self.run,
												pipeline = self.pipeline,
												analysis_type = self.analysis_type,
												worksheet = worksheet
												)
		ntc_samples = []

		for sample in samples:

			for ntc_marker in ['ntc', 'NTC']:

				if ntc_marker in sample.sample_id:

					ntc_samples.append(sample)

		return ntc_samples

	def get_worksheets(self):

		worksheets = []

		samples = SampleAnalysis.objects.filter(
			run = self.run,
			pipeline = self.pipeline,
			analysis_type = self.analysis_type
			)

		for sample in samples:

			worksheets.append(sample.worksheet.worksheet_id)

		return '|'.join(list(set(worksheets)))


	def passes_sensitivity(self):

		if self.min_sensitivity == None:

			return None

		elif self.sensitivity == None:

			return None

		elif self.sensitivity_lower_ci == None:

			return None

		elif self.sensitivity_higher_ci == None:

			return None

		else:

			if self.sensitivity_lower_ci > self.min_sensitivity:

				return True

			else:

				return False


	def passes_relatedness(self):

		relatedness_obj = RelatednessQuality.objects.filter(run_analysis = self)

		if len(relatedness_obj) == 1:

			return relatedness_obj[0].results_valid, relatedness_obj[0].comment

		return False, 'Oops'


	def passes_auto_qc(self):
		"""
		Check whether the run analysis passes all QC checks.

		Reads from config file to find out which checks to complete.

		"""

		checks_to_do = self.auto_qc_checks

		if checks_to_do == None:

			return False, ['No Configuration For this Pipeline.']

		checks_to_do = checks_to_do.split(',')

		samples = SampleAnalysis.objects.filter(run = self.run,
												pipeline = self.pipeline,
												analysis_type = self.analysis_type)


		# check is complete and valid

		new_samples_list = []

		reasons_to_fail = []

		if self.demultiplexing_completed == False:

			reasons_to_fail.append('Demultiplexing not complete for some samples')

		if self.demultiplexing_valid == False:

			reasons_to_fail.append( 'Demultiplexing not valid for some samples')

		if self.results_completed == False:

			return False,['Run results not completed']

		if self.results_valid == False:

			return False,['Run results not valid']

		for sample in samples:

			if sample.results_completed == False:

				reasons_to_fail.append('Results not complete for some samples')

			if sample.results_valid == False:

				reasons_to_fail.append('Results not valid for some samples')


			if sample.sample.is_ntc() == False:

				new_samples_list.append(sample)

		if 'pct_q30' in checks_to_do:

			if self.passes_run_level_qc() == False:

				reasons_to_fail.append('Q30 Fail')


		if 'relatedness' in checks_to_do:
			
			if self.passes_relatedness()[0] == False:
				
				reasons_to_fail.append(self.passes_relatedness()[1])


		if 'contamination' in checks_to_do:

			for sample in new_samples_list:

				if sample.passes_contamination() == False:

					reasons_to_fail.append('Contamination Fail')

		if 'ntc_contamination' in checks_to_do:

			for sample in new_samples_list:

				if sample.passes_ntc_contamination() != True:

					reasons_to_fail.append('NTC Contamination Fail')

		# DNA
		if 'ntc_contamination_TSO500' in checks_to_do:

			for sample_object in new_samples_list:

				if "NTC" not in sample_object.sample_id:

					if sample_object.passes_percent_ntc_tso500() != True:

						reasons_to_fail.append('NTC Contamination Fail')

		# RNA
		if 'reads_tso500' in checks_to_do:

			for sample in new_samples_list:

				if sample.passes_reads_tso500() != True:

					reasons_to_fail.append('TSO500 Read Fail')

		if 'sex_match' in checks_to_do:

			for sample in new_samples_list:

				if sample.passes_sex_check() == False:

					reasons_to_fail.append('Sex Match Fail')

		if 'variant_check' in checks_to_do:

			for sample in new_samples_list:

				if sample.passes_variant_count_check() == False:

					reasons_to_fail.append('Variant Count Fail')

		if 'sensitivity' in checks_to_do:

			if self.passes_sensitivity() == False:

				reasons_to_fail.append('Low Sensitivity')

		if 'coverage' in checks_to_do:
			
			for sample in new_samples_list:

				if sample.passes_region_coverage_over_20() == False:

					reasons_to_fail.append('Low Coverage >20x')

		if 'titv' in checks_to_do:

			for sample in new_samples_list:

				if sample.passes_titv() == False:

					reasons_to_fail.append('Titv Ratio out of range for at least one sample')

		if 'fastqc' in checks_to_do:

			for sample in new_samples_list:

				if sample.passes_fastqc() == False:

					reasons_to_fail.append('FASTQC Fail')


		if 'fusion_contamination' in checks_to_do:

			for sample in new_samples_list:

				if sample.passes_fusion_contamination() == False:

					reasons_to_fail.append('Fusion Contamination Fail')

		if 'fusion_alignment' in checks_to_do:

			for sample in new_samples_list:

				if sample.passes_fusion_aligned_reads_duplicates() == False:

					reasons_to_fail.append('Fusion Aligned Reads Unique Fail')	

		if len(reasons_to_fail) ==0:

			return True, ['All Pass']

		else:

			return False, list(set(reasons_to_fail))
			

class RelatednessQuality(models.Model):
	"""
	Model to calculate whether relatedness passes or fails
	"""
	run_analysis = models.ForeignKey(RunAnalysis, on_delete=models.CASCADE)
	results_valid = models.BooleanField(default=False)
	comment = models.TextField(null=True, blank=True)

	def __str__(self):
		return str(self.run_analysis) + " - " + str(self.results_valid)

class SampleAnalysis(models.Model):
	"""
	A SampleAnalysis object is a Sample analysed on a specific Run with a specific Pipeline on \
	a specific AnalysisType.

	"""

	sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
	run = models.ForeignKey(Run, on_delete=models.CASCADE)
	pipeline = models.ForeignKey(Pipeline, on_delete=models.CASCADE)
	analysis_type = models.ForeignKey(AnalysisType, on_delete=models.CASCADE)
	worksheet = models.ForeignKey(WorkSheet, on_delete=models.CASCADE)
	results_completed = models.BooleanField(default = False)
	results_valid = models.BooleanField(default=False)
	sex = models.CharField(max_length=10, null=True, blank=True)
	contamination_cutoff = models.DecimalField(max_digits=6, decimal_places=3, default=0.15, null=True, blank=True)
	ntc_contamination_cutoff = models.DecimalField(max_digits=6, decimal_places=3, default=10.0, null=True, blank=True)

	history = AuditlogHistoryField()

	class Meta:
		unique_together = [['sample', 'run', 'pipeline', 'analysis_type', 'worksheet']]

	def __str__(self):
		return f'{self.run.run_id}_{self.pipeline.pipeline_id}_{self.analysis_type.analysis_type_id}_{self.sample.sample_id}'

	def passes_fastqc(self):
		"""
		Does the sample have a PASS for the key FASTQC metrics?
		"""

		fastqc_objs = SampleFastqcData.objects.filter(sample_analysis=self)

		if len(fastqc_objs) == 0:

			return None

		for fastqc in fastqc_objs:

			if fastqc.basic_statistics == 'FAIL':

				return False

			elif fastqc.per_base_sequencing_quality == 'FAIL':

				return False

			elif fastqc.per_tile_sequence_quality == 'FAIL': 

				return False

			elif fastqc.per_sequence_quality_scores == 'FAIL': 

				return False

			elif fastqc.per_base_n_content == 'FAIL': 

				return False

		return True

	def get_total_reads(self):


		try:

			hs_metrics_obj = SampleHsMetrics.objects.get(sample_analysis= self)
			return hs_metrics_obj.total_reads

		except:

			try:

				dragen_alignment_metrics = DragenAlignmentMetrics.objects.get(sample_analysis= self)
				return dragen_alignment_metrics.total_input_reads

			except:

				return None

		return None

	def get_contamination(self):


		if 'DragenWGS' in self.pipeline.pipeline_id:

			contamination_obj = DragenAlignmentMetrics.objects.get(sample_analysis=self)

			return contamination_obj.estimated_sample_contamination

		else:

			try:

				contamination_obj = ContaminationMetrics.objects.get(sample_analysis=self)

			except:

				return 'NA'


		return contamination_obj.freemix

	def passes_contamination(self):

		try:

			contamination = self.get_contamination()

		except:
			
			return None

		if contamination > self.contamination_cutoff:

				return False

		return True

	def passes_ntc_contamination(self):

		run_analysis = RunAnalysis.objects.get(run = self.run,
											pipeline = self.pipeline,
											analysis_type = self.analysis_type
												)

		total_reads = self.get_total_reads()

		if total_reads == None:

			return 'Cannot count reads for sample.'

		ntc_objs = run_analysis.get_ntc_sample(self.worksheet)

		if len(ntc_objs) == 0:

			return False

		for ntc in ntc_objs:

			ntc_reads = ntc.get_total_reads()

			if self == ntc:

				return 'NA'

			if ntc_reads == None:

				return 'Cannot count reads for sample.'

			if (ntc_reads * self.ntc_contamination_cutoff) > total_reads:

				return False

		return True

	def get_reads_tso500(self):

		try:

			tso500_reads = Tso500Reads.objects.filter(sample_analysis = self)

		except:

			return None

		if len(tso500_reads) != 1:

			return None

		else:

			return tso500_reads[0].total_on_target_reads

	def passes_reads_tso500(self):

		run_analysis = self.get_run_analysis()

		try:
			reads = self.get_reads_tso500()

			if reads < run_analysis.min_on_target_reads:

				return False
		except:

			return None

		return True

	def get_sex(self):

		sex = self.sex

		if sex == '0':

			return 'unknown'

		elif sex == '1':

			return 'male'

		elif sex == '2':

			return 'female'

		else:

			return 'NA'


	def get_calculated_sex(self):

		if 'DragenWGS' in self.pipeline.pipeline_id:

			wgs_obj = DragenWGSCoverageMetrics.objects.get(sample_analysis=self)

			if wgs_obj.predicted_sex_chromosome_ploidy is None:

				wgs_obj = DragenPloidyMetrics.objects.get(sample_analysis=self)
				
				if wgs_obj.ploidy_estimation == 'XX':

					return 'female'

				elif wgs_obj.ploidy_estimation == 'XY':

					return 'male'

				else:

					return 'unknown'

			elif wgs_obj.predicted_sex_chromosome_ploidy == 'XX':

				return 'female'

			elif wgs_obj.predicted_sex_chromosome_ploidy == 'XY':

				return 'male'

			else:

				return 'unknown'

		else:

			try:
				sex_obj = CalculatedSexMetrics.objects.get(sample_analysis=self)
			except:
				return 'NA'

			return sex_obj.calculated_sex.lower()

	def passes_sex_check(self):

		if self.get_calculated_sex() == 'unknown':

			return False

		if self.get_calculated_sex() == self.get_sex():

			return True

		return False

	def get_run_analysis(self):

		try:

			run_analysis = RunAnalysis.objects.get(
				run = self.run,
				pipeline = self.pipeline,
				analysis_type = self.analysis_type
				)

		except:

			return None

		return run_analysis

	def get_variant_count(self):

		if 'DragenWGS' in self.pipeline.pipeline_id:

			variant_calling_metrics = DragenVariantCallingMetrics.objects.get(sample_analysis=self)

			return variant_calling_metrics.total

		else:

			try:

				variant_calling_metrics = VariantCallingMetrics.objects.get(sample_analysis=self)

				return variant_calling_metrics.total_snps + variant_calling_metrics.total_indels + variant_calling_metrics.total_complex_indels

			except:

				try:

					variant_count_metrics = VCFVariantCount.objects.get(sample_analysis=self)

					return variant_count_metrics.variant_count

				except:

					pass

			return 'NA'

	def passes_variant_count_check(self):

		run_analysis = self.get_run_analysis()

		if run_analysis == None:

			return False

		min_variants = run_analysis.min_variants
		max_variants = run_analysis.max_variants

		variant_count = self.get_variant_count()

		if variant_count == 'NA':

			return False

		else:

			if variant_count > min_variants and variant_count < max_variants:

				return True

		return False

	def get_region_coverage_over_20(self):

		try:
			coverage = DragenRegionCoverageMetrics.objects.get(sample_analysis = self)
		except:
			
			try:
				coverage = CustomCoverageMetrics.objects.filter(sample_analysis = self)

				if len(coverage) != 1:

					return None

				else:

					return coverage[0].pct_greater_20x

			except:
				return None





		return coverage.pct_of_qc_coverage_region_with_coverage_20x_inf

	def passes_region_coverage_over_20(self):

		run_analysis = self.get_run_analysis()

		if run_analysis == None:

			return False

		min_cov = run_analysis.min_coverage

		cov_gtr_20 = self.get_region_coverage_over_20()

		if cov_gtr_20 == None:

			return False

		else:

			if cov_gtr_20 >= min_cov:

				return True

		return False

	def get_titv(self):

		try:
			titv = DragenVariantCallingMetrics.objects.filter(sample_analysis = self)
		except:
			return None

		if len(titv) != 1:

			return None

		else:

			return titv[0].titv_ratio


	def passes_titv(self):

		titv = self.get_titv()

		run_analysis = self.get_run_analysis()

		if run_analysis == None:

			return False

		min_titv = run_analysis.min_titv
		max_titv = run_analysis.max_titv

		if titv < min_titv:

			return False

		if titv > max_titv:

			return False

		return True


	def get_aligned_reads_fusion(self):

		try:
			alignment_metrics = FusionAlignmentMetrics.objects.filter(sample_analysis = self)
		except:
			return None

		if len(alignment_metrics) != 1:

			return None

		else:

			return alignment_metrics[0]





	def get_percent_ntc_tso500(self):

		try:
			tso500_reads = Tso500Reads.objects.filter(sample_analysis = self)
		except:
			return None

		if len(tso500_reads) != 1:

			return None

		else:

			return tso500_reads[0].percent_ntc_reads




	def get_percent_ntc_aligned_tso500(self):

		try:
			tso500_aligned_reads = Tso500Reads.objects.filter(sample_analysis = self)
		except:
			return None

		if len(tso500_aligned_reads) != 1:

			return None

		else:

			return tso500_aligned_reads[0].percent_ntc_contamination



	def passes_percent_ntc_tso500(self):

		run_analysis = self.get_run_analysis()

		if run_analysis == None:

			return False


		try:

			percent_ntc = self.get_percent_ntc_tso500()


			if percent_ntc < run_analysis.max_ntc_contamination:

				return True
		except:

			return None

		return False


	def passes_percent_ntc_aligned_tso500(self):

		run_analysis = self.get_run_analysis()

		if run_analysis == None:

			return False



		try:

			percent_ntc = self.get_percent_ntc_aligned_tso500()


			if percent_ntc < run_analysis.max_ntc_contamination:

				return True
		except:

			return None

		return False


	def get_total_pf_reads_tso500(self):

		try:
			tso500_reads_DNA= Tso500Reads.objects.filter(sample_analysis = self)
		except:
			return None

		if len(tso500_reads_DNA) != 1:

			return None

		else:

			return tso500_reads_DNA[0].total_pf_reads

	def get_total_aligned_reads_tso500(self):

		try:
			tso500_aligned_reads_DNA= Tso500Reads.objects.filter(sample_analysis = self)
		except:
			return None

		if len(tso500_aligned_reads_DNA) != 1:

			return None

		else:

			return tso500_aligned_reads_DNA[0].aligned_reads



	def get_contamination_fusion(self):

		try:
			contamination_metrics = FusionContamination.objects.filter(sample_analysis = self)
		except:
			return None

		if len(contamination_metrics) != 1:

			return None

		else:

			return contamination_metrics[0].contamination

	def get_contamination_referral_fusion(self):

		try:
			contamination_metrics = FusionContamination.objects.filter(sample_analysis = self)
		except:
			return None

		if len(contamination_metrics) != 1:

			return None

		else:

			return contamination_metrics[0].contamination_referral

	def passes_fusion_contamination(self):

		if self.get_contamination_fusion() == True:

			return False

		elif self.get_contamination_referral_fusion() == True:

			return False

		else:

			return True

	def passes_fusion_aligned_reads_duplicates(self):

		run_analysis = self.get_run_analysis()

		aligned_reads = self.get_aligned_reads_fusion()

		if aligned_reads == None:

			return False

		if aligned_reads.unique_reads_aligned < run_analysis.min_fusion_aligned_reads_unique:

			return False

		return True

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
	kmer_content = models.CharField(max_length=10, null=True, blank=True)

	def __str__(self):
		return f'{self.sample_analysis}_{self.read_number}_{self.lane}'


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
	bait_design_efficiency = models.DecimalField(max_digits=20, decimal_places=4, null=True)
	total_reads = models.BigIntegerField(null=True)
	pf_reads = models.BigIntegerField(null=True)
	pf_unique_reads = models.BigIntegerField(null=True)
	pct_pf_reads = models.DecimalField(max_digits=20, decimal_places=4, null=True)
	pct_pf_uq_reads = models.DecimalField(max_digits=20, decimal_places=4, null=True)
	pf_uq_reads_aligned = models.BigIntegerField(null=True)
	pct_pf_uq_reads_aligned = models.DecimalField(max_digits=20, decimal_places=4, null=True) 
	pf_bases_aligned = models.BigIntegerField(null=True)
	pf_uq_bases_aligned = models.BigIntegerField(null=True)
	on_bait_bases = models.BigIntegerField(null=True) 
	near_bait_bases = models.BigIntegerField(null=True)
	off_bait_bases = models.BigIntegerField(null=True)
	on_target_bases = models.BigIntegerField(null=True)
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
	het_snp_q = models.BigIntegerField(null=True) 
	pf_bases = models.BigIntegerField(null=True, blank=True)
	min_target_coverage = models.BigIntegerField(null=True, blank=True)
	pct_exc_adapter = models.DecimalField(max_digits=20, decimal_places=4, null=True)

	def __str__(self):
		return str(self.sample_analysis)


class SampleDepthofCoverageMetrics(models.Model):
	"""
	Model for GATK DepthOfCoverage summary metrics

	"""

	sample_analysis = models.ForeignKey(SampleAnalysis, on_delete=models.CASCADE)
	total = models.BigIntegerField()
	mean = models.DecimalField(max_digits=20, decimal_places=4, null=True)
	granular_first_quartile = models.IntegerField()
	granular_median = models.IntegerField()
	granular_third_quartile = models.IntegerField()
	pct_bases_above_20  = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
	pct_bases_above_250 = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
	pct_bases_above_500 = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)

	def __str__(self):
		return str(self.sample_analysis)


class DuplicationMetrics(models.Model):
	"""
	Metrics from the MarkDuplicates program.

	"""

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

	def __str__(self):
		return str(self.sample_analysis)


class ContaminationMetrics(models.Model):
	"""
	Metrics from the Contamination program
	"""

	sample_analysis = models.ForeignKey(SampleAnalysis, on_delete=models.CASCADE)
	num_snps = models.IntegerField()
	num_reads = models.IntegerField()
	avg_dp = models.DecimalField(max_digits=20, decimal_places=4)
	freemix = models.DecimalField(max_digits=20, decimal_places=4)
	freelk1 = models.DecimalField(max_digits=20, decimal_places=4)
	freelk0 = models.DecimalField(max_digits=20, decimal_places=4)

	def __str__(self):
		return str(self.sample_analysis)


class CalculatedSexMetrics(models.Model):
	"""
	Store the calculated sex
	"""

	sample_analysis = models.ForeignKey(SampleAnalysis, on_delete=models.CASCADE)
	calculated_sex = models.CharField(max_length=10)

	def __str__(self):
		return str(self.sample_analysis)


class AlignmentMetrics(models.Model):
	"""
	Store alignment metrics

	"""

	sample_analysis = models.ForeignKey(SampleAnalysis, on_delete=models.CASCADE)
	category = models.CharField(max_length=16)
	total_reads = models.BigIntegerField()
	pf_reads = models.BigIntegerField()
	pct_pf_reads = models.DecimalField(max_digits=6, decimal_places=4)
	pf_noise_reads = models.IntegerField()
	pf_reads_aligned = models.BigIntegerField()
	pct_pf_reads_aligned = models.DecimalField(max_digits=6, decimal_places=4)
	pf_aligned_bases = models.BigIntegerField()
	pf_hq_aligned_reads = models.BigIntegerField()
	pf_hq_aligned_bases = models.BigIntegerField()
	pf_hq_aligned_q20_bases = models.BigIntegerField()
	pf_hq_median_mismatches = models.DecimalField(max_digits=6, decimal_places=4)
	pf_mismatch_rate = models.DecimalField(max_digits=6, decimal_places=4)
	pf_hq_error_rate = models.DecimalField(max_digits=6, decimal_places=4)
	pf_indel_rate = models.DecimalField(max_digits=6, decimal_places=4)
	mean_read_length = models.DecimalField(max_digits=20, decimal_places=4)
	reads_aligned_in_pairs = models.BigIntegerField()
	pct_reads_aligned_in_pairs = models.DecimalField(max_digits=6, decimal_places=4)
	pf_reads_improper_pairs = models.IntegerField()
	pct_pf_reads_improper_pairs = models.DecimalField(max_digits=6, decimal_places=4)
	bad_cycles = models.IntegerField()
	strand_balance = models.DecimalField(max_digits=6, decimal_places=4)
	pct_chimeras = models.DecimalField(max_digits=6, decimal_places=4)
	pct_adapter = models.DecimalField(max_digits=6, decimal_places=4)

	def __str__(self):
		return str(self.sample_analysis) + '_' + self.category


class VariantCallingMetrics(models.Model):
	"""
	Store variant calling detail metrics

	"""

	sample_analysis = models.ForeignKey(SampleAnalysis, on_delete=models.CASCADE)
	het_homvar_ratio = models.DecimalField(max_digits=7, decimal_places=3, null=True, blank=True)
	pct_gq0_variants = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
	total_gq0_variants  = models.IntegerField()
	total_het_depth = models.BigIntegerField()
	total_snps = models.IntegerField()
	num_in_db_snp = models.IntegerField()
	novel_snps = models.IntegerField()
	filtered_snps = models.IntegerField()
	pct_dbsnp = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
	dbsnp_titv = models.DecimalField(max_digits=7, decimal_places=3)
	novel_titv = models.DecimalField(max_digits=7, decimal_places=3)
	total_indels = models.IntegerField()
	novel_indels = models.IntegerField()
	filtered_indels = models.IntegerField()
	pct_dbsnp_indels = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
	num_in_db_snp_indels = models.IntegerField()
	dbsnp_ins_del_ratio = models.DecimalField(max_digits=6, decimal_places=3)
	novel_ins_del_ratio = models.DecimalField(max_digits=6, decimal_places=3)
	total_multiallelic_snps = models.IntegerField()
	num_in_db_snp_multiallelic = models.IntegerField()
	total_complex_indels = models.IntegerField()
	num_in_db_snp_complex_indels = models.IntegerField()
	snp_reference_bias = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
	num_singletons = models.IntegerField()

	def __str__(self):
		return str(self.sample_analysis)


class InsertMetrics(models.Model):
	"""
	Store insert metrics

	"""

	sample_analysis = models.ForeignKey(SampleAnalysis, on_delete=models.CASCADE)
	mode_insert_size = models.IntegerField(null=True, blank=True) 
	median_insert_size = models.DecimalField(max_digits=10, decimal_places=3)
	median_absolute_deviation = models.DecimalField(max_digits=6, decimal_places=3)
	min_insert_size = models.IntegerField()
	max_insert_size = models.BigIntegerField()
	mean_insert_size = models.DecimalField(max_digits=10, decimal_places=3)
	standard_deviation = models.DecimalField(max_digits=10, decimal_places=3)
	read_pairs = models.BigIntegerField()
	pair_orientation = models.CharField(max_length=3)
	width_of_10_percent = models.IntegerField(null=True, blank=True)
	width_of_20_percent = models.IntegerField(null=True, blank=True)
	width_of_30_percent = models.IntegerField(null=True, blank=True)
	width_of_40_percent = models.IntegerField(null=True, blank=True)
	width_of_50_percent = models.IntegerField(null=True, blank=True)
	width_of_60_percent = models.IntegerField(null=True, blank=True)
	width_of_70_percent = models.IntegerField(null=True, blank=True)
	width_of_80_percent = models.IntegerField(null=True, blank=True)
	width_of_90_percent = models.IntegerField(null=True, blank=True)
	width_of_95_percent = models.IntegerField(null=True, blank=True)
	width_of_99_percent = models.IntegerField(null=True, blank=True)

	def __str__(self):
		return str(self.sample_analysis)


class VCFVariantCount(models.Model):
	"""
	Store a count of the variants in a VCF

	"""
	sample_analysis = models.ForeignKey(SampleAnalysis, on_delete=models.CASCADE)
	variant_count = models.IntegerField()


class InteropIndexMetrics(models.Model):
	"""
	Store the interop index information
	"""

	sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
	run = models.ForeignKey(Run, on_delete=models.CASCADE)
	pct_reads_identified = models.DecimalField(max_digits=10, decimal_places=3)

	def __str__(self):
		return str(self.run) + '_' + str(self.sample)

class DragenAlignmentMetrics(models.Model):
	"""
	Store the dragen alignments metrics file
	"""

	sample_analysis = models.ForeignKey(SampleAnalysis, on_delete=models.CASCADE)
	total_input_reads = models.BigIntegerField(null=True, blank=True)
	number_of_duplicate_marked_reads = models.BigIntegerField(null=True, blank=True)
	number_of_duplicate_marked_and_mate_reads_removed = models.BigIntegerField(null=True, blank=True)
	number_of_unique_reads_excl_duplicate_marked_reads = models.BigIntegerField(null=True, blank=True)
	reads_with_mate_sequenced = models.BigIntegerField(null=True, blank=True)
	reads_without_mate_sequenced = models.BigIntegerField(null=True, blank=True)
	qcfailed_reads = models.BigIntegerField(null=True, blank=True)
	mapped_reads = models.BigIntegerField(null=True, blank=True)
	mapped_reads_adjusted_for_filtered_mapping = models.BigIntegerField(null=True, blank=True)
	mapped_reads_r1 = models.BigIntegerField(null=True, blank=True)
	mapped_reads_r2 = models.BigIntegerField(null=True, blank=True)
	number_of_unique_mapped_reads_excl_duplicate_marked_reads = models.BigIntegerField(null=True, blank=True)
	unmapped_reads = models.BigIntegerField(null=True, blank=True)
	unmapped_reads_adjusted_for_filtered_mapping = models.BigIntegerField(null=True, blank=True)
	adjustment_of_reads_matching_nonreference_decoys = models.BigIntegerField(null=True, blank=True)
	singleton_reads_itself_mapped_mate_unmapped = models.BigIntegerField(null=True, blank=True)
	paired_reads_itself_mate_mapped = models.BigIntegerField(null=True, blank=True)
	properly_paired_reads = models.BigIntegerField(null=True, blank=True)
	not_properly_paired_reads_discordant = models.BigIntegerField(null=True, blank=True)
	paired_reads_mapped_to_different_chromosomes = models.BigIntegerField(null=True, blank=True)
	paired_reads_mapped_to_different_chromosomes_mapq10 = models.BigIntegerField(null=True, blank=True)
	reads_with_mapq_40inf = models.BigIntegerField(null=True, blank=True)
	reads_with_mapq_3040 = models.BigIntegerField(null=True, blank=True)
	reads_with_mapq_2030 = models.BigIntegerField(null=True, blank=True)
	reads_with_mapq_1020 = models.BigIntegerField(null=True, blank=True)
	reads_with_mapq_010 = models.BigIntegerField(null=True, blank=True)
	reads_with_mapq_na_unmapped_reads = models.BigIntegerField(null=True, blank=True)
	reads_with_indel_r1 = models.BigIntegerField(null=True, blank=True)
	reads_with_indel_r2 = models.BigIntegerField(null=True, blank=True)
	total_bases = models.BigIntegerField(null=True, blank=True)
	total_bases_r1 = models.BigIntegerField(null=True, blank=True)
	total_bases_r2 = models.BigIntegerField(null=True, blank=True)
	mapped_bases = models.BigIntegerField(null=True, blank=True)
	mapped_bases_r1 = models.BigIntegerField(null=True, blank=True)
	mapped_bases_r2 = models.BigIntegerField(null=True, blank=True)
	softclipped_bases = models.BigIntegerField(null=True, blank=True)
	softclipped_bases_r1 = models.BigIntegerField(null=True, blank=True)
	softclipped_bases_r2 = models.BigIntegerField(null=True, blank=True)
	hardclipped_bases = models.BigIntegerField(null=True, blank=True)
	hardclipped_bases_r1 = models.BigIntegerField(null=True, blank=True)
	hardclipped_bases_r2 = models.BigIntegerField(null=True, blank=True)
	mismatched_bases_r1 = models.BigIntegerField(null=True, blank=True)
	mismatched_bases_r2 = models.BigIntegerField(null=True, blank=True)
	mismatched_bases_r1_excl_indels = models.BigIntegerField(null=True, blank=True)
	mismatched_bases_r2_excl_indels = models.BigIntegerField(null=True, blank=True)
	q30_bases = models.BigIntegerField(null=True, blank=True)
	q30_bases_r1 = models.BigIntegerField(null=True, blank=True)
	q30_bases_r2 = models.BigIntegerField(null=True, blank=True)
	q30_bases_excl_dups_clipped_bases = models.BigIntegerField(null=True, blank=True)
	total_alignments = models.BigIntegerField(null=True, blank=True)
	secondary_alignments = models.IntegerField(null=True, blank=True)
	supplementary_chimeric_alignments = models.BigIntegerField(null=True, blank=True)
	estimated_read_length = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	average_sequenced_coverage_over_target_region = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True)
	bases_in_reference_genome = models.BigIntegerField(null=True, blank=True)
	bases_in_target_bed_of_genome = models.BigIntegerField(null=True, blank=True)
	insert_length_mean = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	insert_length_median = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	insert_length_standard_deviation = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	provided_sex_chromosome_ploidy = models.IntegerField(null=True, blank=True)
	dragen_mapping_rate_mil_readssecond = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	average_sequenced_coverage_over_genome = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	estimated_sample_contamination = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	estimated_sample_contamination_standard_error = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

class DragenVariantCallingMetrics(models.Model):
	"""
	Store the dragen variant calling metrics file
	"""
	sample_analysis = models.ForeignKey(SampleAnalysis, on_delete=models.CASCADE)
	total = models.IntegerField(null=True, blank=True)
	biallelic = models.IntegerField(null=True, blank=True)
	multiallelic = models.IntegerField(null=True, blank=True)
	snps = models.IntegerField(null=True, blank=True)
	insertions_hom = models.IntegerField(null=True, blank=True)
	insertions_het = models.IntegerField(null=True, blank=True)
	deletions_hom = models.IntegerField(null=True, blank=True)
	deletions_het = models.IntegerField(null=True, blank=True)
	indels_het = models.IntegerField(null=True, blank=True)
	chr_x_number_of_snps_over_genome = models.IntegerField(null=True, blank=True)
	chr_y_number_of_snps_over_genome = models.IntegerField(null=True, blank=True)
	chr_x_snpschr_y_snps_ratio_over_genome = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
	snp_transitions = models.IntegerField(null=True, blank=True)
	snp_transversions = models.IntegerField(null=True, blank=True)
	titv_ratio = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	heterozygous = models.IntegerField(null=True, blank=True)
	homozygous = models.IntegerField(null=True, blank=True)
	hethom_ratio  = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	in_dbsnp = models.IntegerField(null=True, blank=True)
	not_in_dbsnp = models.IntegerField(null=True, blank=True)


class DragenWGSCoverageMetrics(models.Model):
	"""
	Store the dragen WGS coverage metrics file
	"""
	sample_analysis = models.ForeignKey(SampleAnalysis, on_delete=models.CASCADE)
	aligned_bases = models.BigIntegerField(null=True, blank=True)
	aligned_bases_in_genome = models.BigIntegerField(null=True, blank=True)
	average_alignment_coverage_over_genome = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	uniformity_of_coverage_pct_02mean_over_genome = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	uniformity_of_coverage_pct_04mean_over_genome = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	pct_of_genome_with_coverage_1500x_inf = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	pct_of_genome_with_coverage_1000x_inf = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	pct_of_genome_with_coverage_500x_inf = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	pct_of_genome_with_coverage_100x_inf = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	pct_of_genome_with_coverage_50x_inf = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	pct_of_genome_with_coverage_20x_inf = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	pct_of_genome_with_coverage_15x_inf = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	pct_of_genome_with_coverage_10x_inf = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	pct_of_genome_with_coverage_3x_inf = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	pct_of_genome_with_coverage_1x_inf = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	pct_of_genome_with_coverage_0x_inf = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	pct_of_genome_with_coverage_1000x1500x = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	pct_of_genome_with_coverage_500x1000x = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	pct_of_genome_with_coverage_100x_500x = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	pct_of_genome_with_coverage_50x100x = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	pct_of_genome_with_coverage_20x_50x = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	pct_of_genome_with_coverage_15x_20x = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	pct_of_genome_with_coverage_10x_15x = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	pct_of_genome_with_coverage_3x_10x = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	pct_of_genome_with_coverage_1x_3x = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	pct_of_genome_with_coverage_0x_1x = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	average_chr_x_coverage_over_genome = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	average_chr_y_coverage_over_genome = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	average_mitochondrial_coverage_over_genome = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
	average_autosomal_coverage_over_genome = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	median_autosomal_coverage_over_genome = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	meanmedian_autosomal_coverage_ratio_over_genome = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	xavgcovyavgcov_ratio_over_genome = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	xavgcovautosomalavgcov_ratio_over_genome = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	yavgcovautosomalavgcov_ratio_over_genome = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	predicted_sex_chromosome_ploidy = models.CharField(max_length=10, blank=True, null=True)
	aligned_reads = models.BigIntegerField(null=True, blank=True)
	aligned_reads_in_genome = models.BigIntegerField(null=True, blank=True)


class DragenRegionCoverageMetrics(models.Model):
	"""
	Store the dragen region coverage metrics file
	"""
	sample_analysis = models.ForeignKey(SampleAnalysis, on_delete=models.CASCADE)
	aligned_bases  = models.BigIntegerField(null=True, blank=True)
	aligned_bases_in_qc_coverage_region  = models.BigIntegerField(null=True, blank=True)
	average_alignment_coverage_over_qc_coverage_region = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	uniformity_of_coverage_pct_02mean_over_qc_coverage_region = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	uniformity_of_coverage_pct_04mean_over_qc_coverage_region = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	pct_of_qc_coverage_region_with_coverage_1500x_inf = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	pct_of_qc_coverage_region_with_coverage_1000x_inf = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	pct_of_qc_coverage_region_with_coverage_500x_inf = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	pct_of_qc_coverage_region_with_coverage_100x_inf = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	pct_of_qc_coverage_region_with_coverage_50x_inf = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	pct_of_qc_coverage_region_with_coverage_20x_inf = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	pct_of_qc_coverage_region_with_coverage_15x_inf = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	pct_of_qc_coverage_region_with_coverage_10x_inf = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	pct_of_qc_coverage_region_with_coverage_3x_inf = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	pct_of_qc_coverage_region_with_coverage_1x_inf = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	pct_of_qc_coverage_region_with_coverage_0x_inf = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	pct_of_qc_coverage_region_with_coverage_1000x1500x = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	pct_of_qc_coverage_region_with_coverage_500x1000x = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	pct_of_qc_coverage_region_with_coverage_100x_500x = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	pct_of_qc_coverage_region_with_coverage_50x100x = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	pct_of_qc_coverage_region_with_coverage_20x_50x = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	pct_of_qc_coverage_region_with_coverage_15x_20x = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	pct_of_qc_coverage_region_with_coverage_10x_15x = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	pct_of_qc_coverage_region_with_coverage_3x_10x = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	pct_of_qc_coverage_region_with_coverage_1x_3x = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	pct_of_qc_coverage_region_with_coverage_0x_1x = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	average_chr_x_coverage_over_qc_coverage_region = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	average_chr_y_coverage_over_qc_coverage_region = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	average_mitochondrial_coverage_over_qc_coverage_region = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	average_autosomal_coverage_over_qc_coverage_region = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	median_autosomal_coverage_over_qc_coverage_region = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	meanmedian_autosomal_coverage_ratio_over_qc_coverage_region = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	xavgcovyavgcov_ratio_over_qc_coverage_region = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	xavgcovautosomalavgcov_ratio_over_qc_coverage_region = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	yavgcovautosomalavgcov_ratio_over_qc_coverage_region = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	predicted_sex_chromosome_ploidy = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	aligned_reads = models.BigIntegerField(null=True, blank=True)
	aligned_reads_in_qc_coverage_region = models.BigIntegerField(null=True, blank=True)


class FusionContamination(models.Model):
	"""
	Data for the SomaticFusion pipelines contamination metric

	"""
	sample_analysis = models.ForeignKey(SampleAnalysis, on_delete=models.CASCADE)
	contamination = models.BooleanField()
	contamination_referral = models.BooleanField()



class FusionAlignmentMetrics(models.Model):
	"""
	Data on SomaticFusion alignment metrics

	"""
	sample_analysis = models.ForeignKey(SampleAnalysis, on_delete=models.CASCADE)
	aligned_reads = models.IntegerField()
	pct_reads_aligned = models.DecimalField(max_digits=6, decimal_places=2)
	unique_reads_aligned = models.IntegerField()
	pct_unique_reads_aligned = models.DecimalField(max_digits=6, decimal_places=2)



class Tso500Reads(models.Model):
	"""
	Data on SomaticFusion alignment metrics

	"""
	sample_analysis = models.ForeignKey(SampleAnalysis, on_delete=models.CASCADE)
	total_on_target_reads= models.IntegerField(null=True)
	total_pf_reads = models.IntegerField(null=True)
	percent_ntc_reads = models.IntegerField(null=True)
	aligned_reads=models.IntegerField(null=True)
	percent_ntc_contamination=models.IntegerField(null=True)


class DragenPloidyMetrics(models.Model):
	"""
	Data for Dragen V7 Sex Metrics

	"""
	sample_analysis = models.ForeignKey(SampleAnalysis, on_delete=models.CASCADE)
	ploidy_estimation = models.CharField(max_length=10, blank=True, null=True)


class CustomCoverageMetrics(models.Model):
	"""
	Model for custom coverage metrics from nextflow pipeline

	"""
	sample_analysis = models.ForeignKey(SampleAnalysis, on_delete=models.CASCADE)
	mean_depth = models.DecimalField(max_digits=8, decimal_places=1, null=True)
	min_depth = models.DecimalField(max_digits=8, decimal_places=1, null=True)
	max_depth = models.DecimalField(max_digits=8, decimal_places=1, null=True)
	stddev_depth = models.DecimalField(max_digits=8, decimal_places=1, null=True)
	pct_greater_20x = models.DecimalField(max_digits=5, decimal_places=2, null=True)
	pct_greater_30x = models.DecimalField(max_digits=5, decimal_places=2, null=True)
	pct_greater_250x = models.DecimalField(max_digits=5, decimal_places=2, null=True)
	pct_greater_160x = models.DecimalField(max_digits=5, decimal_places=2, null=True)

auditlog.register(RunAnalysis)
auditlog.register(SampleAnalysis)
