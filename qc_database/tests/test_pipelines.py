import unittest
from pipelines import germline_pipelines, fusion_pipelines, nextflow_pipelines, somatic_pipelines, dragen_pipelines, TSO500_pipeline


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

	def test_somaticamplicon_101X_valid(self):


			results_dir = 'test_data/210823_M00766_0416_000000000-JMTTY/NGHS-101X'
			sample_names = ['21M15195']
			run_id = '210823_M00766_0416_000000000-JMTTY'

			somatic_amplicon = somatic_pipelines.SomaticAmplicon(results_dir = results_dir,
												sample_names = sample_names,
												run_id = run_id,
												sample_expected_files = ['*_VariantReport.txt',
				  														'*.bam',
				  														'*_DepthOfCoverage.sample_summary',
				  														'*_QC.txt',
				  														'*_filtered_meta_annotated.vcf',
				  														'hotspot_variants',
				  														'hotspot_coverage'
				  														],
				  								run_expected_files = ['*CRM.xlsx']


				)

			run_complete = somatic_amplicon.run_is_valid()

			self.assertEqual(run_complete, True)

	def test_somaticamplicon_102X_valid(self):


			results_dir = 'test_data/210823_M00766_0416_000000000-JMTTY/NGHS-102X'
			sample_names = ['21M14838']
			run_id = '210823_M00766_0416_000000000-JMTTY'

			somatic_amplicon = somatic_pipelines.SomaticAmplicon(results_dir = results_dir,
												sample_names = sample_names,
												run_id = run_id,
												sample_expected_files = ['*_VariantReport.txt',
                  														'*.bam',
                  														'*_DepthOfCoverage.sample_summary',
                  														'*_QC.txt',
                  														'*_filtered_meta_annotated.vcf'
                  														],
                  								run_expected_files = ['*merged_coverage_report.txt',
                  													'*merged_variant_report.txt',
                        											]
				)

			run_complete = somatic_amplicon.run_is_valid()

			self.assertEqual(run_complete, True)


	def test_tso500(self):


			results_dir = 'test_data/tso500_test'
			tso500 = TSO500_pipeline.TSO500_DNA(results_dir = 'test_data/tso500_test/',
																sample_completed_files= ['*variants.tsv', '*_coverage.json'],
																sample_valid_files = [ 'DNA_QC_combined.txt'],
																run_completed_files =['contamination-*.csv'],
																run_expected_files=['DNA_QC_combined.txt','completed_samples.txt' ],
																metrics_file=['DNA_QC_combined.txt'],
																run_id = 'run1',
																sample_names = ['Sample1', 'Sample2', 'Sample3', 'NTC-worksheet2'])


			#run complete
			run_complete= tso500.run_is_complete()
			self.assertEqual(run_complete, True)


			#run complete
			run_valid= tso500.run_is_valid()
			self.assertEqual(run_valid, True)
		
		
			#samples complete
			sample_complete=tso500.sample_is_complete(sample='Sample1')
			self.assertEqual(sample_complete, True)

			sample_complete=tso500.sample_is_complete(sample='Sample2')
			self.assertEqual(sample_complete, False)

			sample_complete=tso500.sample_is_complete(sample='Sample3')
			self.assertEqual(sample_complete, False)

			sample_complete=tso500.sample_is_complete(sample='NTC-worksheet2')
			self.assertEqual(sample_complete, True)



			#samples valid
			sample_valid=tso500.sample_is_valid(sample='Sample1')
			self.assertEqual(sample_valid, True)

			sample_valid=tso500.sample_is_valid(sample='Sample2')
			self.assertEqual(sample_valid, True)

			sample_valid=tso500.sample_is_valid(sample='Sample3')
			self.assertEqual(sample_valid, False)

			sample_valid=tso500.sample_is_valid(sample='NTC-worksheet2')
			self.assertEqual(sample_valid, True)


			#ntc contamination
			ntc_contamination=tso500.ntc_contamination()
			self.assertEqual(ntc_contamination.get('Sample1'), 81)
			self.assertEqual(ntc_contamination.get('Sample2'), 0)
			self.assertEqual(ntc_contamination.get('Sample3'), 0)





			results_dir = 'test_data/tso500_test'
			tso500 = TSO500_pipeline.TSO500_RNA(results_dir = 'test_data/tso500_test/',
																sample_completed_files = ['*_fusion_check.csv'],
																sample_valid_files = ['RNA_QC_combined.txt'],
																run_completed_files =['contamination-*.csv'],
																run_expected_files=['RNA_QC_combined.txt', 'contamination-*.csv' ,'completed_samples.txt'],
																metrics_file=['RNA_QC_combined.txt'],
																sample_names = ['Sample4', 'Sample5', 'Sample6', 'NTC-worksheet1'],
																run_id = 'run1'
																)




			#run complete
			run_complete= tso500.run_is_complete()
			self.assertEqual(run_complete, True)

			#run valid
			run_valid= tso500.run_is_valid()
			self.assertEqual(run_valid, True)


			#sample complete RNA
			sample_complete=tso500.sample_is_complete(sample='Sample4')
			self.assertEqual(sample_complete, True)

			sample_complete=tso500.sample_is_complete(sample='Sample5')
			self.assertEqual(sample_complete, False)


			sample_complete=tso500.sample_is_complete(sample='Sample6')
			self.assertEqual(sample_complete, False)

			sample_complete=tso500.sample_is_complete(sample='NTC-worksheet1')
			self.assertEqual(sample_complete, True)


			#sample valid RNA
			sample_valid=tso500.sample_is_valid(sample='Sample4')
			self.assertEqual(sample_valid, True)                            

			sample_valid=tso500.sample_is_valid(sample='Sample5')                                                                                                             
			self.assertEqual(sample_valid, False)


			sample_valid=tso500.sample_is_valid(sample='Sample6')
			self.assertEqual(sample_valid, True)

			sample_valid=tso500.sample_is_valid(sample='NTC-worksheet1')
			self.assertEqual(sample_valid, False)


			#reads RNA
			reads=tso500.get_reads()
			self.assertEqual(reads, {'NTC-worksheet1': None, 'Sample4': None, 'Sample5': 5000, 'Sample6': 28146104})








			#check DNA run level checks fail

			results_dir = 'test_data/tso500_test'
			tso500 = TSO500_pipeline.TSO500_DNA(results_dir = 'test_data/tso500_test/',
																sample_completed_files= ['*variants.tsv', '*_coverage.json'],
																sample_valid_files = [ 'DNA_QC_combined.txt'],
																run_completed_files =['contamination-*.csv'],
																run_expected_files=['DNA_QC_combined.txt','completed_samples.txt' ],
																metrics_file=['DNA_QC_combined.txt'],
																run_id = 'run2',
																sample_names = ['Sample1', 'Sample2', 'Sample3', 'NTC-worksheet2'])


			#run complete
			run_complete= tso500.run_is_complete()
			self.assertEqual(run_complete, False)


			#run complete
			run_valid= tso500.run_is_valid()
			self.assertEqual(run_valid, False)



			#check RNA run level checks fail

			results_dir = 'test_data/tso500_test'
			tso500 = TSO500_pipeline.TSO500_RNA(results_dir = 'test_data/tso500_test/',
																sample_completed_files = ['*_fusion_check.csv'],
																sample_valid_files = ['RNA_QC_combined.txt'],
																run_completed_files =['contamination-*.csv'],
																run_expected_files=['RNA_QC_combined.txt', 'contamination-*.csv' ,'completed_samples.txt'],
																metrics_file=['RNA_QC_combined.txt'],
																sample_names = ['Sample4', 'Sample5', 'Sample6', 'NTC-worksheet1'],
																run_id = 'run2'
																)

			#run complete
			run_complete= tso500.run_is_complete()
			self.assertEqual(run_complete, False)

			#run valid
			run_valid= tso500.run_is_valid()
			self.assertEqual(run_valid, False)


