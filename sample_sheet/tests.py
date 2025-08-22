from django.test import TestCase
from django.shortcuts import get_object_or_404
from sample_sheet.models import *
from sample_sheet.utils import *

from django.core.management import call_command
from sample_sheet.management.commands.import_indexes import Command

from io import StringIO

import csv


# Create your tests here.


'''
test for each assay type including referral 

test for double index set
test for single index set



'''


class TestSampleSheet(TestCase):
	'''
	Test that samplesheet generator works
	'''

	fixtures = ['assay.json','referraltype.json']


	def test_ts1(self):
		'''
		tests:
		worksheet/assay exists
		test upload script from utils
			- returns True
			- returns worksheet ID
		models updated with worksheet information
			- samples exist
			- worksheet exists
			- all referral types are TS1

		'''
		shire_filepath = 'sample_sheet/example_shire_queries/TSone_shire_query.csv'

		with open(shire_filepath) as file:
			completed, message, ws, assay_name = import_worksheet_data(file)

		self.assertEqual(ws, '21-8282')
		self.assertTrue(completed)

		# get worksheet info dict
		worksheet_info = Worksheet.get_samples_from_ws(ws)
		# create empty list
		sample_list = []
		for key, values in worksheet_info.items():
			# append sample id to sample list
			sample_list.append(values['sample'])

		self.assertEqual(sample_list, ['20M12220','21M18505','21M18653','21M18811','21M18445','21M18124','21M18588','21M18613','21M18965','21M18447','21M18152','21M18052','21M18085','21M18540','21M18673','21M18872','21M18173','21M18034','21M18627','21M18923','21M18941','21M19417','18M01796','NTC-21-8282'])

		# extract first sample
		test_sample = worksheet_info['1']['sample']
		# check referral from sample to worksheets
		sample_ws_obj = SampleToWorksheet.objects.get(sample=test_sample)
		referral_test = sample_ws_obj.referral.name

		self.assertEqual(referral_test, 'TS1')
		


	def test_wgs(self):
		'''
		tests:
		worksheet/assay exists
		test upload script from utils
			- returns True
			- returns worksheet ID
		models updated with worksheet information
			- samples exist
			- worksheet exists
			- referral type edited from rapidWGS to wgs~wings

		'''
		shire_filepath = 'sample_sheet/example_shire_queries/wgs_nextera_shire_query.csv'

		with open(shire_filepath) as file:
			completed, message, ws, assay_name = import_worksheet_data(file)

		self.assertEqual(ws, '21-5748')
		self.assertTrue(completed)

		# get worksheet info dict
		worksheet_info = Worksheet.get_samples_from_ws(ws)
		# extract first sample
		test_sample = worksheet_info['1']['sample']
		# check referral from sample to worksheets
		sample_ws_obj = SampleToWorksheet.objects.get(sample=test_sample)
		referral_test = sample_ws_obj.referral.name

		self.assertEqual(referral_test, 'wgs~wings')
		

	def test_wings_fail(self):
		'''
		tests:
		worksheet/assay exists
		test upload script from utils
			- fails
		'''
		shire_filepath = 'sample_sheet/example_shire_queries/wings_shire_referralfail.csv'

		with open(shire_filepath) as file:
			completed, message, ws, assay_name = import_worksheet_data(file)

		self.assertFalse(completed)


	def test_BRCA(self):
		'''
		tests:
		worksheet/assay exists
		test upload script from utils
			- returns True
			- returns worksheet ID
		models updated with worksheet information
			- samples exist
			- worksheet exists

		'''
		shire_filepath = 'sample_sheet/example_shire_queries/BRCA_shire_query.csv'

		with open(shire_filepath) as file:
			completed, message, ws, assay_name = import_worksheet_data(file)

		self.assertEqual(ws, '21-5644')
		self.assertTrue(completed)

		# get worksheet info dict
		worksheet_info = Worksheet.get_samples_from_ws(ws)
		# extract first sample
		test_sample = worksheet_info['1']['sample']
		# check referral from sample to worksheets
		sample_ws_obj = SampleToWorksheet.objects.get(sample=test_sample)
		referral_test = sample_ws_obj.referral.name

		self.assertEqual(referral_test, 'sec:familialcancer')


	def test_CRM(self):
		'''
		tests:
		worksheet/assay exists
		test upload script from utils
			- returns True
			- returns worksheet ID
		models updated with worksheet information
			- samples exist
			- worksheet exists

		'''
		shire_filepath = 'sample_sheet/example_shire_queries/CRM_shire_query.csv'

		with open(shire_filepath) as file:
			completed, message, ws, assay_name = import_worksheet_data(file)

		self.assertEqual(ws, '21-4365')
		self.assertTrue(completed)

		# get worksheet info dict
		worksheet_info = Worksheet.get_samples_from_ws(ws)
		# extract first sample
		test_sample = worksheet_info['1']['sample']
		# check referral from sample to worksheets
		sample_ws_obj = SampleToWorksheet.objects.get(sample=test_sample)
		referral_test = sample_ws_obj.referral.name

		self.assertEqual(referral_test, 'lung')


	def test_FH(self):
		'''
		tests:
		worksheet/assay exists
		test upload script from utils
			- returns True
			- returns worksheet ID
		models updated with worksheet information
			- samples exist
			- worksheet exists

		'''
		shire_filepath = 'sample_sheet/example_shire_queries/FH_shire_query.csv'

		with open(shire_filepath) as file:
			completed, message, ws, assay_name = import_worksheet_data(file)

		self.assertEqual(ws, '21-1619')
		self.assertTrue(completed)

		# get worksheet info dict
		worksheet_info = Worksheet.get_samples_from_ws(ws)
		# extract first sample
		test_sample = worksheet_info['1']['sample']
		# check referral from sample to worksheets
		sample_ws_obj = SampleToWorksheet.objects.get(sample=test_sample)
		referral_test = sample_ws_obj.referral.name

		self.assertEqual(referral_test, 'fh')


	def test_Myeloid(self):
		'''
		tests:
		worksheet/assay exists
		test upload script from utils
			- returns True
			- returns worksheet ID
		models updated with worksheet information
			- samples exist
			- worksheet exists

		'''
		shire_filepath = 'sample_sheet/example_shire_queries/Myeloid_shire_query.csv'

		with open(shire_filepath) as file:
			completed, message, ws, assay_name = import_worksheet_data(file)

		self.assertEqual(ws, '21-4798')
		self.assertTrue(completed)

		# get worksheet info dict
		worksheet_info = Worksheet.get_samples_from_ws(ws)
		# extract first sample
		test_sample = worksheet_info['1']['sample']
		# check referral from sample to worksheets
		sample_ws_obj = SampleToWorksheet.objects.get(sample=test_sample)
		referral_test = sample_ws_obj.referral.name

		self.assertEqual(referral_test, 'cll')


	def test_TSC(self):
		'''
		tests:
		worksheet/assay exists
		test upload script from utils
			- returns True
			- returns worksheet ID
		models updated with worksheet information
			- samples exist
			- worksheet exists

		'''
		shire_filepath = 'sample_sheet/example_shire_queries/TScancer_shire_query.csv'

		with open(shire_filepath) as file:
			completed, message, ws, assay_name = import_worksheet_data(file)

		self.assertEqual(ws, '21-4325')
		self.assertTrue(completed)

		# get worksheet info dict
		worksheet_info = Worksheet.get_samples_from_ws(ws)
		# extract first sample
		test_sample = worksheet_info['1']['sample']
		# check referral from sample to worksheets
		sample_ws_obj = SampleToWorksheet.objects.get(sample=test_sample)
		referral_test = sample_ws_obj.referral.name

		self.assertEqual(referral_test, 'TSC')


	def test_TSO500DNA(self):
		'''
		tests:
		worksheet/assay exists
		test upload script from utils
			- returns True
			- returns worksheet ID
		models updated with worksheet information
			- samples exist
			- worksheet exists

		'''
		shire_filepath = 'sample_sheet/example_shire_queries/tso500dna_shire_query.csv'

		with open(shire_filepath) as file:
			completed, message, ws, assay_name = import_worksheet_data(file)

		self.assertEqual(ws, '21-1975')
		self.assertTrue(completed)

		# get worksheet info dict
		worksheet_info = Worksheet.get_samples_from_ws(ws)
		# extract first sample
		test_sample = worksheet_info['1']['sample']
		# check referral from sample to worksheets
		sample_ws_obj = SampleToWorksheet.objects.get(sample=test_sample)
		referral_test = sample_ws_obj.referral.name

		self.assertEqual(referral_test, 'endometrial-pole')


	def test_TSO500RNA(self):
		'''
		tests:
		worksheet/assay exists
		test upload script from utils
			- returns True
			- returns worksheet ID
		models updated with worksheet information
			- samples exist
			- worksheet exists

		'''
		shire_filepath = 'sample_sheet/example_shire_queries/tso500rna_shire_query.csv'

		with open(shire_filepath) as file:
			completed, message, ws, assay_name = import_worksheet_data(file)

		self.assertEqual(ws, '21-1971')
		self.assertTrue(completed)

		# get worksheet info dict
		worksheet_info = Worksheet.get_samples_from_ws(ws)
		# extract first sample
		test_sample = worksheet_info['1']['sample']
		# check referral from sample to worksheets
		sample_ws_obj = SampleToWorksheet.objects.get(sample=test_sample)
		referral_test = sample_ws_obj.referral.name

		self.assertEqual(referral_test, 'lung')


	def test_WES(self):
		'''
		tests:
		worksheet/assay exists
		test upload script from utils
			- returns True
			- returns worksheet ID
		models updated with worksheet information
			- samples exist
			- worksheet exists

		'''
		shire_filepath = 'sample_sheet/example_shire_queries/WES_shire_query.csv'

		with open(shire_filepath) as file:
			completed, message, ws, assay_name = import_worksheet_data(file)

		self.assertEqual(ws, '22-5090')
		self.assertTrue(completed)

		# get worksheet info dict
		worksheet_info = Worksheet.get_samples_from_ws(ws)
		# extract first sample
		test_sample = worksheet_info['1']['sample']
		# check referral from sample to worksheets
		sample_ws_obj = SampleToWorksheet.objects.get(sample=test_sample)
		referral_test = sample_ws_obj.referral.name

		self.assertEqual(referral_test, 'wes~paediatric_disorders_green_wes')

	def test_ctDNA(self):
		'''
		tests:
		worksheet/assay exists
  		test upload script from utils
			- returns True
			- returns worksheet ID
		models updated with worksheet information
			- samples exist
			- worksheet exists

		'''
		shire_filepath = 'sample_sheet/example_shire_queries/ctdna_shire_query2.csv'

		with open(shire_filepath) as file:
 			completed, message, ws, assay_name = import_worksheet_data(file)

		self.assertEqual(ws, '23-1763')
		self.assertTrue(completed)

		# get worksheet info dict
		worksheet_info = Worksheet.get_samples_from_ws(ws)
		# extract first sample
		test_sample = worksheet_info['1']['sample']
		# check referral from sample to worksheets
		sample_ws_obj = SampleToWorksheet.objects.get(sample=test_sample)
		referral_test = sample_ws_obj.referral.name

		self.assertEqual(referral_test, 'lung')



	## test index import management command
	def test_indexupload(self):
		'''
		tests:
		upload an indexset using management command
		test index set exists by querying model
		'''
		kwargs = {
		'index_tsv':['sample_sheet/index_files/FH_indexes_short.tsv'],
		'set_name':['FH'],
		'vendor_name':['Illumina']}

		call_command(
			"import_indexes",
			stdout=StringIO(),
			stderr=StringIO(),
			**kwargs,
		)

		# query for index info
		index_obj = Index.objects.get(index_name = '1', i7_or_i5 = 'i7')

		self.assertEqual(index_obj.sequence, 'AACGTGAT')

if __name__ == '__main__':
    unittest.main()
