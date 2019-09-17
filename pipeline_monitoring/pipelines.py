from pathlib import Path



class GermlineEnrichment:


	def __init__(self, results_dir, sample_names, run_id):


		self.results_dir = results_dir
		self.sample_names = sample_names
		self.run_id = run_id
		self.sample_complete_marker = '1_GermlineEnrichment.sh.e*'
		self.run_complete_marker = '2_GermlineEnrichment.sh.e*'

		self.sample_expected_files = ['*.bam',
		 							'*.g.vcf',
		  							'*_AlignmentSummaryMetrics.txt',
		  							'*_cnv.vcf.gz',
		  							'*_Contamination.selfSM',
		  							'*_DepthOfCoverage.gz',
		  							'*_HsMetrics.txt',
		  							'*_InsertMetrics.txt',
		  							'*_MarkDuplicatesMetrics.txt',
		  							'*_QC.txt',
		  							'*_sv_filtered.vcf.gz']

		self.sample_not_expected_files = ['*_rmdup.bam',
										 '*_DepthOfCoverage']

		self.run_expected_files = ['*_filtered_annotated_roi.vcf',
									'*_filtered_annotated_roi_noMT.vcf',
									'*_pedigree.ped',
									'*_CollectVariantCallingMetrics.txt.variant_calling_detail_metrics',
									'*_CollectVariantCallingMetrics.txt.variant_calling_summary_metrics',
									'*_ExomeDepth_Metrics.txt',
									'*_relatedness.relatedness2',
									'combined_QC.txt',
									'*_cnvReport.csv']


		self.run_not_expected_files =['*_variants_filtered.vcf',
									'BAMs.list']

	def sample_is_complete(self, sample):
		"""	
		Look for presence of file indicating that a sample has completed the pipeline.

		For example the output error log.
		"""	

		results_path = Path(self.results_dir)

		sample_path = results_path.joinpath(sample)

		marker = sample_path.glob(self.sample_complete_marker)

		if len(list(marker)) == 1:

			return True

		return False

	def sample_is_valid(self, sample):
		"""
		Look for files which have to be present for a sample level pipeline to have completed \
		correctly.

		Look for file which if present indicate the pipeline has not finished correctly e.g. intermediate files.
		"""

		results_path = Path(self.results_dir)

		sample_path = results_path.joinpath(sample)

		# check files we want to be there are there
		for file in self.sample_expected_files:

			found_file = sample_path.glob(file)

			if len(list(found_file)) != 1:

				return False

		# check file we do not want to be there are not there
		for file in self.sample_not_expected_files:

			found_file = sample_path.glob(file)

			if len(list(found_file)) > 0:

				return False			

		return True


	def run_is_complete(self):
		"""	
		Look for presence of file indicating that a sample has completed the pipeline.

		For example the output error log.
		"""	

		results_path = Path(self.results_dir)

		marker = results_path.glob(self.run_complete_marker)

		if len(list(marker)) == 1:

			return True

		return False

	def run_is_valid(self):
		"""
		Look for files which have to be present for a run level pipeline to have completed \
		correctly.

		Look for files which if present indicate the pipeline has not finished correctly e.g. intermediate files.
		"""

		results_path = Path(self.results_dir)

		# check files we want to be there are there
		for file in self.run_expected_files:

			found_file = results_path.glob(file)

			if len(list(found_file)) != 1:

				return False

		# check file we do not want to be there are not there
		for file in self.run_not_expected_files:

			found_file = results_path.glob(file)

			if len(list(found_file)) > 0:

				return False			

		return True

	def run_complete_and_valid(self):
		"""
		Return True if all samples are complete and valid and the run
		level is complete and valid. Otherwise return False.

		"""

		# sample level
		for sample in self.sample_names:

			if self.sample_is_complete(sample) == False or self.sample_is_valid(sample) == False:

				return False

		# run level
		if self.run_is_complete() == False or self.run_is_valid() == False:

			return False

		return True


class IlluminaQC:

	def __init__(self,
	 			fastq_dir,
	  			results_dir,
				sample_names,
				n_lanes,
				run_id,
				min_fastq_size=10000,
				ntc_pattern = '*NTC*',
				run_complete_marker = '1_IlluminaQC.sh.e*'):

		self.fastq_dir = fastq_dir
		self.results_dir = results_dir
		self.sample_names = sample_names
		self.n_lanes = n_lanes
		self.run_id = run_id
		self.run_complete_marker = run_complete_marker
		self.min_fastq_size = min_fastq_size
		self.ntc_pattern = ntc_pattern

	def demultiplex_run_is_complete(self):

		results_path = Path(self.fastq_dir)

		marker = results_path.glob(self.run_complete_marker)

		if len(list(marker)) == 1:

			return True

		return False

	def demultiplex_run_is_valid(self):

		for sample in self.samples:




	def pipeline_copy_complete(self):

		pass

	def pipeline_copy_valid(self):

		pass


class SomaticAmplicon:

	pass


class SomaticEnrichment:

	pass

