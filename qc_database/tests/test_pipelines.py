import unittest
from pipelines import germline_pipelines, fusion_pipelines


class TestPipelineMonitoring(unittest.TestCase):

	def test_germline_enrichment_valid(self):

		results_dir = 'test_data/190520_M02641_0219_000000000-CGJT6/IlluminaTruSightCancer'
		sample_names = ['19M06586']
		run_id = '190520_M02641_0219_000000000-CGJT6'

		germline_enrichment = germline_pipelines.GermlineEnrichment(results_dir = results_dir,
											sample_names = sample_names,
											run_id = run_id
			)

		sample_complete = germline_enrichment.sample_is_complete('19M06586')

		self.assertEqual(sample_complete, True)

		sample_valid = germline_enrichment.sample_is_valid('19M06586')

		self.assertEqual(sample_valid, True)

		def test_somatic_fusion_valid(self):

			results_dir = 'test_data/200731_NB551319_0117_AH7K2TAFX2/RocheSTFusion'
			sample_names = ['19M80611_zymo']
			run_id = '200731_NB551319_0117_AH7K2TAFX2-CGJT6'

			somatic_fusion = fusion_pipelines.SomaticFusion(results_dir = results_dir,
												sample_names = sample_names,
												run_id = run_id
				)

			sample_complete = germline_enrichment.sample_is_complete('19M80611_zymo')

			self.assertEqual(sample_complete, True)

			sample_valid = germline_enrichment.sample_is_valid('19M80611_zymo')

			self.assertEqual(sample_valid, True)