from pathlib import Path
import glob
import re
from pipelines import parsers


class DragenGE:

	def __init__(self,
				 results_dir,
				 sample_names,
				 run_id,
				 sample_expected_files= ['*.bam',
									'*.mapping_metrics.csv',
									'*.insert-stats.tab'],
				run_expected_files = ['*.hard-filtered.vcf.gz',
									'*.vc_metrics.csv',
									 'results/relatedness/*.relatedness2',
									 'results/sensitivity/*_sensitivity.txt',
									 'results/database_vcf/*.roi.filtered.database.vcf',
									 'results/annotated_vcf/*.roi.filtered.norm.anno.vcf.gz'],
				sample_not_expected_files =[],
				run_not_expected_files= [],
				post_sample_files = ['results/contamination/*{sample}_contamination.selfSM',
									'results/calculated_sex/*{sample}_calculated_sex.txt',
									'results/coverage/*{sample}_depth_of_coverage.gz',
									'results/coverage/*{sample}_gaps.bed'
									],
				run_complete_marker  = 'post_processing_finished.txt',
				sample_complete_marker  = 'post_processing_finished.txt'
				):

		self.results_dir = results_dir
		self.sample_names = sample_names
		self.run_id = run_id
		self.run_complete_marker = run_complete_marker
		self.sample_complete_marker = sample_complete_marker
		self.sample_expected_files = sample_expected_files
		self.sample_not_expected_files = sample_not_expected_files
		self.run_expected_files = run_expected_files
		self.run_not_expected_files = run_not_expected_files
		self.post_sample_files = post_sample_files
		
		
	def sample_is_complete(self, sample):
		"""
		Look for presence of file indicating that a sample has completed the pipeline.

		For example the output error log.
		"""

		results_path = Path(self.results_dir)
		
		results_path = results_path.joinpath('results')

		marker = results_path.glob(self.sample_complete_marker)

		if len(list(marker)) >= 1:

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
			
		for file in self.post_sample_files:
			
			split = file.split('{sample}')
			
			joined = f'{sample}'.join(split)
						
			found_file = results_path.glob(joined)
			
			if len(list(found_file)) < 1:

				return False

		return True
	
	def run_is_complete(self):
		"""
		Look for presence of file indicating that a sample has completed the pipeline.

		For example the output error log.
		"""

		results_path = Path(self.results_dir)
		
		results_path = results_path.joinpath('results')

		marker = results_path.glob(self.sample_complete_marker)

		if len(list(marker)) >= 1:

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
						
			found_file = results_path.glob(file)

			if len(list(found_file)) != 1:
								
				return False

		# check file we do not want to be there are not there
		for file in self.run_not_expected_files:
			

			found_file = results_path.glob(file)

			if len(list(found_file)) > 0:

				return False
			
		return True

	def run_and_samples_complete(self):
			"""
			Return True if all samples are complete and valid and the run
			level is complete and valid. Otherwise return False.

			"""

			# sample level
			for sample in self.sample_names:

				if self.sample_is_complete(sample) == False:

					return False

			# run level
			if self.run_is_complete() == False:

				return False

			return True


	def run_and_samples_valid(self):

		# sample level
		for sample in self.sample_names:

			if self.sample_is_valid(sample) == False:

				return False

		# run level
		if self.run_is_valid() == False:

			return False

		return True	
	
	
	def get_depth_metrics(self):

		results_path = Path(self.results_dir)

		run_depth_metrics_dict = {}

		for sample in self.sample_names:

			sample_depth_summary_file = results_path.joinpath('results', 'coverage').glob(f'*{sample}_depth_of_coverage.sample_summary')

			sample_depth_summary_file = list(sample_depth_summary_file)[0]

			parsed_depth_metrics = parsers.parse_gatk_depth_summary_file(sample_depth_summary_file)

			run_depth_metrics_dict[sample] = parsed_depth_metrics

		return run_depth_metrics_dict
	
	def get_contamination(self):

		results_path = Path(self.results_dir)

		run_contamination_metrics_dict = {}

		for sample in self.sample_names:

			sample_contamination_metrics_file = results_path.joinpath('results', 'contamination').glob(f'*{sample}_contamination.selfSM')

			sample_contamination_metrics_file = list(sample_contamination_metrics_file)[0]	

			parsed_contamination_metrics = parsers.parse_contamination_metrics(sample_contamination_metrics_file)

			run_contamination_metrics_dict[sample] = parsed_contamination_metrics

		return run_contamination_metrics_dict
	
	def get_sex_metrics(self):
		
		results_path = Path(self.results_dir)

		run_sex_metrics_dict = {}

		for sample in self.sample_names:

			sample_sex_metrics_file = results_path.joinpath('results', 'calculated_sex').glob(f'*{sample}_calculated_sex.txt')

			sample_sex_metrics_file = list(sample_sex_metrics_file)[0]
			
			parsed_sex_metrics = parsers.parse_dragen_sex_file(sample_sex_metrics_file)

			run_sex_metrics_dict[sample] = parsed_sex_metrics

		return run_sex_metrics_dict   
	
	
	def get_variant_calling_metrics(self):
		
		results_path = Path(self.results_dir)

		variant_metrics_file = results_path.glob(f'{self.run_id}.vc_metrics.csv')
		
		variant_metrics_file = list(variant_metrics_file)[0]
		
		parsed_variant_metrics_file = parsers.parse_dragen_vc_metrics_file(variant_metrics_file)

		return parsed_variant_metrics_file  
	
	
	def get_alignment_metrics(self):
		
		results_path = Path(self.results_dir)

		run_alignment_metrics_dict = {}

		for sample in self.sample_names:

			alignment_metrics_file = results_path.joinpath(sample).glob(f'*{sample}.mapping_metrics.csv')

			alignment_metrics_file = list(alignment_metrics_file)[0]
			
			parsed_alignment_metrics = parsers.parse_dragen_alignment_metrics_file(alignment_metrics_file)

			run_alignment_metrics_dict[sample] = parsed_alignment_metrics

		return run_alignment_metrics_dict
	
	
	def get_sensitivity(self):
		
		results_path = Path(self.results_dir)

		sensitivity_file = results_path.glob(f'results/sensitivity/{self.run_id}*_sensitivity.txt')
		
		sensitivity_file = list(sensitivity_file)[0]
		
		parsed_sensitivity_file = parsers.parse_sensitivity_file(sensitivity_file)

		return parsed_sensitivity_file  
	
	
	def get_variant_count_metrics(self):
		
		results_path = Path(self.results_dir)

		sample_variant_count_dict = {}

		for sample in self.sample_names:

			vcf_file = results_path.glob(f'results/database_vcf/{self.run_id}.roi.filtered.database.vcf')

			vcf_file = list(vcf_file)[0]

			vcf_count_metrics = parsers.get_passing_variant_count(vcf_file, [sample])

			sample_variant_count_dict[sample] = vcf_count_metrics

		return sample_variant_count_dict


class DragenWGS:

	def __init__(self,
				 results_dir,
				 sample_names,
				 run_id,
				 sample_expected_files= ['*.bam',
									'*.mapping_metrics.csv',
									'*.insert-stats.tab'],
				run_expected_files = ['*.hard-filtered.vcf.gz',
									'*.vc_metrics.csv'],
				sample_not_expected_files =[],
				run_not_expected_files= [],
				post_sample_files = [],
				run_complete_marker  = 'post_processing_finished.txt',
				sample_complete_marker  = 'post_processing_finished.txt'
				):

		self.results_dir = results_dir
		self.sample_names = sample_names
		self.run_id = run_id
		self.run_complete_marker = run_complete_marker
		self.sample_complete_marker = sample_complete_marker
		self.sample_expected_files = sample_expected_files
		self.sample_not_expected_files = sample_not_expected_files
		self.run_expected_files = run_expected_files
		self.run_not_expected_files = run_not_expected_files
		self.post_sample_files = post_sample_files
		
		
	def sample_is_complete(self, sample):
		"""
		Look for presence of file indicating that a sample has completed the pipeline.

		For example the output error log.
		"""

		results_path = Path(self.results_dir)

		new_path = False

		for i in self.run_expected_files:

			if 'post_processing' in i:

				
				new_path = True
				break

		if new_path:

			results_path = results_path.joinpath('post_processing')

		else:

			results_path = results_path.joinpath('results')


		print(results_path)

		marker = results_path.glob(self.sample_complete_marker)

		if len(list(marker)) >= 1:

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
			
		for file in self.post_sample_files:
			
			split = file.split('{sample}')
			
			joined = f'{sample}'.join(split)
						
			found_file = results_path.glob(joined)
			
			if len(list(found_file)) < 1:

				return False

		return True
	
	def run_is_complete(self):
		"""
		Look for presence of file indicating that a sample has completed the pipeline.

		For example the output error log.
		"""

		results_path = Path(self.results_dir)

		new_path = False
		
		for i in self.run_expected_files:

			if 'post_processing' in i:

				new_path = True
				break

		if new_path:

			results_path = results_path.joinpath('post_processing')

		else:

			results_path = results_path.joinpath('results')

		marker = results_path.glob(self.sample_complete_marker)

		if len(list(marker)) >= 1:

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

	def run_and_samples_complete(self):
			"""
			Return True if all samples are complete and valid and the run
			level is complete and valid. Otherwise return False.

			"""

			# sample level
			for sample in self.sample_names:

				if self.sample_is_complete(sample) == False:

					return False

			# run level
			if self.run_is_complete() == False:

				return False

			return True


	def run_and_samples_valid(self):

		# sample level
		for sample in self.sample_names:

			if self.sample_is_valid(sample) == False:

				return False

		# run level
		if self.run_is_valid() == False:

			return False

		return True	
	
	
	
	def get_variant_calling_metrics(self):
		
		results_path = Path(self.results_dir)

		variant_metrics_file = results_path.glob(f'{self.run_id}.vc_metrics.csv')
		
		variant_metrics_file = list(variant_metrics_file)[0]
		
		parsed_variant_metrics_file = parsers.parse_dragen_vc_metrics_file(variant_metrics_file)

		return parsed_variant_metrics_file  
	
	
	def get_alignment_metrics(self):
		
		results_path = Path(self.results_dir)

		run_alignment_metrics_dict = {}

		for sample in self.sample_names:

			alignment_metrics_file = results_path.joinpath(sample).glob(f'*{sample}.mapping_metrics.csv')

			alignment_metrics_file = list(alignment_metrics_file)[0]
			
			parsed_alignment_metrics = parsers.parse_dragen_alignment_metrics_file(alignment_metrics_file)

			run_alignment_metrics_dict[sample] = parsed_alignment_metrics

		return run_alignment_metrics_dict


	def get_wgs_mapping_metrics(self):
		
		results_path = Path(self.results_dir)

		run_wgs_coverage_metrics_dict = {}

		for sample in self.sample_names:

			wgs_coverage_metrics_file = results_path.joinpath(sample).glob(f'*{sample}.wgs_coverage_metrics.csv')

			wgs_coverage_metrics_file = list(wgs_coverage_metrics_file)[0]
			
			parsed_wgs_coverage_metrics = parsers.parse_dragen_wgs_coverage_metrics_file(wgs_coverage_metrics_file)

			run_wgs_coverage_metrics_dict[sample] = parsed_wgs_coverage_metrics

		return run_wgs_coverage_metrics_dict

	def get_exonic_mapping_metrics(self):
		
		results_path = Path(self.results_dir)

		run_wgs_coverage_metrics_dict = {}

		for sample in self.sample_names:

			wgs_coverage_metrics_file = results_path.joinpath(sample).glob(f'*{sample}.qc-coverage-region-1_coverage_metrics.csv')

			wgs_coverage_metrics_file = list(wgs_coverage_metrics_file)[0]
			
			parsed_wgs_coverage_metrics = parsers.parse_dragen_wgs_coverage_metrics_file(wgs_coverage_metrics_file)

			run_wgs_coverage_metrics_dict[sample] = parsed_wgs_coverage_metrics

		return run_wgs_coverage_metrics_dict