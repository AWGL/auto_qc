from pathlib import Path
import glob
import re
from pipelines import parsers

class SomaticFusion:

	def __init__(self,
				results_dir,
				sample_names,
				run_id,
				sample_expected_files = ['*_DepthOfCoverage.sample_summary',
				  '*.bam',

				  ],
				sample_not_expected_files = [],
				run_expected_files = ['contamination.csv', 'combined_QC.txt', '*-aligned_reads.csv' ],
				run_not_expected_files = []
				):


		self.results_dir = results_dir
		self.sample_names = sample_names
		self.run_id = run_id
		self.sample_complete_marker = '1_SomaticFusion.sh.e*'
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

			if len(list(found_file)) < 1:

				print(file)

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

		return True

	def get_fastqc_data(self):

		fastqc_dict = {}

		results_path = Path(self.results_dir)

		for sample in self.sample_names:

			fastqc_data_files = results_path.joinpath(sample).glob(f'*{sample}*_fastqc.txt')

			sample_fastqc_list = []

			for fastqc_data in fastqc_data_files:

				file = fastqc_data.name

				read_number = file.split('_')[-2]
				lane = file.split('_')[-3]

				parsed_fastqc_data = parsers.parse_fastqc_file(fastqc_data)

				file_fastqc_dict = {} 
				file_fastqc_dict['lane'] = lane
				file_fastqc_dict['read_number'] = read_number
				file_fastqc_dict['basic_statistics'] = parsed_fastqc_data['Basic Statistics']
				file_fastqc_dict['per_tile_sequence_quality'] = parsed_fastqc_data['Per tile sequence quality']
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

	def get_contamination_metrics(self):

		results_path = Path(self.results_dir)

		fusion_contamination_file = results_path.joinpath('contamination.csv')

		parsed_fusion_contamination_data  = parsers.parse_fusion_contamination_metrics_file(fusion_contamination_file)

		return parsed_fusion_contamination_data

	def get_alignment_metrics(self):

		results_path = Path(self.results_dir)

		fusion_alignment_metrics_file = results_path.glob(f'*{self.run_id}*-aligned_reads.csv')

		fusion_alignment_metrics_file = list(fusion_alignment_metrics_file)[0]

		fusion_alignment_metrics_data  = parsers.parse_fusion_alignment_metrics_file(fusion_alignment_metrics_file)

		return fusion_alignment_metrics_data
