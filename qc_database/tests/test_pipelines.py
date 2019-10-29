import unittest
from pipeline_monitoring.pipelines import *


class TestPipelineMonitoring(unittest.TestCase):

	def test_germline_enrichment_valid(self):

		results_dir = 'test_data/190520_M02641_0219_000000000-CGJT6/IlluminaTruSightCancer'
		sample_names = ['19M06586']
		run_id = '190520_M02641_0219_000000000-CGJT6'

		germline_enrichment = GermlineEnrichment(results_dir = results_dir,
											sample_names = sample_names,
											run_id = run_id
			)

		sample_valid = germline_enrichment.sample_is_complete('19M06586')

		print(sample_valid)

		self.assertEqual(sample_valid, True)