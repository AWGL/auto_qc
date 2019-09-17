from django.core.management.base import BaseCommand, CommandError
from qc_database.models import *
from qc_analysis.parsers import *
from django.db import transaction
import csv
from pathlib import Path

class Command(BaseCommand):

	def add_arguments(self, parser):

		parser.add_argument('--raw_data_folder', nargs =1, type = str)
	
	def handle(self, *args, **options):


		# Make or get initial model instances
		raw_data_folder = options['raw_data_folder'][0]

		# don't process existing runs
		existing_runs = Run.objects.all()

		existing_runs = [run.pk for run in existing_runs]

		# get runs in folder

		raw_data_folder = list(Path(raw_data_folder).glob('*/'))

		# for each folder in directory
		for raw_data in raw_data_folder:

			if raw_data.is_dir() == False:

				next

			sample_sheet = raw_data.joinpath('SampleSheet.csv')

			if sample_sheet.exists() == False:

				next

			run_id = raw_data.name

		
			if run_id  not in existing_runs:

				# parse runlog data 
				pass

			
			# regardless of whether we have seen it before then 
			run_obj, created = Run.objects.get_or_create(run_id=run_id)

			sample_sheet_data = sample_sheet_parser(sample_sheet)

			run_analyses_to_create = set()

			for sample in sample_sheet_data:

				sample_obj, created = Sample.objects.get_or_create(sample_id=sample)
				pipeline = sample_sheet_data[sample]['pipelineName']
				pipeline_version = sample_sheet_data[sample]['pipelineVersion']
				panel = sample_sheet_data[sample]['panel']
				sex = sample_sheet_data[sample]['sex']
				worksheet = sample_sheet_data[sample]['Sample_Plate']

				pipeline_and_version = pipeline + '-' + pipeline_version

				pipeline_obj, created = Pipeline.objects.get_or_create(pipeline_id= pipeline_and_version)
				worksheet_obj, created = WorkSheet.objects.get_or_create(worksheet_id= worksheet)
				analysis_type_obj, created = AnalysisType.objects.get_or_create(analysis_type_id=panel)

				new_sample_analysis_obj, created = SampleAnalysis.objects.get_or_create(sample=sample_obj,
																		run = run_obj,
																		pipeline = pipeline_obj,
																		analysis_type = analysis_type_obj,
																		worksheet = worksheet_obj)

				run_analyses_to_create.add((pipeline_and_version, panel ))

			for run_analysis in run_analyses_to_create:

				new_run_analysis_obj, created = RunAnalysis.objects.get_or_create(run = run_obj,
																		pipeline = pipeline_obj,
																		analysis_type = analysis_type_obj)



			