from pathlib import Path
import glob
import re
from pipelines import parsers

class GermlineEnrichment:


	def __init__(self,
				 results_dir,
				 sample_names,
				 run_id,
				 sample_expected_files= ['*.bam',
									'*.g.vcf',
									'*_AlignmentSummaryMetrics.txt',
									'*_Contamination.selfSM',
									'*_DepthOfCoverage.gz',
									'*_HsMetrics.txt',
									'*_InsertMetrics.txt',
									'*_MarkDuplicatesMetrics.txt',
										'*_QC.txt'],

				sample_not_expected_files = ['*_rmdup.bam',
										 '*_DepthOfCoverage'],

				run_expected_files = ['*_filtered_annotated_roi.vcf',
									'*_filtered_annotated_roi_noMT.vcf',
									'*_pedigree.ped',
									'*_CollectVariantCallingMetrics.txt.variant_calling_detail_metrics',
									'*_CollectVariantCallingMetrics.txt.variant_calling_summary_metrics',
									'*_ExomeDepth_Metrics.txt',
									'*_relatedness.relatedness2',
									'combined_QC.txt',
									'*_cnvReport.csv'],

				run_not_expected_files= ['*_variants_filtered.vcf',
									'BAMs.list']

				):


		self.results_dir = results_dir
		self.sample_names = sample_names
		self.run_id = run_id
		self.sample_complete_marker = '1_GermlineEnrichment*.sh.e*'
		self.run_complete_marker = '2_GermlineEnrichment*.sh.e*'
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
		Look for presence of file indicating that a sample has completed the pipeline.

		For example the output error log.
		"""	

		results_path = Path(self.results_dir)

		marker = results_path.glob(self.run_complete_marker)

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
				file_fastqc_dict['kmer_content'] = parsed_fastqc_data['Kmer Content']

				sample_fastqc_list.append(file_fastqc_dict)

			fastqc_dict[sample] = sample_fastqc_list


		return fastqc_dict


	def get_hs_metrics(self):

		results_path = Path(self.results_dir)

		run_hs_metrics_dict = {}

		for sample in self.sample_names:

			hs_metrics_file = results_path.joinpath(sample).glob(f'*{sample}*_HsMetrics.txt')

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

	def get_duplication_metrics(self):

		results_path = Path(self.results_dir)

		run_duplication_metrics_dict = {}

		for sample in self.sample_names:

			sample_duplication_metrics_file = results_path.joinpath(sample).glob(f'*{sample}*_MarkDuplicatesMetrics.txt')

			sample_duplication_metrics_file = list(sample_duplication_metrics_file)[0]	

			parsed_duplication_metrics = parsers.parse_duplication_metrics_file(sample_duplication_metrics_file)

			run_duplication_metrics_dict[sample] = parsed_duplication_metrics

		return run_duplication_metrics_dict

	def get_contamination(self):

		results_path = Path(self.results_dir)

		run_contamination_metrics_dict = {}

		for sample in self.sample_names:

			sample_contamination_metrics_file = results_path.joinpath(sample).glob(f'*{sample}*_Contamination.selfSM')

			sample_contamination_metrics_file = list(sample_contamination_metrics_file)[0]	

			parsed_contamination_metrics = parsers.parse_contamination_metrics(sample_contamination_metrics_file)

			run_contamination_metrics_dict[sample] = parsed_contamination_metrics

		return run_contamination_metrics_dict


	def get_calculated_sex(self):

		results_path = Path(self.results_dir)

		calculated_sex_dict = {}

		for sample in self.sample_names:

			qc_metrics_file = results_path.joinpath(sample).glob(f'*{sample}*_QC.txt')

			qc_metrics_file = list(qc_metrics_file)[0]

			parsed_qc_metrics_file = parsers.parse_qc_metrics_file(qc_metrics_file)

			calculated_sex_dict[sample] = parsed_qc_metrics_file

		return calculated_sex_dict

	def get_alignment_metrics(self):

		results_path = Path(self.results_dir)

		alignment_metrics_dict = {}

		for sample in self.sample_names:

			alignment_metrics_file = results_path.joinpath(sample).glob(f'*{sample}*_AlignmentSummaryMetrics.txt')

			alignment_metrics_file = list(alignment_metrics_file)[0]

			parsed_alignment_metrics_file = parsers.parse_alignment_metrics_file(alignment_metrics_file)

			alignment_metrics_dict[sample] = parsed_alignment_metrics_file

		return alignment_metrics_dict

	def get_variant_calling_metrics(self):

		results_path = Path(self.results_dir)

		variant_metrics_dict = {}

		variant_detail_metrics_file = results_path.glob(f'*{self.run_id}*_CollectVariantCallingMetrics.txt.variant_calling_detail_metrics')

		variant_detail_metrics_file = list(variant_detail_metrics_file)[0]

		variant_metrics_dict = parsers.parse_variant_detail_metrics_file(variant_detail_metrics_file)

		return variant_metrics_dict


	def get_insert_metrics(self):

		results_path = Path(self.results_dir)

		insert_metrics_dict = {}

		for sample in self.sample_names:

			insert_metrics_file = results_path.joinpath(sample).glob(f'*{sample}*_InsertMetrics.txt')

			insert_metrics_file = list(insert_metrics_file)[0]

			parsed_insert_metrics_file = parsers.parse_insert_metrics_file(insert_metrics_file)

			insert_metrics_dict[sample] = parsed_insert_metrics_file

		return insert_metrics_dict