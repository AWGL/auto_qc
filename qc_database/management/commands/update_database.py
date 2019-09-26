from django.core.management.base import BaseCommand, CommandError
from qc_database.models import *
from qc_analysis.parsers import *
from pipeline_monitoring.pipelines import IlluminaQC, GermlineEnrichment
from django.db import transaction
import csv
from pathlib import Path

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
	experiment = run_params_dict['RunParameters']['ExperimentName']
	workflow = run_params_dict['RunParameters']['Workflow']['Analysis']
	chemistry = run_params_dict['RunParameters']['Chemistry']
	num_reads = processed_run_info_dict['num_reads']
	length_read1 = processed_run_info_dict['length_read1']
	length_read2 = processed_run_info_dict['length_read2']
	num_indexes= processed_run_info_dict['num_indexes']
	length_index1 = processed_run_info_dict['length_index1']
	length_index2 = processed_run_info_dict['length_index2']

	instrument, created = Instrument.objects.get_or_create(instrument_id= instrument_id, instrument_type= instrument_type)

	run_obj.instrument = instrument
	run_obj.instrument_date = instrument_date
	run_obj.lanes = lane_count
	run_obj.investigator = None # get from sample sheet
	run_obj.experiment = experiment
	run_obj.workflow = workflow
	run_obj.chemistry = chemistry

	run_obj.num_reads = num_reads
	run_obj.length_read1 = length_read1
	run_obj.length_read2 = length_read2
	run_obj.num_indexes = num_indexes
	run_obj.length_index1 = length_index1
	run_obj.length_index2 = length_index2
	
	interop_dict = parse_interop_data(str(raw_data_dir))

	run_obj.percent_q30 = interop_dict['percent_q30']
	run_obj.cluster_density = interop_dict['cluster_density']
	run_obj.percent_pf = interop_dict['percent_pf']
	run_obj.phasing = interop_dict['phasing']
	run_obj.prephasing = interop_dict['prephasing']
	run_obj.error_rate = interop_dict['error_rate']
	run_obj.aligned = interop_dict['aligned']

	run_obj.save()

	return None


def add_fastqc_data(fastqc_dict, run_analysis_obj):

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

	pipeline = run_analysis_obj.pipeline
	run = run_analysis_obj.run

	for key in depth_metrics_dict:

		sample_obj = Sample.objects.get(sample_id=key)

		sample_analysis_obj = SampleAnalysis.objects.get(sample=sample_obj,
														run=run,
														pipeline = pipeline)

		existing_data = SampleHsMetrics.objects.filter(sample_analysis= sample_analysis_obj)

		if len(existing_data) < 1:

			sample_data = depth_metrics_dict[key]
			del sample_data['%_bases_above_20']
			del sample_data['sample_id']

			sample_data['sample_analysis'] = sample_analysis_obj
			new_depth_obj = SampleDepthofCoverageMetrics(**sample_data)
			new_depth_obj.save()



def add_duplication_metrics(duplication_metrics_dict, run_analysis_obj):

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

def add_sex_metrics(qc_metrics_dict, run_analysis_obj):

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
												calculated_sex = sample_data['gender'])
			new_depth_obj.save()


def add_alignment_metrics(alignment_metrics_dict, run_analysis_obj):

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

def add_variant_calling_metrics(variant_metrics_dict, run_analysis_obj):


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




class Command(BaseCommand):

	def add_arguments(self, parser):

		parser.add_argument('--raw_data_dir', nargs =1, type = str)
		parser.add_argument('--fastq_data_dir', nargs =1, type = str)
		parser.add_argument('--results_dir', nargs =1, type = str)
	
	def handle(self, *args, **options):


		# Make or get initial model instances
		raw_data_dir = options['raw_data_dir'][0]
		fastq_data_dir = options['fastq_data_dir'][0]
		results_dir = options['results_dir'][0]

		# don't process existing runs
		existing_runs = Run.objects.all()

		existing_runs = [run.pk for run in existing_runs]

		# get runs in folder

		raw_data_dir = list(Path(raw_data_dir).glob('*/'))

		# for each folder in directory
		for raw_data in raw_data_dir:

			if raw_data.is_dir() == False:

				continue

			sample_sheet = raw_data.joinpath('SampleSheet.csv')

			# to do what if sample sheet is named something else?
			# maybe send warning that a run has appeared but could not be processed

			if sample_sheet.exists() == False:

				continue

			run_id = raw_data.name

			# regardless of whether we have seen it before then 
			run_obj, created = Run.objects.get_or_create(run_id=run_id)

			if created == True:

				print (f'new run {run_id} off sequencer')
		
			if run_id not in existing_runs:

				# parse runlog data 
				run_info = raw_data.joinpath('RunInfo.xml')
				run_parameters = raw_data.joinpath('runParameters.xml')

				if run_info.exists() == False or run_parameters.exists() == False:

					continue

				add_run_log_info(run_info, run_parameters, run_obj, raw_data)

			



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


		# now get all runs and see if they have fastqs

		existing_run_analyses = RunAnalysis.objects.all()

		for run_analysis in existing_run_analyses:

			# make IlluminaQC object

			samples = SampleAnalysis.objects.filter(run = run_analysis.run,
											 pipeline= run_analysis.pipeline,
											 analysis_type= run_analysis.analysis_type)

			sample_ids = [sample.sample.sample_id for sample in samples]

			run_fastq_dir = Path(fastq_data_dir).joinpath(run_analysis.run.run_id)

			run_data_dir = Path(results_dir).joinpath(run_analysis.run.run_id, run_analysis.analysis_type.analysis_type_id)

			# ADD n LANES FROM DB

			illumina_qc = IlluminaQC(fastq_dir= run_fastq_dir,
									results_dir= results_dir,
									sample_names = sample_ids,
									n_lanes = 1,
									run_id = run_analysis.run.run_id)

			has_completed = illumina_qc.demultiplex_run_is_complete()

			is_valid = illumina_qc.demultiplex_run_is_valid()

			if run_analysis.run.demultiplexing_completed == False and has_completed == True:

				if is_valid == True:

					print (f'Run {run_id} has now completed demultiplexing')


				else:

					print (f'Run {run_id} has now failed demultiplexing')

			run_analysis.run.demultiplexing_completed = has_completed
			run_analysis.run.demultiplexing_valid = is_valid
			run_analysis.run.save()

			# now check pipeline results

			# for germline enrichment
			if 'GermlineEnrichment' in run_analysis.pipeline.pipeline_id:

				germline_enrichment = GermlineEnrichment(results_dir = run_data_dir,
														sample_names = sample_ids,
														run_id = run_analysis.run.run_id)

				for sample in sample_ids:

					sample_complete = germline_enrichment.sample_is_complete(sample)
					sample_valid = germline_enrichment.sample_is_valid(sample)

					sample_obj = Sample.objects.get(sample_id = sample)

					sample_analysis_obj = SampleAnalysis.objects.get(sample=sample,
																	run = run_analysis.run,
																	pipeline = run_analysis.pipeline)

					if sample_analysis_obj.results_completed == False and sample_complete == True:

						if sample_valid == True:

							print (f'Sample {sample} on run {run_analysis.run.run_id} has finished script one successfully.')

						else:
							print (f'Sample {sample} on run {run_analysis.run.run_id} has failed script one.')

		
					sample_analysis_obj.results_completed = sample_complete
					sample_analysis_obj.results_valid = sample_valid
					sample_analysis_obj.save()

				run_complete = germline_enrichment.run_is_complete()
				run_valid = germline_enrichment.run_is_valid()

				#if run_analysis.results_completed == False and run_complete == True:
				if  run_complete == True:

					if run_valid == True:

						print (f'Run {run_id} has now completed pipeline {run_analysis.pipeline.pipeline_id}')
						print ('putting fastqc into db')

						fastqc_dict = germline_enrichment.get_fastqc_data()
						add_fastqc_data(fastqc_dict, run_analysis)

						hs_metrics_dict = germline_enrichment.get_hs_metrics()

						add_hs_metrics(hs_metrics_dict, run_analysis)

						depth_metrics_dict = germline_enrichment.get_depth_metrics()
						# add qc data for all samples and run level

						add_depth_of_coverage_metrics(depth_metrics_dict, run_analysis)


						duplication_metrics_dict = germline_enrichment.get_duplication_metrics()
						add_duplication_metrics(duplication_metrics_dict, run_analysis)

						contamination_metrics_dict = germline_enrichment.get_contamination()

						add_contamination_metrics(contamination_metrics_dict, run_analysis)

						sex_dict = germline_enrichment.get_calculated_sex()

						add_sex_metrics(sex_dict, run_analysis)

						alignment_metrics_dict = germline_enrichment.get_alignment_metrics()

						add_alignment_metrics(alignment_metrics_dict, run_analysis)

						variant_calling_metrics_dict = germline_enrichment.get_variant_calling_metrics()

						add_variant_calling_metrics(variant_calling_metrics_dict, run_analysis)

						insert_metrics_dict = germline_enrichment.get_insert_metrics()

						add_insert_metrics(insert_metrics_dict, run_analysis)

					else:

						print (f'Run {run_id} has now failed pipeline {run_analysis.pipeline.pipeline_id}')

				run_analysis.results_completed = run_complete
				run_analysis.results_valid = run_valid

				run_analysis.save()