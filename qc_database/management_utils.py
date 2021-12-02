from pipelines import parsers
from qc_database.models import *
from django.contrib.auth.models import User


def add_run_log_info(run_info, run_parameters, run_obj, raw_data_dir):
	"""
	parse data from the xml files and put into run_obj

	"""

	run_params_dict = parsers.get_run_parameters_dict(run_parameters)
	run_info_dict = parsers.get_run_info_dict(run_info)

	processed_run_info_dict = parsers.extract_data_from_run_info_dict(run_info_dict)

	instrument_id = processed_run_info_dict['instrument']
	instrument_type = parsers.get_instrument_type(instrument_id)
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
	
	interop_dict = parsers.parse_interop_data(str(raw_data_dir), int(num_reads) + int(num_indexes), int(lane_count))

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
														pipeline = pipeline,
														analysis_type = run_analysis_obj.analysis_type)

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
														pipeline = pipeline,
														analysis_type = run_analysis_obj.analysis_type)

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
														pipeline = pipeline,
														analysis_type = run_analysis_obj.analysis_type)

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
														pipeline = pipeline,
														analysis_type = run_analysis_obj.analysis_type)
		
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
														pipeline = pipeline,
														analysis_type = run_analysis_obj.analysis_type)


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
														pipeline = pipeline,
														analysis_type = run_analysis_obj.analysis_type)
		
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
														pipeline = pipeline,
														analysis_type = run_analysis_obj.analysis_type)

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
														pipeline = pipeline,
														analysis_type = run_analysis_obj.analysis_type)

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
														pipeline = pipeline,
														analysis_type = run_analysis_obj.analysis_type)
		
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
														pipeline = pipeline,
														analysis_type = run_analysis_obj.analysis_type)
		
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
														pipeline = pipeline,
														analysis_type = run_analysis_obj.analysis_type)
		
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
														pipeline = pipeline,
														analysis_type = run_analysis_obj.analysis_type)
		
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

	if sensitivity_metrics['sensitivity'] is None:

		run_analysis_obj.sensitivity = None
		run_analysis_obj.sensitivity_lower_ci = None
		run_analysis_obj.sensitivity_higher_ci = None
		run_analysis_obj.sensitivity_user = User.objects.get(pk=1)

	else:

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
														pipeline = pipeline,
														analysis_type = run_analysis_obj.analysis_type)
		
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
														pipeline = pipeline,
														analysis_type = run_analysis_obj.analysis_type)
		
		existing_data = DragenRegionCoverageMetrics.objects.filter(sample_analysis= sample_analysis_obj)
		
		if len(existing_data) < 1:

			sample_data = dragen_exonic_coverage_metrics[key]

			sample_data['sample_analysis'] = sample_analysis_obj
			
			for key in sample_data:

				if sample_data[key] == 'NA' or sample_data[key] == ''  or sample_data[key] == 'inf':

					sample_data[key] = None

			new_dragen_region_cov_obj = DragenRegionCoverageMetrics(**sample_data)
			new_dragen_region_cov_obj.save()


def add_dragen_ploidy_metrics(dragen_ploidy_metrics, run_analysis_obj):

	"""
	Add data from the Dragen ploidy files to database.

	"""
	pipeline = run_analysis_obj.pipeline
	run = run_analysis_obj.run

	for key in dragen_ploidy_metrics:
		
		sample_obj = Sample.objects.get(sample_id=key)

		sample_analysis_obj = SampleAnalysis.objects.get(sample=sample_obj,
														run=run,
														pipeline = pipeline,
														analysis_type = run_analysis_obj.analysis_type)
		
		existing_data = DragenPloidyMetrics.objects.filter(sample_analysis= sample_analysis_obj)
		
		if len(existing_data) < 1:

			sample_data = dragen_ploidy_metrics[key]

			sample_data['sample_analysis'] = sample_analysis_obj
			
			for key in sample_data:

				if sample_data[key] == 'NA' or sample_data[key] == ''  or sample_data[key] == 'inf':

					sample_data[key] = None

			new_dragen_ploidy_metrics_obj = DragenPloidyMetrics(sample_analysis=sample_analysis_obj, ploidy_estimation=sample_data['ploidy_estimation'])
			new_dragen_ploidy_metrics_obj.save()


def add_fusion_contamination_metrics(contamination_metrics_dict, run_analysis_obj):
	"""
	Add data from fusion contamination file to database

	"""
	pipeline = run_analysis_obj.pipeline
	run = run_analysis_obj.run

	for key in contamination_metrics_dict:

		sample_obj = Sample.objects.get(sample_id=key)

		sample_analysis_obj = SampleAnalysis.objects.get(sample=sample_obj,
														run=run,
														pipeline = pipeline,
														analysis_type = run_analysis_obj.analysis_type)
		
		existing_data = FusionContamination.objects.filter(sample_analysis= sample_analysis_obj)
		
		if len(existing_data) < 1:

			sample_data = contamination_metrics_dict[key]

			sample_data['sample_analysis'] = sample_analysis_obj

			new_fusion_contamination_obj = FusionContamination(**sample_data)
			new_fusion_contamination_obj.save()


def add_fusion_alignment_metrics(alignment_metrics_dict, run_analysis_obj):
	"""
	Add data from fusion alignments file to database

	"""
	pipeline = run_analysis_obj.pipeline
	run = run_analysis_obj.run

	for key in alignment_metrics_dict:

		sample_obj = Sample.objects.get(sample_id=key)

		sample_analysis_obj = SampleAnalysis.objects.get(sample=sample_obj,
														run=run,
														pipeline = pipeline,
														analysis_type = run_analysis_obj.analysis_type)
		
		existing_data = FusionAlignmentMetrics.objects.filter(sample_analysis= sample_analysis_obj)
		
		if len(existing_data) < 1:

			sample_data = alignment_metrics_dict[key]

			sample_data['sample_analysis'] = sample_analysis_obj

			new_fusion_alignments_obj = FusionAlignmentMetrics(**sample_data)
			new_fusion_alignments_obj.save()


def add_custom_coverage_metrics(coverage_metrics_dict, run_analysis_obj):
	"""
	Add data from custom coverage metrics file to database

	"""
	pipeline = run_analysis_obj.pipeline
	run = run_analysis_obj.run

	for key in coverage_metrics_dict:

		sample_obj = Sample.objects.get(sample_id=key)

		sample_analysis_obj = SampleAnalysis.objects.get(sample=sample_obj,
														run=run,
														pipeline = pipeline,
														analysis_type = run_analysis_obj.analysis_type)

		existing_data = CustomCoverageMetrics.objects.filter(sample_analysis= sample_analysis_obj)
		
		if len(existing_data) < 1:

			sample_data = coverage_metrics_dict[key]

			sample_data['sample_analysis'] = sample_analysis_obj

			new_custom_coverage_obj = CustomCoverageMetrics(**sample_data)
			new_custom_coverage_obj.save()




def add_relatedness_metrics(parsed_relatedness, parsed_relatedness_comment, run_analysis_obj):
	"""
	Add data relatedness metrics file to database
	"""
	run = run_analysis_obj.run

	relatedness_data = RelatednessQuality.objects.filter(run_analysis=run_analysis_obj)

	if len(relatedness_data) < 1:

		 new_relatedness_obj = RelatednessQuality(results_valid=parsed_relatedness, comment=' | '.join(parsed_relatedness_comment), run_analysis=run_analysis_obj)

		 new_relatedness_obj.save()

def add_tso500_reads(reads_dict, run_analysis_obj):

	pipeline = run_analysis_obj.pipeline
	run = run_analysis_obj.run

	for key in reads_dict:
		
		sample_obj = Sample.objects.get(sample_id=key)

		sample_analysis_obj = SampleAnalysis.objects.get(sample=sample_obj,
														run=run,
														pipeline = pipeline,
														analysis_type = run_analysis_obj.analysis_type)
		
		existing_data = Tso500Reads.objects.filter(sample_analysis= sample_analysis_obj)
		
		if len(existing_data) < 1:

			reads= reads_dict[key]

			new_reads_obj = Tso500Reads(sample_analysis = sample_analysis_obj, total_on_target_reads= reads)
			
			new_reads_obj.save()



def add_tso500_ntc_contamination(ntc_contamination_dict, run_analysis_obj):

	pipeline = run_analysis_obj.pipeline
	run = run_analysis_obj.run

	for key in ntc_contamination_dict:
		
		sample_obj = Sample.objects.get(sample_id=key)


		sample_analysis_obj = SampleAnalysis.objects.get(sample=sample_obj,
														run=run,
														pipeline = pipeline,
														analysis_type = run_analysis_obj.analysis_type)
		
		existing_data = Tso500Reads.objects.filter(sample_analysis= sample_analysis_obj)
		
		if len(existing_data) < 1:

			sample_data = ntc_contamination_dict[key]

			new_reads_obj = Tso500Reads(sample_analysis = sample_analysis_obj, percent_ntc_reads= sample_data)

			new_reads_obj.save()



