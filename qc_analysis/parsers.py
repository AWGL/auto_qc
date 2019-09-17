import csv

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