import csv
import os
import xmltodict
from datetime import date
import json
from interop import py_interop_run_metrics, py_interop_run, py_interop_summary
import yaml
import math
import pandas as pd
from pysam import VariantFile
import string


def sample_sheet_parser(sample_sheet_path):

	sample_sheet_dict = {}

	start = False

	with open(sample_sheet_path, 'r') as csvfile:

		spamreader = csv.reader(csvfile, delimiter=',')

		for row in spamreader:

			sample_id = row[0]

			if sample_id == 'Sample_ID':

				start = True
				desc = row

			if sample_id == '':

				continue

			if start == True and sample_id != 'Sample_ID':

				sample_sheet_dict[sample_id] = {}

				for i, col in enumerate(row):

					sample_sheet_dict[sample_id][desc[i]] = col

				description = sample_sheet_dict[sample_id]['Description'].split(';')

				for item in description:

					split_item = item.split('=')

					sample_sheet_dict[sample_id][split_item[0]] = split_item[1]

				for tag in ['pipelineName', 'pipelineVersion', 'panel']:

					if tag not in sample_sheet_dict[sample_id]:

						raise Exception(f'The following items are required in the description field: pipelineName, pipelineVersion, panel and sex. {tag} was not in it for {sample_sheet_path}')

	return sample_sheet_dict


def sample_sheet_parser_nipt(sample_sheet_path):

	sample_sheet_dict = {}

	start = False

	with open(sample_sheet_path, 'r') as csvfile:

		spamreader = csv.reader(csvfile, delimiter=',')

		for row in spamreader:

			sample_id = row[1]

			if sample_id == 'Sample_ID':

				start = True
				desc = row

			if sample_id == '':

				continue

			if start == True and sample_id != 'Sample_ID':

				sample_sheet_dict[sample_id] = {}

				for i, col in enumerate(row):

					sample_sheet_dict[sample_id][desc[i]] = col

	return sample_sheet_dict

def get_run_parameters_dict(run_parameters_path):

	# turn XML file into a dictionary
	with open(run_parameters_path) as f:

		runinfo_dict = xmltodict.parse(f.read())

	return runinfo_dict

def get_run_info_dict(run_info_path):

	# turn XML file into a dictionary
	with open(run_info_path) as f:

		run_info_dict = xmltodict.parse(f.read())

	return run_info_dict

def get_instrument_type(instrument_id):

	if instrument_id.startswith('M'):
		instrument_type = 'MiSeq'

	elif instrument_id.startswith('D'):

		instrument_type = 'HiSeq'

	elif instrument_id.startswith('NB'):

		instrument_type = 'NextSeq'

	elif instrument_id.startswith('A'):

		instrument_type = 'Novaseq'

	else:

		instrument_type = ''

	return instrument_type


def extract_data_from_run_info_dict(run_info_dict):

	# parse simple variables from xml dict
	runinfo_sorted_dict = {
		'run_id': run_info_dict['RunInfo']['Run']['@Id'],   #@ == attribute
		'instrument': run_info_dict['RunInfo']['Run']['Instrument'],
	}

	# format date object
	instrument_date = run_info_dict['RunInfo']['Run']['Date']
	year = '20' + instrument_date[0:2]
	month = instrument_date[2:4]
	day = instrument_date[4:6]
		
	try:
		runinfo_sorted_dict['instrument_date'] = date(int(year), int(month), int(day)).isoformat()
	except:
		
		year = instrument_date.split(' ')[0].split('/')[2]
		month = instrument_date.split(' ')[0].split('/')[0]
		day = instrument_date.split(' ')[0].split('/')[1]
		
		runinfo_sorted_dict['instrument_date'] = date(int(year), int(month), int(day)).isoformat()		

	# parse reads from xml dict and sort data
	reads = run_info_dict['RunInfo']['Run']['Reads']['Read']
	num_reads = 0
	num_indexes = 0

	for r in reads:

		if r['@IsIndexedRead'] == 'Y':

			num_indexes += 1

			if num_indexes == 1:

				runinfo_sorted_dict['length_index1'] = r['@NumCycles']

			if num_indexes == 2:

				runinfo_sorted_dict['length_index2'] = r['@NumCycles']

		if r['@IsIndexedRead'] == 'N':

			num_reads += 1

			if num_reads == 1:

				runinfo_sorted_dict['length_read1'] = r['@NumCycles']

			if num_reads == 2:

				runinfo_sorted_dict['length_read2'] = r['@NumCycles']

	runinfo_sorted_dict['num_reads'] = num_reads
	runinfo_sorted_dict['num_indexes'] = num_indexes

	# encode xml dict as a json string
	runinfo_sorted_dict['raw_runinfo_json'] = json.dumps(run_info_dict, indent=2, separators=(',', ':'))

	return runinfo_sorted_dict

def parse_interop_data(run_folder_dir, num_reads, num_lanes):
	"""
	Parses summary statistics out of interops data using the Illumina interops package
	"""

	# make empty dict to store output
	interop_dict = {'read_summaries': {}}


	# taken from illumina interops package documentation, all of this is required, 
	# even though only the summary variable is used further on
	run_metrics = py_interop_run_metrics.run_metrics()
	valid_to_load = py_interop_run.uchar_vector(py_interop_run.MetricCount, 0)
	py_interop_run_metrics.list_summary_metrics_to_load(valid_to_load)
	run_folder = run_metrics.read(run_folder_dir, valid_to_load)
	summary = py_interop_summary.run_summary()
	py_interop_summary.summarize_run_metrics(run_metrics, summary)


	for read in range(num_reads):

		new_read = read + 1

		if new_read not in interop_dict['read_summaries']:

			interop_dict['read_summaries'][new_read] = {}


		for lane in range(num_lanes):

			new_lane = lane + 1

			if new_lane not in interop_dict['read_summaries'][new_read]:

				interop_dict['read_summaries'][new_read][new_lane] = {}

			interop_dict['read_summaries'][read+1][lane+1]['percent_q30'] = summary.at(read).at(lane).percent_gt_q30()
			interop_dict['read_summaries'][read+1][lane+1]['density'] = summary.at(read).at(lane).density().mean()
			interop_dict['read_summaries'][read+1][lane+1]['density_pf'] = summary.at(read).at(lane).density_pf().mean()
			interop_dict['read_summaries'][read+1][lane+1]['cluster_count'] = summary.at(read).at(lane).density_pf().mean()
			interop_dict['read_summaries'][read+1][lane+1]['cluster_count_pf'] = summary.at(read).at(lane).cluster_count_pf().mean()
			interop_dict['read_summaries'][read+1][lane+1]['error_rate'] = summary.at(read).at(lane).error_rate().mean()
			interop_dict['read_summaries'][read+1][lane+1]['percent_aligned'] = summary.at(read).at(lane).percent_aligned().mean()
			interop_dict['read_summaries'][read+1][lane+1]['percent_pf'] = summary.at(read).at(lane).percent_pf().mean()
			interop_dict['read_summaries'][read+1][lane+1]['phasing'] = summary.at(read).at(lane).phasing().mean()
			interop_dict['read_summaries'][read+1][lane+1]['prephasing'] = summary.at(read).at(lane).prephasing().mean()
			interop_dict['read_summaries'][read+1][lane+1]['reads'] = summary.at(read).at(lane).reads()
			interop_dict['read_summaries'][read+1][lane+1]['reads_pf'] = summary.at(read).at(lane).reads_pf()
			interop_dict['read_summaries'][read+1][lane+1]['yield_g'] = summary.at(read).at(lane).yield_g()

			for key in interop_dict['read_summaries'][read+1][lane+1]:

				if math.isnan(interop_dict['read_summaries'][read+1][lane+1][key]):

					interop_dict['read_summaries'][read+1][lane+1][key] = None


	run_metrics = py_interop_run_metrics.run_metrics()
	valid_to_load = py_interop_run.uchar_vector(py_interop_run.MetricCount, 0)
	py_interop_run_metrics.list_index_metrics_to_load(valid_to_load)
	run_folder = run_metrics.read(run_folder_dir, valid_to_load)


	return interop_dict


def parse_fastqc_file(fastqc_text_file):

	with open (fastqc_text_file) as file:

		fqcfile = csv.reader(file, delimiter='\t')
		fqcdict = {}

		for column in fqcfile:

				metrics = column[1]
				result = column[0]
				input_dir = column[2].split('_')
				UniqueID = "_".join(input_dir[:5])
				SampleID = input_dir[4]
				Read_Group = input_dir[-1].strip('.fastq')
				Lane = input_dir[5]
				RunID = '_'.join(input_dir[:4])
				fqcdict["UniqueID"] = UniqueID
				fqcdict["general_readinfo"]= column[2]
				fqcdict["SampleID"]= SampleID
				fqcdict["RunID"] = RunID
				fqcdict["Read_Group"] = Read_Group
				fqcdict["Lane"] = Lane
				fqcdict[metrics] = result

		return fqcdict



def parse_fastqc_file_tso500(fastqc_text_file):

	with open (fastqc_text_file) as file:

		fqcfile = csv.reader(file, delimiter='\t')
		fqcdict = {}

		for column in fqcfile:

				metrics = column[1]
				result = column[0]
				input_dir = column[2].split('_')
				UniqueID = "_".join(input_dir[:5])
				SampleID = input_dir[0]
				Read_Group = input_dir[-1].strip('.fastq')
				Lane = input_dir[2]
				fqcdict["UniqueID"] = UniqueID
				fqcdict["general_readinfo"]= column[2]
				fqcdict["SampleID"]= SampleID
				fqcdict["Read_Group"] = Read_Group
				fqcdict["Lane"] = Lane
				fqcdict[metrics] = result

		return fqcdict

def parse_fastqc_file_cruk(fastqc_text_file, run_id):

	with open (fastqc_text_file) as file:

		fqcfile = csv.reader(file, delimiter='\t')
		fqcdict = {}

		for column in fqcfile:

				metrics = column[1]
				result = column[0]
				input_dir = column[2].split('_')
				SampleID = input_dir[0]
				Read_Group = input_dir[-1].strip('.fastq.gz')
				Lane = input_dir[2]
				fqcdict["general_readinfo"]= column[2]
				fqcdict["SampleID"]= SampleID
				fqcdict["RunID"] = run_id
				fqcdict["Read_Group"] = Read_Group
				fqcdict["Lane"] = Lane
				fqcdict[metrics] = result

		return fqcdict

def parse_hs_metrics_file(hs_metrics_file):

	hs_metrics_dict = {}

	with open (hs_metrics_file) as file:

		hs_metrics_file = csv.reader(file, delimiter='\t')

		next_keys = False
		next_values = False

		keys = []
		values = []

		for row in hs_metrics_file:

			if len(row) != 0:

				if next_values == True:

					values = row
					break

				if next_keys == True:

					keys = row
					next_keys = False
					next_values = True

				if row[0] == '## METRICS CLASS':

					next_keys = True

	for key, value in zip(keys, values):

		hs_metrics_dict[key.lower()] = value

	return hs_metrics_dict


def parse_gatk_depth_summary_file(gatk_depth_summary_file):

	gatk_depth_summary_dict = {}

	with open (gatk_depth_summary_file) as file:

		keys = []
		values = []

		gatk_depth_summary_file = csv.reader(file, delimiter='\t')

		for row in gatk_depth_summary_file:

			if row[0] == 'sample_id':

				keys = row

			elif row[0] == 'Total':

				pass

			else:

				values = row

		for key, value in zip(keys, values):

			new_key = key.replace('%', 'pct').lower()

			gatk_depth_summary_dict[new_key] = value

	return gatk_depth_summary_dict


def parse_duplication_metrics_file(duplication_metrics_file):

	duplication_metrics_dict = {}

	with open (duplication_metrics_file) as file:

		duplication_metrics_file = csv.reader(file, delimiter='\t')

		next_keys = False
		next_values = False

		keys = []
		values = []

		for row in duplication_metrics_file:

			if len(row) != 0:

				if next_values == True:

					values = row
					break

				if next_keys == True:

					keys = row
					next_keys = False
					next_values = True

				if row[0] == '## METRICS CLASS':

					next_keys = True

	for key, value in zip(keys, values):

		duplication_metrics_dict[key.lower()] = value

	return duplication_metrics_dict


def parse_contamination_metrics(self_sm_contamination_file):

	contamination_metrics_dict = {}

	keys = []
	values = []

	with open (self_sm_contamination_file) as file:

		self_sm_contamination_file = csv.reader(file, delimiter='\t')

		row_count = 0

		for row in self_sm_contamination_file:

			if row_count == 0:

				keys = row

			elif row_count == 1:

				values = row
				break

			row_count = row_count + 1

	for key, value in zip(keys, values):

		new_key = key.replace('#', 'num_').lower()

		if new_key not in ['num_seq_id',
					'rg',
					'chip_id',
					'free_rh',
					'free_ra',
					'chipmix',
					'chiplk1',
					'chiplk0',
					'chip_rh',
					'chip_ra',
					'dpref',
					'rdphet',
					'rdpalt' ]:

			contamination_metrics_dict[new_key] = value

	return contamination_metrics_dict

def parse_qc_metrics_file(qc_metrics_file):

	qc_metrics_dict = {}

	keys = []
	values = []

	with open(qc_metrics_file) as file:

		qc_metrics_file = csv.reader(file, delimiter='\t')

		count = 0

		for row in qc_metrics_file:

			if count == 0:

				keys = row

			elif count == 1:

				values = row

			count = count + 1

	for key, value in zip(keys, values):

		qc_metrics_dict[key.lower()] = value

	return qc_metrics_dict

def parse_alignment_metrics_file(alignments_metric_file):

	alignment_metrics_dicts = []

	with open (alignments_metric_file) as file:

		alignments_metric_file = csv.reader(file, delimiter='\t')

		next_keys = False
		next_values = False

		keys = []
		values = []

		for row in alignments_metric_file:

			if len(row) != 0:

				if next_values == True:

					row_dict = {}

					values = row

					for key, value in zip(keys, values):

						if key.lower() not in ['read_group',  'sample', 'library']:

							row_dict[key.lower()] = value

					alignment_metrics_dicts.append(row_dict)

				if next_keys == True:

					keys = row
					next_keys = False
					next_values = True

				if row[0] == '## METRICS CLASS':

					next_keys = True

	return alignment_metrics_dicts
	
def parse_variant_detail_metrics_file(variant_detail_metrics_file):

	variant_detail_metrics_dict = {}

	with open (variant_detail_metrics_file) as file:

		variant_detail_metrics_file = csv.reader(file, delimiter='\t')

		next_keys = False
		next_values = False

		keys = []
		values = []

		for row in variant_detail_metrics_file:

			if len(row) != 0:

				if next_values == True:

					sample_details_dict = {}

					for key, value in zip(keys, row):

						if key.lower() not in ['sample_alias']:

							sample_details_dict[key.lower()] = value
					
					variant_detail_metrics_dict[row[0]] = sample_details_dict

				if next_keys == True:

					keys = row
					next_keys = False
					next_values = True

				if row[0] == '## METRICS CLASS':

					next_keys = True

	return variant_detail_metrics_dict


def parse_insert_metrics_file(insert_metrics_file):

	insert_metrics_dict = {}

	with open (insert_metrics_file) as file:

		insert_metrics_file = csv.reader(file, delimiter='\t')

		next_keys = False
		next_values = False

		keys = []
		values = []

		for row in insert_metrics_file:

			if len(row) != 0:

				if next_values == True:

					values = row
					break

				if next_keys == True:

					keys = row
					next_keys = False
					next_values = True

				if row[0] == '## METRICS CLASS':

					next_keys = True

	for key, value in zip(keys, values):

		if key.lower() not in ['read_group',  'sample', 'library']:

			insert_metrics_dict[key.lower()] = value

	return insert_metrics_dict

def parse_config(config_location):
	"""
	Parse the YAML config file.
	"""
	with open(config_location, 'r') as stream:
		return yaml.safe_load(stream)

def get_passing_variant_count(vcf_path, samples):
	"""
	count number of passing variants in vcf

	"""
	
	bcf_in = VariantFile(vcf_path)

	count_dict = {}

	for rec in bcf_in.fetch():

		chrom = rec.chrom
		pos = rec.pos
		ref = rec.ref
		alt = rec.alts
		filter_status = rec.filter.keys()
		info = rec.info
		quality = rec.qual

		for sample in samples:

			sample_genotype_data = rec.samples[sample]

			gt_list = []

			for allele in sample_genotype_data['GT']:

				if allele == None or allele == 0:

					pass

				else:

					gt_list.append(allele)

			if 'PASS' in filter_status and len(gt_list) > 0:

				if sample not in count_dict:

					count_dict[sample] = 0

				else:

					count_dict[sample] = count_dict[sample] + 1
	
	if len(count_dict) == 0:

		for sample in samples:

			count_dict[sample] = 0

	return count_dict


def parse_dragen_sex_file(dragen_sex_file):
	"""
	Parse the calculated sex file from the post processing pipeline.

	"""
	
	sex_dict = {}
	
	
	with open(dragen_sex_file) as csvfile:
		reader = csv.DictReader(csvfile)
		for row in reader:
			sex = row['calculated_sex']
			
			sex_dict['sex'] = sex
	
	return sex_dict

def parse_dragen_vc_metrics_file(dragen_vc_metrics_file):
	"""
	Parse the dragen variant calling metrics file.
	
	"""
	
	dragen_vc_metrics_file_dict = {}

	with open (dragen_vc_metrics_file) as file:

		dragen_vc_metrics_file = csv.reader(file, delimiter=',')
		
		for row in dragen_vc_metrics_file:
						
			prefix = row[0]
			sample = row[1]
			key = row[2]
			value = row[3]
	
			new_key = key.translate(str.maketrans('', '', string.punctuation.replace('_' ,'')))
			
			new_key = new_key.lower().replace(' ', '_').replace('__', '_')
			
			if prefix == 'JOINT CALLER PREFILTER':
								
				if sample not in dragen_vc_metrics_file_dict:
					
					dragen_vc_metrics_file_dict[sample] = {}
					
				dragen_vc_metrics_file_dict[sample][new_key] = value
				
	return dragen_vc_metrics_file_dict


def parse_dragen_alignment_metrics_file(dragen_alignment_metrics_file):
	"""
	Parse the dragen alignment metrics file.
	
	"""
	
	dragen_alignment_metrics_file_dict = {}

	with open (dragen_alignment_metrics_file) as file:

		dragen_alignment_metrics_file = csv.reader(file, delimiter=',')
		
		for row in dragen_alignment_metrics_file:
						
			prefix = row[0]
			key = row[2]
			value = row[3]
	
			new_key = key.translate(str.maketrans('', '', string.punctuation.replace('_' ,'')))
			
			new_key = new_key.lower().replace(' ', '_').replace('__', '_')
			
			if prefix == 'MAPPING/ALIGNING SUMMARY':
								
				dragen_alignment_metrics_file_dict[new_key] = value
				
	return dragen_alignment_metrics_file_dict

def parse_sensitivity_file(sensitivity_file):
	"""
	Parse the sensitivity calculation file.
	
	"""
	
	sensitivity_dict = {}
	
	with open (sensitivity_file) as file:
			
		for line in file:
				
			split_line = line.strip().strip('"').split(' ')
						
			if split_line[0] == '[1]':
				
				sensitivity_dict['sensitivity'] = split_line[2]
				sensitivity_dict['sensitivity_lower_ci'] = split_line[3].split('-')[0]
				sensitivity_dict['sensitivity_higher_ci'] = split_line[3].split('-')[1]
			
	return sensitivity_dict


def parse_dragen_wgs_coverage_metrics_file(dragen_wgs_coverage_metrics_file):
	"""
	Parse the dragen alignment metrics file.
	
	"""
	
	dragen_wgs_coverage_metrics_file_dict = {}

	with open (dragen_wgs_coverage_metrics_file) as file:

		dragen_wgs_file = csv.reader(file, delimiter=',')
		
		for row in dragen_wgs_file:
						
			prefix = row[0]
			key = row[2]
			value = row[3]
						
			new_key = key.translate(str.maketrans('', '', string.punctuation.replace('_' ,'')))
			
			new_key = new_key.lower().replace(' ', '_').replace('__', '_')

			new_key = new_key.replace('__', '_')

			# fix strange NTC results in Dragen 3.7

			new_key = new_key.replace('xinf', 'x_inf')

			new_key = new_key.replace('20x50x', '20x_50x')

			new_key = new_key.replace('15x20x', '15x_20x')

			new_key = new_key.replace('10x15x', '10x_15x')

			new_key = new_key.replace('3x10x', '3x_10x')

			new_key = new_key.replace('1x3x', '1x_3x')

			new_key = new_key.replace('0x1x', '0x_1x')
			
			if prefix == 'COVERAGE SUMMARY':
								
				dragen_wgs_coverage_metrics_file_dict[new_key] = value
				
	return dragen_wgs_coverage_metrics_file_dict


def parse_fusion_contamination_metrics_file(fusion_contamination_metrics_file):

	fusion_contamination_metrics_dict = {}

	with open (fusion_contamination_metrics_file) as file:

		fusion_file = csv.reader(file, delimiter=',')

		for row in fusion_file:

			if row[0] == 'Sample':

				pass

			else:

				sample = row[0].strip()
				contamination = row[1].strip()
				contamination_referral = row[2].strip()

				if contamination == 'No':

					contamination = False

				else:

					contamination = True

				if contamination_referral == 'No':

					contamination_referral = False

				else:

					contamination_referral = True


				if sample not in fusion_contamination_metrics_dict:
					
					fusion_contamination_metrics_dict[sample] = {}
					
				fusion_contamination_metrics_dict[sample]['contamination'] = contamination
				fusion_contamination_metrics_dict[sample]['contamination_referral'] = contamination_referral

	return fusion_contamination_metrics_dict

def parse_fusion_alignment_metrics_file(fusion_alignment_metrics_file):

	fusion_alignment_metrics_dict = {}

	with open (fusion_alignment_metrics_file) as file:

		fusion_file = csv.reader(file, delimiter=',')

		for row in fusion_file:

			if row[0] == 'sample':

				pass

			else:

				sample = row[0].strip()
				aligned_reads = row[1].strip()
				pct_reads_aligned = row[2].strip()
				unique_reads_aligned = row[3].strip()
				pct_unique_reads_aligned = row[4].strip()

				if sample not in fusion_alignment_metrics_dict:
					
					fusion_alignment_metrics_dict[sample] = {}
					
				fusion_alignment_metrics_dict[sample]['aligned_reads'] = aligned_reads
				fusion_alignment_metrics_dict[sample]['pct_reads_aligned'] = pct_reads_aligned
				fusion_alignment_metrics_dict[sample]['unique_reads_aligned'] = unique_reads_aligned
				fusion_alignment_metrics_dict[sample]['pct_unique_reads_aligned'] = pct_unique_reads_aligned

	return fusion_alignment_metrics_dict

def parse_ploidy_metrics_file(ploidy_metrics_file):
	"""
	Parse the dragen ploidy metrics file.
	
	"""
	
	dragen_ploidy_metrics_file_dict = {}

	with open (ploidy_metrics_file) as file:

		dragen_ploidy_file = csv.reader(file, delimiter=',')
		
		for row in dragen_ploidy_file:
						
			prefix = row[0]
			key = row[2]
			value = row[3]
	
			new_key = key.translate(str.maketrans('', '', string.punctuation.replace('_' ,'')))
			
			new_key = new_key.lower().replace(' ', '_').replace('__', '_')

			new_key = new_key.replace('__', '_')
			
			if prefix == 'PLOIDY ESTIMATION':
								
				dragen_ploidy_metrics_file_dict[new_key] = value
				
	return dragen_ploidy_metrics_file_dict


def parse_custom_coverage_metrics(custom_coverage_file):
	"""
	Parse the coverage summary file from germline enrichment nextflow
	"""

	custom_coverage_dict  = {}

	with open (custom_coverage_file) as file:

		coverage_file = csv.reader(file, delimiter=',')

		for row in coverage_file:
						
			key = row[0]
			value = row[1]
			custom_coverage_dict[key] = value

	return custom_coverage_dict