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


		self.assertEqual(run_analysis.passes_auto_qc(), (False, ['Q30 Fail']))

	
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

		first_fastqc.basic_statistics = 'FAIL'
		first_fastqc.save()

		self.assertEqual(run_analysis.passes_auto_qc(), (False, ['FASTQC Fail']))
	

	
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

		self.assertEqual(run_analysis.passes_auto_qc(), (False, ['Contamination Fail']))
	

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

		self.assertEqual(run_analysis.passes_auto_qc(), (False, ['NTC Contamination Fail']))


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

		self.assertEqual(run_analysis.passes_auto_qc(), (False, ['Sex Match Fail']))

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

		self.assertEqual(run_analysis.passes_auto_qc(), (False, ['Sex Match Fail']))