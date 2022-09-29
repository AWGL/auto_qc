from pathlib import Path
import glob
import re
import os
from pipelines import parsers

class SomaticAmplicon:

	def __init__(self, results_dir, sample_names, run_id, sample_expected_files, sample_not_expected_files, run_expected_files, run_not_expected_files):


		self.results_dir = results_dir
		self.sample_names = sample_names
		self.run_id = run_id
		self.ntc_patterns = ['NTC', 'ntc']
		self.sample_complete_marker = '1_SomaticAmplicon.sh.e*'
		self.sample_expected_files = sample_expected_files
		self.sample_not_expected_files = sample_not_expected_files
		self.run_expected_files = run_expected_files
		self.run_not_expected_files = run_not_expected_files


	def sample_is_complete(self, sample):
		"""	
		Look for presence of file indicating that a sample has completed the pipeline.

		For example the output error log.
		"""	

		results_path = Path(self.results_dir)

		sample_path = results_path.joinpath(sample)

		marker = sample_path.glob(self.sample_complete_marker)

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

		return True


	def run_is_complete(self):
		"""	
		Check everyone except NTC has the CNV logs
		"""	

		results_path = Path(self.results_dir)

		for sample in self.sample_names:

			if self.sample_is_complete(sample) == False:

				return False
		return True


	def run_is_valid(self):
		"""	
		Check everyone except NTC has the CNV logs
		"""	

		results_path = Path(self.results_dir)

		for sample in self.sample_names:

			if self.sample_is_valid(sample) == False:

				return False

		for file in self.run_expected_files:
			found_file = results_path.glob(file)
			if len(list(found_file)) == 0:
				return False
		return True

	def get_fastqc_data(self):

		fastqc_dict = {}

		results_path = Path(self.results_dir)

		for sample in self.sample_names:

			fastqc_data_files = results_path.joinpath(sample).glob(f'*{sample}*fastqc/summary.txt')

			sample_fastqc_list = []

			for fastqc_data in fastqc_data_files:

				file = fastqc_data.parent.name
				read_number = file.split('_')[-2]
				lane = file.split('_')[-3]

				parsed_fastqc_data = parsers.parse_fastqc_file(fastqc_data)

				file_fastqc_dict = {} 
				file_fastqc_dict['lane'] = lane
				file_fastqc_dict['read_number'] = read_number
				file_fastqc_dict['basic_statistics'] = parsed_fastqc_data['Basic Statistics']
				try:
					file_fastqc_dict['per_tile_sequence_quality'] = parsed_fastqc_data['Per tile sequence quality']
				except KeyError:
					file_fastqc_dict['per_tile_sequence_quality'] = 'FAIL'
				file_fastqc_dict['per_base_sequencing_quality'] = parsed_fastqc_data['Per base sequence quality']
				file_fastqc_dict['per_sequence_quality_scores'] = parsed_fastqc_data['Per sequence quality scores']
				file_fastqc_dict['per_base_sequence_content'] = parsed_fastqc_data['Per base sequence content']
				file_fastqc_dict['per_sequence_gc_content'] = parsed_fastqc_data['Per sequence GC content']
				file_fastqc_dict['per_base_n_content'] = parsed_fastqc_data['Per base N content']
				file_fastqc_dict['per_base_sequence_content'] = parsed_fastqc_data['Per base sequence content']
				file_fastqc_dict['sequence_length_distribution'] = parsed_fastqc_data['Sequence Length Distribution']
				file_fastqc_dict['sequence_duplication_levels'] = parsed_fastqc_data['Sequence Duplication Levels']
				file_fastqc_dict['overrepresented_sequences'] = parsed_fastqc_data['Overrepresented sequences']
				file_fastqc_dict['adapter_content'] = parsed_fastqc_data['Adapter Content']
				sample_fastqc_list.append(file_fastqc_dict)

			fastqc_dict[sample] = sample_fastqc_list


		return fastqc_dict

	def get_hs_metrics(self):

		results_path = Path(self.results_dir)

		run_hs_metrics_dict = {}

		for sample in self.sample_names:

			hs_metrics_file = results_path.joinpath(sample).glob(f'*{sample}*_hs_metrics.txt')

			hs_metrics_file = list(hs_metrics_file)[0]

			parsed_hs_metrics_data  = parsers.parse_hs_metrics_file(hs_metrics_file)

			run_hs_metrics_dict[sample] = parsed_hs_metrics_data

		return run_hs_metrics_dict

	def get_depth_metrics(self):

		results_path = Path(self.results_dir)

		run_depth_metrics_dict = {}

		for sample in self.sample_names:

			sample_depth_summary_file = results_path.joinpath(sample).glob(f'*{sample}*_DepthOfCoverage.sample_summary')

			sample_depth_summary_file = list(sample_depth_summary_file)[0]	

			parsed_depth_metrics = parsers.parse_gatk_depth_summary_file(sample_depth_summary_file)

			run_depth_metrics_dict[sample] = parsed_depth_metrics

		return run_depth_metrics_dict


	def get_variant_count(self):

		results_path = Path(self.results_dir)

		sample_variant_count_dict = {}

		for sample in self.sample_names:

			vcf_file = results_path.joinpath(sample).glob(f'*{sample}*_filtered_meta_annotated.vcf')

			vcf_file = list(vcf_file)[0]	

			vcf_count_metrics = parsers.get_passing_variant_count(vcf_file, [sample])

			sample_variant_count_dict[sample] = vcf_count_metrics

		return sample_variant_count_dict

