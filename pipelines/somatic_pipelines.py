from pathlib import Path
import glob
import re
import os
from pipelines import parsers

class SomaticEnrichment:


	def __init__(self,
				results_dir,
				sample_names,
				run_id,
				ntc_patterns = ['NTC', 'ntc'],
				sample_expected_files= ['*_VariantReport.txt',
									'*.bam',
									'*_AlignmentSummaryMetrics.txt',
									'*_DepthOfCoverage.sample_summary',
									'*_QC.txt',
									'*_filteredStrLeftAligned_annotated.vcf',
									'hotspot_variants',
									'hotspot_coverage_135x'
									],

				sample_not_expected_files = [],
				run_sample_expected_files = ['CNVKit/*_common.vcf'],
				run_expected_files = ['combined_QC.txt', 'samplesCNVKit.txt'],
				run_not_expected_files = ['*.bed']
									):

		self.results_dir = results_dir
		self.sample_names = sample_names
		self.run_id = run_id
		self.ntc_patterns = ntc_patterns
		self.sample_complete_marker = '1_SomaticEnrichment.sh.e*'
		self.run_complete_markers = ['1_cnvkit.sh.e*', '2_cnvkit.sh.e*']

		self.sample_expected_files = sample_expected_files
		self.sample_not_expected_files = sample_not_expected_files

		self.run_sample_expected_files = run_sample_expected_files
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

			skip_sample = False

			for ntc in self.ntc_patterns:

				if ntc in sample:

					skip_sample = True
					break

			if skip_sample == True:

				continue

			for marker in self.run_complete_markers:

				globbed_marker = results_path.joinpath(sample).glob(marker)

		
				if len(list(globbed_marker)) < 1:

					return False

		return True

	def run_is_valid(self):
		"""
		Look for files which have to be present for a run level pipeline to have completed \
		correctly.

		Look for files which if present indicate the pipeline has not finished correctly e.g. intermediate files.
		"""


		results_path = Path(self.results_dir)

		for sample in self.sample_names:

			skip_sample = False

			for ntc in self.ntc_patterns:

				if ntc in sample:

					skip_sample = True
					break

			if skip_sample == True:

				continue

			for file in self.run_sample_expected_files:

				found_file = results_path.joinpath(sample).glob(file)

				if len(list(found_file)) != 1:

					return False

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

			fastqc_data_files = results_path.joinpath(sample, 'FASTQC').glob(f'*{sample}*_fastqc.txt')

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

			sample_duplication_metrics_file = results_path.joinpath(sample).glob(f'*{sample}*_markDuplicatesMetrics.txt')

			sample_duplication_metrics_file = list(sample_duplication_metrics_file)[0]	

			parsed_duplication_metrics = parsers.parse_duplication_metrics_file(sample_duplication_metrics_file)

			run_duplication_metrics_dict[sample] = parsed_duplication_metrics

		return run_duplication_metrics_dict


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

	def get_insert_metrics(self):

		results_path = Path(self.results_dir)

		insert_metrics_dict = {}

		for sample in self.sample_names:

			insert_metrics_file = results_path.joinpath(sample).glob(f'*{sample}*_InsertMetrics.txt')

			insert_metrics_file = list(insert_metrics_file)[0]

			parsed_insert_metrics_file = parsers.parse_insert_metrics_file(insert_metrics_file)

			insert_metrics_dict[sample] = parsed_insert_metrics_file

		return insert_metrics_dict

	def get_variant_count(self):

		results_path = Path(self.results_dir)

		sample_variant_count_dict = {}

		for sample in self.sample_names:

			vcf_file = results_path.joinpath(sample).glob(f'*{sample}*_filteredStrLeftAligned_annotated.vcf')

			vcf_file = list(vcf_file)[0]	

			vcf_count_metrics = parsers.get_passing_variant_count(vcf_file, [sample])

			sample_variant_count_dict[sample] = vcf_count_metrics

		return sample_variant_count_dict


class SomaticAmplicon:

	def __init__(self,
				results_dir,
				sample_names,
				run_id,
				ntc_patterns = ['NTC', 'ntc'],
				sample_expected_files = ['*_VariantReport.txt',
				  '*.bam',
				  '*_DepthOfCoverage.sample_summary',
				  '*_qc.txt',
				  '*_filtered_meta_annotated.vcf',
				  'hotspot_variants',
				  'hotspot_coverage'
				  ],
				sample_not_expected_files = ['*_fastqc.zip', 'VariantCallingLogs'],
				run_expected_files = [],
				run_not_expected_files = []
				):


		self.results_dir = results_dir
		self.sample_names = sample_names
		self.run_id = run_id
		self.ntc_patterns = ntc_patterns
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


class Cruk:

	def __init__(self,
				results_dir,
				sample_names,
				run_id,
				sample_sheet_data,
				ntc_patterns = ['NTC', 'ntc'],
				sample_expected_files = [],
				sample_not_expected_files = [],
				run_valid_extra_marker = 'cruk_smp.out',
				sample_run_dna_expected_files = ['_realigned.bam', '_realigned.bam.bai', '_report.xlsm'],
				sample_run_rna_expected_files=[".bam", ".bam.bai"],
				run_complete_expected_files = ['FASTQs.list', 'cruk_smp.dbg', 'cruk_smp.err', 'cruk_smp.out'],
				run_valid_expected_files = ['FASTQs.list', 'tst_170.json', 'smp.json', 'cruk_smp.dbg','cruk_smp.err','cruk_smp.out'],
				run_not_expected_files = []
				):

		self.results_dir = results_dir
		self.sample_names = sample_names
		self.run_id = run_id
		self.ntc_patterns = ntc_patterns
		self.sample_complete_marker = '1_launch_SMP2v3.sh.e*'
		self.sample_expected_files = sample_expected_files
		self.sample_not_expected_files = sample_not_expected_files
		self.sample_run_dna_expected_files = sample_run_dna_expected_files
		self.sample_run_rna_expected_files = sample_run_rna_expected_files
		self.run_complete_expected_files = run_complete_expected_files
		self.run_valid_expected_files = run_valid_expected_files
		self.run_not_expected_files = run_not_expected_files
		self.run_valid_extra_marker = run_valid_extra_marker
		self.sample_sheet_data = sample_sheet_data
		self.sample_pairs = {}

	def pair_samples(self, sample):
		"""
		Pair sample with its pair from the same patient (Note: some samples may not have pairs)
		Returns the sample id of the pair, None if no pair is found
		"""

		# Make a copy of the dictionary from which to remove current sample data
		remaining_sample_sheet_data = self.sample_sheet_data.copy()
		remaining_sample_sheet_data.pop(sample, None)

		# Retrieve data for current sample
		sample_data = self.sample_sheet_data.get(sample)

		sample_lpid = sample_data.get('pairs')

		for s, d in remaining_sample_sheet_data.items():

			lpid = d.get('pairs')

			if lpid == sample_lpid:

				return s

		return None

	def sample_is_complete(self, sample):
		"""
		Look for presence of file indicating that a sample has completed the pipeline.

		For example the output error log.
		"""

		results_path = Path(self.results_dir)

		sample_path = results_path.joinpath(sample)

		marker = sample_path.glob(self.sample_complete_marker)

		if len(list(marker)) < 1: 

			return False

		return True

	def sample_is_valid(self, sample):
		"""
		Look for files which have to be present for a sample level pipeline to have completed \
		correctly.

		Look for file which if present indicate the pipeline has not finished correctly e.g. intermediate files.

		Check results are available for all samples (bam, bai and Excel file)
		"""

		results_path = Path(self.results_dir)
		sample_path = results_path.joinpath(sample)

		# Get samples that are DNA samples (not RNA)
		cruk_dna_samples = []

		for s, d in self.sample_sheet_data.items():

			if d.get('sampleType') == 'DNA':

				cruk_dna_samples.append(s)

		# Get DNA-RNA sample pair identifier
		sample_pair = self.pair_samples(sample)

		# Get worksheet id from the sample sheet (needed for the file path to the results)
		cruk_worksheets = list(set([d.get('Sample_Plate') for s, d in self.sample_sheet_data.items()]))

		if len(cruk_worksheets) > 1:

			raise IndexError(f'More than one worksheet id for a CRUK run is not permitted. Look at sample sheet to determine source of error.')

		cruk_worksheet = cruk_worksheets[0]

		# Path to results
		res_path = results_path.joinpath(cruk_worksheet)

		if res_path.exists() == False:

			return False

		# Directories containing results
		samples_results_dir = os.listdir(res_path)

		# Check samples in directory match all DNA samples- if absent directory for a DNA sample, sample is invalid
		# This check cannot be done for RNA samples
		if sample in cruk_dna_samples and sample not in samples_results_dir:

			return False

		# Check for missing files per sample (DNA as key, RNA checked as part of check)
		# Note that it is untested what will occur if the connection is interrupted during file download (whether a file \
		# will be partially downloaded or will not appear at all). It has been assumed that the file will not be present \
		# rather than incomplete

		if sample in cruk_dna_samples:

			directory_list = os.listdir(os.path.join(res_path, sample))

			for f_dna in self.sample_run_dna_expected_files:

				if f'{cruk_worksheet}-{sample}{f_dna}' not in directory_list:

					return False

			# If sample has an RNA sample pair, check those files are also present
			if sample_pair:

				for f_rna in self.sample_run_rna_expected_files:

					if f'{cruk_worksheet}-{sample_pair}{f_rna}' not in directory_list:

						return False

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
		Check all log files are present.
		"""

		results_path = Path(self.results_dir)

		for sample in self.sample_names:

			if self.sample_is_complete(sample) == False:

				return False

		# check files we want to be there are there
		for file in self.run_complete_expected_files:

			found_file = results_path.glob(file)

			if len(list(found_file)) != 1:

				return False

		return True

	def run_is_valid(self):
		"""
		Check final entry text is present in log file as final line
		Check all log files are present.
		"""

		results_path = Path(self.results_dir)

		marker_path = results_path.joinpath(self.run_valid_extra_marker)

		if marker_path.exists() == False:

			return False

		with open(marker_path) as f:

			lines = f.read().splitlines()

			last_line = lines[-1]

			if last_line != 'CRUK workflow completed':

				return False

		for sample in self.sample_names:

			if self.sample_is_valid(sample) == False:

				return False

		# check files we want to be there are there
		for file in self.run_valid_expected_files:

			found_file = results_path.glob(file)

			if len(list(found_file)) != 1:

				return False


		return True

	def ok_to_upload_fastqc_data(self):
		"""
		Check whether a run has all the fastqcs for import
		"""
		results_path = Path(self.results_dir)

		for sample in self.sample_names:

			if self.sample_is_complete(sample) == True:

				# check we have fastqcs

				sample_path = results_path.joinpath(sample)

				fastqcs = sample_path.glob('*_fastqc.txt')

				if len(list(fastqcs)) == 0:

					return False

			else:

				return False

		return True


	def get_fastqc_data(self):

		fastqc_dict = {}

		results_path = Path(self.results_dir)

		for sample in self.sample_names:

			fastqc_data_files = results_path.joinpath(sample).glob(f'*{sample}*fastqc.txt')

			sample_fastqc_list = []

			for fastqc_data in fastqc_data_files:

				file = fastqc_data.name

				read_number = file.split('_')[-2]
				lane = file.split('_')[-3]

				parsed_fastqc_data = parsers.parse_fastqc_file_cruk(fastqc_data, self.run_id)

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