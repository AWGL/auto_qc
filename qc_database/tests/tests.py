from django.test import TestCase
from qc_database.models import *

class TestAutoQC(TestCase):
	"""
	Test that AutoQC works
	"""

	fixtures = ['test_data']

	def setUp(self):

		self.client.login(username='admin', password= 'hello123')


	def test_q30_fail(self):

		run_analysis= RunAnalysis.objects.get(pk=16)

		interops = InteropRunQuality.objects.filter(
			run = run_analysis.run
			)

		self.assertEqual(run_analysis.passes_auto_qc(), (True, ['All Pass']))

		first_interop = interops[0]
		first_interop.percent_q30 = 73
		first_interop.save()


		self.assertEqual(run_analysis.passes_auto_qc(), (False, ['Q30 Fail'],['19M07162', '19M07267', '19M07040', '19M07041', '19M07167', '19M07203', '19M07356', '19M07411', '19M07039', '19M07048', '19M07121', '19M07234', '19M07084', '19M07098', '19M07173', '19M07248', '19M07398', '19M07333', '19M06586', '19M07251', '19M07089', '19M07435', '19M07436']))

	
	def test_fastqc_fail(self):

		run_analysis= RunAnalysis.objects.get(pk=16)

		samples = SampleAnalysis.objects.filter(
			run = run_analysis.run,
			pipeline = run_analysis.pipeline,
			analysis_type = run_analysis.analysis_type
			)

		fastqcs = SampleFastqcData.objects.filter(sample_analysis= samples[0])

		first_fastqc = fastqcs[0]

		self.assertEqual(run_analysis.passes_auto_qc(), (True, ['All Pass']))

		# check passes if only per tile fails
		first_fastqc.per_tile_sequence_quality = 'FAIL'
		first_fastqc.save()
		self.assertEqual(run_analysis.passes_auto_qc(), (True, ['All Pass']))

		# check fails if basic stats, per base sequence quality, per sequence quality scores or per base n content fail
		# basic stats
		first_fastqc.basic_statistics = 'FAIL'
		first_fastqc.save()
		self.assertEqual(run_analysis.passes_auto_qc(), (False, ['FASTQC Fail'],['19M07162']))

		# per base sequence quality
		first_fastqc.basic_statistics = 'PASS'
		first_fastqc.per_base_sequencing_quality = 'FAIL'
		first_fastqc.save()
		self.assertEqual(run_analysis.passes_auto_qc(), (False, ['FASTQC Fail'],['19M07162']))

		# per sequence quality scores
		first_fastqc.per_base_sequencing_quality = 'PASS'
		first_fastqc.per_sequence_quality_scores = 'FAIL'
		first_fastqc.save()
		self.assertEqual(run_analysis.passes_auto_qc(), (False, ['FASTQC Fail'],['19M07162']))

		# per base n content
		first_fastqc.per_sequence_quality_scores = 'PASS'
		first_fastqc.per_base_n_content = 'FAIL'
		first_fastqc.save()
		self.assertEqual(run_analysis.passes_auto_qc(), (False, ['FASTQC Fail'],['19M07162']))


	def test_contamination_fail(self):

		run_analysis= RunAnalysis.objects.get(pk=16)

		samples = SampleAnalysis.objects.filter(
			run = run_analysis.run,
			pipeline = run_analysis.pipeline,
			analysis_type = run_analysis.analysis_type
			)

		contamination = ContaminationMetrics.objects.get(sample_analysis = samples[0])

		self.assertEqual(run_analysis.passes_auto_qc(), (True, ['All Pass']))

		contamination.freemix = 0.25
		contamination.save()

		self.assertEqual(run_analysis.passes_auto_qc(), (False, ['Contamination Fail'],['19M07162']))
	

	def test_ntc_contamination_fail(self):

		run_analysis= RunAnalysis.objects.get(pk=16)

		samples = SampleAnalysis.objects.filter(
			run = run_analysis.run,
			pipeline = run_analysis.pipeline,
			analysis_type = run_analysis.analysis_type
			)

		hs_metrics = SampleHsMetrics.objects.get(sample_analysis = samples[0])

		self.assertEqual(run_analysis.passes_auto_qc(), (True, ['All Pass']))

		hs_metrics.total_reads = 10000
		hs_metrics.save()

		self.assertEqual(run_analysis.passes_auto_qc(), (False, ['NTC Contamination Fail'],['19M07162']))


	def test_sex_match_fail(self):

		run_analysis= RunAnalysis.objects.get(pk=16)

		samples = SampleAnalysis.objects.filter(
			run = run_analysis.run,
			pipeline = run_analysis.pipeline,
			analysis_type = run_analysis.analysis_type
			)

		sex = CalculatedSexMetrics.objects.get(sample_analysis=samples[0])

		self.assertEqual(run_analysis.passes_auto_qc(), (True, ['All Pass']))

		sex.calculated_sex = 'FEMALE'
		sex.save()

		self.assertEqual(run_analysis.passes_auto_qc(), (False, ['Sex Match Fail'],['19M07162']))


	def test_variant_count_fail(self):

		run_analysis= RunAnalysis.objects.get(pk=16)

		samples = SampleAnalysis.objects.filter(
			run = run_analysis.run,
			pipeline = run_analysis.pipeline,
			analysis_type = run_analysis.analysis_type
			)

		sex = CalculatedSexMetrics.objects.get(sample_analysis=samples[0])

		self.assertEqual(run_analysis.passes_auto_qc(), (True, ['All Pass']))

		sex.calculated_sex = 'FEMALE'
		sex.save()

		self.assertEqual(run_analysis.passes_auto_qc(), (False, ['Sex Match Fail'],['19M07162']))


	def test_determine_worst_consequence(self):
		
		list1 = ["PASS", "WARN", "FAIL"]
		list2 = ["PASS", "WARN", "PASS"]
		list3 = ["PASS", "PASS", "PASS"]
		list4 = []
		list5 = ["PASS", "PASS", "PASS "]
		list6 = ["PASS", "FAIL", "FIAL"]

		list1_worst_consequence = SampleAnalysis.determine_worst_consequence(list1)
		list2_worst_consequence = SampleAnalysis.determine_worst_consequence(list2)
		list3_worst_consequence = SampleAnalysis.determine_worst_consequence(list3)
		list4_worst_consequence = SampleAnalysis.determine_worst_consequence(list4)
		list5_worst_consequence = SampleAnalysis.determine_worst_consequence(list5)

		self.assertEqual(list1_worst_consequence, "FAIL")
		self.assertEqual(list2_worst_consequence, "WARN")
		self.assertEqual(list3_worst_consequence, "PASS")
		self.assertEqual(list4_worst_consequence, "N/A")
		self.assertEqual(list5_worst_consequence, "PASS")
		with self.assertRaises(KeyError):
			SampleAnalysis.determine_worst_consequence(list6)