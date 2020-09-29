from pathlib import Path
import glob
import re
from pipelines import parsers

class IlluminaQC:

	def __init__(self,
				fastq_dir,
				sample_names,
				n_lanes,
				run_id,
				analysis_type,
				min_fastq_size=1000000,
				ntc_patterns = ['NTC', 'ntc'],
				run_complete_marker = '1_IlluminaQC.sh.e*'):

		self.fastq_dir = fastq_dir
		self.sample_names = sample_names
		self.n_lanes = n_lanes
		self.run_id = run_id
		self.analysis_type = analysis_type
		self.run_complete_marker = run_complete_marker
		self.min_fastq_size = min_fastq_size
		self.ntc_patterns = ntc_patterns

	def demultiplex_run_is_complete(self):

		results_path = Path(self.fastq_dir)

		marker = results_path.glob(self.run_complete_marker)

		if len(list(marker)) >= 1:

			return True

		return False

	def demultiplex_run_is_valid(self):

		fastq_data_path = Path(self.fastq_dir)

		fastq_data_path = fastq_data_path.joinpath('Data')

		for sample in self.sample_names:

			is_negative_control = False

			for pattern in self.ntc_patterns:

				if pattern in sample:

					is_negative_control = True
					break

			sample_fastq_path = fastq_data_path.joinpath(sample)

			# check fastqs created
			for lane in range(1,self.n_lanes+1):

				fastq_r1 = sample_fastq_path.glob(f'{sample}*L00{lane}_R1_001.fastq.gz')
				fastq_r2 = sample_fastq_path.glob(f'{sample}*L00{lane}_R2_001.fastq.gz')
				variables = sample_fastq_path.glob(f'{sample}.variables')

				if len(list(fastq_r1)) != 1:

					return False

				elif len(list(fastq_r2)) != 1:
					return False

				elif len(list(variables)) != 1:
					return False

				fastq_r1 = sample_fastq_path.glob(f'{sample}*L00{lane}_R1_001.fastq.gz')
				fastq_r2 = sample_fastq_path.glob(f'{sample}*L00{lane}_R2_001.fastq.gz')
				
				fastq_r1 = list(fastq_r1)[0]
				fastq_r2 = list(fastq_r2)[0]

				if fastq_r1.stat().st_size < self.min_fastq_size and is_negative_control == False:
					return False

				elif fastq_r2.stat().st_size < self.min_fastq_size  and is_negative_control == False:
					return False


		return True




class DragenQC(IlluminaQC):

	def demultiplex_run_is_complete(self):

		if self.demultiplex_run_is_valid() == True:

			return True

		else:

			return False


	def demultiplex_run_is_valid(self):

		fastq_data_path = Path(self.fastq_dir)

		fastq_data_path = fastq_data_path.joinpath('Data', self.analysis_type)

		for sample in self.sample_names:

			is_negative_control = False

			for pattern in self.ntc_patterns:

				if pattern in sample:

					is_negative_control = True
					break

			sample_fastq_path = fastq_data_path.joinpath(sample)

			# check fastqs created
			for lane in range(1,self.n_lanes+1):

				fastq_r1 = sample_fastq_path.glob(f'{sample}*L00{lane}_R1_001.fastq.gz')
				fastq_r2 = sample_fastq_path.glob(f'{sample}*L00{lane}_R2_001.fastq.gz')
				variables = sample_fastq_path.glob(f'{sample}.variables')

				if len(list(fastq_r1)) != 1:

					return False

				elif len(list(fastq_r2)) != 1:
					return False

				elif len(list(variables)) != 1:
					return False

				fastq_r1 = sample_fastq_path.glob(f'{sample}*L00{lane}_R1_001.fastq.gz')
				fastq_r2 = sample_fastq_path.glob(f'{sample}*L00{lane}_R2_001.fastq.gz')
				
				fastq_r1 = list(fastq_r1)[0]
				fastq_r2 = list(fastq_r2)[0]

				if fastq_r1.stat().st_size < self.min_fastq_size and is_negative_control == False:
					return False

				elif fastq_r2.stat().st_size < self.min_fastq_size  and is_negative_control == False:
					return False


		return True