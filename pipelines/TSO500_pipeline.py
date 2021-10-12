
from pathlib import Path
import glob
import re
import os
from pipelines import parsers
import pandas

class TSO500_DNA():

	def __init__(self,results_dir, sample_expected_files,sample_not_expected_files,  run_expected_files, dna_or_rna, sample_names ):

		self.dna_or_rna=dna_or_rna
		self.results_dir = results_dir
	


		self.run_completed_files=['contamination-worksheet1.xlsx']
		self.run_expected_files=['DNA_QC_combined.txt','completed_samples.txt' ]
		self.metrics_file=['DNA_QC_combined.txt']



		self.sample_completed_files=['*variants.tsv', '*_coverage.json']
		self.sample_valid_files=['DNA_QC_combined.txt']
		self.sample_names=sample_names


	def run_is_complete(self, dna_or_rna):

		found_file_list=[]
		results_path = Path(self.results_dir)
		for file in self.run_completed_files:
			found_file = results_path.glob(file)
			found_file_list.append(found_file)
		if len(found_file_list) >=1:
			return True
		
		return False


	def run_is_valid(self, dna_or_rna):


		results_path = Path(self.results_dir)

		found_file_list=[]

		for file in self.run_expected_files:
			found_file = results_path.glob(file)
			found_file_list.append(found_file)
		if len(list(found_file_list)) >= 2:
				return True

		return False



	def sample_is_valid(self, sample, dna_or_rna):

		value=False

		results_path = Path(self.results_dir)
		for file in self.sample_valid_files:
			found_file = results_path.glob(file)
			for metrics_file in found_file:
				dna_metrics_data = pandas.read_csv(metrics_file, sep="\t")
				dna_metrics_filtered=dna_metrics_data[["Sample", "completed_all_steps"]]
				sample_metrics=dna_metrics_filtered[dna_metrics_filtered["Sample"]==sample]
				if sample_metrics.iloc[0,1]==True:
					value= True

		return value






	def sample_is_complete(self, sample, dna_or_rna):

		results_path = Path(self.results_dir)

		sample_files=0


		for file in self.sample_completed_files:
			found_file = results_path.glob(file)
			for file in found_file:
				file2=str(file)
				if sample in file2:
					sample_files=sample_files+1


		if sample_files >= 2:
			return True
		if "NTC" in sample:
			return True
		return False






	def ntc_contamination(self):

		ntc_contamination_dict={}

		for sample in self.sample_names:

			results_path = Path(self.results_dir)

			for file in self.metrics_file:
				found_file = results_path.glob(file)
				for file in found_file:

					dna_metrics_data = pandas.read_csv(file, sep="\t")
					dna_metrics_filtered=dna_metrics_data[["Sample", "total_pf_reads"]]

					ntc_metrics=dna_metrics_filtered[dna_metrics_filtered["Sample"].str.contains("NTC")]
					ntc_reads=ntc_metrics.iloc[0,1]

					sample_metrics=dna_metrics_filtered[dna_metrics_filtered["Sample"]==sample]
					sample_reads=sample_metrics.iloc[0,1]


					ntc_contamination_dict[sample]=((ntc_reads/sample_reads)*100)


		return(ntc_contamination_dict)
	





	def get_fastqc_data(self):

		fastqc_dict = {}

		results_path = Path(self.results_dir)

		for sample in self.sample_names:
			fastqc_data_files = results_path.glob(f'*{sample}*_fastqc.txt')

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


	def __init__(self,results_dir, sample_expected_files,sample_not_expected_files,  run_expected_files, dna_or_rna, sample_names):
		self.results_dir = results_dir


		self.run_completed_files=['contamination-worksheet1.xlsx']
		self.run_expected_files=['RNA_QC_combined.txt', 'contamination-worksheet1.xlsx' ,'completed_samples.txt']
		self.metrics_file=['RNA_QC_combined.txt']


		self.sample_completed_files=['*_fusion_check.tsv']
		self.sample_valid_files=['RNA_QC_combined.txt']


		self.dna_or_rna=dna_or_rna

		self.sample_names=sample_names




	def run_is_complete(self, dna_or_rna):

		results_path = Path(self.results_dir)

		found_file_list=[]

		for file in self.run_completed_files:
			found_file = results_path.glob(file)
			found_file_list.append(found_file)
		if len(list(found_file)) >=1:
			return True
	
		return False


	def run_is_valid(self, dna_or_rna):


		results_path = Path(self.results_dir)

		found_file_list=[]

		for file in self.run_expected_files:
			found_file = results_path.glob(file)
			found_file_list.append(found_file)
		if len(list(found_file_list)) >= 3:
			return True

		return False




	def sample_is_complete(self, sample, dna_or_rna):


		results_path = Path(self.results_dir)

		sample_files=0


		for file in self.sample_completed_files:
			found_file = results_path.glob(file)
			for file in found_file:
				file2=str(file)
				if sample in file2:
					sample_files=sample_files+1


		if sample_files >= 1:
			return True
		if "NTC" in sample:
			return True
		return False






	def sample_is_valid(self, sample, dna_or_rna):


		results_path = Path(self.results_dir)

		for file in self.metrics_file:
			found_file = results_path.glob(file)
			for file in found_file:

				rna_metrics_data = pandas.read_csv(file, sep="\t")
				rna_metrics_filtered=rna_metrics_data[["Sample", "completed_all_steps"]]
				sample_metrics=rna_metrics_filtered[rna_metrics_filtered["Sample"]==sample]
				if sample_metrics.iloc[0,1]==True:
					return True

		return False





	def get_reads(self, sample, dna_or_rna):


		results_path = Path(self.results_dir)

		reads_dict={}


		for sample in self.sample_names:

			for file in self.metrics_file:
				found_file = results_path.glob(file)
				for file in found_file:

					rna_metrics_data = pandas.read_csv(file, sep="\t")
					rna_metrics_filtered=rna_metrics_data[["Sample", "total_on_target_reads"]]
					sample_metrics=rna_metrics_filtered[rna_metrics_filtered["Sample"]==sample]
					reads=sample_metrics.iloc[0,1]

					reads_dict[sample]=reads


		return reads_dict




	def get_fastqc_data(self):

		fastqc_dict = {}

		results_path = Path(self.results_dir)
		print(results_path)

		for sample in self.sample_names:
			fastqc_data_files = results_path.glob(f'*{sample}*_fastqc.txt')
			print(fastqc_data_files)

			sample_fastqc_list = []

			for fastqc_data in fastqc_data_files:
				print (fastqc_data)

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






