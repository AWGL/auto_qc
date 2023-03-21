from pathlib import Path
import glob
import os
import re
from pipelines import parsers 
from qc_database.utils import relatedness2 

class DragenGE:

	def __init__(self,
				 results_dir,
				 sample_names,
				 run_id,
				 sample_expected_files= [],
				run_expected_files = [],
				sample_not_expected_files =[],
				run_not_expected_files= [],
				post_sample_files = [],
				run_complete_marker  = 'post_processing/results/post_processing_finished.txt',
				sample_complete_marker  = 'post_processing/results/post_processing_finished.txt'
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
		
	def run_is_complete(self):
		"""
		Look for the file nextflow creates on run end
		"""

		results_path = Path(self.results_dir)
		
		marker = results_path.glob(self.run_complete_marker)

		if len(list(marker)) == 1:

			return True

		return False	

	def run_is_valid(self):
		"""
		Read the file nextflow created on run end (post_processing/results/post_processing_finished.txt)

		open it and see if the success or fail mark is there

		"""

		if self.run_is_complete():

			results_path = Path(self.results_dir)
		
			marker = results_path.glob(self.run_complete_marker)

			marker = list(marker)[0]

			# last line in file
			last_report = ''

			with open(marker, 'r') as outfile:

				for x in outfile:
					last_report = x.strip()

			if 'success' in last_report:

				return True

			
		return False
	
	def get_coverage_metrics(self):

		results_path = Path(self.results_dir)

		run_coverage_metrics_dict = {}

		for sample in self.sample_names:

			sample_coverage_metrics_file = results_path.glob(f'post_processing/results/coverage/*{sample}.depth_summary')

			sample_coverage_metrics_file = list(sample_coverage_metrics_file)[0]	

			parsed_coverage_metrics = parsers.parse_custom_coverage_metrics(sample_coverage_metrics_file)

			run_coverage_metrics_dict[sample] = parsed_coverage_metrics

		return run_coverage_metrics_dict
	
	def get_contamination(self):

		results_path = Path(self.results_dir)

		run_contamination_metrics_dict = {}

		for sample in self.sample_names:

			sample_contamination_metrics_file = results_path.glob(f'post_processing/results/contamination/*{sample}_contamination.selfSM')

			sample_contamination_metrics_file = list(sample_contamination_metrics_file)[0]	

			parsed_contamination_metrics = parsers.parse_contamination_metrics(sample_contamination_metrics_file)

			run_contamination_metrics_dict[sample] = parsed_contamination_metrics

		return run_contamination_metrics_dict
	
	def get_sex_metrics(self):
		
		results_path = Path(self.results_dir)

		run_sex_metrics_dict = {}

		for sample in self.sample_names:

			sample_sex_metrics_file = results_path.glob(f'post_processing/results/sex/*{sample}_calculated_sex.txt')

			try:
				sample_sex_metrics_file = list(sample_sex_metrics_file)[0]
			
				parsed_sex_metrics = parsers.parse_dragen_sex_file(sample_sex_metrics_file)

				run_sex_metrics_dict[sample] = parsed_sex_metrics

			except:

				run_sex_metrics_dict[sample] = {'sex': 'Unknown'}

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

		sensitivity_file = results_path.glob(f'post_processing/results/sensitivity/{self.run_id}*_sensitivity.txt')
		
		sensitivity_file = list(sensitivity_file)

		if len(sensitivity_file) == 0:

			return {'sensitivity': None, 'sensitivity_lower_ci': None, 'sensitivity_higher_ci': None}

		sensitivity_file = sensitivity_file[0]
		
		parsed_sensitivity_file = parsers.parse_sensitivity_file(sensitivity_file)

		return parsed_sensitivity_file  
	
	def get_variant_count_metrics(self):
		
		results_path = Path(self.results_dir)

		sample_variant_count_dict = {}

		for sample in self.sample_names:

			vcf_file = results_path.glob(f'post_processing/results/annotated_vcf/{self.run_id}*.vcf.gz')

			vcf_file = list(vcf_file)[0]

			vcf_count_metrics = parsers.get_passing_variant_count(vcf_file, [sample])

			sample_variant_count_dict[sample] = vcf_count_metrics

		return sample_variant_count_dict
	
	def display_cnv_qc_metrics(self):
		
		try:
			results_path = Path(self.results_dir)

			cnv_metrics_file = results_path.glob(f'post_processing/results/sv_cnv/qc/{self.run_id}.cnv_qc_report.csv')

			cnv_metrics_file = list(cnv_metrics_file)[0]

			if os.path.isfile(cnv_metrics_file):
				return True
			else:
				return False
		
		except:
			return False

	def get_postprocessing_cnv_qc_metrics(self):
		
		results_path = Path(self.results_dir)

		cnv_metrics_file = results_path.glob(f'post_processing/results/sv_cnv/qc/{self.run_id}.cnv_qc_report.csv')

		cnv_metrics_file = list(cnv_metrics_file)[0]

		cnv_metrics_qc_dict = parsers.parse_exome_postprocessing_cnv_qc_metrics(cnv_metrics_file)

		return cnv_metrics_qc_dict

	def get_relatedness_metrics(self, min_relatedness_parents, max_relatedness_unrelated, max_relatedness_between_parents, max_child_parent_relatedness):

		results_path = Path(self.results_dir)

		ped_file = results_path.glob(f'post_processing/results/ped/{self.run_id}.ped')

		ped_file = list(ped_file)[0]
	
		relatedness_file = results_path.glob(f'post_processing/results/relatedness/{self.run_id}.relatedness2')

		relatedness_file = list(relatedness_file)[0]

		parsed_relatedness, parsed_relatedness_comment = relatedness2.relatedness_test(ped_file, relatedness_file,
																					 min_relatedness_parents,
																					 max_relatedness_unrelated,
																					 max_relatedness_between_parents,
																					 max_child_parent_relatedness)
		return parsed_relatedness, parsed_relatedness_comment


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

			results_path = results_path.joinpath('post_processing/results/')

		else:

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

			if len(list(found_file)) == 0:

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

			results_path = results_path.joinpath('post_processing/results/')

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


	def get_relatedness_metrics(self, min_relatedness_parents, max_relatedness_unrelated, max_relatedness_between_parents, max_child_parent_relatedness):

		results_path = Path(self.results_dir)

		ped_file = results_path.glob(f'post_processing/results/ped/{self.run_id}.ped')

		ped_file = list(ped_file)[0]
	
		relatedness_file = results_path.glob(f'post_processing/results/relatedness/{self.run_id}.relatedness2')

		relatedness_file = list(relatedness_file)[0]

		parsed_relatedness, parsed_relatedness_comment = relatedness2.relatedness_test(ped_file, relatedness_file,
																					 min_relatedness_parents,
																					 max_relatedness_unrelated,
																					 max_relatedness_between_parents,
																					 max_child_parent_relatedness)
		return parsed_relatedness, parsed_relatedness_comment

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

	def get_ploidy_metrics(self):
		"""
		Need this for version 3.7 Dragen VC to get calculated sex.
		"""

		results_path = Path(self.results_dir)

		run_ploidy_metrics_dict = {}

		for sample in self.sample_names:

			run_ploidy_metrics_file = results_path.joinpath(sample).glob(f'*{sample}.ploidy_estimation_metrics.csv')

			if len(list(run_ploidy_metrics_file)) ==1:

				run_ploidy_metrics_file = results_path.joinpath(sample).glob(f'*{sample}.ploidy_estimation_metrics.csv')

				run_ploidy_metrics_file = list(run_ploidy_metrics_file)[0]
				
				parsed_run_ploidy_metrics = parsers.parse_ploidy_metrics_file(run_ploidy_metrics_file)

				run_ploidy_metrics_dict[sample] = parsed_run_ploidy_metrics

		return run_ploidy_metrics_dict
		
	def get_cnv_metrics(self):
		"""
		Get sample level CNV metrics from dragen cnv metrics file
		"""
		
		results_path = Path(self.results_dir)
		
		dragen_cnv_metrics_dict = {}
		
		for sample in self.sample_names:
		
			cnv_metrics_file = results_path.joinpath(sample).glob(f'*{sample}.cnv_metrics.csv')
			
			if len(list(cnv_metrics_file)) == 1:
			
				cnv_file = list(cnv_metrics_file)[0]
				
				parsed_cnv_metrics = parsers.parse_dragen_cnv_metrics_file(cnv_file)
				
				dragen_cnv_metrics_dict[sample] = parsed_cnv_metrics
		
		return dragen_cnv_metrics_dict
