from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
import csv
from pathlib import Path
import datetime
from qc_database.models import *
from qc_analysis.parsers import *
from ...utils.slack import message_slack
import logging
from pipeline_monitoring.pipelines import IlluminaQC, GermlineEnrichment, SomaticEnrichment, SomaticAmplicon, Cruk, DragenQC, DragenGE, DragenWGS

def add_run_log_info(run_info, run_parameters, run_obj, raw_data_dir):
	"""
	parse data from the xml files and put into run_obj

	"""

	run_params_dict = get_run_parameters_dict(run_parameters)
	run_info_dict = get_run_info_dict(run_info)

	processed_run_info_dict = extract_data_from_run_info_dict(run_info_dict)

	instrument_id = processed_run_info_dict['instrument']
	instrument_type = get_instrument_type(instrument_id)
	instrument_date = processed_run_info_dict['instrument_date']
	lane_count = run_info_dict['RunInfo']['Run']['FlowcellLayout']['@LaneCount']

	if instrument_type == 'HiSeq':

		experiment = run_params_dict['RunParameters']['Setup']['ExperimentName']
		chemistry = None

	elif instrument_type == 'Novaseq':

		experiment = None
		chemistry = None

	else:
		experiment = run_params_dict['RunParameters']['ExperimentName']
		chemistry = run_params_dict['RunParameters']['Chemistry']
		

	num_reads = processed_run_info_dict['num_reads']
	length_read1 = processed_run_info_dict['length_read1']
	length_read2 = processed_run_info_dict.get('length_read2', None)
	num_indexes= processed_run_info_dict['num_indexes']
	length_index1 = processed_run_info_dict['length_index1']
	length_index2 = processed_run_info_dict.get('length_index2', None)

	instrument, created = Instrument.objects.get_or_create(instrument_id= instrument_id, instrument_type= instrument_type)

	run_obj.instrument = instrument
	run_obj.instrument_date = instrument_date
	run_obj.lanes = lane_count
	run_obj.investigator = None # get from sample sheet
	run_obj.experiment = experiment
	run_obj.chemistry = chemistry

	run_obj.num_reads = num_reads
	run_obj.length_read1 = length_read1
	run_obj.length_read2 = length_read2
	run_obj.num_indexes = num_indexes
	run_obj.length_index1 = length_index1
	run_obj.length_index2 = length_index2
	
	interop_dict = parse_interop_data(str(raw_data_dir), int(num_reads) + int(num_indexes), int(lane_count))

	for read in interop_dict['read_summaries']:

		read_dict = interop_dict['read_summaries'][read]

		for lane in read_dict:

			lane_read_summary = read_dict[lane]

			new_interop_quality_obj = InteropRunQuality(
					run = run_obj,
					read_number = read,
					lane_number = lane,
					percent_q30 = lane_read_summary['percent_q30'],
					density = lane_read_summary['density'],
					density_pf = lane_read_summary['density_pf'],
					cluster_count = lane_read_summary['cluster_count'],
					cluster_count_pf = lane_read_summary['cluster_count_pf'],
					error_rate = lane_read_summary['error_rate'],
					percent_aligned = lane_read_summary['percent_aligned'],
					percent_pf =  lane_read_summary['percent_pf'],
					phasing = lane_read_summary['phasing'],
					prephasing = lane_read_summary['prephasing'],
					reads = lane_read_summary['reads'],
					reads_pf = lane_read_summary['reads_pf'],
					yield_g = lane_read_summary['yield_g']
				)
			new_interop_quality_obj.save()


	run_obj.save()

	return interop_dict


def add_fastqc_data(fastqc_dict, run_analysis_obj):
	"""
	Add data from fastqc files to database.

	"""

	pipeline = run_analysis_obj.pipeline
	run = run_analysis_obj.run

	for key in fastqc_dict:

		sample_obj = Sample.objects.get(sample_id=key)

		sample_analysis_obj = SampleAnalysis.objects.get(sample=sample_obj,
														run=run,
														pipeline = pipeline)

		sample_data = fastqc_dict[key]

		for read in sample_data:

			existing_data = SampleFastqcData.objects.filter(sample_analysis= sample_analysis_obj,
													read_number = read['read_number'],
													lane = read['lane'])
			
			if len(existing_data) < 1:

				read['sample_analysis'] = sample_analysis_obj
				
				new_fastqc_obj = SampleFastqcData(**read)
				new_fastqc_obj.save()

def add_hs_metrics(hs_metrics_dict, run_analysis_obj):
	"""
	Add data from picard hs metrics files to database.

	"""
	pipeline = run_analysis_obj.pipeline
	run = run_analysis_obj.run

	for key in hs_metrics_dict:

		sample_obj = Sample.objects.get(sample_id=key)

		sample_analysis_obj = SampleAnalysis.objects.get(sample=sample_obj,
														run=run,
														pipeline = pipeline)

		existing_data = SampleHsMetrics.objects.filter(sample_analysis= sample_analysis_obj)
			
		if len(existing_data) < 1:

			sample_data = hs_metrics_dict[key]

			del sample_data['sample']
			del sample_data['library']
			del sample_data['read_group']

			sample_data['sample_analysis'] = sample_analysis_obj

			for key in sample_data:

				if sample_data[key] == '?' or sample_data[key] == '':

					sample_data[key] = None
					
			new_hsmetrics_obj = SampleHsMetrics(**sample_data)
			new_hsmetrics_obj.save()

def add_depth_of_coverage_metrics(depth_metrics_dict, run_analysis_obj):
	"""
	Add data from depth of coverage summary files to database.

	"""
	pipeline = run_analysis_obj.pipeline
	run = run_analysis_obj.run

	for key in depth_metrics_dict:

		sample_obj = Sample.objects.get(sample_id=key)

		sample_analysis_obj = SampleAnalysis.objects.get(sample=sample_obj,
														run=run,
														pipeline = pipeline)

		existing_data = SampleDepthofCoverageMetrics.objects.filter(sample_analysis= sample_analysis_obj)

		if len(existing_data) < 1:

			sample_data = depth_metrics_dict[key]
			del sample_data['sample_id']

			sample_data['sample_analysis'] = sample_analysis_obj
			new_depth_obj = SampleDepthofCoverageMetrics(**sample_data)
			new_depth_obj.save()



def add_duplication_metrics(duplication_metrics_dict, run_analysis_obj):
	"""
	Add data from picard mark duplicates summary files to database.

	"""
	pipeline = run_analysis_obj.pipeline
	run = run_analysis_obj.run

	for key in duplication_metrics_dict:

		sample_obj = Sample.objects.get(sample_id=key)

		sample_analysis_obj = SampleAnalysis.objects.get(sample=sample_obj,
														run=run,
														pipeline = pipeline)
		
		existing_data = DuplicationMetrics.objects.filter(sample_analysis= sample_analysis_obj)
		
		if len(existing_data) < 1:

			sample_data = duplication_metrics_dict[key]

			sample_data['sample_analysis'] = sample_analysis_obj

			for key in sample_data:

				if sample_data[key] == '?' or sample_data[key] == '':

					sample_data[key] = None

			new_duplication_obj = DuplicationMetrics(**sample_data)
			new_duplication_obj.save()
		
def add_contamination_metrics(contamination_metrics_dict, run_analysis_obj):
	"""
	Add data from contamination summary files to database.

	"""


	pipeline = run_analysis_obj.pipeline
	run = run_analysis_obj.run

	for key in contamination_metrics_dict:

		sample_obj = Sample.objects.get(sample_id=key)

		sample_analysis_obj = SampleAnalysis.objects.get(sample=sample_obj,
														run=run,
														pipeline = pipeline)


		existing_data = ContaminationMetrics.objects.filter(sample_analysis= sample_analysis_obj)

		if len(existing_data) < 1:
			
			sample_data = contamination_metrics_dict[key]

			sample_data['sample_analysis'] = sample_analysis_obj

			for key in sample_data:

				if sample_data[key] == '?' or sample_data[key] == '':

					sample_data[key] = None

			new_contamination_obj = ContaminationMetrics(**sample_data)
			new_contamination_obj.save()

def add_sex_metrics(qc_metrics_dict, run_analysis_obj, sex_key):
	"""
	Add data from sex calculation files to database.

	"""
	pipeline = run_analysis_obj.pipeline
	run = run_analysis_obj.run

	for key in qc_metrics_dict:

		sample_obj = Sample.objects.get(sample_id=key)

		sample_analysis_obj = SampleAnalysis.objects.get(sample=sample_obj,
														run=run,
														pipeline = pipeline)
		
		existing_data = CalculatedSexMetrics.objects.filter(sample_analysis= sample_analysis_obj)
		
		if len(existing_data) < 1:

			sample_data = qc_metrics_dict[key]

			new_depth_obj = CalculatedSexMetrics(sample_analysis = sample_analysis_obj,
												calculated_sex = sample_data[sex_key])
			new_depth_obj.save()


def add_alignment_metrics(alignment_metrics_dict, run_analysis_obj):
	"""
	Add data from picard alignment metrics files to database.

	"""

	pipeline = run_analysis_obj.pipeline
	run = run_analysis_obj.run

	for key in alignment_metrics_dict:

		sample_obj = Sample.objects.get(sample_id=key)

		sample_analysis_obj = SampleAnalysis.objects.get(sample=sample_obj,
														run=run,
														pipeline = pipeline)

		for metric in alignment_metrics_dict[key]:


			existing_data = AlignmentMetrics.objects.filter(sample_analysis= sample_analysis_obj,
															category = metric['category'])

			if len(existing_data) < 1:
				
				sample_data = metric

				sample_data['sample_analysis'] = sample_analysis_obj

				for key in sample_data:

					if sample_data[key] == '?' or sample_data[key] == '':

						sample_data[key] = None

				new_alignment_obj = AlignmentMetrics(**sample_data)
				new_alignment_obj.save()


def add_dragen_alignment_metrics(alignment_metrics_dict, run_analysis_obj):
	"""
	Add data from dragen mapping metrics files to database.

	"""
	pipeline = run_analysis_obj.pipeline
	run = run_analysis_obj.run

	for key in alignment_metrics_dict:

		sample_obj = Sample.objects.get(sample_id=key)

		sample_analysis_obj = SampleAnalysis.objects.get(sample=sample_obj,
														run=run,
														pipeline = pipeline)

		existing_data = DragenAlignmentMetrics.objects.filter(sample_analysis= sample_analysis_obj)

		if len(existing_data) < 1:

			sample_data = alignment_metrics_dict[key]
			
			sample_data['sample_analysis'] = sample_analysis_obj

			for key in sample_data:

				if sample_data[key] == 'NA' or sample_data[key] == '':

					sample_data[key] = None

			new_dragen_alignment_obj = DragenAlignmentMetrics(**sample_data)
			new_dragen_alignment_obj.save()

def add_variant_calling_metrics(variant_metrics_dict, run_analysis_obj):
	"""
	Add data from picard variant calling metrics files to database.

	"""

	pipeline = run_analysis_obj.pipeline
	run = run_analysis_obj.run


	for key in variant_metrics_dict:

		sample_obj = Sample.objects.get(sample_id=key)

		sample_analysis_obj = SampleAnalysis.objects.get(sample=sample_obj,
														run=run,
														pipeline = pipeline)
		
		existing_data = VariantCallingMetrics.objects.filter(sample_analysis= sample_analysis_obj)
		
		if len(existing_data) < 1:

			sample_data = variant_metrics_dict[key]

			sample_data['sample_analysis'] = sample_analysis_obj

			for key in sample_data:

				if sample_data[key] == '?' or sample_data[key] == '':

					sample_data[key] = None

			new_variant_obj = VariantCallingMetrics(**sample_data)
			new_variant_obj.save()

def add_insert_metrics(insert_metrics_dict, run_analysis_obj):
	"""
	Add data from picard insert metrics files to database.

	"""
	pipeline = run_analysis_obj.pipeline
	run = run_analysis_obj.run

	for key in insert_metrics_dict:
		
		sample_obj = Sample.objects.get(sample_id=key)

		sample_analysis_obj = SampleAnalysis.objects.get(sample=sample_obj,
														run=run,
														pipeline = pipeline)
		
		existing_data = InsertMetrics.objects.filter(sample_analysis= sample_analysis_obj)
		
		if len(existing_data) < 1:

			sample_data = insert_metrics_dict[key]

			sample_data['sample_analysis'] = sample_analysis_obj
			
			for key in sample_data:

				if sample_data[key] == '?' or sample_data[key] == '':

					sample_data[key] = None

			new_insert_obj = InsertMetrics(**sample_data)
			new_insert_obj.save()


def add_variant_count_metrics(variant_count_metrics_dict, run_analysis_obj):

	pipeline = run_analysis_obj.pipeline
	run = run_analysis_obj.run

	for key in variant_count_metrics_dict:
		
		sample_obj = Sample.objects.get(sample_id=key)

		sample_analysis_obj = SampleAnalysis.objects.get(sample=sample_obj,
														run=run,
														pipeline = pipeline)
		
		existing_data = VCFVariantCount.objects.filter(sample_analysis= sample_analysis_obj)
		
		if len(existing_data) < 1:

			sample_data = variant_count_metrics_dict[key][key]

			new_count_obj = VCFVariantCount(sample_analysis = sample_analysis_obj, variant_count= sample_data)
			new_count_obj.save()

def add_dragen_variant_calling_metrics(variant_metrics_dict, run_analysis_obj):
	"""
	Add data from the Dragen Variant Calling metrics files to database.

	"""
	pipeline = run_analysis_obj.pipeline
	run = run_analysis_obj.run

	for key in variant_metrics_dict:
		
		sample_obj = Sample.objects.get(sample_id=key)

		sample_analysis_obj = SampleAnalysis.objects.get(sample=sample_obj,
														run=run,
														pipeline = pipeline)
		
		existing_data = DragenVariantCallingMetrics.objects.filter(sample_analysis= sample_analysis_obj)
		
		if len(existing_data) < 1:

			sample_data = variant_metrics_dict[key]

			sample_data['sample_analysis'] = sample_analysis_obj
			
			for key in sample_data:

				if sample_data[key] == 'NA' or sample_data[key] == '':

					sample_data[key] = None

			new_dragen_vc_obj = DragenVariantCallingMetrics(**sample_data)
			new_dragen_vc_obj.save()

def add_sensitivity_metrics(sensitivity_metrics, run_analysis_obj):
	"""
	Add sensitivity data for a run

	"""
	run_analysis_obj.sensitivity = float(sensitivity_metrics['sensitivity'])
	run_analysis_obj.sensitivity_lower_ci = float(sensitivity_metrics['sensitivity_lower_ci'])
	run_analysis_obj.sensitivity_higher_ci = float(sensitivity_metrics['sensitivity_higher_ci'])
	run_analysis_obj.sensitivity_user = User.objects.get(pk=1)

	run_analysis_obj.save()

def add_dragen_wgs_coverage_metrics(dragen_wgs_coverage_metrics, run_analysis_obj):

	"""
	Add data from the Dragen Variant Calling WGS coverage files to database.

	"""
	pipeline = run_analysis_obj.pipeline
	run = run_analysis_obj.run

	for key in dragen_wgs_coverage_metrics:
		
		sample_obj = Sample.objects.get(sample_id=key)

		sample_analysis_obj = SampleAnalysis.objects.get(sample=sample_obj,
														run=run,
														pipeline = pipeline)
		
		existing_data = DragenWGSCoverageMetrics.objects.filter(sample_analysis= sample_analysis_obj)
		
		if len(existing_data) < 1:

			sample_data = dragen_wgs_coverage_metrics[key]

			sample_data['sample_analysis'] = sample_analysis_obj
			
			for key in sample_data:

				if sample_data[key] == 'NA' or sample_data[key] == ''  or sample_data[key] == 'inf':

					sample_data[key] = None

			new_dragen_wgs_cov_obj = DragenWGSCoverageMetrics(**sample_data)
			new_dragen_wgs_cov_obj.save()

def add_dragen_exonic_coverage_metrics(dragen_exonic_coverage_metrics, run_analysis_obj):

	"""
	Add data from the Dragen Variant Calling WGS coverage files to database.

	"""
	pipeline = run_analysis_obj.pipeline
	run = run_analysis_obj.run

	for key in dragen_exonic_coverage_metrics:
		
		sample_obj = Sample.objects.get(sample_id=key)

		sample_analysis_obj = SampleAnalysis.objects.get(sample=sample_obj,
														run=run,
														pipeline = pipeline)
		
		existing_data = DragenRegionCoverageMetrics.objects.filter(sample_analysis= sample_analysis_obj)
		
		if len(existing_data) < 1:

			sample_data = dragen_exonic_coverage_metrics[key]

			sample_data['sample_analysis'] = sample_analysis_obj
			
			for key in sample_data:

				if sample_data[key] == 'NA' or sample_data[key] == ''  or sample_data[key] == 'inf':

					sample_data[key] = None

			new_dragen_region_cov_obj = DragenRegionCoverageMetrics(**sample_data)
			new_dragen_region_cov_obj.save()

class Command(BaseCommand):

	def add_arguments(self, parser):

		parser.add_argument('--raw_data_dir', nargs =1, type = str, required=True)

		parser.add_argument('--config', nargs =1, type = str, required=True)
	
	def handle(self, *args, **options):


		logging.basicConfig(level=logging.DEBUG)
		logger = logging.getLogger(__name__)

		# Make or get initial model instances
		raw_data_dir = options['raw_data_dir'][0]
		config = options['config'][0]

		# Read config file and create dictionary
		config_dict = parse_config(config)

		# don't process existing runs
		existing_runs = Run.objects.all()
		existing_runs = [run.pk for run in existing_runs]

		# get runs in existing archive directory
		raw_data_dir = list(Path(raw_data_dir).glob('*/'))


		sample_sheet_dict = {}

		with transaction.atomic():

			# for each folder in  archive directory
			for raw_data in raw_data_dir:

				# skip non directory items
				if raw_data.is_dir() == False:
					continue

				sample_sheet = raw_data.joinpath('SampleSheet.csv')

				# skip if no sample sheet
				if sample_sheet.exists() == False:

					logger.info(f'Could not find sample sheet for {raw_data}')
					continue

				copy_complete = raw_data.joinpath('run_copy_complete.txt')

				if copy_complete.exists() == False:

					continue

				run_id = raw_data.name
				run_obj, created = Run.objects.get_or_create(run_id=run_id)
			
				if run_id not in existing_runs:

					logger.info (f'A new run has been detected: {run_id}')

					# parse runlog data 
					run_info = raw_data.joinpath('RunInfo.xml')
					run_parameters = raw_data.joinpath('runParameters.xml')

					if run_parameters.exists() == False:

						run_parameters = raw_data.joinpath('RunParameters.xml')

						if run_parameters.exists() == False:

							logger.warn (f'Can\'t find run parameters file for {run_id}')
							continue

					if run_info.exists() == False or run_parameters.exists() == False:

						logger.warn (f'Can\'t find required XML files for {run_id}')
						continue


					# add runlog stats to database
					interop_data = add_run_log_info(run_info, run_parameters, run_obj, raw_data)

				else:

					interop_data = None
				
				try:
					# parse sample sheet
					sample_sheet_data = sample_sheet_parser(sample_sheet)

					sample_sheet_dict[run_id] = sample_sheet_data


				except Exception as e:

					logger.exception(e)

					logger.warn(f'Could not parse sample sheet for run {run_id}')
					continue
				
				# set to hold different pipeline combinations
				run_analyses_to_create = set()

				# create sample analysis objects for each sample
				for sample in sample_sheet_data:

					sample_obj, created = Sample.objects.get_or_create(sample_id=sample)
					pipeline = sample_sheet_data[sample]['pipelineName']
					pipeline_version = sample_sheet_data[sample]['pipelineVersion']
					panel = sample_sheet_data[sample]['panel']
					sex = sample_sheet_data[sample].get('sex', None)

					worksheet = sample_sheet_data[sample].get('Sample_Plate', 'Unknown')

					pipeline_and_version = pipeline + '-' + pipeline_version

					pipeline_obj, created = Pipeline.objects.get_or_create(pipeline_id= pipeline_and_version)
					worksheet_obj, created = WorkSheet.objects.get_or_create(worksheet_id= worksheet)
					analysis_type_obj, created = AnalysisType.objects.get_or_create(analysis_type_id=panel)

					run_config_key = pipeline_obj.pipeline_id + '-' + analysis_type_obj.analysis_type_id

					try:
						contamination_cutoff = config_dict['pipelines'][run_config_key]['contamination_cutoff']
						ntc_contamination_cutoff = config_dict['pipelines'][run_config_key]['ntc_contamination_cutoff']
					except:
						contamination_cutoff = 0.015
						ntc_contamination_cutoff = 10



					new_sample_analysis_obj, created = SampleAnalysis.objects.get_or_create(sample=sample_obj,
																			run = run_obj,
																			pipeline = pipeline_obj,
																			analysis_type = analysis_type_obj,
																			worksheet = worksheet_obj
																			)
					if created == True:
						new_sample_analysis_obj.contamination_cutoff = contamination_cutoff
						new_sample_analysis_obj.ntc_contamination_cutoff = ntc_contamination_cutoff

					new_sample_analysis_obj.sex = sex
					new_sample_analysis_obj.save()

					run_analyses_to_create.add((pipeline_and_version, panel ))

				# now create a corresponding run analysis object
				for run_analysis in run_analyses_to_create:

					pipeline = run_analysis[0]
					analysis_type = run_analysis[1]

					pipeline_obj = Pipeline.objects.get(pipeline_id=pipeline)
					analysis_type_obj = AnalysisType.objects.get(analysis_type_id=analysis_type)

					run_config_key = pipeline_obj.pipeline_id + '-' + analysis_type_obj.analysis_type_id

					try:

						min_q30_score = config_dict['pipelines'][run_config_key]['min_q30_score']

					except:

						min_q30_score = 0.8


					try:

						checks_to_try = config_dict['pipelines'][run_config_key]['qc_checks']
						checks_to_try = ','.join(checks_to_try)

					except:

						checks_to_try = None

					try:

						min_variants =  config_dict['pipelines'][run_config_key]['min_variants']
						max_variants =  config_dict['pipelines'][run_config_key]['max_variants']

					except:

						min_variants =  25
						max_variants =  1000	

					try:

						min_sensitivity = config_dict['pipelines'][run_config_key]['min_sensitivity']

					except:

						min_sensitivity = None

					try:

						min_titv =  config_dict['pipelines'][run_config_key]['min_titv']
						max_titv =  config_dict['pipelines'][run_config_key]['max_titv']

					except:

						min_titv = 2.0		
						max_titv = 2.1

					try:

						min_coverage = config_dict['pipelines'][run_config_key]['min_coverage']

					except:

						min_coverage = 90.0

					new_run_analysis_obj, created = RunAnalysis.objects.get_or_create(run = run_obj,
																			pipeline = pipeline_obj,
																			analysis_type = analysis_type_obj)


					if created == True:

						new_run_analysis_obj.auto_qc_checks = checks_to_try
						new_run_analysis_obj.min_variants = min_variants
						new_run_analysis_obj.max_variants = max_variants
						new_run_analysis_obj.min_q30_score = min_q30_score
						new_run_analysis_obj.start_date = datetime.datetime.now()
						new_run_analysis_obj.min_sensitivity = min_sensitivity
						new_run_analysis_obj.min_titv = min_titv
						new_run_analysis_obj.max_titv = max_titv
						new_run_analysis_obj.min_coverage = min_coverage

						# message slack

						if settings.MESSAGE_SLACK:
							message_slack(
								f':information_source: *{new_run_analysis_obj.analysis_type} run {new_run_analysis_obj.get_worksheets()} has finished sequencing*\n' +
								f'```Run ID:          {new_run_analysis_obj.run}```'
							)

					new_run_analysis_obj.save()



			# Loop through existing run analysis objects
			existing_run_analyses = RunAnalysis.objects.filter(watching=True)

			for run_analysis in existing_run_analyses:

				# make IlluminaQC object

				run_config_key = run_analysis.pipeline.pipeline_id + '-' + run_analysis.analysis_type.analysis_type_id

				samples = SampleAnalysis.objects.filter(run = run_analysis.run,
												 pipeline= run_analysis.pipeline,
												 analysis_type= run_analysis.analysis_type)

				sample_ids = [sample.sample.sample_id for sample in samples]


				# have we configured a fastq folder
				has_fastqs = config_dict['pipelines'][run_config_key].get('fastq_dir')


				try:
					results_dir = config_dict['pipelines'][run_config_key]['results_dir']

				except:

					logger.warn(f'No results directory configured for this pipeline {run_config_key}')
					results_dir = '/data/results/'

				if has_fastqs != None:
					
					fastq_data_dir = config_dict['pipelines'][run_config_key]['fastq_dir']
					run_fastq_dir = Path(fastq_data_dir).joinpath(run_analysis.run.run_id)

				else:

					run_fastq_dir = '/data/'

				run_data_dir = Path(results_dir).joinpath(run_analysis.run.run_id, run_analysis.analysis_type.analysis_type_id)

				lanes = run_analysis.run.lanes

				try:

					min_fastq_size = config_dict['pipelines'][run_config_key]['min_fastq_size']

				except:

					min_fastq_size = 100000

				if 'Dragen' in run_config_key:

					illumina_qc = DragenQC(fastq_dir= run_fastq_dir,
										sample_names = sample_ids,
										n_lanes = lanes,
										analysis_type = run_analysis.analysis_type.analysis_type_id,
										min_fastq_size = min_fastq_size,
										run_id = run_analysis.run.run_id)

				else:

					illumina_qc = IlluminaQC(fastq_dir= run_fastq_dir,
											sample_names = sample_ids,
											n_lanes = lanes,
											analysis_type = run_analysis.analysis_type.analysis_type_id,
											min_fastq_size = min_fastq_size,
											run_id = run_analysis.run.run_id)


				# if we have not given a directory for fastqs then pretend everything is ok
				if has_fastqs == None:

					has_completed = True
					is_valid = True

				else:

					has_completed = illumina_qc.demultiplex_run_is_complete()

					is_valid = illumina_qc.demultiplex_run_is_valid()

				if run_analysis.demultiplexing_completed == False and has_completed == True:

					if is_valid == True:

						logger.info(f'Run {run_analysis} {run_analysis.analysis_type.analysis_type_id} has now completed demultiplexing')
						
						# set slack status message
						status_message = f':information_source: *{run_analysis.analysis_type} run {run_analysis.get_worksheets()} has generated FASTQs successfully*\n'

					else:

						logger.info(f'Run {run_id} {run_analysis.analysis_type.analysis_type_id} has now failed demultiplexing')
						run_analysis.demultiplexing_completed = has_completed
						run_analysis.demultiplexing_valid = is_valid
						run_analysis.save()
						
						# set slack status message
						status_message = f':heavy_exclamation_mark: *{run_analysis.analysis_type} run {run_analysis.get_worksheets()} has failed FASTQ generation*\n'
						

					# send slack message
					if settings.MESSAGE_SLACK:

						message_slack(
							status_message +
							f'```Run ID:          {run_analysis.run}\n' + 
							f'QC link:          http://10.59.210.245:5000/run_analysis/{run_analysis.pk}/```'
						)

				run_analysis.demultiplexing_completed = has_completed
				run_analysis.demultiplexing_valid = is_valid
				run_analysis.save()
				
				# set to false, will be overwritten if pipeline is comleted
				send_to_slack = False

				# for germline enrichment
				if 'GermlineEnrichment' in run_analysis.pipeline.pipeline_id:

					run_config_key = run_analysis.pipeline.pipeline_id + '-' + run_analysis.analysis_type.analysis_type_id

					try:
						sample_expected_files = config_dict['pipelines'][run_config_key]['sample_expected_files']
						sample_not_expected_files = config_dict['pipelines'][run_config_key]['sample_not_expected_files']
						run_expected_files = config_dict['pipelines'][run_config_key]['run_expected_files']
						run_not_expected_files = config_dict['pipelines'][run_config_key]['run_not_expected_files']

						germline_enrichment = GermlineEnrichment(results_dir = run_data_dir,
															sample_names = sample_ids,
															run_id = run_analysis.run.run_id,
															sample_expected_files = sample_expected_files,
															sample_not_expected_files = sample_not_expected_files,
															run_expected_files = run_expected_files,
															run_not_expected_files = run_not_expected_files
															)

					except:

						germline_enrichment = GermlineEnrichment(results_dir = run_data_dir,
															sample_names = sample_ids,
															run_id = run_analysis.run.run_id
															)

					for sample in sample_ids:

						sample_complete = germline_enrichment.sample_is_complete(sample)
						sample_valid = germline_enrichment.sample_is_valid(sample)

						sample_obj = Sample.objects.get(sample_id = sample)

						sample_analysis_obj = SampleAnalysis.objects.get(sample=sample,
																		run = run_analysis.run,
																		pipeline = run_analysis.pipeline)

						if sample_analysis_obj.results_completed == False and sample_complete == True:

							if sample_valid == True:

								logger.info(f'Sample {sample} on run {run_analysis.run.run_id} has finished GermlineEnrichment script one successfully.')

							else:
								logger.info(f'Sample {sample} on run {run_analysis.run.run_id} has failed GermlineEnrichment script one.')

						elif sample_analysis_obj.results_valid == False and sample_valid == True and sample_complete == True:

							logger.info(f'Sample {sample} on run {run_analysis.run.run_id} has now completed successfully.')


						sample_analysis_obj.results_completed = sample_complete
						sample_analysis_obj.results_valid = sample_valid
						sample_analysis_obj.save()

					run_complete = germline_enrichment.run_and_samples_complete()
					run_valid = germline_enrichment.run_and_samples_valid()

					if run_analysis.results_completed == False and run_complete == True:

						if run_valid == True:

							logger.info(f'Run {run_id} has now successfully completed pipeline {run_analysis.pipeline.pipeline_id}')
							logger.info('putting fastqc into db')

							logger.info(f'Putting fastqc data into db for run {run_analysis.run.run_id}')
							fastqc_dict = germline_enrichment.get_fastqc_data()
							add_fastqc_data(fastqc_dict, run_analysis)

							logger.info(f'Putting hs metrics into db for run {run_analysis.run.run_id}')
							hs_metrics_dict = germline_enrichment.get_hs_metrics()
							add_hs_metrics(hs_metrics_dict, run_analysis)

							logger.info (f'Putting depth metrics into db for run {run_analysis.run.run_id}')
							depth_metrics_dict = germline_enrichment.get_depth_metrics()
							add_depth_of_coverage_metrics(depth_metrics_dict, run_analysis)

							logger.info (f'Putting duplication into db for run {run_analysis.run.run_id}')
							duplication_metrics_dict = germline_enrichment.get_duplication_metrics()
							add_duplication_metrics(duplication_metrics_dict, run_analysis)

							logger.info (f'Putting contamination metrics into db for run {run_analysis.run.run_id}')
							contamination_metrics_dict = germline_enrichment.get_contamination()
							add_contamination_metrics(contamination_metrics_dict, run_analysis)

							logger.info (f'Putting sex metrics into db for run {run_analysis.run.run_id}')
							sex_dict = germline_enrichment.get_calculated_sex()
							add_sex_metrics(sex_dict, run_analysis, 'gender')

							logger.info (f'Putting alignment metrics into db for run {run_analysis.run.run_id}')
							alignment_metrics_dict = germline_enrichment.get_alignment_metrics()
							add_alignment_metrics(alignment_metrics_dict, run_analysis)

							logger.info (f'Putting variant calling metrics into db for run {run_analysis.run.run_id}')
							variant_calling_metrics_dict = germline_enrichment.get_variant_calling_metrics()
							add_variant_calling_metrics(variant_calling_metrics_dict, run_analysis)

							logger.info (f'Putting insert metrics into db for run {run_analysis.run.run_id}')
							insert_metrics_dict = germline_enrichment.get_insert_metrics()
							add_insert_metrics(insert_metrics_dict, run_analysis)

							send_to_slack = True

						else:

							logger.info (f'Run {run_id} has failed pipeline {run_analysis.pipeline.pipeline_id}')

					elif run_analysis.results_valid == False and run_valid == True and run_complete == True:

							logger.info (f'Run {run_id} now successfully completed pipeline {run_analysis.pipeline.pipeline_id}')

							logger.info (f'Putting fastqc data into db for run {run_analysis.run.run_id}')
							fastqc_dict = germline_enrichment.get_fastqc_data()
							add_fastqc_data(fastqc_dict, run_analysis)

							logger.info (f'Putting hs metrics into db for run {run_analysis.run.run_id}')
							hs_metrics_dict = germline_enrichment.get_hs_metrics()
							add_hs_metrics(hs_metrics_dict, run_analysis)

							logger.info (f'Putting depth metrics into db for run {run_analysis.run.run_id}')
							depth_metrics_dict = germline_enrichment.get_depth_metrics()
							add_depth_of_coverage_metrics(depth_metrics_dict, run_analysis)

							logger.info (f'Putting duplication into db for run {run_analysis.run.run_id}')
							duplication_metrics_dict = germline_enrichment.get_duplication_metrics()
							add_duplication_metrics(duplication_metrics_dict, run_analysis)

							logger.info (f'Putting contamination metrics into db for run {run_analysis.run.run_id}')
							contamination_metrics_dict = germline_enrichment.get_contamination()
							add_contamination_metrics(contamination_metrics_dict, run_analysis)

							logger.info (f'Putting sex metrics into db for run {run_analysis.run.run_id}')
							sex_dict = germline_enrichment.get_calculated_sex()
							add_sex_metrics(sex_dict, run_analysis, 'gender')

							logger.info (f'Putting alignment metrics into db for run {run_analysis.run.run_id}')
							alignment_metrics_dict = germline_enrichment.get_alignment_metrics()
							add_alignment_metrics(alignment_metrics_dict, run_analysis)

							logger.info (f'Putting variant calling metrics into db for run {run_analysis.run.run_id}')
							variant_calling_metrics_dict = germline_enrichment.get_variant_calling_metrics()
							add_variant_calling_metrics(variant_calling_metrics_dict, run_analysis)

							logger.info (f'Putting insert metrics into db for run {run_analysis.run.run_id}')
							insert_metrics_dict = germline_enrichment.get_insert_metrics()
							add_insert_metrics(insert_metrics_dict, run_analysis)

							send_to_slack = True

					run_analysis.results_completed = run_complete
					run_analysis.results_valid = run_valid

					run_analysis.save()

				elif 'SomaticEnrichment' in run_analysis.pipeline.pipeline_id:

					run_config_key = run_analysis.pipeline.pipeline_id + '-' + run_analysis.analysis_type.analysis_type_id

					if run_config_key not in config_dict['pipelines']:

						somatic_enrichment = SomaticEnrichment(results_dir = run_data_dir,
															sample_names = sample_ids,
															run_id = run_analysis.run.run_id
															)
					else:

						sample_expected_files = config_dict['pipelines'][run_config_key]['sample_expected_files']
						sample_not_expected_files = config_dict['pipelines'][run_config_key]['sample_not_expected_files']
						run_sample_expected_files = config_dict['pipelines'][run_config_key]['run_sample_expected_files']
						run_expected_files = config_dict['pipelines'][run_config_key]['run_expected_files']
						run_not_expected_files = config_dict['pipelines'][run_config_key]['run_not_expected_files']

						somatic_enrichment = SomaticEnrichment(results_dir = run_data_dir,
																sample_names = sample_ids,
																run_id = run_analysis.run.run_id,
																sample_expected_files = sample_expected_files,
																sample_not_expected_files = sample_not_expected_files,
																run_sample_expected_files = run_sample_expected_files,
																run_expected_files = run_expected_files,
																run_not_expected_files = run_not_expected_files
																)


					for sample in sample_ids:

						sample_complete = somatic_enrichment.sample_is_complete(sample)
						sample_valid = somatic_enrichment.sample_is_valid(sample)

						sample_obj = Sample.objects.get(sample_id = sample)

						sample_analysis_obj = SampleAnalysis.objects.get(sample=sample,
																		run = run_analysis.run,
																		pipeline = run_analysis.pipeline)

						if sample_analysis_obj.results_completed == False and sample_complete == True:

							if sample_valid == True:

								logger.info (f'Sample {sample} on run {run_analysis.run.run_id} has finished sample level SomaticEnrichment successfully.')

							else:
								logger.info (f'Sample {sample} on run {run_analysis.run.run_id} has failed sample level SomaticEnrichment.')

						elif sample_analysis_obj.results_valid == False and sample_valid == True and sample_complete == True:

							logger.info (f'Sample {sample} on run {run_analysis.run.run_id} has now completed successfully.')

			
						sample_analysis_obj.results_completed = sample_complete
						sample_analysis_obj.results_valid = sample_valid
						sample_analysis_obj.save()

					run_complete = somatic_enrichment.run_and_samples_complete()
					run_valid = somatic_enrichment.run_and_samples_valid()

					if run_analysis.results_completed == False and run_complete == True:

						if run_valid == True:

							logger.info (f'Run {run_id} has now successfully completed pipeline {run_analysis.pipeline.pipeline_id}')

							logger.info (f'Putting fastqc data into db for run {run_analysis.run.run_id}')
							fastqc_dict = somatic_enrichment.get_fastqc_data()
							add_fastqc_data(fastqc_dict, run_analysis)
							
							logger.info (f'Putting hs metrics data into db for run {run_analysis.run.run_id}')
							hs_metrics_dict = somatic_enrichment.get_hs_metrics()
							add_hs_metrics(hs_metrics_dict, run_analysis)

							logger.info (f'Putting depth metrics data into db for run {run_analysis.run.run_id}')
							depth_metrics_dict = somatic_enrichment.get_depth_metrics()
							add_depth_of_coverage_metrics(depth_metrics_dict, run_analysis)

							logger.info (f'Putting duplication metrics data into db for run {run_analysis.run.run_id}')
							duplication_metrics_dict = somatic_enrichment.get_duplication_metrics()
							add_duplication_metrics(duplication_metrics_dict, run_analysis)

							logger.info (f'Putting sex metrics data into db for run {run_analysis.run.run_id}')
							sex_dict = somatic_enrichment.get_calculated_sex()
							add_sex_metrics(sex_dict, run_analysis, 'gender')

							logger.info (f'Putting alignment metrics data into db for run {run_analysis.run.run_id}')
							alignment_metrics_dict = somatic_enrichment.get_alignment_metrics()
							add_alignment_metrics(alignment_metrics_dict, run_analysis)

							logger.info (f'Putting insert metrics data into db for run {run_analysis.run.run_id}')
							insert_metrics_dict = somatic_enrichment.get_insert_metrics()
							add_insert_metrics(insert_metrics_dict, run_analysis)

							logger.info (f'Putting variant count metrics data into db for run {run_analysis.run.run_id}')
							variant_count_metrics_dict = somatic_enrichment.get_variant_count()
							add_variant_count_metrics(variant_count_metrics_dict, run_analysis)

							send_to_slack = True

						else:

							logger.info (f'Run {run_id} has failed pipeline {run_analysis.pipeline.pipeline_id}')

					elif run_analysis.results_valid == False and run_valid == True and run_complete == True:

							logger.info (f'Run {run_id} has now successfully completed pipeline {run_analysis.pipeline.pipeline_id}')

							logger.info (f'Putting fastqc data into db for run {run_analysis.run.run_id}')
							fastqc_dict = somatic_enrichment.get_fastqc_data()
							add_fastqc_data(fastqc_dict, run_analysis)
							
							logger.info (f'Putting hs metrics data into db for run {run_analysis.run.run_id}')
							hs_metrics_dict = somatic_enrichment.get_hs_metrics()
							add_hs_metrics(hs_metrics_dict, run_analysis)

							logger.info (f'Putting depth metrics data into db for run {run_analysis.run.run_id}')
							depth_metrics_dict = somatic_enrichment.get_depth_metrics()
							add_depth_of_coverage_metrics(depth_metrics_dict, run_analysis)

							logger.info (f'Putting duplication metrics data into db for run {run_analysis.run.run_id}')
							duplication_metrics_dict = somatic_enrichment.get_duplication_metrics()
							add_duplication_metrics(duplication_metrics_dict, run_analysis)

							logger.info (f'Putting sex metrics data into db for run {run_analysis.run.run_id}')
							sex_dict = somatic_enrichment.get_calculated_sex()
							add_sex_metrics(sex_dict, run_analysis, 'gender')

							logger.info (f'Putting alignment metrics data into db for run {run_analysis.run.run_id}')
							alignment_metrics_dict = somatic_enrichment.get_alignment_metrics()
							add_alignment_metrics(alignment_metrics_dict, run_analysis)

							logger.info (f'Putting insert metrics data into db for run {run_analysis.run.run_id}')
							insert_metrics_dict = somatic_enrichment.get_insert_metrics()
							add_insert_metrics(insert_metrics_dict, run_analysis)

							logger.info (f'Putting variant count metrics data into db for run {run_analysis.run.run_id}')
							variant_count_metrics_dict = somatic_enrichment.get_variant_count()
							add_variant_count_metrics(variant_count_metrics_dict, run_analysis)

							send_to_slack = True

					run_analysis.results_completed = run_complete
					run_analysis.results_valid = run_valid

					run_analysis.save()

				elif 'SomaticAmplicon' in run_analysis.pipeline.pipeline_id:

					run_config_key = run_analysis.pipeline.pipeline_id + '-' + run_analysis.analysis_type.analysis_type_id

					if run_config_key not in config_dict['pipelines']:

						somatic_amplicon = SomaticAmplicon(results_dir = run_data_dir,
															sample_names = sample_ids,
															run_id = run_analysis.run.run_id
															)
					else:

						sample_expected_files = config_dict['pipelines'][run_config_key]['sample_expected_files']
						sample_not_expected_files = config_dict['pipelines'][run_config_key]['sample_not_expected_files']
						run_expected_files = config_dict['pipelines'][run_config_key]['run_expected_files']
						run_not_expected_files = config_dict['pipelines'][run_config_key]['run_not_expected_files']

						somatic_amplicon = SomaticAmplicon(results_dir = run_data_dir,
																sample_names = sample_ids,
																run_id = run_analysis.run.run_id,
																sample_expected_files = sample_expected_files,
																sample_not_expected_files = sample_not_expected_files,
																run_expected_files = run_expected_files,
																run_not_expected_files = run_not_expected_files
																)

					for sample in sample_ids:

						sample_complete = somatic_amplicon.sample_is_complete(sample)
						sample_valid = somatic_amplicon.sample_is_valid(sample)

						sample_obj = Sample.objects.get(sample_id = sample)

						sample_analysis_obj = SampleAnalysis.objects.get(sample=sample,
																		run = run_analysis.run,
																		pipeline = run_analysis.pipeline)

						if sample_analysis_obj.results_completed == False and sample_complete == True:

							if sample_valid == True:

								logger.info (f'Sample {sample} on run {run_analysis.run.run_id} {run_analysis.analysis_type.analysis_type_id} has finished sample level SomaticAmplicon successfully.')

							else:
								logger.info (f'Sample {sample} on run {run_analysis.run.run_id} {run_analysis.analysis_type.analysis_type_id} has failed sample level SomaticAmplicon.')

						elif sample_analysis_obj.results_valid == False and sample_valid == True and sample_complete == True:

							logger.info (f'Sample {sample} on run {run_analysis.run.run_id} {run_analysis.analysis_type.analysis_type_id} has now completed successfully.')

			
						sample_analysis_obj.results_completed = sample_complete
						sample_analysis_obj.results_valid = sample_valid
						sample_analysis_obj.save()

					run_complete = somatic_amplicon.run_is_complete()
					run_valid = somatic_amplicon.run_is_valid()

					if run_analysis.results_completed == False and run_complete == True:

						if run_valid == True:

							logger.info (f'Run {run_analysis.run.run_id} {run_analysis.analysis_type.analysis_type_id} has now successfully completed pipeline {run_analysis.pipeline.pipeline_id}')

							logger.info (f'Putting fastqc data into db for run {run_analysis.run.run_id}')
							fastqc_dict = somatic_amplicon.get_fastqc_data()
							add_fastqc_data(fastqc_dict, run_analysis)
							
							logger.info (f'Putting hs metrics data into db for run {run_analysis.run.run_id}')
							hs_metrics_dict = somatic_amplicon.get_hs_metrics()
							add_hs_metrics(hs_metrics_dict, run_analysis)

							logger.info (f'Putting depth metrics data into db for run {run_analysis.run.run_id}')
							depth_metrics_dict = somatic_amplicon.get_depth_metrics()
							add_depth_of_coverage_metrics(depth_metrics_dict, run_analysis)


							logger.info (f'Putting variant count metrics data into db for run {run_analysis.run.run_id}')
							variant_count_metrics_dict = somatic_amplicon.get_variant_count()
							add_variant_count_metrics(variant_count_metrics_dict, run_analysis)

							send_to_slack = True

						else:

							logger.info (f'Run {run_id} {run_analysis.analysis_type.analysis_type_id} has failed pipeline {run_analysis.pipeline.pipeline_id}')

					elif run_analysis.results_valid == False and run_valid == True and run_complete == True:

							logger.info (f'Run {run_id} {run_analysis.analysis_type.analysis_type_id} has now successfully completed pipeline {run_analysis.pipeline.pipeline_id}')

							logger.info (f'Putting fastqc data into db for run {run_analysis.run.run_id}')
							fastqc_dict = somatic_amplicon.get_fastqc_data()
							add_fastqc_data(fastqc_dict, run_analysis)
							
							logger.info (f'Putting hs metrics data into db for run {run_analysis.run.run_id}')
							hs_metrics_dict = somatic_amplicon.get_hs_metrics()
							add_hs_metrics(hs_metrics_dict, run_analysis)

							logger.info (f'Putting depth metrics data into db for run {run_analysis.run.run_id}')
							depth_metrics_dict = somatic_amplicon.get_depth_metrics()
							add_depth_of_coverage_metrics(depth_metrics_dict, run_analysis)

							logger.info (f'Putting variant count metrics data into db for run {run_analysis.run.run_id}')
							variant_count_metrics_dict = somatic_amplicon.get_variant_count()
							add_variant_count_metrics(variant_count_metrics_dict, run_analysis)

							send_to_slack = True

					run_analysis.results_completed = run_complete
					run_analysis.results_valid = run_valid

					run_analysis.save()

				elif 'CRUK' in run_analysis.pipeline.pipeline_id:

					run_config_key = run_analysis.pipeline.pipeline_id + '-' + run_analysis.analysis_type.analysis_type_id

					if run_analysis.run.run_id in sample_sheet_dict:

						sample_sheet_data = sample_sheet_dict[run_analysis.run.run_id]

					else:

						continue

					if run_config_key not in config_dict['pipelines']:

						cruk = Cruk(results_dir=run_data_dir,
								   sample_names=sample_ids,
								   run_id=run_analysis.run.run_id,
								   sample_sheet_data=sample_sheet_data)
					else:

						sample_expected_files = config_dict['pipelines'][run_config_key]['sample_expected_files']
						sample_not_expected_files = config_dict['pipelines'][run_config_key]['sample_not_expected_files']
						sample_run_dna_expected_files = config_dict['pipelines'][run_config_key]['sample_run_dna_expected_files']
						sample_run_rna_expected_files = config_dict['pipelines'][run_config_key]['sample_run_rna_expected_files']
						run_complete_expected_files = config_dict['pipelines'][run_config_key]['run_complete_expected_files']
						run_not_expected_files = config_dict['pipelines'][run_config_key]['run_not_expected_files']
						run_valid_expected_files = config_dict['pipelines'][run_config_key]['run_valid_expected_files']

						cruk = Cruk(results_dir=run_data_dir,
								   sample_names=sample_ids,
								   run_id=run_analysis.run.run_id,
								   sample_sheet_data = sample_sheet_data,
								   sample_expected_files=sample_expected_files,
								   sample_not_expected_files=sample_not_expected_files,
								   sample_run_dna_expected_files=sample_run_dna_expected_files,
								   sample_run_rna_expected_files=sample_run_rna_expected_files,
								   run_valid_expected_files = run_valid_expected_files,
								   run_complete_expected_files=run_complete_expected_files,
								   run_not_expected_files=run_not_expected_files
								   )

					for sample in sample_ids:

						sample_complete = cruk.sample_is_complete(sample)
						sample_valid = cruk.sample_is_valid(sample)

						sample_obj = Sample.objects.get(sample_id=sample)
						sample_analysis_obj = SampleAnalysis.objects.get(sample=sample,
												run=run_analysis.run,
												pipeline=run_analysis.pipeline)

						if sample_analysis_obj.results_completed == False and sample_complete == True:

							if sample_valid == True:

								logger.info(f'Sample {sample} on run {run_analysis.run.run_id} {run_analysis.analysis_type.analysis_type_id} has finished sample level Cruk successfully.')

							else:
								logger.info(f'Sample {sample} on run {run_analysis.run.run_id} {run_analysis.analysis_type.analysis_type_id} has failed sample level Cruk.')

						elif sample_analysis_obj.results_valid == False and sample_valid == True and sample_complete == True:

							logger.info(f'Sample {sample} on run {run_analysis.run.run_id} {run_analysis.analysis_type.analysis_type_id} has now completed successfully.')

						sample_analysis_obj.results_completed = sample_complete
						sample_analysis_obj.results_valid = sample_valid
						sample_analysis_obj.save()


					run_complete = cruk.run_is_complete()
					run_valid = cruk.run_is_valid()

					ok_to_upload = cruk.ok_to_upload_fastqc_data()

					if ok_to_upload == True:

						logger.info(f'Putting fastqc data into db for run {run_analysis.run.run_id}')
						fastqc_dict = cruk.get_fastqc_data()
						add_fastqc_data(fastqc_dict, run_analysis)	

					if run_analysis.results_completed == False and run_complete == True:

						if run_valid == True:

							logger.info(f'Run {run_analysis.run.run_id} {run_analysis.analysis_type.analysis_type_id} has now successfully completed pipeline {run_analysis.pipeline.pipeline_id}')

							send_to_slack = True

						else:

							logger.info(f'Run {run_id} {run_analysis.analysis_type.analysis_type_id} has failed pipeline {run_analysis.pipeline.pipeline_id}')

					elif run_analysis.results_valid == False and run_valid == True and run_complete == True:

						logger.info(f'Run {run_id} {run_analysis.analysis_type.analysis_type_id} has now successfully completed pipeline {run_analysis.pipeline.pipeline_id}')

						send_to_slack = True

					run_analysis.results_completed = run_complete
					run_analysis.results_valid = run_valid

					run_analysis.save()


				# for germline enrichment
				elif 'DragenGE' in run_analysis.pipeline.pipeline_id:

					run_config_key = run_analysis.pipeline.pipeline_id + '-' + run_analysis.analysis_type.analysis_type_id

					try:

						sample_expected_files = config_dict['pipelines'][run_config_key]['sample_expected_files']
						post_sample_files = config_dict['pipelines'][run_config_key]['post_sample_files']
						sample_not_expected_files = config_dict['pipelines'][run_config_key]['sample_not_expected_files']
						run_expected_files = config_dict['pipelines'][run_config_key]['run_expected_files']
						run_not_expected_files = config_dict['pipelines'][run_config_key]['run_not_expected_files']

						dragen_ge = DragenGE(results_dir = run_data_dir,
															sample_names = sample_ids,
															run_id = run_analysis.run.run_id,
															sample_expected_files = sample_expected_files,
															sample_not_expected_files = sample_not_expected_files,
															run_expected_files = run_expected_files,
															run_not_expected_files = run_not_expected_files,
															post_sample_files = post_sample_files
															)

					except:

						dragen_ge = DragenGE(results_dir = run_data_dir,
															sample_names = sample_ids,
															run_id = run_analysis.run.run_id
															)

					for sample in sample_ids:

						sample_complete = dragen_ge.sample_is_complete(sample)
						sample_valid = dragen_ge.sample_is_valid(sample)

						sample_obj = Sample.objects.get(sample_id = sample)

						sample_analysis_obj = SampleAnalysis.objects.get(sample=sample,
																		run = run_analysis.run,
																		pipeline = run_analysis.pipeline)

						if sample_analysis_obj.results_completed == False and sample_complete == True:

							if sample_valid == True:

								logger.info (f'Sample {sample} on run {run_analysis.run.run_id} has finished DragenGE pipelines successfully.')

							else:
								logger.info (f'Sample {sample} on run {run_analysis.run.run_id} has failed DragenGE pipeline.')

						elif sample_analysis_obj.results_valid == False and sample_valid == True and sample_complete == True:

							logger.info (f'Sample {sample} on run {run_analysis.run.run_id} has now completed successfully.')


						sample_analysis_obj.results_completed = sample_complete
						sample_analysis_obj.results_valid = sample_valid
						sample_analysis_obj.save()

					run_complete = dragen_ge.run_and_samples_complete()
					run_valid = dragen_ge.run_and_samples_valid()

					if run_analysis.results_completed == False and run_complete == True:

						if run_valid == True:

							logger.info (f'Run {run_analysis.run.run_id} has now successfully completed pipeline {run_analysis.pipeline.pipeline_id}')

							logger.info (f'Putting depth metrics into db for run {run_analysis.run.run_id}')
							depth_metrics_dict = dragen_ge.get_depth_metrics()
							add_depth_of_coverage_metrics(depth_metrics_dict, run_analysis)

							logger.info (f'Putting contamination metrics into db for run {run_analysis.run.run_id}')
							contamination_metrics_dict = dragen_ge.get_contamination()
							add_contamination_metrics(contamination_metrics_dict, run_analysis)

							logger.info (f'Putting sex metrics into db for run {run_analysis.run.run_id}')
							sex_dict = dragen_ge.get_sex_metrics()
							add_sex_metrics(sex_dict, run_analysis, 'sex')

							logger.info (f'Putting alignment metrics into db for run {run_analysis.run.run_id}')
							alignment_metrics_dict = dragen_ge.get_alignment_metrics()
							add_dragen_alignment_metrics(alignment_metrics_dict, run_analysis)

							logger.info (f'Putting variant calling metrics into db for run {run_analysis.run.run_id}')
							variant_calling_metrics_dict = dragen_ge.get_variant_calling_metrics()
							add_dragen_variant_calling_metrics(variant_calling_metrics_dict, run_analysis)

							logger.info (f'Putting sensitivity metrics into db for run {run_analysis.run.run_id}')
							sensitivity_metrics = dragen_ge.get_sensitivity()
							add_sensitivity_metrics(sensitivity_metrics, run_analysis)

							logger.info (f'Adding variant count metrics into db for run {run_analysis.run.run_id}')
							variant_count = dragen_ge.get_variant_count_metrics()
							add_variant_count_metrics(variant_count, run_analysis)

							send_to_slack = True

						else:

							logger.info (f'Run {run_analysis.run.run_id} has failed pipeline {run_analysis.pipeline.pipeline_id}')

					elif run_analysis.results_valid == False and run_valid == True and run_complete == True:

							logger.info (f'Run {run_analysis.run.run_id} now successfully completed pipeline {run_analysis.pipeline.pipeline_id}')

							logger.info (f'Putting depth metrics into db for run {run_analysis.run.run_id}')
							depth_metrics_dict = dragen_ge.get_depth_metrics()
							add_depth_of_coverage_metrics(depth_metrics_dict, run_analysis)

							logger.info (f'Putting contamination metrics into db for run {run_analysis.run.run_id}')
							contamination_metrics_dict = dragen_ge.get_contamination()
							add_contamination_metrics(contamination_metrics_dict, run_analysis)

							logger.info (f'Putting sex metrics into db for run {run_analysis.run.run_id}')
							sex_dict = dragen_ge.get_sex_metrics()
							add_sex_metrics(sex_dict, run_analysis, 'sex')

							logger.info (f'Putting alignment metrics into db for run {run_analysis.run.run_id}')
							alignment_metrics_dict = dragen_ge.get_alignment_metrics()
							add_dragen_alignment_metrics(alignment_metrics_dict, run_analysis)

							logger.info (f'Putting variant calling metrics into db for run {run_analysis.run.run_id}')
							variant_calling_metrics_dict = dragen_ge.get_variant_calling_metrics()
							add_dragen_variant_calling_metrics(variant_calling_metrics_dict, run_analysis)

							logger.info (f'Adding variant count metrics into db for run {run_analysis.run.run_id}')
							variant_count = dragen_ge.get_variant_count_metrics()
							add_variant_count_metrics(variant_count, run_analysis)


							send_to_slack = True

					run_analysis.results_completed = run_complete
					run_analysis.results_valid = run_valid

					run_analysis.save()

				# for germline enrichment
				elif 'DragenWGS' in run_analysis.pipeline.pipeline_id:

					run_config_key = run_analysis.pipeline.pipeline_id + '-' + run_analysis.analysis_type.analysis_type_id

					try:

						sample_expected_files = config_dict['pipelines'][run_config_key]['sample_expected_files']
						post_sample_files = config_dict['pipelines'][run_config_key]['post_sample_files']
						sample_not_expected_files = config_dict['pipelines'][run_config_key]['sample_not_expected_files']
						run_expected_files = config_dict['pipelines'][run_config_key]['run_expected_files']
						run_not_expected_files = config_dict['pipelines'][run_config_key]['run_not_expected_files']

						dragen_wgs = DragenWGS(results_dir = run_data_dir,
															sample_names = sample_ids,
															run_id = run_analysis.run.run_id,
															sample_expected_files = sample_expected_files,
															sample_not_expected_files = sample_not_expected_files,
															run_expected_files = run_expected_files,
															run_not_expected_files = run_not_expected_files,
															post_sample_files = post_sample_files
															)

					except:

						dragen_wgs = DragenWGS(results_dir = run_data_dir,
															sample_names = sample_ids,
															run_id = run_analysis.run.run_id
															)

					for sample in sample_ids:

						sample_complete = dragen_wgs.sample_is_complete(sample)
						sample_valid = dragen_wgs.sample_is_valid(sample)

						sample_obj = Sample.objects.get(sample_id = sample)

						sample_analysis_obj = SampleAnalysis.objects.get(sample=sample,
																		run = run_analysis.run,
																		pipeline = run_analysis.pipeline)

						if sample_analysis_obj.results_completed == False and sample_complete == True:

							if sample_valid == True:

								logger.info (f'Sample {sample} on run {run_analysis.run.run_id} has finished DragenWGS pipelines successfully.')

							else:
								logger.info (f'Sample {sample} on run {run_analysis.run.run_id} has failed DragenWGS pipeline.')

						elif sample_analysis_obj.results_valid == False and sample_valid == True and sample_complete == True:

							logger.info (f'Sample {sample} on run {run_analysis.run.run_id} has now completed successfully.')


						sample_analysis_obj.results_completed = sample_complete
						sample_analysis_obj.results_valid = sample_valid
						sample_analysis_obj.save()

					run_complete = dragen_wgs.run_and_samples_complete()
					run_valid = dragen_wgs.run_and_samples_valid()

					if run_analysis.results_completed == False and run_complete == True:

						if run_valid == True:

							logger.info (f'Run {run_analysis.run.run_id} has now successfully completed pipeline {run_analysis.pipeline.pipeline_id}')

							logger.info (f'Putting alignment metrics into db for run {run_analysis.run.run_id}')
							alignment_metrics_dict = dragen_wgs.get_alignment_metrics()
							add_dragen_alignment_metrics(alignment_metrics_dict, run_analysis)

							logger.info (f'Putting variant calling metrics into db for run {run_analysis.run.run_id}')
							variant_calling_metrics_dict = dragen_wgs.get_variant_calling_metrics()
							add_dragen_variant_calling_metrics(variant_calling_metrics_dict, run_analysis)

							logger.info (f'Putting WGS metrics into db for run {run_analysis.run.run_id}')
							wgs_coverage_metrics_dict = dragen_wgs.get_wgs_mapping_metrics()
							add_dragen_wgs_coverage_metrics(wgs_coverage_metrics_dict, run_analysis)

							logger.info (f'Putting exonic coverage metrics into db for run {run_analysis.run.run_id}')
							exonic_coverage_metrics_dict = dragen_wgs.get_exonic_mapping_metrics()
							add_dragen_exonic_coverage_metrics(exonic_coverage_metrics_dict, run_analysis)



							send_to_slack = True

						else:

							logger.info (f'Run {run_analysis.run.run_id} has failed pipeline {run_analysis.pipeline.pipeline_id}')

					elif run_analysis.results_valid == False and run_valid == True and run_complete == True:

							logger.info (f'Run {run_analysis.run.run_id} now successfully completed pipeline {run_analysis.pipeline.pipeline_id}')

							logger.info (f'Putting alignment metrics into db for run {run_analysis.run.run_id}')
							alignment_metrics_dict = dragen_wgs.get_alignment_metrics()
							add_dragen_alignment_metrics(alignment_metrics_dict, run_analysis)

							logger.info (f'Putting variant calling metrics into db for run {run_analysis.run.run_id}')
							variant_calling_metrics_dict = dragen_wgs.get_variant_calling_metrics()
							add_dragen_variant_calling_metrics(variant_calling_metrics_dict, run_analysis)

							logger.info (f'Putting WGS metrics into db for run {run_analysis.run.run_id}')
							wgs_coverage_metrics_dict = dragen_wgs.get_wgs_mapping_metrics()
							add_dragen_wgs_coverage_metrics(wgs_coverage_metrics_dict, run_analysis)

							logger.info (f'Putting exonic coverage metrics into db for run {run_analysis.run.run_id}')
							exonic_coverage_metrics_dict = dragen_wgs.get_exonic_mapping_metrics()
							add_dragen_exonic_coverage_metrics(exonic_coverage_metrics_dict, run_analysis)
							send_to_slack = True

					run_analysis.results_completed = run_complete
					run_analysis.results_valid = run_valid

					run_analysis.save()			

				# message slack
				if settings.MESSAGE_SLACK:
					if send_to_slack:
						message_slack(
							f':heavy_exclamation_mark: *{run_analysis.analysis_type} run {run_analysis.get_worksheets()} is ready for QC*\n' +
							f'```Run ID:          {run_analysis.run}\n' + 
							f'QC link:          http://10.59.210.245:5000/run_analysis/{run_analysis.pk}/```'
						)
