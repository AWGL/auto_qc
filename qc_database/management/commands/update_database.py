import csv
from pathlib import Path
import datetime
import logging

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction

from qc_database.models import *
from pipelines import dragen_pipelines, parsers, quality_pipelines, somatic_pipelines, nextflow_pipelines, TSO500_pipeline
from qc_database import management_utils

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
		config_dict = parsers.parse_config(config)

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

				# skip if we don't have marker file
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
					interop_data = management_utils.add_run_log_info(run_info, run_parameters, run_obj, raw_data)

				else:

					interop_data = None
				
				try:
					# parse sample sheet
					sample_sheet_data = parsers.sample_sheet_parser(sample_sheet)

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

					if pipeline == 'TSO500':

						panel = sample_sheet_data[sample]['Sample_Type']
						panel = 'TSO500_' + panel

					else:

						panel = sample_sheet_data[sample]['panel']					

					sex = sample_sheet_data[sample].get('sex', None)

					worksheet = sample_sheet_data[sample].get('Sample_Plate', 'Unknown')

					pipeline_and_version = pipeline + '-' + pipeline_version

					pipeline_obj, created = Pipeline.objects.get_or_create(pipeline_id= pipeline_and_version)
					worksheet_obj, created = WorkSheet.objects.get_or_create(worksheet_id= worksheet)
					analysis_type_obj, created = AnalysisType.objects.get_or_create(analysis_type_id=panel)

					run_config_key = pipeline_obj.pipeline_id + '-' + analysis_type_obj.analysis_type_id

					try:

						#put checks to try into dictionary

						checks_to_try = config_dict['pipelines'][run_config_key]['qc_checks']
						checks_to_try_dict=dict(zip(checks_to_try, checks_to_try))
						checks_to_try=','.join(checks_to_try)


					except:

						checks_to_try = None

					new_sample_analysis_obj, created = SampleAnalysis.objects.get_or_create(sample=sample_obj,
																			run = run_obj,
																			pipeline = pipeline_obj,
																			analysis_type = analysis_type_obj,
																			worksheet = worksheet_obj)


					if checks_to_try is not None:

						for key in checks_to_try_dict.keys():

							if 'contamination' == key :

								try:

									contamination_cutoff = config_dict['pipelines'][run_config_key]['contamination_cutoff']

									if created:

										new_sample_analysis_obj.contamination_cutoff = contamination_cutoff

								except:

									raise Exception ("ERROR: Contamination cutoff not in config file")

							if 'ntc_contamination' == key :

								try:

									ntc_contamination_cutoff = config_dict['pipelines'][run_config_key]['ntc_contamination_cutoff']

									if created:

										new_sample_analysis_obj.ntc_contamination_cutoff = ntc_contamination_cutoff

								except:

									raise Exception ("ERROR: NTC contamination cutoff not in config file")
								
							if 'max_cnv_calls' == key:

								try:

									max_cnvs_called_cutoff = config_dict['pipelines'][run_config_key]['max_cnvs_called_cutoff']

									if created:

										new_sample_analysis_obj.max_cnvs_called_cutoff = max_cnvs_called_cutoff

								except:

									raise Exception ("ERROR: Max CNVs called cutoff not in config file")

					new_sample_analysis_obj.sex = sex
					new_sample_analysis_obj.save()

					run_analyses_to_create.add((pipeline_and_version, panel ))

				# now create a corresponding run analysis object
				for run_analysis in run_analyses_to_create:

					pipeline = run_analysis[0]
					analysis_type = run_analysis[1]

					pipeline_obj = Pipeline.objects.get(pipeline_id = pipeline)
					analysis_type_obj = AnalysisType.objects.get(analysis_type_id = analysis_type)

					run_config_key = pipeline_obj.pipeline_id + '-' + analysis_type_obj.analysis_type_id

					new_run_analysis_obj, created = RunAnalysis.objects.get_or_create(run = run_obj,
																			pipeline = pipeline_obj,
																			analysis_type = analysis_type_obj)

					try:

						#put checks to try into dictionary

						checks_to_try = config_dict['pipelines'][run_config_key]['qc_checks']
						checks_to_try_dict=dict(zip(checks_to_try, checks_to_try))
						checks_to_try=','.join(checks_to_try)


					except:

						checks_to_try = None


					if checks_to_try is not None:

						new_run_analysis_obj.auto_qc_checks = checks_to_try
						new_run_analysis_obj.start_date = datetime.datetime.now()

						for key in checks_to_try_dict.keys():

							if 'pct_q30' in checks_to_try_dict:


								try: 
						
									min_q30_score = config_dict['pipelines'][run_config_key]['min_q30_score']

									if created:
										new_run_analysis_obj.min_q30_score = min_q30_score

								except:

									raise Exception ("ERROR: min_q30_score not in config file")


							if 'variant_check' in checks_to_try_dict:

								try:

									min_variants =  config_dict['pipelines'][run_config_key]['min_variants']
									max_variants =  config_dict['pipelines'][run_config_key]['max_variants']

									if created:
										new_run_analysis_obj.min_variants = min_variants
										new_run_analysis_obj.max_variants = max_variants

								except:

									raise Exception ("ERROR: Min or max variants not in config file")


							if 'sensitivity' in checks_to_try_dict:

								try:

									min_sensitivity = config_dict['pipelines'][run_config_key]['min_sensitivity']

									if created:
										new_run_analysis_obj.min_sensitivity = min_sensitivity

								except:

									raise Exception ("ERROR: Sensitivity not in config file")


							if 'titv' in checks_to_try_dict:

								try:

									min_titv =  config_dict['pipelines'][run_config_key]['min_titv']
									max_titv =  config_dict['pipelines'][run_config_key]['max_titv']

									if created:

										new_run_analysis_obj.min_titv = min_titv
										new_run_analysis_obj.max_titv = max_titv

								except:
									raise Exception ("ERROR: Titv values not in config file")


							if 'coverage' in checks_to_try_dict:

								try:

									min_coverage = config_dict['pipelines'][run_config_key]['min_coverage']

									if created:

										new_run_analysis_obj.min_coverage = min_coverage

								except:

									raise Exception ("ERROR: Coverage values not in config file")



							if 'reads_tso500' in checks_to_try_dict:

								try:

									min_on_target_reads = config_dict['pipelines'][run_config_key]['min_on_target_reads']

									if created:

										new_run_analysis_obj.min_on_target_reads = min_on_target_reads

								except:

									raise Exception ("ERROR: TSO500 reads not in config file")


							if 'relatedness' in checks_to_try_dict:

								try:

									min_relatedness_parents = config_dict['pipelines'][run_config_key]['min_relatedness_parents']
									max_relatedness_unrelated = config_dict['pipelines'][run_config_key]['max_relatedness_unrelated']
									max_relatedness_between_parents = config_dict['pipelines'][run_config_key]['max_relatedness_between_parents']
									max_child_parent_relatedness = config_dict['pipelines'][run_config_key]['max_child_parent_relatedness']

									if created:
										new_run_analysis_obj.min_relatedness_parents = min_relatedness_parents
										new_run_analysis_obj.max_relatedness_unrelated = max_relatedness_unrelated
										new_run_analysis_obj.max_relatedness_between_parents = max_relatedness_between_parents
										new_run_analysis_obj.max_child_parent_relatedness = max_child_parent_relatedness

								except:

									raise Exception ("ERROR: Relatedness values not in config file")


							if 'ntc_contamination_TSO500' in checks_to_try_dict:

								try:

									max_ntc_contamination = config_dict['pipelines'][run_config_key]['max_ntc_contamination']

									if created:

										new_run_analysis_obj.max_ntc_contamination = max_ntc_contamination

								except:

									raise Exception ("ERROR: max_ntc_contamination not in config file")
								
							if 'max_cnv_calls' in checks_to_try_dict:

								try:

									max_cnvs_called_cutoff = config_dict['pipelines'][run_config_key]['max_cnvs_called_cutoff']

									if created:

										new_run_analysis_obj.max_cnv_calls = max_cnvs_called_cutoff
								
								except:

									raise Exception("ERROR: max_cnv_calls_cutoff not in config file")

					new_run_analysis_obj.save()

			# Loop through existing run analysis objects
			existing_run_analyses = RunAnalysis.objects.filter(watching = True)

			for run_analysis in existing_run_analyses:

				# make IlluminaQC object
				run_config_key = run_analysis.pipeline.pipeline_id + '-' + run_analysis.analysis_type.analysis_type_id

				samples = SampleAnalysis.objects.filter(run = run_analysis.run,
												 pipeline= run_analysis.pipeline,
												 analysis_type= run_analysis.analysis_type)


				sample_ids = [sample.sample.sample_id for sample in samples]

				# have we configured a fastq folder
				try:

					has_fastqs = config_dict['pipelines'][run_config_key].get('fastq_dir')

				except:

					has_fastqs = None

				try:

					results_dir = config_dict['pipelines'][run_config_key]['results_dir']

				except:

					logger.warn(f'No results directory configured for this pipeline {run_config_key}')
					results_dir = '/data/results/'



				if has_fastqs is not None:
					
					fastq_data_dir = config_dict['pipelines'][run_config_key]['fastq_dir']
					run_fastq_dir = Path(fastq_data_dir).joinpath(run_analysis.run.run_id)

				else:

					run_fastq_dir = 'test'

				if 'TSO500' in run_config_key:

					run_data_dir = Path(results_dir)

				else:

					run_data_dir = Path(results_dir).joinpath(run_analysis.run.run_id, run_analysis.analysis_type.analysis_type_id)

				lanes = run_analysis.run.lanes

				try:

					min_fastq_size = config_dict['pipelines'][run_config_key]['min_fastq_size']

				except:

					min_fastq_size = 100000

				if 'Dragen' in run_config_key:

					illumina_qc = quality_pipelines.DragenQC(fastq_dir= run_fastq_dir,
										sample_names = sample_ids,
										n_lanes = lanes,
										analysis_type = run_analysis.analysis_type.analysis_type_id,
										min_fastq_size = min_fastq_size,
										run_id = run_analysis.run.run_id)


				if 'TSO500' in run_config_key:

					illumina_qc = quality_pipelines.TSO500_demultiplex(fastq_dir= run_fastq_dir,
											sample_names = sample_ids,
											n_lanes = lanes,
											analysis_type = run_analysis.analysis_type.analysis_type_id,
											min_fastq_size = min_fastq_size,
											run_id = run_analysis.run.run_id)

				else:

					illumina_qc = quality_pipelines.IlluminaQC(fastq_dir= run_fastq_dir,
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
						
					else:

						logger.info(f'Run {run_analysis} {run_analysis.analysis_type.analysis_type_id} has now failed demultiplexing')
						run_analysis.demultiplexing_completed = has_completed
						run_analysis.demultiplexing_valid = is_valid
						run_analysis.save()
						
				run_analysis.demultiplexing_completed = has_completed
				run_analysis.demultiplexing_valid = is_valid
				run_analysis.save()
				
				if 'SomaticAmplicon' in run_analysis.pipeline.pipeline_id:

					run_config_key = run_analysis.pipeline.pipeline_id + '-' + run_analysis.analysis_type.analysis_type_id

					if run_config_key not in config_dict['pipelines']:

						somatic_amplicon = somatic_pipelines.SomaticAmplicon(results_dir = run_data_dir,
															sample_names = sample_ids,
															run_id = run_analysis.run.run_id
															)
					else:

						sample_expected_files = config_dict['pipelines'][run_config_key]['sample_expected_files']
						sample_not_expected_files = config_dict['pipelines'][run_config_key]['sample_not_expected_files']
						run_expected_files = config_dict['pipelines'][run_config_key]['run_expected_files']
						run_not_expected_files = config_dict['pipelines'][run_config_key]['run_not_expected_files']

						somatic_amplicon = somatic_pipelines.SomaticAmplicon(results_dir = run_data_dir,
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
																		pipeline = run_analysis.pipeline,
																		analysis_type = run_analysis.analysis_type)

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
							management_utils.add_fastqc_data(fastqc_dict, run_analysis)
							
							logger.info (f'Putting hs metrics data into db for run {run_analysis.run.run_id}')
							hs_metrics_dict = somatic_amplicon.get_hs_metrics()
							management_utils.add_hs_metrics(hs_metrics_dict, run_analysis)

							logger.info (f'Putting depth metrics data into db for run {run_analysis.run.run_id}')
							depth_metrics_dict = somatic_amplicon.get_depth_metrics()
							management_utils.add_depth_of_coverage_metrics(depth_metrics_dict, run_analysis)

							logger.info (f'Putting variant count metrics data into db for run {run_analysis.run.run_id}')
							variant_count_metrics_dict = somatic_amplicon.get_variant_count()
							management_utils.add_variant_count_metrics(variant_count_metrics_dict, run_analysis)

						else:

							logger.info (f'Run {run_id} {run_analysis.analysis_type.analysis_type_id} has failed pipeline {run_analysis.pipeline.pipeline_id}')

					elif run_analysis.results_valid == False and run_valid == True and run_complete == True:

							logger.info (f'Run {run_id} {run_analysis.analysis_type.analysis_type_id} has now successfully completed pipeline {run_analysis.pipeline.pipeline_id}')

							logger.info (f'Putting fastqc data into db for run {run_analysis.run.run_id}')
							fastqc_dict = somatic_amplicon.get_fastqc_data()
							management_utils.add_fastqc_data(fastqc_dict, run_analysis)
							
							logger.info (f'Putting hs metrics data into db for run {run_analysis.run.run_id}')
							hs_metrics_dict = somatic_amplicon.get_hs_metrics()
							management_utils.add_hs_metrics(hs_metrics_dict, run_analysis)

							logger.info (f'Putting depth metrics data into db for run {run_analysis.run.run_id}')
							depth_metrics_dict = somatic_amplicon.get_depth_metrics()
							management_utils.add_depth_of_coverage_metrics(depth_metrics_dict, run_analysis)

							logger.info (f'Putting variant count metrics data into db for run {run_analysis.run.run_id}')
							variant_count_metrics_dict = somatic_amplicon.get_variant_count()
							management_utils.add_variant_count_metrics(variant_count_metrics_dict, run_analysis)

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

						dragen_ge = dragen_pipelines.DragenGE(results_dir = run_data_dir,
															sample_names = sample_ids,
															run_id = run_analysis.run.run_id,
															sample_expected_files = sample_expected_files,
															sample_not_expected_files = sample_not_expected_files,
															run_expected_files = run_expected_files,
															run_not_expected_files = run_not_expected_files,
															post_sample_files = post_sample_files
															)

					except:

						dragen_ge = dragen_pipelines.DragenGE(results_dir = run_data_dir,
															sample_names = sample_ids,
															run_id = run_analysis.run.run_id
															)

					# just say all samples are valid - we only check run level here
					for sample in sample_ids:

						sample_obj = Sample.objects.get(sample_id = sample)

						sample_analysis_obj = SampleAnalysis.objects.get(sample=sample,
																		run = run_analysis.run,
																		pipeline = run_analysis.pipeline,
																		analysis_type = run_analysis.analysis_type)


						sample_analysis_obj.results_completed = True
						sample_analysis_obj.results_valid = True
						sample_analysis_obj.save()


					run_complete = dragen_ge.run_is_complete()
					run_valid = dragen_ge.run_is_valid()

					if run_analysis.results_completed == False and run_complete == True:

						if run_valid == True:

							logger.info (f'Run {run_analysis.run.run_id} has now successfully completed pipeline {run_analysis.pipeline.pipeline_id}')

							logger.info (f'Putting coverage metrics into db for run {run_analysis.run.run_id}')
							coverage_metrics_dict = dragen_ge.get_coverage_metrics()
							management_utils.add_custom_coverage_metrics(coverage_metrics_dict, run_analysis)

							logger.info (f'Putting sex metrics into db for run {run_analysis.run.run_id}')
							sex_dict = dragen_ge.get_sex_metrics()
							management_utils.add_sex_metrics(sex_dict, run_analysis, 'sex')

							logger.info (f'Putting alignment metrics into db for run {run_analysis.run.run_id}')
							alignment_metrics_dict = dragen_ge.get_alignment_metrics()
							management_utils.add_dragen_alignment_metrics(alignment_metrics_dict, run_analysis)

							logger.info (f'Putting variant calling metrics into db for run {run_analysis.run.run_id}')
							variant_calling_metrics_dict = dragen_ge.get_variant_calling_metrics()
							management_utils.add_dragen_variant_calling_metrics(variant_calling_metrics_dict, run_analysis)

							logger.info (f'Putting sensitivity metrics into db for run {run_analysis.run.run_id}')
							sensitivity_metrics = dragen_ge.get_sensitivity()
							management_utils.add_sensitivity_metrics(sensitivity_metrics, run_analysis)

							logger.info (f'Putting CNV QC metrics into db for run {run_analysis.run.run_id}')
							cnv_qc_metrics = dragen_ge.get_cnv_qc_metrics()
							management_utils.add_dragen_cnv_qc_metrics(cnv_qc_metrics, run_analysis)

							logger.info (f'Putting relatedness metrics into db for run {run_analysis.run.run_id}')
							parsed_relatedness, parsed_relatedness_comment = dragen_ge.get_relatedness_metrics(run_analysis.min_relatedness_parents,
																												run_analysis.max_relatedness_unrelated,
																												run_analysis.max_relatedness_between_parents,
																												run_analysis.max_child_parent_relatedness)

							management_utils.add_relatedness_metrics(parsed_relatedness, parsed_relatedness_comment, run_analysis)

						else:

							logger.info (f'Run {run_analysis.run.run_id} has failed pipeline {run_analysis.pipeline.pipeline_id}')

					elif run_analysis.results_valid == False and run_valid == True and run_complete == True:

							logger.info (f'Run {run_analysis.run.run_id} now successfully completed pipeline {run_analysis.pipeline.pipeline_id}')

							logger.info (f'Putting coverage metrics into db for run {run_analysis.run.run_id}')
							coverage_metrics_dict = dragen_ge.get_coverage_metrics()
							management_utils.add_custom_coverage_metrics(coverage_metrics_dict, run_analysis)

							logger.info (f'Putting sex metrics into db for run {run_analysis.run.run_id}')
							sex_dict = dragen_ge.get_sex_metrics()
							management_utils.add_sex_metrics(sex_dict, run_analysis, 'sex')

							logger.info (f'Putting alignment metrics into db for run {run_analysis.run.run_id}')
							alignment_metrics_dict = dragen_ge.get_alignment_metrics()
							management_utils.add_dragen_alignment_metrics(alignment_metrics_dict, run_analysis)

							logger.info (f'Putting variant calling metrics into db for run {run_analysis.run.run_id}')
							variant_calling_metrics_dict = dragen_ge.get_variant_calling_metrics()
							management_utils.add_dragen_variant_calling_metrics(variant_calling_metrics_dict, run_analysis)

							logger.info (f'Putting sensitivity metrics into db for run {run_analysis.run.run_id}')
							sensitivity_metrics = dragen_ge.get_sensitivity()
							management_utils.add_sensitivity_metrics(sensitivity_metrics, run_analysis)

							logger.info (f'Putting CNV QC metrics into db for run {run_analysis.run.run_id}')
							cnv_qc_metrics = dragen_ge.get_cnv_qc_metrics()
							management_utils.add_dragen_cnv_qc_metrics(cnv_qc_metrics, run_analysis)

							logger.info (f'Putting relatedness metrics into db for run {run_analysis.run.run_id}')
							parsed_relatedness, parsed_relatedness_comment = dragen_ge.get_relatedness_metrics(run_analysis.min_relatedness_parents,
																												run_analysis.max_relatedness_unrelated,
																												run_analysis.max_relatedness_between_parents,
																												run_analysis.max_child_parent_relatedness)

							management_utils.add_relatedness_metrics(parsed_relatedness, parsed_relatedness_comment, run_analysis)

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

						dragen_wgs = dragen_pipelines.DragenWGS(results_dir = run_data_dir,
															sample_names = sample_ids,
															run_id = run_analysis.run.run_id,
															sample_expected_files = sample_expected_files,
															sample_not_expected_files = sample_not_expected_files,
															run_expected_files = run_expected_files,
															run_not_expected_files = run_not_expected_files,
															post_sample_files = post_sample_files
															)

					except:

						dragen_wgs = dragen_pipelines.DragenWGS(results_dir = run_data_dir,
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
							management_utils.add_dragen_alignment_metrics(alignment_metrics_dict, run_analysis)

							logger.info (f'Putting variant calling metrics into db for run {run_analysis.run.run_id}')
							variant_calling_metrics_dict = dragen_wgs.get_variant_calling_metrics()
							management_utils.add_dragen_variant_calling_metrics(variant_calling_metrics_dict, run_analysis)

							logger.info (f'Putting relatedness metrics into db for run {run_analysis.run.run_id}')
							parsed_relatedness, parsed_relatedness_comment = dragen_wgs.get_relatedness_metrics(run_analysis.min_relatedness_parents,
																												run_analysis.max_relatedness_unrelated,
																												run_analysis.max_relatedness_between_parents,
																												run_analysis.max_child_parent_relatedness)

							management_utils.add_relatedness_metrics(parsed_relatedness, parsed_relatedness_comment, run_analysis)

							logger.info (f'Putting WGS metrics into db for run {run_analysis.run.run_id}')
							wgs_coverage_metrics_dict = dragen_wgs.get_wgs_mapping_metrics()
							management_utils.add_dragen_wgs_coverage_metrics(wgs_coverage_metrics_dict, run_analysis)

							logger.info (f'Putting exonic coverage metrics into db for run {run_analysis.run.run_id}')
							exonic_coverage_metrics_dict = dragen_wgs.get_exonic_mapping_metrics()
							management_utils.add_dragen_exonic_coverage_metrics(exonic_coverage_metrics_dict, run_analysis)

							logger.info (f'Putting ploidy metrics into db for run {run_analysis.run.run_id}')
							dragen_ploidy_metrics_dict = dragen_wgs.get_ploidy_metrics()
							management_utils.add_dragen_ploidy_metrics(dragen_ploidy_metrics_dict, run_analysis)

						else:

							logger.info (f'Run {run_analysis.run.run_id} has failed pipeline {run_analysis.pipeline.pipeline_id}')

					elif run_analysis.results_valid == False and run_valid == True and run_complete == True:

							logger.info (f'Run {run_analysis.run.run_id} now successfully completed pipeline {run_analysis.pipeline.pipeline_id}')

							logger.info (f'Putting alignment metrics into db for run {run_analysis.run.run_id}')
							alignment_metrics_dict = dragen_wgs.get_alignment_metrics()
							management_utils.add_dragen_alignment_metrics(alignment_metrics_dict, run_analysis)

							logger.info (f'Putting variant calling metrics into db for run {run_analysis.run.run_id}')
							variant_calling_metrics_dict = dragen_wgs.get_variant_calling_metrics()
							management_utils.add_dragen_variant_calling_metrics(variant_calling_metrics_dict, run_analysis)

							
							logger.info (f'Putting relatedness metrics into db for run {run_analysis.run.run_id}')
							parsed_relatedness, parsed_relatedness_comment = dragen_wgs.get_relatedness_metrics(run_analysis.min_relatedness_parents,
																												run_analysis.max_relatedness_unrelated,
																												run_analysis.max_relatedness_between_parents,
																												run_analysis.max_child_parent_relatedness)
							management_utils.add_relatedness_metrics(parsed_relatedness, parsed_relatedness_comment, run_analysis)

							logger.info (f'Putting WGS metrics into db for run {run_analysis.run.run_id}')
							wgs_coverage_metrics_dict = dragen_wgs.get_wgs_mapping_metrics()
							management_utils.add_dragen_wgs_coverage_metrics(wgs_coverage_metrics_dict, run_analysis)

							logger.info (f'Putting exonic coverage metrics into db for run {run_analysis.run.run_id}')
							exonic_coverage_metrics_dict = dragen_wgs.get_exonic_mapping_metrics()
							management_utils.add_dragen_exonic_coverage_metrics(exonic_coverage_metrics_dict, run_analysis)

							logger.info (f'Putting ploidy metrics into db for run {run_analysis.run.run_id}')
							dragen_ploidy_metrics_dict = dragen_wgs.get_ploidy_metrics()
							management_utils.add_dragen_ploidy_metrics(dragen_ploidy_metrics_dict, run_analysis)

					run_analysis.results_completed = run_complete
					run_analysis.results_valid = run_valid

					run_analysis.save()


				# for nextflow piplines
				elif 'nextflow' in run_analysis.pipeline.pipeline_id:

					run_config_key = run_analysis.pipeline.pipeline_id + '-' + run_analysis.analysis_type.analysis_type_id

					try:

						nextflow = nextflow_pipelines.NextflowGermlineEnrichment(results_dir = run_data_dir,
															sample_names = sample_ids,
															run_id = run_analysis.run.run_id,
															)

					except:

						nextflow = nextflow_pipelines.NextflowGermlineEnrichment(results_dir = run_data_dir,
															sample_names = sample_ids,
															run_id = run_analysis.run.run_id
															)

					# kust say all samples are valid - we only check run level here
					for sample in sample_ids:

						sample_obj = Sample.objects.get(sample_id = sample)

						sample_analysis_obj = SampleAnalysis.objects.get(sample=sample,
																		run = run_analysis.run,
																		pipeline = run_analysis.pipeline)


						sample_analysis_obj.results_completed = True
						sample_analysis_obj.results_valid = True
						sample_analysis_obj.save()


					run_complete = nextflow.run_is_complete()
					run_valid = nextflow.run_is_valid()

					if run_analysis.results_completed == False and run_complete == True:

						if run_valid == True:

							logger.info (f'Run {run_analysis.run.run_id} has now successfully completed pipeline {run_analysis.pipeline.pipeline_id}')

							# put qc here
							logger.info (f'Putting fastqc data into db for run {run_analysis.run.run_id}')
							fastqc_dict = nextflow.get_fastqc_data()
							management_utils.add_fastqc_data(fastqc_dict, run_analysis)

							logger.info(f'Putting hs metrics into db for run {run_analysis.run.run_id}')
							hs_metrics_dict = nextflow.get_hs_metrics()
							management_utils.add_hs_metrics(hs_metrics_dict, run_analysis)

							logger.info (f'Putting duplication into db for run {run_analysis.run.run_id}')
							duplication_metrics_dict = nextflow.get_duplication_metrics()
							management_utils.add_duplication_metrics(duplication_metrics_dict, run_analysis)

							logger.info (f'Putting contamination metrics into db for run {run_analysis.run.run_id}')
							contamination_metrics_dict = nextflow.get_contamination()
							management_utils.add_contamination_metrics(contamination_metrics_dict, run_analysis)

							logger.info (f'Putting alignment metrics into db for run {run_analysis.run.run_id}')
							alignment_metrics_dict = nextflow.get_alignment_metrics()
							management_utils.add_alignment_metrics(alignment_metrics_dict, run_analysis)

							logger.info (f'Putting variant calling metrics into db for run {run_analysis.run.run_id}')
							variant_calling_metrics_dict = nextflow.get_variant_calling_metrics()
							management_utils.add_variant_calling_metrics(variant_calling_metrics_dict, run_analysis)

							logger.info (f'Putting insert metrics into db for run {run_analysis.run.run_id}')
							insert_metrics_dict = nextflow.get_insert_metrics()
							management_utils.add_insert_metrics(insert_metrics_dict, run_analysis)

							logger.info (f'Putting coverage metrics into db for run {run_analysis.run.run_id}')
							coverage_metrics_dict = nextflow.get_coverage_metrics()
							management_utils.add_custom_coverage_metrics(coverage_metrics_dict, run_analysis)

							logger.info (f'Putting sex metrics into db for run {run_analysis.run.run_id}')
							sex_dict = nextflow.get_sex_metrics()
							management_utils.add_sex_metrics(sex_dict, run_analysis, 'sex')

						else:

							logger.info (f'Run {run_analysis.run.run_id} has failed pipeline {run_analysis.pipeline.pipeline_id}')

					elif run_analysis.results_valid == False and run_valid == True and run_complete == True:

							logger.info (f'Run {run_analysis.run.run_id} now successfully completed pipeline {run_analysis.pipeline.pipeline_id}')


							# put qc here
							logger.info (f'Putting fastqc data into db for run {run_analysis.run.run_id}')
							fastqc_dict = nextflow.get_fastqc_data()
							management_utils.add_fastqc_data(fastqc_dict, run_analysis)

							logger.info(f'Putting hs metrics into db for run {run_analysis.run.run_id}')
							hs_metrics_dict = nextflow.get_hs_metrics()
							management_utils.add_hs_metrics(hs_metrics_dict, run_analysis)

							logger.info (f'Putting duplication into db for run {run_analysis.run.run_id}')
							duplication_metrics_dict = nextflow.get_duplication_metrics()
							management_utils.add_duplication_metrics(duplication_metrics_dict, run_analysis)

							logger.info (f'Putting contamination metrics into db for run {run_analysis.run.run_id}')
							contamination_metrics_dict = nextflow.get_contamination()
							management_utils.add_contamination_metrics(contamination_metrics_dict, run_analysis)

							logger.info (f'Putting alignment metrics into db for run {run_analysis.run.run_id}')
							alignment_metrics_dict = nextflow.get_alignment_metrics()
							management_utils.add_alignment_metrics(alignment_metrics_dict, run_analysis)

							logger.info (f'Putting variant calling metrics into db for run {run_analysis.run.run_id}')
							variant_calling_metrics_dict = nextflow.get_variant_calling_metrics()
							management_utils.add_variant_calling_metrics(variant_calling_metrics_dict, run_analysis)

							logger.info (f'Putting insert metrics into db for run {run_analysis.run.run_id}')
							insert_metrics_dict = nextflow.get_insert_metrics()
							management_utils.add_insert_metrics(insert_metrics_dict, run_analysis)

							logger.info (f'Putting coverage metrics into db for run {run_analysis.run.run_id}')
							coverage_metrics_dict = nextflow.get_coverage_metrics()
							management_utils.add_custom_coverage_metrics(coverage_metrics_dict, run_analysis)

							logger.info (f'Putting sex metrics into db for run {run_analysis.run.run_id}')
							sex_dict = nextflow.get_sex_metrics()
							management_utils.add_sex_metrics(sex_dict, run_analysis, 'sex')

					run_analysis.results_completed = run_complete
					run_analysis.results_valid = run_valid

					run_analysis.save()

				# TSO500 RNA
				elif 'TSO500' in run_analysis.pipeline.pipeline_id and 'RNA' in run_analysis.analysis_type.analysis_type_id:
					
					run_id=run_analysis.run.run_id
					dna_or_rna="RNA"
					run_config_key = run_analysis.pipeline.pipeline_id + '-' + run_analysis.analysis_type.analysis_type_id

					if run_config_key not in config_dict['pipelines']:

						tso500 = TSO500_pipeline.TSO500_RNA(results_dir = run_data_dir,
															sample_names = sample_ids,
															sample_valid_files=None,
															run_id = run_analysis.run.run_id,
															sample_completed_files = ['*_fusion_check.csv'],
															run_completed_files = ['contamination-*.csv'],
															run_expected_files = ['RNA_QC_combined.txt', 'contamination-*.csv' ,'completed_samples.txt'],
															metrics_file = ['RNA_QC_combined.txt']

															)
					else:

						sample_completed_files = config_dict['pipelines'][run_config_key]['sample_completed_files']
						run_completed_files = config_dict['pipelines'][run_config_key]['run_completed_files']
						run_expected_files = config_dict['pipelines'][run_config_key]['run_expected_files']
						metrics_file = config_dict['pipelines'][run_config_key]['metrics_file']

						tso500 = TSO500_pipeline.TSO500_RNA(results_dir = run_data_dir,
    															sample_completed_files=sample_completed_files,
    															sample_valid_files=None,
    															run_completed_files=run_completed_files,
    															run_expected_files=run_expected_files,
    															metrics_file=metrics_file,
																sample_names = sample_ids,
																run_id = run_analysis.run.run_id
																)

					for sample in sample_ids:

						sample_complete = tso500.sample_is_complete(sample)

						sample_valid = tso500.sample_is_valid(sample)

						sample_obj = Sample.objects.get(sample_id = sample)

						sample_analysis_obj = SampleAnalysis.objects.get(sample=sample,
																		run = run_analysis.run,
																		pipeline = run_analysis.pipeline,
																		analysis_type = run_analysis.analysis_type)

						if sample_analysis_obj.results_completed == False and sample_complete == True:

							if sample_valid == True:

								logger.info (f'Sample {sample} on run {run_analysis.run.run_id} {run_analysis.analysis_type.analysis_type_id} has finished sample level TSO500 successfully.')

							else:
								logger.info (f'Sample {sample} on run {run_analysis.run.run_id} {run_analysis.analysis_type.analysis_type_id} has failed sample level TSO500.')

						elif sample_analysis_obj.results_valid == False and sample_valid == True and sample_complete == True:

							logger.info (f'Sample {sample} on run {run_analysis.run.run_id} {run_analysis.analysis_type.analysis_type_id} has now completed successfully.')

			
						sample_analysis_obj.results_completed = sample_complete
						sample_analysis_obj.results_valid = sample_valid
						sample_analysis_obj.save()

					run_complete = tso500.run_is_complete()
					run_valid = tso500.run_is_valid()

					if run_analysis.results_completed == False and run_complete == True:

						if run_valid == True:

							logger.info (f'Run {run_analysis.run.run_id} {run_analysis.analysis_type.analysis_type_id} has now successfully completed pipeline {run_analysis.pipeline.pipeline_id}')

							logger.info (f'Putting fastqc data into db for run {run_analysis.run.run_id}')
							fastqc_dict = tso500.get_fastqc_data()
							management_utils.add_fastqc_data(fastqc_dict, run_analysis)
							
							logger.info (f'Putting reads data into db for run {run_analysis.run.run_id}')
							reads_dict = tso500.get_reads()
							management_utils.add_tso500_reads(reads_dict, run_analysis)

						else:

							logger.info (f'Run {run_id} {run_analysis.analysis_type.analysis_type_id} has failed pipeline {run_analysis.pipeline.pipeline_id}')

					elif run_analysis.results_valid == False and run_valid == True and run_complete == True:

							logger.info (f'Run {run_id} {run_analysis.analysis_type.analysis_type_id} has now successfully completed pipeline {run_analysis.pipeline.pipeline_id}')

							logger.info (f'Putting fastqc data into db for run {run_analysis.run.run_id}')
							fastqc_dict = tso500.get_fastqc_data()
							management_utils.add_fastqc_data(fastqc_dict, run_analysis)
							
							logger.info (f'Putting reads data into db for run {run_analysis.run.run_id}')
							reads_dict = tso500.get_reads()
							management_utils.add_tso500_reads(reads_dict, run_analysis)

					run_analysis.results_completed = run_complete
					run_analysis.results_valid = run_valid

					run_analysis.save()

				# TS500 DNA
				elif 'TSO500' in run_analysis.pipeline.pipeline_id and 'DNA' in run_analysis.analysis_type.analysis_type_id:

					run_id=run_analysis.run.run_id
					run_config_key = run_analysis.pipeline.pipeline_id + '-' + run_analysis.analysis_type.analysis_type_id
					dna_or_rna=run_analysis.analysis_type.analysis_type_id

					if run_config_key not in config_dict['pipelines']:

						tso500 = TSO500_pipeline.TSO500_DNA(results_dir = run_data_dir,
															sample_names = sample_ids,
															run_id = run_analysis.run.run_id,
															sample_completed_files=['*variants.tsv', '*_coverage.json'],
															sample_valid_files= ['DNA_QC_combined.txt'],
															run_completed_files = ['contamination-*.csv'],
															run_expected_files = ['DNA_QC_combined.txt','completed_samples.txt'],
															metrics_file =['DNA_QC_combined.txt']

															)
					else:

						sample_completed_files = config_dict['pipelines'][run_config_key]['sample_completed_files']
						sample_valid_files = config_dict['pipelines'][run_config_key]['sample_valid_files']
						run_expected_files = config_dict['pipelines'][run_config_key]['run_expected_files']
						run_completed_files = config_dict['pipelines'][run_config_key]['run_completed_files']
						metrics_file = config_dict['pipelines'][run_config_key]['metrics_file']

						tso500 = TSO500_pipeline.TSO500_DNA(results_dir = run_data_dir,
    															sample_completed_files=sample_completed_files,
    															sample_valid_files=sample_valid_files,
    															run_completed_files=run_completed_files,
    															run_expected_files=run_expected_files,
    															metrics_file= metrics_file,
																run_id = run_analysis.run.run_id,
																sample_names=sample_ids,
																)

					for sample in sample_ids:

						sample_complete = tso500.sample_is_complete(sample)

						sample_valid = tso500.sample_is_valid(sample)

						sample_obj = Sample.objects.get(sample_id = sample)

						sample_analysis_obj = SampleAnalysis.objects.get(sample=sample,
																		run = run_analysis.run,
																		pipeline = run_analysis.pipeline,
																		analysis_type_id=run_analysis.analysis_type)

						if sample_analysis_obj.results_completed == False and sample_complete == True:

							if sample_valid == True:

								logger.info (f'Sample {sample} on run {run_analysis.run.run_id} {run_analysis.analysis_type.analysis_type_id} has finished sample level TSO500 successfully.')

							else:
								logger.info (f'Sample {sample} on run {run_analysis.run.run_id} {run_analysis.analysis_type.analysis_type_id} has failed sample level TSO500.')

						elif sample_analysis_obj.results_valid == False and sample_valid == True and sample_complete == True:

							logger.info (f'Sample {sample} on run {run_analysis.run.run_id} {run_analysis.analysis_type.analysis_type_id} has now completed successfully.')

			
						sample_analysis_obj.results_completed = sample_complete
						sample_analysis_obj.results_valid = sample_valid
						sample_analysis_obj.save()

					run_complete = tso500.run_is_complete()
					run_valid = tso500.run_is_valid()

					if run_analysis.results_completed == False and run_complete == True:

						if run_valid == True:

							logger.info (f'Run {run_analysis.run.run_id} {run_analysis.analysis_type.analysis_type_id} has now successfully completed pipeline {run_analysis.pipeline.pipeline_id}')

							logger.info (f'Putting fastqc data into db for run {run_analysis.run.run_id}')
							fastqc_dict = tso500.get_fastqc_data()
							management_utils.add_fastqc_data(fastqc_dict, run_analysis)
							
							logger.info (f'Putting ntc contamination data into db for run {run_analysis.run.run_id}')
							ntc_contamination_dict, total_pf_reads_dict, aligned_reads_dict, ntc_contamination_aligned_reads_dict= tso500.ntc_contamination()
							management_utils.add_tso500_ntc_contamination(ntc_contamination_dict, total_pf_reads_dict, aligned_reads_dict, ntc_contamination_aligned_reads_dict, run_analysis)

						else:

							logger.info (f'Run {run_id} {run_analysis.analysis_type.analysis_type_id} has failed pipeline {run_analysis.pipeline.pipeline_id}')

					elif run_analysis.results_valid == False and run_valid == True and run_complete == True:

							logger.info (f'Run {run_id} {run_analysis.analysis_type.analysis_type_id} has now successfully completed pipeline {run_analysis.pipeline.pipeline_id}')

							logger.info (f'Putting fastqc data into db for run {run_analysis.run.run_id}')
							fastqc_dict = tso500.get_fastqc_data()
							management_utils.add_fastqc_data(fastqc_dict, run_analysis)
							
							logger.info (f'Putting ntc contamination data into db for run {run_analysis.run.run_id}')
							ntc_contamination_dict, total_pf_reads_dict, aligned_reads_dict, ntc_contamination_aligned_reads_dict= tso500.ntc_contamination()
							management_utils.add_tso500_ntc_contamination(ntc_contamination_dict, total_pf_reads_dict, aligned_reads_dict, ntc_contamination_aligned_reads_dict, run_analysis)

					run_analysis.results_completed = run_complete
					run_analysis.results_valid = run_valid

					run_analysis.save()