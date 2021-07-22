import unittest
from pipelines import germline_pipelines, fusion_pipelines, nextflow_pipelines, somatic_pipelines


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

			sample_complete = somatic_fusion.sample_is_complete('19M80611_zymo')

			self.assertEqual(sample_complete, True)

			sample_valid = somatic_fusion.sample_is_valid('19M80611_zymo')

			self.assertEqual(sample_valid, True)


	"""
	def test_somatic_enrichment_valid(self):



			#run without sample 3
			results_dir = 'test_data/run1/RochePanCancer'
			sample_names = ['sample1', 'sample2']
			run_id = 'run1'

			somatic_enrichment = somatic_pipelines.SomaticEnrichment(results_dir = results_dir,
												sample_names = sample_names,
												run_id = run_id
				)


			#sample1

			sample_complete = somatic_enrichment.sample_is_complete('sample1')

			self.assertEqual(sample_complete, True)

			sample_valid = somatic_enrichment.sample_is_valid('sample1')

			self.assertEqual(sample_valid, True)



			#sample2
			sample_complete = somatic_enrichment.sample_is_complete('sample2')

			self.assertEqual(sample_complete, True)

			sample_valid = somatic_enrichment.sample_is_valid('sample2')

			self.assertEqual(sample_valid, True)


			#run without sample 3 valid/complete

			run_complete = somatic_enrichment.run_is_complete()

			self.assertEqual(run_complete, True)



			run_valid = somatic_enrichment.run_is_valid()

			self.assertEqual(run_valid, True)





			#run with sample3

			results_dir = 'test_data/run1/RochePanCancer'
			sample_names = ['sample1', 'sample2', 'sample3']
			run_id = 'run1'

			somatic_enrichment = somatic_pipelines.SomaticEnrichment(results_dir = results_dir,
												sample_names = sample_names,
												run_id = run_id
				)




			#sample3
			sample_complete = somatic_enrichment.sample_is_complete('sample3')

			self.assertEqual(sample_complete, True)

			sample_valid = somatic_enrichment.sample_is_valid('sample3')

			self.assertEqual(sample_valid, True)


			#run with sample 3 complete/valid
			run_complete = somatic_enrichment.run_is_complete()

			self.assertEqual(run_complete, False)



			run_valid = somatic_enrichment.run_is_valid()

			self.assertEqual(run_valid, False)
	"""

	def test_nextflow_germline_valid(self):


			results_dir = 'test_data/190916_M00766_0252_000000000-CJMB5/AgilentOGTFH'
			sample_names = ['na']
			run_id = '190916_M00766_0252_000000000-CD583'

			nextflow = nextflow_pipelines.NextflowGermlineEnrichment(results_dir = results_dir,
												sample_names = sample_names,
												run_id = run_id
				)


			run_valid = nextflow.run_is_valid()

			self.assertEqual(run_valid, True)


	def test_nextflow_germline_not_valid(self):


			results_dir = 'test_data/190916_M00766_0252_000000000-CJMB5/AgilentOGTFH2'
			sample_names = ['na']
			run_id = '190916_M00766_0252_000000000-CD583'

			nextflow = nextflow_pipelines.NextflowGermlineEnrichment(results_dir = results_dir,
												sample_names = sample_names,
												run_id = run_id
				)


			run_valid = nextflow.run_is_valid()

			self.assertEqual(run_valid, False)
	
	
	def test_nextflow_germline_tsc(self):
			
			results_dir = ''
			sample_names = ['na']
			run_id = '210225_NB551415_0194_AHMGV3AFX2'
			
			nextflow = nextflow_pipelines.NextflowGermlineEnrichment(results_dir = results_dir, 
												sample_names = sample_names, 
												run_id = run_id
				)
			
			run_valid = nextflow.run_is_valid()
			
			self.assertEqual(run_valid, False)
