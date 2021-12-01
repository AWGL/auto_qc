
from pathlib import Path
import glob
import re
import os
from pipelines import parsers
import pandas as pd

class TSO500_DNA():
	"""
	TSO500 model for DNA

	"""

	def __init__(self,results_dir, sample_completed_files, sample_valid_files, run_completed_files, run_expected_files, metrics_file, run_id, sample_names):

		self.results_dir = results_dir
		self.sample_completed_files=sample_completed_files
		self.sample_valid_files=sample_valid_files
		self.run_completed_files=run_completed_files
		self.run_expected_files=run_expected_files
		self.metrics_file= metrics_file
		self.run_id = run_id
		self.sample_names=sample_names

	def run_is_complete(self):
		"""
		Looks for files in self.run_completed_files

		I
		"""

		results_dir_path = Path(self.results_dir)
		results_path = results_dir_path.joinpath(self.run_id)

		found_file_list = []

		for file in self.run_completed_files:

			found_file = results_path.glob(file)

			for file in found_file:

				found_file_list.append(file)

		if len(found_file_list) > 0:

			return True
		
		return False


	def run_is_valid(self):
		"""
		Is the TSO500 DNA run Valid?

		Checks all self.run_expected_files are present.

		"""

		results_dir_path = Path(self.results_dir)
		results_path = results_dir_path.joinpath(self.run_id)

		found_file_list = []

		for file in self.run_expected_files:

			found_file = results_path.glob(file)

			for file in found_file:

				found_file_list.append(file)

		if len(list(found_file_list)) == len(self.run_expected_files):

				return True

		return False


	def sample_is_valid(self, sample):
		"""
		For each sample checks that it is valid.

		Opens the DNA_QC_combined.txt and checks the completed_all_steps column is True

		"""
		results_dir_path = Path(self.results_dir)
		results_path = results_dir_path.joinpath(self.run_id)

		found_file = results_path.glob(self.metrics_file[0])

		found_file = list(found_file)[0]

		dna_metrics_data = pd.read_csv(found_file, sep='\t')

		dna_metrics_filtered = dna_metrics_data[['Sample', 'completed_all_steps']]
		sample_metrics = dna_metrics_filtered[dna_metrics_filtered['Sample']==sample]

		if sample_metrics.iloc[0,1]:

			return True

		return False


	def sample_is_complete(self, sample):
		"""
		Has each sample in the TS500 DNA pipeline completed?

		"""
		results_dir_path = Path(self.results_dir)
		results_path = results_dir_path.joinpath(self.run_id)

		sample_files = 0

		for sample_completed_file in self.sample_completed_files:

			found_file = results_path.joinpath('Gathered_Results/Database').glob(sample_completed_file)

			for file in found_file:

				file2 = str(file)

				if sample in file2:

					sample_files = sample_files + 1

		if sample_files >= 2:

			return True

		if 'NTC' in sample:

			return True

		return False

	def ntc_contamination(self):
		"""
		Is there NTC contamination in the TSO500 DNA?
		"""

		ntc_contamination_dict={}

		for sample in self.sample_names:

			results_dir_path = Path(self.results_dir)
			results_path = results_dir_path.joinpath(self.run_id)

			for file in self.metrics_file:

				found_file = results_path.glob(file)

				for file in found_file:

					dna_metrics_data = pd.read_csv(file, sep='\t')
					dna_metrics_filtered = dna_metrics_data[['Sample', 'total_pf_reads']]

					ntc_metrics = dna_metrics_filtered[dna_metrics_filtered['Sample'].str.contains('NTC')]
					ntc_reads = ntc_metrics.iloc[0,1]

					sample_metrics = dna_metrics_filtered[dna_metrics_filtered['Sample']==sample]
					sample_reads = sample_metrics.iloc[0,1]

					# if there are no reads report as 100% 
					if sample_reads == 0:

						ntc_contamination_dict[sample] = 100

					else:

						ntc_contamination_dict[sample] = ((ntc_reads/sample_reads)*100)

		return ntc_contamination_dict
	

	def get_fastqc_data(self):
		"""
		Get the FASTQC data for TSO500 DNA
		"""

		fastqc_dict = {}

		for sample in self.sample_names:

			results_dir_path = Path(self.results_dir)
			results_path = results_dir_path.joinpath(self.run_id)

			fastqc_data_files = results_path.glob(f'analysis/{sample}/FastQC/*{sample}*_fastqc.txt')

			sample_fastqc_list = []

			for fastqc_data in fastqc_data_files:

				file = fastqc_data.name
				read_number = file.split('_')[-2]
				lane = file.split('_')[-3]

				parsed_fastqc_data = parsers.parse_fastqc_file_tso500(fastqc_data)

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


class TSO500_RNA():
	"""
	Pipeline class for TSO500 RNA

	"""

	def __init__(self,results_dir, sample_completed_files, sample_valid_files, run_completed_files, run_expected_files, metrics_file, sample_names, run_id):

		self.results_dir = results_dir
		self.run_id = run_id
		self.run_completed_files = run_completed_files
		self.run_expected_files = run_expected_files
		self.metrics_file = metrics_file
		self.sample_completed_files = sample_completed_files
		self.sample_valid_files = sample_valid_files
		self.sample_names = sample_names

	def run_is_complete(self):
		"""
		Has the RNA part of the pipeline completed run level?

		Looks for all files in self.run_completed_files

		"""

		results_dir_path = Path(self.results_dir)
		results_path = results_dir_path.joinpath(self.run_id)


		found_file_list=[]

		for file in self.run_completed_files:
			found_file = results_path.glob(file)

			found_file_list.append(found_file)

		if len(list(found_file_list)) >= 1:

			return True
	
		return False


	def run_is_valid(self):
		"""
		Checks for presence of each self.run_expected_files

		"""

		results_path = Path(self.results_dir)

		found_file_list=[]

		for file in self.run_expected_files:

			found_file = results_path.joinpath(self.run_id).glob(file)

			for output_file in found_file:

				found_file_list.append(output_file)

		if len(found_file_list) >= 3:

			return True

		return False

	def sample_is_complete(self, sample):
		"""
		Is a specific sample for TSO500 RNA complete?

		Looks for self.sample_completed_files

		"""

		results_dir_path = Path(self.results_dir)
		results_path = results_dir_path.joinpath(self.run_id)

		sample_files = 0

		for sample_completed_file in self.sample_completed_files:

			found_file = results_path.joinpath('Gathered_Results/Database').glob(sample_completed_file)

			for file in found_file:

				if sample in str(file):

					sample_files=sample_files+1

		if sample_files >= 1:

			return True

		if 'NTC' in sample:

			return True

		return False

	def sample_is_valid(self, sample):
		"""
		Is a specific sample valid?

		Looks in the RNA_QC_combined.txt file to see this

		"""

		results_dir_path = Path(self.results_dir)
		results_path = results_dir_path.joinpath(self.run_id)

		for file in self.metrics_file:

			found_file = results_path.glob(file)

			for file in found_file:

				rna_metrics_data = pd.read_csv(file, sep='\t')
				rna_metrics_filtered = rna_metrics_data[['Sample', 'completed_all_steps']]

				sample_metrics=rna_metrics_filtered[rna_metrics_filtered['Sample']==sample]

				if sample_metrics.iloc[0,1]:
					return True

		return False

	def get_reads(self):
		"""
		Get the reads for a specific sample
		"""

		results_dir_path = Path(self.results_dir)
		results_path = results_dir_path.joinpath(self.run_id)
		reads_dict={}

		for sample in self.sample_names:

			for file in self.metrics_file:

				found_file = results_path.glob(file)

				for file in found_file:

					rna_metrics_data = pd.read_csv(file, sep='\t')
					rna_metrics_filtered = rna_metrics_data[['Sample', 'total_on_target_reads']]
					sample_metrics = rna_metrics_filtered[rna_metrics_filtered['Sample'] == sample]
					reads = sample_metrics.iloc[0,1]

					if pd.isna(reads):

						reads = 0

					reads_dict[sample] = reads

		return reads_dict

	def get_fastqc_data(self):
		"""	
		Get FASTQC data for TS500 RNA
		"""

		fastqc_dict = {}

		for sample in self.sample_names:

			results_dir_path = Path(self.results_dir)
			results_path = results_dir_path.joinpath(self.run_id)

			fastqc_data_files = results_path.glob(f'analysis/{sample}/FastQC/*{sample}*_fastqc.txt')

			sample_fastqc_list = []

			for fastqc_data in fastqc_data_files:

				file = fastqc_data.name
				read_number = file.split('_')[-2]
				lane = file.split('_')[-3]

				parsed_fastqc_data = parsers.parse_fastqc_file_tso500(fastqc_data)

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






