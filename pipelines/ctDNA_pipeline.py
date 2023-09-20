
from pathlib import Path
import glob
import re
import os
import pandas as pd
import decimal

from pipelines import parsers

class TSO500_ctDNA():
	"""
	Analysis for ctDNA TSO500 App 

	"""

	def __init__(self,results_dir, sample_completed_files, run_completed_files, metrics_file, run_id, sample_names):

		self.results_dir = results_dir
		self.sample_completed_files=sample_completed_files
		self.run_completed_files=run_completed_files
		self.metrics_file= metrics_file
		self.run_id = run_id
		self.sample_names=sample_names

	def run_is_complete(self):
		"""
		Looks for files in self.run_completed_files to check if pipeline is complete

		"""

		results_path = Path(self.results_dir)

		found_file_list = []

		for file in self.run_completed_files:

			found_file = results_path.glob(file)

			for file in found_file:

				found_file_list.append(file)

		if len(found_file_list) > 0:

			return True
		
		return False


	def sample_is_valid(self, sample):
		"""
		For each sample checks that it is valid.

		Opens the QC_combined.txt file and checks the completed_app column is True

		"""
		results_dir_path = Path(self.results_dir)
		results_path = results_dir_path.joinpath('post_processing')

		found_file = results_path.glob(self.metrics_file[0])
		
		try:
			found_file = list(found_file)[0]

		except:

			return False

		metrics_data = pd.read_csv(found_file, sep='\t')

		metrics_filtered = metrics_data[['sample', 'completed_app']]
		sample_metrics = metrics_filtered[metrics_filtered['sample']==sample]

		#Weird instance where sometimes this was read in as a string and TRUE and sometimes as a boolean and True
		if sample_metrics['completed_app'].iloc[0] == "TRUE" or sample_metrics['completed_app'].iloc[0] == True:

			return True

		return False


	def sample_is_complete(self, sample):
		"""
		Has each sample in the TSO500 ctDNA pipeline completed?

		"""
		results_path = Path(self.results_dir)

		# the NTC doesn't make variants, fusions or coverage files
		if 'NTC' in sample:

			return True

		# now loop through the expected files
		for sample_completed_file in self.sample_completed_files:
			
			#found_files = results_path.joinpath(f'post_processing/database/{sample}').glob(sample_completed_file)
			found_files = glob.glob(f"{results_path}/post_processing/database/{sample}{sample_completed_file}")

			if len(found_files) == 0:
				# we would expect at least one file each for variants, fusions and coverage
				return False
			
		# if the loop is unbroken there's at least one file per expected file - the sample pipeline is complete
		return True

	def ntc_contamination(self):
		"""
		Is there NTC contamination in the TSO500 ctDNA?
		"""

		aligned_reads_dict={}
		ntc_contamination_aligned_reads_dict={}

		for sample in self.sample_names:

			results_dir_path = Path(self.results_dir)
			results_path = results_dir_path.joinpath('post_processing')

			for file in self.metrics_file:

				found_file = results_path.glob(file)

				for file in found_file:

					metrics_data = pd.read_csv(file, sep='\t')

					metrics_filtered = metrics_data[['sample', 'mapped_reads']]

					#get ntc data
					ntc_metrics = metrics_filtered[metrics_filtered['sample'].str.contains('NTC')]

					#get aligned reads in NTC
					ntc_reads = ntc_metrics.iloc[0,1]

					#get sample data
					sample_metrics = metrics_filtered[metrics_filtered['sample']==sample]

					#get total aligned reads
					sample_reads = sample_metrics.iloc[0,1]

					# if there are no reads report as 100% 
					if sample_reads == 0:
						aligned_reads_dict[sample]=0
						ntc_contamination_aligned_reads_dict[sample] = 100

					#if number of pf reads is na report as None
					elif pd.isna(sample_reads):
						aligned_reads_dict[sample]= None
						ntc_contamination_aligned_reads_dict[sample] = None

					else:

						ntc_contamination = ((ntc_reads/sample_reads)*100)
						decimal.getcontext().rounding=decimal.ROUND_DOWN
						ntc_contamination_aligned_reads_dict[sample]=(decimal.Decimal(ntc_contamination).quantize(decimal.Decimal('1')))
						aligned_reads_dict[sample]= sample_reads


		return aligned_reads_dict, ntc_contamination_aligned_reads_dict
	

	def determine_fastqc_metrics(self):
		"""
		Determine if FastQC or DragenFastQC has been used to determine FastQC metrics
		"""

		results_path = Path(self.results_dir)
		dragen_fastqc_metrics_files = glob.glob(f'{results_path}/post_processing/FastQC/*-dragen_fastq_qc.txt')

		if len(dragen_fastqc_metrics_files) >= 1:
			fastqc_metrics = "DragenFastQC"
		else:
			fastqc_metrics = "FastQC"

		return fastqc_metrics


	def get_fastqc_data(self):
		"""
		Get the FASTQC data for TSO500 ctDNA from FastQC files
		"""

		fastqc_dict = {}

		for sample in self.sample_names:

			results_path = Path(self.results_dir)

			fastqc_data_files = results_path.glob(f'post_processing/FastQC/*{sample}*_fastqc.txt')

			sample_fastqc_list = []

			for fastqc_data in fastqc_data_files:

				file = fastqc_data.name
				read_number = file.split('_')[-2]
				lane = file.split('_')[-3]

				#Going to use TSO500 parsers as identical files but caution needed if this changes for the new pipeline
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

	def get_dragen_fastqc_data(self):
		"""
		Get FastQC data from the dragen FastQC metrics for ctDNA
		"""

		fastqc_dict = {}

		for sample in self.sample_names:

			results_path = Path(self.results_dir)

			dragen_fastqc_metrics_file = f'{results_path}/post_processing/FastQC/{self.run_id}-{sample}-dragen_fastq_qc.txt'

			parsed_dragen_fastqc_data = parsers.parse_dragen_fastqc_file(dragen_fastqc_metrics_file)

			fastqc_dict[sample] = parsed_dragen_fastqc_data
		
		return fastqc_dict


