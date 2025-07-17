from django.test import TestCase
import unittest

from qc_database.models import AnalysisType, CNVMetrics, Pipeline, Run, RunAnalysis, Sample, SampleAnalysis, WorkSheet, DragenCNVMetrics, DragenWGSCoverageMetrics, CustomCoverageMetrics
from pipelines.parsers import parse_exome_postprocessing_cnv_qc_metrics, parse_dragen_cnv_metrics_file

class TestParseCNVQC(unittest.TestCase):
    
    def setUp(self):

        self.test_data = "qc_database/tests/test_data/test.cnv_qc_report.csv"

    def test_parse_dragen_cnv_qc_metrics(self):
        expected = {
            "sample1": {
                "max_corr": "0.99583",
                "max_over_threshold": "True",
                "n_over_threshold": "61",
                "cnv_fail": "False",
                "exome_depth_xcount": "13",
                "manta_xcount": "1",
                "manta_count": "102",
                "exome_depth_count": "459",
                "exome_depth_autosomal_reference_count": "8",
                "exome_depth_x_reference_count": "3"
                },
            "sample2": {
                "max_corr": "0.99694",
                "max_over_threshold": "True",
                "n_over_threshold": "86",
                "cnv_fail": "False",
                "exome_depth_xcount": "2",
                "manta_xcount": "1",
                "manta_count": "107",
                "exome_depth_count": "73",
                "exome_depth_autosomal_reference_count": "7",
                "exome_depth_x_reference_count": "1"
                }
        }
        result = parse_exome_postprocessing_cnv_qc_metrics(self.test_data)
        self.assertEqual(expected, result)

class TestCNVModels(TestCase):

    def setUp(self):

        Run.objects.create(
            run_id = "230307_TEST"
        )
        self.run_obj = Run.objects.get(run_id="230307_TEST")

        Sample.objects.create(
            sample_id = "TEST_SAMPLE"
        )
        self.sample_obj = Sample.objects.get(sample_id="TEST_SAMPLE")

        Pipeline.objects.create(
            pipeline_id = "DragenGE-master"
        )
        self.pipeline_obj = Pipeline.objects.get(pipeline_id="DragenGE-master")

        AnalysisType.objects.create(
            analysis_type_id = "NonocusWES38"
        )
        self.analysis_type_obj = AnalysisType.objects.get(analysis_type_id="NonocusWES38")

        WorkSheet.objects.create(
            worksheet_id = "TEST_WORKSHEET"
        )
        self.worksheet_obj = WorkSheet.objects.get(worksheet_id="TEST_WORKSHEET")

        RunAnalysis.objects.create(
            run=self.run_obj,
            pipeline=self.pipeline_obj,
            analysis_type=self.analysis_type_obj,
            max_cnv_calls=300
        )

        SampleAnalysis.objects.create(
            sample=self.sample_obj,
            run=self.run_obj,
            pipeline=self.pipeline_obj,
            analysis_type=self.analysis_type_obj,
            worksheet=self.worksheet_obj,
            results_completed=True,
            results_valid=True,
            sex="male",
            contamination_cutoff=10,
            ntc_contamination_cutoff=10,
            max_cnvs_called_cutoff=300,
            min_average_coverage_cutoff=80,
        )
        self.sample_analysis_obj = SampleAnalysis.objects.get(sample=self.sample_obj)

        CNVMetrics.objects.create(
            sample_analysis=self.sample_analysis_obj,
            max_corr=0.99583,
            max_over_threshold=True,
            n_over_threshold=61,
            cnv_fail=False,
            exome_depth_xcount=13,
            manta_xcount=1,
            manta_count=102,
            exome_depth_count=459,
            exome_depth_autosomal_reference_count=8,
            exome_depth_x_reference_count=4
        )
        self.dragen_cnv_metrics_obj = CNVMetrics.objects.get(sample_analysis=self.sample_analysis_obj)

        CustomCoverageMetrics.objects.create(
            sample_analysis=self.sample_analysis_obj,
            mean_depth=100,
            min_depth=100,
            max_depth=100,
            stddev_depth=0.1,
            pct_greater_20x=0.99,
            pct_greater_30x=0.99,
            pct_greater_250x=0.99,
            pct_greater_160x=0.99
        )
        self.custom_cov_metrics = CustomCoverageMetrics.objects.get(sample_analysis=self.sample_analysis_obj)

    def test_get_exome_cnv_qc_metrics(self):
        max_over_threshold, cnv_fail, total_cnv_count, autosomal_reference_count, x_reference_count = self.sample_analysis_obj.get_exome_cnv_qc_metrics()
        expected_total_cnv_count = 472
        expected_autosomal_reference_count = 8
        expected_x_reference_count = 4
        self.assertTrue(max_over_threshold)
        self.assertFalse(cnv_fail)
        self.assertEqual(total_cnv_count, expected_total_cnv_count)
        self.assertEqual(autosomal_reference_count, expected_autosomal_reference_count)
        self.assertEqual(x_reference_count, expected_x_reference_count)

    def test_passes_cnv_calling_pass(self):
        # update CNVMetrics object so exome depth count is in pass range
        CNVMetrics.objects.filter(sample_analysis=self.sample_analysis_obj).update(exome_depth_count=150)
        passes_cnv_calling = self.sample_analysis_obj.passes_cnv_calling()
        self.assertTrue(passes_cnv_calling)

    def test_passes_cnv_calling_correlation_fail(self):
        # update CNVMetrics object so max_over_threshold causes an overall fail
        CNVMetrics.objects.filter(sample_analysis=self.sample_analysis_obj).update(max_over_threshold=False)
        passes_cnv_calling = self.sample_analysis_obj.passes_cnv_calling()
        self.assertFalse(passes_cnv_calling)

    def test_passes_cnv_calling_cnv_fail_fail(self):
        # update CNVMetrics object so cnv_fail causes an overall fail
        CNVMetrics.objects.filter(sample_analysis=self.sample_analysis_obj).update(cnv_fail=True)
        passes_cnv_calling = self.sample_analysis_obj.passes_cnv_calling()
        self.assertFalse(passes_cnv_calling)

    def test_passes_cnv_calling_variant_count_fail(self):
        passes_cnv_calling = self.sample_analysis_obj.passes_cnv_calling()
        self.assertFalse(passes_cnv_calling)

    def test_passes_cnv_calling_autosomal_reference_count_fail(self):
        # update CNVMetrics object so exome_depth_autosomal_reference_count causes an overall fail
        CNVMetrics.objects.filter(sample_analysis=self.sample_analysis_obj).update(exome_depth_autosomal_reference_count=1)
        passes_cnv_calling = self.sample_analysis_obj.passes_cnv_calling()
        self.assertFalse(passes_cnv_calling)

    def test_passes_cnv_calling_x_reference_count_fail(self):
        # update CNVMetrics object so exome_depth_x_reference_count causes an overall fail
        CNVMetrics.objects.filter(sample_analysis=self.sample_analysis_obj).update(exome_depth_x_reference_count=1)
        passes_cnv_calling = self.sample_analysis_obj.passes_cnv_calling()
        self.assertFalse(passes_cnv_calling)

    def test_passes_cnv_coverage(self):
        passes_cnv_cov = self.sample_analysis_obj.passes_average_coverage()
        self.assertTrue(passes_cnv_cov)

    def test_fails_cnv_coverage(self):
        CustomCoverageMetrics.objects.filter(sample_analysis=self.sample_analysis_obj).update(mean_depth=50)
        passes_cnv_cov = self.sample_analysis_obj.passes_average_coverage()
        self.assertFalse(passes_cnv_cov)

class TestWGSCNVQC(unittest.TestCase):
    
    def setUp(self):

        self.test_data_1 = "qc_database/tests/test_data/wgs_test1.cnv_metrics.csv"
        self.test_data_2 = "qc_database/tests/test_data/wgs_test2.cnv_metrics.csv"

    def test_parse_wgs_cnv_qc_metrics(self):
        """
        Test that WGS CNV metrics files are being parsed correctly
        """
        expected_1 = {
            "bases_in_reference_genome":"3215250450",
            "average_alignment_coverage_over_genome":"26.65",
            "number_of_alignment_records":"620819033",
            "number_of_filtered_records_total":"3423906",
            "number_of_filtered_records_duplicates":"0",
            "number_of_filtered_records_mapq":"1358349",
            "number_of_filtered_records_unmapped":"2065557",
            "number_of_target_intervals":"2430731",
            "number_of_segments":"1564",
            "number_of_amplifications":"149",
            "number_of_deletions":"358",
            "number_of_passing_amplifications":"87",
            "number_of_passing_deletions":"62"
        }
        result_1 = parse_dragen_cnv_metrics_file(self.test_data_1)
        self.assertEqual(expected_1, result_1)
        
        expected_2 = {
            "bases_in_reference_genome":"3215250450",
            "average_alignment_coverage_over_genome":"47.54",
            "number_of_alignment_records":"1096341764",
            "number_of_filtered_records_total":"6518876",
            "number_of_filtered_records_duplicates":"0",
            "number_of_filtered_records_mapq":"2246715",
            "number_of_filtered_records_unmapped":"4272161",
            "number_of_target_intervals":"2430731",
            "number_of_segments":"1700",
            "number_of_amplifications":"140",
            "number_of_deletions":"530",
            "number_of_passing_amplifications":"79",
            "number_of_passing_deletions":"62"
        }
        result_2 = parse_dragen_cnv_metrics_file(self.test_data_2)
        self.assertEqual(expected_2, result_2)

class test_WGS_cnv_checks(unittest.TestCase):  

    def setUp(self):
 
        Run.objects.create(
            run_id = "TEST_RUN"
        )
        self.run_obj = Run.objects.get(run_id="TEST_RUN")

        Sample.objects.create(
            sample_id = "sample_1"
        )
        self.sample1_obj = Sample.objects.get(sample_id="sample_1")
        
        Sample.objects.create(
            sample_id = "sample_2"
        )
        self.sample2_obj = Sample.objects.get(sample_id="sample_2")
        
        Sample.objects.create(
            sample_id = "sample_3"
        )
        self.sample3_obj = Sample.objects.get(sample_id="sample_3")

        Pipeline.objects.create(
            pipeline_id = "DragenWGS-master"
        )
        self.pipeline_obj = Pipeline.objects.get(pipeline_id="DragenWGS-master")

        AnalysisType.objects.create(
            analysis_type_id = "WGS"
        )
        self.analysis_type_obj = AnalysisType.objects.get(analysis_type_id="WGS")

        WorkSheet.objects.create(
            worksheet_id = "TEST_WORKSHEET"
        )
        self.worksheet_obj = WorkSheet.objects.get(worksheet_id="TEST_WORKSHEET")

        RunAnalysis.objects.create(
            run=self.run_obj,
            pipeline=self.pipeline_obj,
            analysis_type=self.analysis_type_obj,
            min_cnv_calls=50,
            max_cnv_calls=300,
            min_average_coverage_cutoff=30
        )

        SampleAnalysis.objects.create(
            sample=self.sample1_obj,
            run=self.run_obj,
            pipeline=self.pipeline_obj,
            analysis_type=self.analysis_type_obj,
            worksheet=self.worksheet_obj,
            results_completed=True,
            results_valid=True,
            sex="male",
            contamination_cutoff=10,
            ntc_contamination_cutoff=10,
            min_cnvs_called_cutoff=50,
            max_cnvs_called_cutoff=300,
            min_average_coverage_cutoff=30
        )
        self.sample_analysis_obj_1 = SampleAnalysis.objects.get(sample=self.sample1_obj)
        
        SampleAnalysis.objects.create(
            sample=self.sample2_obj,
            run=self.run_obj,
            pipeline=self.pipeline_obj,
            analysis_type=self.analysis_type_obj,
            worksheet=self.worksheet_obj,
            results_completed=True,
            results_valid=True,
            sex="male",
            contamination_cutoff=10,
            ntc_contamination_cutoff=10,
            min_cnvs_called_cutoff=50,
            max_cnvs_called_cutoff=300,
            min_average_coverage_cutoff=30
        )
        self.sample_analysis_obj_2 = SampleAnalysis.objects.get(sample=self.sample2_obj) 
        
        SampleAnalysis.objects.create(
            sample=self.sample3_obj,
            run=self.run_obj,
            pipeline=self.pipeline_obj,
            analysis_type=self.analysis_type_obj,
            worksheet=self.worksheet_obj,
            results_completed=True,
            results_valid=True,
            sex="male",
            contamination_cutoff=10,
            ntc_contamination_cutoff=10,
            min_cnvs_called_cutoff=50,
            max_cnvs_called_cutoff=300,
            min_average_coverage_cutoff=30
        )
        self.sample_analysis_obj_3 = SampleAnalysis.objects.get(sample=self.sample3_obj)  
        
        DragenCNVMetrics.objects.create(
            sample_analysis = self.sample_analysis_obj_1,
            average_alignment_coverage_over_genome = 26.65,
            number_of_passing_amplifications = 87,
            number_of_passing_deletions = 62
        )
        self.dragen_cnv_metrics_1 = DragenCNVMetrics.objects.get(sample_analysis=self.sample_analysis_obj_1)
        
        DragenWGSCoverageMetrics.objects.create(
            sample_analysis = self.sample_analysis_obj_1,
            average_alignment_coverage_over_genome = 26.65,
        )
        self.dragen_cov_metrics_1 = DragenWGSCoverageMetrics.objects.get(sample_analysis=self.sample_analysis_obj_1)
        
        DragenCNVMetrics.objects.create(
            sample_analysis = self.sample_analysis_obj_2,
            average_alignment_coverage_over_genome = 47.54,
            number_of_passing_amplifications = 200,
            number_of_passing_deletions = 200
        )
        self.dragen_cnv_metrics_2 = DragenCNVMetrics.objects.get(sample_analysis=self.sample_analysis_obj_2)
        
        DragenWGSCoverageMetrics.objects.create(
            sample_analysis = self.sample_analysis_obj_2,
            average_alignment_coverage_over_genome = 47.54,
        )
        self.dragen_cov_metrics_2 = DragenWGSCoverageMetrics.objects.get(sample_analysis=self.sample_analysis_obj_2)
        
        DragenCNVMetrics.objects.create(
            sample_analysis = self.sample_analysis_obj_3,
            average_alignment_coverage_over_genome = 47.54,
            number_of_passing_amplifications = 10,
            number_of_passing_deletions = 10
        )
        self.dragen_cnv_metrics_3 = DragenCNVMetrics.objects.get(sample_analysis=self.sample_analysis_obj_3)
        
        DragenWGSCoverageMetrics.objects.create(
            sample_analysis = self.sample_analysis_obj_3,
            average_alignment_coverage_over_genome = 47.54,
        )
        self.dragen_cov_metrics_3 = DragenWGSCoverageMetrics.objects.get(sample_analysis=self.sample_analysis_obj_3)
    
    def test_cnv_checks(self):
        """
        Test that CNV metrics populate models correctly and tests pass/fail as expected
        """
        #Fail as <30
        passes_cnv_coverage_1 = self.sample_analysis_obj_1.passes_average_coverage()
        self.assertFalse(passes_cnv_coverage_1)
	
	#Pass as >30
        passes_cnv_coverage_2 = self.sample_analysis_obj_2.passes_average_coverage()
        self.assertTrue(passes_cnv_coverage_2)
        
        #Pass as between 50-300
        passes_cnv_count_1 = self.sample_analysis_obj_1.passes_cnv_count()
        self.assertTrue(passes_cnv_count_1)
        
        #Fail as >300
        passes_cnv_count_2 = self.sample_analysis_obj_2.passes_cnv_count()
        self.assertFalse(passes_cnv_count_2)
        
        #Fail as <50
        passes_cnv_count_3 = self.sample_analysis_obj_3.passes_cnv_count()
        self.assertFalse(passes_cnv_count_3)

if __name__ == "__main__":
    unittest.main()
