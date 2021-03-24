from pathlib import Path
import glob
import re
from pipelines import parsers


class NextflowGermlineEnrichment:

	def __init__(self,
				 results_dir,
				 sample_names,
				 run_id,
				run_complete_marker  = 'post_processing/results/post_processing_finished.txt',
				):

		self.results_dir = results_dir
		self.sample_names = sample_names
		self.run_id = run_id
		self.run_complete_marker = run_complete_marker		
	
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

	def get_fastqc_data(self):

		fastqc_dict = {}

		results_path = Path(self.results_dir)

		for sample in self.sample_names:

			fastqc_data_files = results_path.glob(f'post_processing/results/fastqc/*{sample}*/summary.txt')

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

			hs_metrics_file = results_path.glob(f'post_processing/results/metrics/*{sample}_hs_metrics.txt')

			hs_metrics_file = list(hs_metrics_file)[0]

			parsed_hs_metrics_data  = parsers.parse_hs_metrics_file(hs_metrics_file)

			run_hs_metrics_dict[sample] = parsed_hs_metrics_data

		return run_hs_metrics_dict


	def get_duplication_metrics(self):

		results_path = Path(self.results_dir)

		run_duplication_metrics_dict = {}

		for sample in self.sample_names:

			sample_duplication_metrics_file = results_path.glob(f'post_processing/results/metrics/*{sample}_markduplicate_metrics.txt')

			sample_duplication_metrics_file = list(sample_duplication_metrics_file)[0]	

			parsed_duplication_metrics = parsers.parse_duplication_metrics_file(sample_duplication_metrics_file)

			run_duplication_metrics_dict[sample] = parsed_duplication_metrics

		return run_duplication_metrics_dict


	def get_alignment_metrics(self):

		results_path = Path(self.results_dir)

		alignment_metrics_dict = {}

		for sample in self.sample_names:

			alignment_metrics_file = results_path.glob(f'post_processing/results/metrics/*{sample}_alignment_summary_metrics.txt')

			alignment_metrics_file = list(alignment_metrics_file)[0]

			parsed_alignment_metrics_file = parsers.parse_alignment_metrics_file(alignment_metrics_file)

			alignment_metrics_dict[sample] = parsed_alignment_metrics_file

		return alignment_metrics_dict


	def get_variant_calling_metrics(self):

		results_path = Path(self.results_dir)

		variant_metrics_dict = {}

		variant_detail_metrics_file = results_path.glob(f'post_processing/results/metrics/*.variant_calling_detail_metrics')

		variant_detail_metrics_file = list(variant_detail_metrics_file)[0]

		variant_metrics_dict = parsers.parse_variant_detail_metrics_file(variant_detail_metrics_file)

		return variant_metrics_dict


	def get_insert_metrics(self):

		results_path = Path(self.results_dir)

		insert_metrics_dict = {}

		for sample in self.sample_names:

			insert_metrics_file = results_path.glob(f'post_processing/results/metrics/*{sample}_insert_metrics.txt')

			insert_metrics_file = list(insert_metrics_file)[0]

			parsed_insert_metrics_file = parsers.parse_insert_metrics_file(insert_metrics_file)

			insert_metrics_dict[sample] = parsed_insert_metrics_file

		return insert_metrics_dict


	def get_contamination(self):

		results_path = Path(self.results_dir)

		run_contamination_metrics_dict = {}

		for sample in self.sample_names:

			sample_contamination_metrics_file = results_path.glob(f'post_processing/results/contamination/*{sample}_contamination.selfSM')

			sample_contamination_metrics_file = list(sample_contamination_metrics_file)[0]	

			parsed_contamination_metrics = parsers.parse_contamination_metrics(sample_contamination_metrics_file)

			run_contamination_metrics_dict[sample] = parsed_contamination_metrics

		return run_contamination_metrics_dict


	def get_coverage_metrics(self):

		results_path = Path(self.results_dir)

		run_coverage_metrics_dict = {}

		for sample in self.sample_names:

			sample_coverage_metrics_file = results_path.glob(f'post_processing/results/coverage/*{sample}.depth_summary')

			sample_coverage_metrics_file = list(sample_coverage_metrics_file)[0]	

			parsed_coverage_metrics = parsers.parse_custom_coverage_metrics(sample_coverage_metrics_file)

			run_coverage_metrics_dict[sample] = parsed_coverage_metrics

		return run_coverage_metrics_dict


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