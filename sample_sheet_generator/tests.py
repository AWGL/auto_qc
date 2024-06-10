#import unittest
from collections import OrderedDict
from django.test import TestCase
from sample_sheet_generator.utils import Assay, GlimsSample

class TestGlimsSample(TestCase):

    fixtures = ["sample_sheet_generator/fixtures/assays.json"]
    
    def setUp(self):

        self.sample = OrderedDict([("LABNO", "24-1331-A-02-01"), ("POSITION", "12"), ("WORKSHEET", "24-TSOSEQ-29"), ("TEST", "TSO500RNA"), 
                                   ("COMMENTS", ""), ("UPDATEDDATE", ""), ("REASON_FOR_REFERRAL", "M1"), ("FIRSTNAME", ""), ("LASTNAME", ""), 
                                   ("SEX", "F"), ("INDEX_WELL", "A-B4"), ("I5_INDEX", "UDP0012"), ("I5_SEQ", "CGCTCCACGA"), ("I7_INDEX", "UDP0012"), 
                                   ("I7_SEQ", "GAACTGAGCG"), ("AFFECTED", "affected"), ("FAMILY_ID", "FAM001"), ("FAMILY_POS", "Proband"), ("HPO_TERMS", "HPO1;HPO2"), ("ROUTINE", "R")])

    def test_create_glims_sample(self):
        self.maxDiff = None
        assay = Assay.objects.get(pk="TSO500RNA")
        expected_dict = {"lab_no": "24-1331-A-02-01", "position": "12", "worksheet": "24-TSOSEQ-29", "test": "TSO500RNA", "reason_for_referral": "M1", 
                         "sex": "F", "index_well": "A-B4", "i5_index": "UDP0012", "i5_seq": "CGCTCCACGA", "i7_index": "UDP0012", "i7_seq": "GAACTGAGCG", 
                         "affected": "affected", "family_id": "FAM001", "family_pos": "Proband", "hpo_terms": "HPO1;HPO2", "urgency": "R", "assay": assay,
                         "header_line": "Sample_ID,Sample_Plate,Sample_Well,Index_ID,index,index2,Sample_Name,Pair_ID,Sample_Type,Description",
                         "samplesheet_line": "24-1331-A-02-01,24-TSOSEQ-29-TSO500RNA,A-B4,UDP0012,GAACTGAGCG,CGCTCCACGA,24-1331-A-02-01,24-1331-A-02-01,RNA,pipelineName=TSO500;pipelineVersion=master;referral=M1"}
        glims_sample = GlimsSample(self.sample)
        self.assertEqual(expected_dict, glims_sample.__dict__)

    def test_parse_lab_no(self):
        self.maxDiff = None

        # test sample in WGS is unchanged
        parsed_lab_no = GlimsSample.parse_lab_no("24-1331-A-02-01", "WGS")
        self.assertEqual(parsed_lab_no, "24-1331-A-02-01")

        # test NTC in WGS is unchanged
        parsed_lab_no = GlimsSample.parse_lab_no("NTC-24-WGSSEQ-30", "WGS")
        self.assertEqual(parsed_lab_no, "NTC-24-WGSSEQ-30")

        # test sample in TSO is unchanged
        parsed_lab_no = GlimsSample.parse_lab_no("24-1331-A-02-01", "TSO500DNA")
        self.assertEqual(parsed_lab_no, "24-1331-A-02-01")

        # test NTC in TSO is changed
        parsed_lab_no = GlimsSample.parse_lab_no("NTC-24-TSOSEQ-30", "TSO500DNA")
        self.assertEqual(parsed_lab_no, "NTC-24-TSOSEQ-30-TSO500DNA")

    def test_parse_worksheet(self):
        self.maxDiff = None
        
        # check TSO500 DNA is renamed
        parsed_worksheet = GlimsSample.parse_worksheet("TSO500DNA", "24-TSOSEQ-30")
        self.assertEqual(parsed_worksheet, "24-TSOSEQ-30-TSO500DNA")

        # check TSO500 RNA is renamed
        parsed_worksheet = GlimsSample.parse_worksheet("TSO500RNA", "24-TSOSEQ-30")
        self.assertEqual(parsed_worksheet, "24-TSOSEQ-30-TSO500RNA")

        # check TSO500 ctDNA is renamed
        parsed_worksheet = GlimsSample.parse_worksheet("TSO500CTDNA", "24-TSOSEQ-30")
        self.assertEqual(parsed_worksheet, "24-TSOSEQ-30-ctDNA")

        # check BRCA is renamed
        parsed_worksheet = GlimsSample.parse_worksheet("NGS GR BC", "24-GRD3POOL-30")
        self.assertEqual(parsed_worksheet, "24-GRD3POOL-30-BRCA")

        # check CRM is renamed
        parsed_worksheet = GlimsSample.parse_worksheet("NGS GR CRM", "24-GRD3POOL-30")
        self.assertEqual(parsed_worksheet, "24-GRD3POOL-30-CRM")

        # check WGS is not renamed
        parsed_worksheet = GlimsSample.parse_worksheet("WGS", "24-WGSSEQ-30")
        self.assertEqual(parsed_worksheet, "24-WGSSEQ-30")

    def test_parse_referral(self):
        #TODO unit tests for this
        self.maxDiff = None
        pass

    def test_parse_sex(self):
        self.maxDiff = None

        # Check M is set to 1
        parsed_sex = GlimsSample.parse_sex("M")
        self.assertEqual(parsed_sex, "1")

        # Check F is set to 2
        parsed_sex = GlimsSample.parse_sex("F")
        self.assertEqual(parsed_sex, "2")

        # Check nothing is set to 0
        parsed_sex = GlimsSample.parse_sex("")
        self.assertEqual(parsed_sex, "0")

        # Check other (e.g. X) is set to 0
        parsed_sex = GlimsSample.parse_sex("X")
        self.assertEqual(parsed_sex, "0")

    def test_parse_hpo_terms(self):
        self.maxDiff = None

        # if no HPO terms, HPO terms should be set as None
        parsed_hpo_terms = GlimsSample.parse_hpo_terms("")
        self.assertEqual(parsed_hpo_terms, "None")

        # if multiple HPO terms, they should be joined with pipes
        parsed_hpo_terms = GlimsSample.parse_hpo_terms("HPO:123;HPO:456;HPO:789")
        self.assertEqual(parsed_hpo_terms, "HPO:123|HPO:456|HPO:789")

        # if one HPO term, no pipes needed
        parsed_hpo_terms = GlimsSample.parse_hpo_terms("HPO:123")
        self.assertEqual(parsed_hpo_terms, "HPO:123")

    def test_parse_affected(self):
        self.maxDiff = None

        # if 2 or affected, return 2
        affected1 = GlimsSample.parse_affected("2")
        affected2 = GlimsSample.parse_affected("Affected")
        self.assertEqual(affected1, "2")
        self.assertEqual(affected2, "2")

        # if 1 or unaffected, return 1
        unaffected1 = GlimsSample.parse_affected("1")
        unaffected2 = GlimsSample.parse_affected("UNAFFECTED")
        self.assertEqual(unaffected1, "1")
        self.assertEqual(unaffected2, "1")

        # if 0 or missing, return 0
        missing1 = GlimsSample.parse_affected("0")
        missing2 = GlimsSample.parse_affected("missing")
        self.assertEqual(missing1, "0")
        self.assertEqual(missing2, "0")

        # everything else return -9 missing
        other1 = GlimsSample.parse_affected("")
        other2 = GlimsSample.parse_affected("random text")
        self.assertEqual(other1, "-9")
        self.assertEqual(other2, "-9")

    def test_parse_family_structure(self):
        self.maxDiff = None    
        # check different permutaitons of no family structure
        self.assertIsNone(GlimsSample.parse_family_structure("",""))
        self.assertIsNone(GlimsSample.parse_family_structure("none","none"))
        self.assertIsNone(GlimsSample.parse_family_structure("NA","1"))
        self.assertIsNone(GlimsSample.parse_family_structure("N/a","NONE"))

        # proband, family structure doesn't need reformatting
        family_pos, family_description = GlimsSample.parse_family_structure("FAM001", "proband")
        self.assertEqual(family_pos, "proband")
        self.assertEqual(family_description, "familyId=FAM001;paternalId=FAM001-father;maternalId=FAM001-mother")

        # mother, family structure does need reformatting
        family_pos, family_description = GlimsSample.parse_family_structure("2", "mother")
        self.assertEqual(family_pos, "mother")
        self.assertEqual(family_description, "familyId=FAM002")

        # father, family structure does need reformatting
        family_pos, family_description = GlimsSample.parse_family_structure("3", "Dad")
        self.assertEqual(family_pos, "father")
        self.assertEqual(family_description, "familyId=FAM003")

    def test_get_assay(self):
        self.maxDiff = None

        # get TSO500 DNA
        tso500dna = GlimsSample.get_assay("TSO500DNA", "U")
        self.assertEqual(tso500dna, Assay.objects.get(pk="TSO500DNA"))

        # get TSO500 RNA
        tso500rna = GlimsSample.get_assay("TSO500RNA", "R")
        self.assertEqual(tso500rna, Assay.objects.get(pk="TSO500RNA"))

        # get TSO500 ctDNA
        tso500ctdna = GlimsSample.get_assay("TSO500CTDNA", "U")
        self.assertEqual(tso500ctdna, Assay.objects.get(pk="ctDNA"))

        # get BRCA
        brca = GlimsSample.get_assay("NGS GR BC", "routine")
        self.assertEqual(brca, Assay.objects.get(pk="BRCA"))

        # get CRM
        crm = GlimsSample.get_assay("NGS GR CRM", "routine")
        self.assertEqual(crm, Assay.objects.get(pk="CRM"))

        # get TSC
        tsc = GlimsSample.get_assay("NGSTRUAUTO", "R")
        self.assertEqual(tsc, Assay.objects.get(pk="TSC"))

        # get FH
        fh = GlimsSample.get_assay("FHNGS", "R")
        self.assertEqual(fh, Assay.objects.get(pk="FH"))

        # get WES
        wes = GlimsSample.get_assay("WES", "U")
        self.assertEqual(wes, Assay.objects.get(pk="WES"))

        # get WGS
        wgs = GlimsSample.get_assay("WGS", "R")
        self.assertEqual(wgs, Assay.objects.get(pk="WGS"))

        # get FastWGS
        fastwgs = GlimsSample.get_assay("WGS", "U")
        self.assertEqual(fastwgs, Assay.objects.get(pk="FastWGS"))

        # if not an assay, raise an error
        with self.assertRaises(Exception) as context:
            GlimsSample.get_assay("NotAnAssay", "U")
        self.assertEqual(context.exception.args, ("This test is not configured - contact bioinformatics.",))
        
    def test_create_samplesheet_header_tso500dna(self):
        self.maxDiff = None
        expected_header = "Sample_ID,Sample_Plate,Sample_Well,Index_ID,index,index2,Sample_Name,Pair_ID,Sample_Type,Description"
        sample = self.sample
        sample["TEST"] = "TSO500DNA"
        sample_obj = GlimsSample(sample)
        self.assertEqual(sample_obj.create_samplesheet_header(),expected_header)

    def test_create_samplesheet_header_tso500rna(self):
        self.maxDiff = None
        expected_header = "Sample_ID,Sample_Plate,Sample_Well,Index_ID,index,index2,Sample_Name,Pair_ID,Sample_Type,Description"
        sample = self.sample
        sample_obj = GlimsSample(sample)
        self.assertEqual(sample_obj.create_samplesheet_header(),expected_header)

    def test_create_samplesheet_header_tso500ctdna(self):
        self.maxDiff = None
        expected_header = "Sample_ID,Sample_Plate,Sample_Well,I7_Index_ID,index,I5_Index_ID,index2,Sample_Name,Pair_ID,Sample_Type,Description"
        sample = self.sample
        sample["TEST"] = "TSO500CTDNA"
        sample_obj = GlimsSample(sample)
        self.assertEqual(sample_obj.create_samplesheet_header(),expected_header)

    def test_create_samplesheet_header_brca(self):
        self.maxDiff = None
        expected_header = "Sample_ID,Sample_Plate,Sample_Well,I7_Index_ID,index,Sample_Project,Description"
        sample = self.sample
        sample["TEST"] = "NGS GR BC"
        sample_obj = GlimsSample(sample)
        self.assertEqual(sample_obj.create_samplesheet_header(),expected_header)
    
    def test_create_samplesheet_header_crm(self):
        self.maxDiff = None
        expected_header = "Sample_ID,Sample_Plate,Sample_Well,I7_Index_ID,index,Sample_Project,Description"
        sample = self.sample
        sample["TEST"] = "NGS GR CRM"
        sample_obj = GlimsSample(sample)
        self.assertEqual(sample_obj.create_samplesheet_header(),expected_header)

    def test_create_samplesheet_header_tsc(self):
        self.maxDiff = None
        expected_header = "Sample_ID,Sample_Plate,Sample_Well,I7_Index_ID,index,I5_Index_ID,index2,Sample_Project,Description"
        sample = self.sample
        sample["TEST"] = "NGSTRUAUTO"
        sample_obj = GlimsSample(sample)
        self.assertEqual(sample_obj.create_samplesheet_header(),expected_header)

    def test_create_samplesheet_header_fh(self):
        self.maxDiff = None
        expected_header = "Sample_ID,Sample_Plate,Sample_Well,I7_Index_ID,index,I5_Index_ID,index2,Sample_Project,Description"
        sample = self.sample
        sample["TEST"] = "FHNGS"
        sample_obj = GlimsSample(sample)
        self.assertEqual(sample_obj.create_samplesheet_header(),expected_header)

    def test_create_samplesheet_header_wes(self):
        self.maxDiff = None
        expected_header = "Sample_ID,Sample_Plate,Sample_Well,I7_Index_ID,index,I5_Index_ID,index2,Sample_Project,Description"
        sample = self.sample
        sample["TEST"] = "WES"
        sample_obj = GlimsSample(sample)
        self.assertEqual(sample_obj.create_samplesheet_header(),expected_header)

    def test_create_samplesheet_header_wgs(self):
        self.maxDiff = None
        expected_header = "Sample_ID,Sample_Plate,Sample_Well,I7_Index_ID,index,I5_Index_ID,index2,Sample_Project,Description"
        sample = self.sample
        sample["TEST"] = "WGS"
        sample_obj = GlimsSample(sample)
        self.assertEqual(sample_obj.create_samplesheet_header(),expected_header)

    def test_create_samplesheet_header_fastwgs(self):
        self.maxDiff = None
        expected_header = "Sample_ID,Sample_Plate,Sample_Well,I7_Index_ID,index,I5_Index_ID,index2,Sample_Project,Description"
        sample = self.sample
        sample["TEST"] = "WGS"
        sample["ROUTINE"] = "U"
        sample_obj = GlimsSample(sample)
        self.assertEqual(sample_obj.create_samplesheet_header(),expected_header)

    def test_create_samplesheet_line_tso500dna(self):
        self.maxDiff = None
        sample = self.sample
        sample["TEST"] = "TSO500DNA"
        sample_obj = GlimsSample(sample)
        samplesheet_line = sample_obj.create_samplesheet_line()
        expected_line = "24-1331-A-02-01,24-TSOSEQ-29-TSO500DNA,A-B4,UDP0012,GAACTGAGCG,CGCTCCACGA,24-1331-A-02-01,24-1331-A-02-01,DNA,pipelineName=TSO500;pipelineVersion=master;referral=M1"
        self.assertEqual(expected_line, samplesheet_line)

    def test_create_samplesheet_line_tso500rna(self):
        self.maxDiff = None
        sample = self.sample
        sample_obj = GlimsSample(sample)
        samplesheet_line = sample_obj.create_samplesheet_line()
        expected_line = "24-1331-A-02-01,24-TSOSEQ-29-TSO500RNA,A-B4,UDP0012,GAACTGAGCG,CGCTCCACGA,24-1331-A-02-01,24-1331-A-02-01,RNA,pipelineName=TSO500;pipelineVersion=master;referral=M1"
        self.assertEqual(expected_line, samplesheet_line)

    def test_create_samplesheet_line_ctdna(self):
        self.maxDiff = None
        sample = self.sample
        sample["TEST"] = "TSO500CTDNA"
        sample_obj = GlimsSample(sample)
        samplesheet_line = sample_obj.create_samplesheet_line()
        expected_line = "24-1331-A-02-01,24-TSOSEQ-29-ctDNA,12,UDP0012,GAACTGAGCG,UDP0012,CGCTCCACGA,24-1331-A-02-01,24-1331-A-02-01,DNA,pipelineName=tso500_ctdna;pipelineVersion=master;referral=M1"
        self.assertEqual(expected_line, samplesheet_line)

    def test_create_samplesheet_line_brca(self):
        self.maxDiff = None
        sample = self.sample
        sample["TEST"] = "NGS GR BC"
        sample_obj = GlimsSample(sample)
        samplesheet_line = sample_obj.create_samplesheet_line()
        expected_line = "24-1331-A-02-01,24-TSOSEQ-29-BRCA,12,UDP0012,GAACTGAGCG,,Name$SA%panel$NGHS102X%"
        self.assertEqual(expected_line, samplesheet_line)

    def test_create_samplesheet_line_crm(self):
        self.maxDiff = None
        sample = self.sample
        sample["TEST"] = "NGS GR CRM"
        sample_obj = GlimsSample(sample)
        samplesheet_line = sample_obj.create_samplesheet_line()
        expected_line = "24-1331-A-02-01,24-TSOSEQ-29-CRM,12,UDP0012,GAACTGAGCG,,Name$SA%panel$NGHS101X%"
        self.assertEqual(expected_line, samplesheet_line)

    def test_create_samplesheet_line_tsc(self):
        self.maxDiff = None
        sample = self.sample
        sample["TEST"] = "NGSTRUAUTO"
        sample_obj = GlimsSample(sample)
        samplesheet_line = sample_obj.create_samplesheet_line()
        expected_line = "24-1331-A-02-01,24-TSOSEQ-29,12,UDP0012,GAACTGAGCG,UDP0012,CGCTCCACGA,,pipelineName=germline_enrichment_nextflow;pipelineVersion=master;panel=IlluminaTruSightCancer;sex=2;order=12"
        self.assertEqual(expected_line, samplesheet_line)

    def test_create_samplesheet_line_fh(self):
        self.maxDiff = None
        sample = self.sample
        sample["TEST"] = "FHNGS"
        sample_obj = GlimsSample(sample)
        samplesheet_line = sample_obj.create_samplesheet_line()
        expected_line = "24-1331-A-02-01,24-TSOSEQ-29,12,UDP0012,GAACTGAGCG,UDP0012,CGCTCCACGA,,pipelineName=deepvariant_nextflow;pipelineVersion=main;panel=NonacusFH;sex=2;order=12"
        self.assertEqual(expected_line, samplesheet_line)

    def test_create_samplesheet_line_wes(self):
        self.maxDiff = None
        sample = self.sample
        sample["TEST"] = "WES"
        sample_obj = GlimsSample(sample)
        samplesheet_line = sample_obj.create_samplesheet_line()
        expected_line = "24-1331-A-02-01,24-TSOSEQ-29,A-B4,UDP0012,GAACTGAGCG,UDP0012,CGCTCCACGA,,pipelineName=DragenGE;pipelineVersion=master;panel=NonocusWES38;sex=2;order=12;referral=M1;hpoId=HPO1|HPO2;familyId=FAM001;paternalId=FAM001-father;maternalId=FAM001-mother;phenotype=2"
        self.assertEqual(expected_line, samplesheet_line)

    def test_create_samplesheet_line_wgs(self):
        self.maxDiff = None
        sample = self.sample
        sample["TEST"] = "WGS"
        sample_obj = GlimsSample(sample)
        samplesheet_line = sample_obj.create_samplesheet_line()
        expected_line = "24-1331-A-02-01,24-TSOSEQ-29,12,UDP0012,GAACTGAGCG,UDP0012,CGCTCCACGA,,pipelineName=DragenWGS;pipelineVersion=master;panel=WGS;sex=2;order=12;referral=M1;hpoId=HPO1|HPO2;familyId=FAM001;paternalId=FAM001-father;maternalId=FAM001-mother;phenotype=2"
        self.assertEqual(expected_line, samplesheet_line)
    
    def test_create_samplesheet_line_fastwgs(self):
        self.maxDiff = None
        sample = self.sample
        sample["TEST"] = "WGS"
        sample["ROUTINE"] = "U"
        sample_obj = GlimsSample(sample)
        samplesheet_line = sample_obj.create_samplesheet_line()
        expected_line = "24-1331-A-02-01,24-TSOSEQ-29,12,UDP0012,GAACTGAGCG,UDP0012,CGCTCCACGA,,pipelineName=DragenWGS;pipelineVersion=master;panel=FastWGS;sex=2;order=12;referral=M1;hpoId=HPO1|HPO2;familyId=FAM001;paternalId=FAM001-father;maternalId=FAM001-mother;phenotype=2"
        self.assertEqual(expected_line, samplesheet_line)

    def tearDown(self):
        pass

