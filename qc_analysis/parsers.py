import csv
import os
import xmltodict
from datetime import date
import json
from interop import py_interop_run_metrics, py_interop_run, py_interop_summary


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

			if start == True and sample_id != 'Sample_ID':

				sample_sheet_dict[sample_id] = {}

				for i, col in enumerate(row):

					sample_sheet_dict[sample_id][desc[i]] = col

				description = sample_sheet_dict[sample_id]['Description'].split(';')

				for item in description:

					split_item = item.split('=')

					sample_sheet_dict[sample_id][split_item[0]] = split_item[1]

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

def parse_interop_data(run_folder):
	"""
	Parses summary statistics out of interops data using the Illumina interops package
	"""

	# make empty dict to store output
	interop_dict = {}



	# taken from illumina interops package documentation, all of this is required, 
	# even though only the summary variable is used further on
	run_metrics = py_interop_run_metrics.run_metrics()
	valid_to_load = py_interop_run.uchar_vector(py_interop_run.MetricCount, 0)
	py_interop_run_metrics.list_summary_metrics_to_load(valid_to_load)
	run_folder = run_metrics.read(run_folder, valid_to_load)
	summary = py_interop_summary.run_summary()
	py_interop_summary.summarize_run_metrics(run_metrics, summary)

	# parse data from interop files -- % reads over Q30, cluster density, clusters passing filter
	interop_dict["percent_q30"] = round(summary.total_summary().percent_gt_q30(), 2)
	interop_dict["cluster_density"] = round(summary.at(0).at(0).density().mean() / 1000, 2)
	interop_dict["percent_pf"] = round(summary.at(0).at(0).percent_pf().mean(), 2)
	interop_dict["phasing"] = round(summary.at(0).at(0).phasing().mean(), 2)
	interop_dict["prephasing"] = round(summary.at(0).at(0).prephasing().mean(), 2)
	interop_dict["error_rate"] = round(summary.total_summary().error_rate(), 2)
	interop_dict["aligned"] = round(summary.total_summary().percent_aligned(), 2)

	# Doesnt throw specific type of error so catching all errors


	return interop_dict