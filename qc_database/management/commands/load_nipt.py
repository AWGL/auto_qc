from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from pathlib import Path
import csv
import datetime
from qc_database.models import *
from pipelines.parsers import *

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

	try:
	
		interop_dict = parse_interop_data(str(raw_data_dir), int(num_reads) + int(num_indexes), int(lane_count))

	except:

		print (f'Could not process interop data for run {run_obj.run_id}')
		return None

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


class Command(BaseCommand):

	def add_arguments(self, parser):

		parser.add_argument('--raw_data_dir', nargs =1, type = str, required=True)
	
	def handle(self, *args, **options):

		# Make or get initial model instances
		raw_data_dir = options['raw_data_dir'][0]

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

					print(f'Could not find sample sheet for {raw_data}')
					continue

				run_id = raw_data.name
				run_obj, created = Run.objects.get_or_create(run_id=run_id)
			
				if run_id not in existing_runs:

					print (f'A new run has been detected: {run_id}')

					# parse runlog data 
					run_info = raw_data.joinpath('RunInfo.xml')
					run_parameters = raw_data.joinpath('runParameters.xml')

					if run_parameters.exists() == False:

						run_parameters = raw_data.joinpath('RunParameters.xml')

						if run_parameters.exists() == False:

							print (f'Can\'t find run parameters file for {run_id}')
							continue

					if run_info.exists() == False or run_parameters.exists() == False:

						print (f'Can\'t find required XML files for {run_id}')
						continue


					# add runlog stats to database
					interop_data = add_run_log_info(run_info, run_parameters, run_obj, raw_data)

				else:

					interop_data = None


				try:
					# parse sample sheet
					sample_sheet_data = sample_sheet_parser_nipt(sample_sheet)

					sample_sheet_dict[run_id] = sample_sheet_data

				except Exception as e:
					print(e)
					print(f'Could not parse sample sheet for run {run_id}')
					continue

				# set to hold different pipeline combinations
				run_analyses_to_create = set()

				# create sample analysis objects for each sample
				for sample in sample_sheet_data:

					sample_obj, created = Sample.objects.get_or_create(sample_id=sample)
					pipeline = 'NIPT'
					pipeline_version = 'NIPT'
					panel = 'NIPT'
					sex = sample_sheet_data[sample].get('sex', None)

					worksheet = sample_sheet_data[sample].get('Sample_Project', 'Unknown')

					pipeline_and_version = pipeline + '-' + pipeline_version

					pipeline_obj, created = Pipeline.objects.get_or_create(pipeline_id= pipeline_and_version)
					worksheet_obj, created = WorkSheet.objects.get_or_create(worksheet_id= worksheet)
					analysis_type_obj, created = AnalysisType.objects.get_or_create(analysis_type_id=panel)

					new_sample_analysis_obj, created = SampleAnalysis.objects.get_or_create(sample=sample_obj,
																			run = run_obj,
																			pipeline = pipeline_obj,
																			analysis_type = analysis_type_obj,
																			worksheet = worksheet_obj,
																			)
					new_sample_analysis_obj.save()

					run_analyses_to_create.add((pipeline_and_version, panel ))

				# now create a corresponding run analysis object
				for run_analysis in run_analyses_to_create:

					pipeline = run_analysis[0]
					analysis_type = run_analysis[1]

					pipeline_obj = Pipeline.objects.get(pipeline_id=pipeline)
					analysis_type_obj = AnalysisType.objects.get(analysis_type_id=analysis_type)

					new_run_analysis_obj, created = RunAnalysis.objects.get_or_create(run = run_obj,
																			pipeline = pipeline_obj,
																			analysis_type = analysis_type_obj,
																			watching=False)


					if created == True:
						new_run_analysis_obj.start_date = datetime.datetime.now()

					new_run_analysis_obj.save()
