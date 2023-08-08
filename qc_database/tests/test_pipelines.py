import unittest
from pipelines import nextflow_pipelines, somatic_pipelines, dragen_pipelines, TSO500_pipeline, ctDNA_pipeline


class TestPipelineMonitoring(unittest.TestCase):

	

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
				  								sample_not_expected_files= ['*_fastqc.zip'],
				  								run_expected_files = ['*CRM.xlsx'],
				  								run_not_expected_files= []


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
                  								sample_not_expected_files= ['*_fastqc.zip'],
                  								run_expected_files = ['*merged_coverage_report.txt',
                  													'*merged_variant_report.txt',
                        											],
                        						run_not_expected_files= []
				)

			run_complete = somatic_amplicon.run_is_valid()

			self.assertEqual(run_complete, True)


	def test_tso500(self):


			results_dir = 'test_data/tso500_test/run1'
			tso500 = TSO500_pipeline.TSO500_DNA(results_dir = 'test_data/tso500_test/run1',
																sample_completed_files= ['*variants.tsv', '*_coverage.json'],
																sample_valid_files = [],
																run_completed_files =['post_processing_finished.txt'],
																run_expected_files=[],
																metrics_file=['*_ntc_cont.txt','*_fastqc_status.txt','_read_number.txt'],
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
			self.assertEqual(sample_valid, True)

			sample_valid=tso500.sample_is_valid(sample='NTC-worksheet2')
			self.assertEqual(sample_valid, True)


			#ntc contamination
			ntc_contamination=tso500.ntc_contamination()
			self.assertEqual(ntc_contamination[0].get('Sample1'), 81)
			self.assertEqual(ntc_contamination[1].get('Sample1'), 11)
			self.assertEqual(ntc_contamination[2].get('Sample1'), 574)
			self.assertEqual(ntc_contamination[3].get('Sample1'), 1)

			self.assertEqual(ntc_contamination[0].get('Sample2'), 0)
			self.assertEqual(ntc_contamination[1].get('Sample2'), 130596554)
			self.assertEqual(ntc_contamination[2].get('Sample2'), 5736)
			self.assertEqual(ntc_contamination[3].get('Sample2'), 0)

			self.assertEqual(ntc_contamination[0].get('Sample3'), 0)
			self.assertEqual(ntc_contamination[1].get('Sample3'), 5000)
			self.assertEqual(ntc_contamination[2].get('Sample3'), 4763)
			self.assertEqual(ntc_contamination[3].get('Sample3'), 0)

			self.assertEqual(ntc_contamination[0].get('NTC-worksheet2'), 100)
			self.assertEqual(ntc_contamination[1].get('NTC-worksheet2'), 9)
			self.assertEqual(ntc_contamination[2].get('NTC-worksheet2'), 6)
			self.assertEqual(ntc_contamination[3].get('NTC-worksheet2'), 100)


			results_dir = 'test_data/tso500_test/run1'
			tso500 = TSO500_pipeline.TSO500_RNA(results_dir = 'test_data/tso500_test/run1',
																sample_completed_files = ['*_fusion_check.csv'],
																sample_valid_files = ['RNA_QC_combined.txt'],
																run_completed_files =['run_complete.txt'],
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

			results_dir = 'test_data/tso500_test/run2'
			tso500 = TSO500_pipeline.TSO500_DNA(results_dir = 'test_data/tso500_test/run2',
																sample_completed_files= ['*variants.tsv', '*_coverage.json'],
																sample_valid_files = [],
																run_completed_files =['post_processing_finished.txt'],
																run_expected_files=[],
																metrics_file=['*_ntc_cont.txt','*_fastqc_status.txt','_read_number.txt'],
																run_id = 'run2',
																sample_names = ['Sample1', 'Sample2', 'Sample3', 'NTC-worksheet2'])


			#run complete
			run_complete= tso500.run_is_complete()
			self.assertEqual(run_complete, False)


			#run complete
			run_valid= tso500.run_is_valid()
			self.assertEqual(run_valid, False)



			#check RNA run level checks fail

			results_dir = 'test_data/tso500_test/run2'
			tso500 = TSO500_pipeline.TSO500_RNA(results_dir = 'test_data/tso500_test/run2',
																sample_completed_files = ['*_fusion_check.csv'],
																sample_valid_files = ['RNA_QC_combined.txt'],
																run_completed_files =['run_complete.txt'],
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
			
	def test_ctDNA(self):


			results_dir = 'test_data/ctDNA_test'
			ctDNA = ctDNA_pipeline.TSO500_ctDNA(results_dir = 'test_data/ctDNA_test/',
																sample_completed_files= ['*_fusion_check.csv', '*_variants.tsv', '*_coverage.json'],
																run_completed_files =['postprocessing_complete.txt'],
																metrics_file=['QC_combined.txt'],
																run_id = 'run1',
																sample_names = ['Sample1', 'Sample2', 'Sample3', 'NTC-TEST'])


			#run complete
			run_complete= ctDNA.run_is_complete()
			self.assertEqual(run_complete, True)
		
		
			#samples complete
			sample_complete=ctDNA.sample_is_complete(sample='Sample1')
			self.assertEqual(sample_complete, True)

			sample_complete=ctDNA.sample_is_complete(sample='Sample2')
			self.assertEqual(sample_complete, True)

			sample_complete=ctDNA.sample_is_complete(sample='Sample3')
			self.assertEqual(sample_complete, False)

			sample_complete=ctDNA.sample_is_complete(sample='NTC-TEST')
			self.assertEqual(sample_complete, True)

			#samples valid
			sample_valid=ctDNA.sample_is_valid(sample='Sample1')
			self.assertEqual(sample_valid, True)

			sample_valid=ctDNA.sample_is_valid(sample='Sample2')
			self.assertEqual(sample_valid, True)

			sample_valid=ctDNA.sample_is_valid(sample='Sample3')
			self.assertEqual(sample_valid, False)

			sample_valid=ctDNA.sample_is_valid(sample='NTC-TEST')
			self.assertEqual(sample_valid, True)


			#ntc contamination
			ntc_contamination=ctDNA.ntc_contamination()
			self.assertEqual(ntc_contamination[0].get('Sample1'), 98449907)
			self.assertEqual(ntc_contamination[1].get('Sample1'), 0)

			self.assertEqual(ntc_contamination[0].get('Sample2'), 500)
			self.assertEqual(ntc_contamination[1].get('Sample2'), 14)

			self.assertEqual(ntc_contamination[0].get('Sample3'), 66140537)
			self.assertEqual(ntc_contamination[1].get('Sample3'), 0)

			self.assertEqual(ntc_contamination[0].get('NTC-TEST'), 71)
			self.assertEqual(ntc_contamination[1].get('NTC-TEST'), 100)
			
