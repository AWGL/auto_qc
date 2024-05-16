import unittest
from collections import OrderedDict
from utils import GlimsSample

class TestGlimsSample(unittest.TestCase):
    
    def setUp(self):
        self.sample = OrderedDict([("LABNO", "24-1331-A-02-01"), ("POSITION", "12"), ("WORKSHEET", "24-TSOSEQ-29"), ("TEST", "TSO500RNA"), 
                                   ("COMMENTS", ""), ("UPDATEDDATE", ""), ("REASON_FOR_REFERRAL", "M1"), ("FIRSTNAME", ""), ("LASTNAME", ""), 
                                   ("SEX", "F"), ("INDEX_WELL", "A-B4"), ("I5_INDEX", "UDP0012"), ("I5_SEQ", "CGCTCCACGA"), ("I7_INDEX", "UDP0012"), 
                                   ("I7_SEQ", "GAACTGAGCG"), ("AFFECTED", ""), ("FAMILY_ID", ""), ("FAMILY_POS", ""), ("HPO_TERMS", "")])

    def test_create_glims_sample(self):
        expected_dict = {"lab_no": "24-1331-A-02-01", "position": "12", "worksheet": "24-TSOSEQ-29", "test": "TSO500RNA", "reason_for_referral": "M1", 
                         "sex": "F", "index_well": "A-B4", "i5_index": "UDP0012", "i5_seq": "CGCTCCACGA", "i7_index": "UDP0012", "i7_seq": "GAACTGAGCG", 
                         "affected": "", "family_id": "", "family_pos": "", "hpo_terms": ""}
        glims_sample = GlimsSample(self.sample)
        self.assertEqual(expected_dict, glims_sample.__dict__)

    def test_parse_lab_no(self):
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

    def test_parse_sex(self):
        # Check M is set to 1
        parsed_sex = GlimsSample.parse_sex("M")
        self.assertEqual(parsed_sex, "1")

        # Check F is set to 2
        parsed_sex = GlimsSample.parse_sex("F")
        self.assertEqual(parsed_sex, "F")

        # Check nothing is set to 0
        parsed_sex = GlimsSample.parse_sex("")
        self.assertEqual(parsed_sex, "0")

        # Check other (e.g. X) is set to 0
        parsed_sex = GlimsSample.parse_sex("X")
        self.assertEqual(parsed_sex, "0")

    def tearDown(self):
        pass

if __name__ == "__main__":
    unittest.main()