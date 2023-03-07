from django.test import TestCase
import unittest

from qc_database.models import AnalysisType, DragenCNVMetrics, Pipeline, Run, RunAnalysis, Sample, SampleAnalysis, WorkSheet
from pipelines.parsers import parse_dragen_cnv_qc_metrics

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
        result = parse_dragen_cnv_qc_metrics(self.test_data)
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
            max_cnvs_called_cutoff=300
        )
        self.sample_analysis_obj = SampleAnalysis.objects.get(sample=self.sample_obj)

        DragenCNVMetrics.objects.create(
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
            exome_depth_x_reference_count=3
        )
        self.dragen_cnv_metrics_obj = DragenCNVMetrics.objects.get(sample_analysis=self.sample_analysis_obj)

    def test_get_exome_depth_correlation(self):
        max_over_threshold = self.sample_analysis_obj.get_exome_depth_correlation()
        self.assertTrue(max_over_threshold)

    def test_get_cnv_fail(self):
        cnv_fail = self.sample_analysis_obj.get_cnv_fail()
        self.assertFalse(cnv_fail)

    def test_get_exome_depth_variant_count(self):
        exome_depth_variant_count = self.sample_analysis_obj.get_exome_depth_variant_count()
        expected_variant_count = 472
        self.assertEqual(exome_depth_variant_count, expected_variant_count)
    
    def test_get_exome_depth_autosomal_reference_count(self):
        autosomal_reference_count = self.sample_analysis_obj.get_exome_depth_autosomal_reference_count()
        expected_autosomal_reference_count = 8
        self.assertEqual(autosomal_reference_count, expected_autosomal_reference_count)

    def test_exome_depth_x_reference_count(self):
        x_reference_count = self.sample_analysis_obj.get_exome_depth_x_reference_count()
        expected_x_reference_count = 3
        self.assertEqual(x_reference_count, expected_x_reference_count)

    def test_passes_cnv_calling_pass(self):
        DragenCNVMetrics.objects.filter(sample_analysis=self.sample_analysis_obj).update(exome_depth_count=150)
        passes_cnv_calling = self.sample_analysis_obj.passes_cnv_calling()
        self.assertTrue(passes_cnv_calling)

    def test_passes_cnv_calling_correlation_fail(self):
        DragenCNVMetrics.objects.filter(sample_analysis=self.sample_analysis_obj).update(max_over_threshold=False)
        passes_cnv_calling = self.sample_analysis_obj.passes_cnv_calling()
        self.assertFalse(passes_cnv_calling)

    def test_passes_cnv_calling_cnv_fail_fail(self):
        DragenCNVMetrics.objects.filter(sample_analysis=self.sample_analysis_obj).update(cnv_fail=True)
        passes_cnv_calling = self.sample_analysis_obj.passes_cnv_calling()
        self.assertFalse(passes_cnv_calling)

    def test_passes_cnv_calling_variant_count_fail(self):
        passes_cnv_calling = self.sample_analysis_obj.passes_cnv_calling()
        self.assertFalse(passes_cnv_calling)

    def test_passes_cnv_calling_autosomal_reference_count_fail(self):
        DragenCNVMetrics.objects.filter(sample_analysis=self.sample_analysis_obj).update(exome_depth_autosomal_reference_count=1)
        passes_cnv_calling = self.sample_analysis_obj.passes_cnv_calling()
        self.assertFalse(passes_cnv_calling)

    def test_passes_cnv_calling_x_reference_count_fail(self):
        DragenCNVMetrics.objects.filter(sample_analysis=self.sample_analysis_obj).update(exome_depth_x_reference_count=1)
        passes_cnv_calling = self.sample_analysis_obj.passes_cnv_calling()
        self.assertFalse(passes_cnv_calling)

if __name__ == "__main__":
    unittest.main()
