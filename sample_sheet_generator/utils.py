import csv
from collections import OrderedDict

from glims_fixtures import *

## sample well in current sample sheet is actually the index well

class GlimsSample:
    
    def __init__(self, sample_info: OrderedDict):
        self.lab_no = sample_info["LABNO"]
        self.position = sample_info["POSITION"]
        self.worksheet = sample_info["WORKSHEET"]
        self.test = sample_info["TEST"]
        self.reason_for_referral = sample_info["REASON_FOR_REFERRAL"]
        self.sex = sample_info["SEX"]
        self.index_well = sample_info["INDEX_WELL"]
        self.i5_index = sample_info["I5_INDEX"]
        self.i5_seq = sample_info["I5_SEQ"]
        self.i7_index = sample_info["I7_INDEX"]
        self.i7_seq = sample_info["I7_SEQ"]
        self.affected = sample_info["AFFECTED"]
        self.family_id = sample_info["FAMILY_ID"]
        self.family_pos = sample_info["FAMILY_POS"]
        self.hpo_terms = sample_info["HPO_TERMS"]

    @staticmethod
    def parse_lab_no(lab_no: str, test: str):
        """
        For assays with 2 NTCs on a sheet (BRCA/CRM and TSO500 DNA/RNA) we need to rename the NTCs to be unique
        """
        tests_to_check = ["TSO500DNA", "TSO500RNA", "GeneReadBRCA", "GeneReadCRM"]
        if "NTC" in lab_no and any(test_to_check in test for test_to_check in tests_to_check):
            lab_no_parsed = f"{lab_no}-{test}"
            return lab_no_parsed
        else:
            return lab_no
        #TODO if loading a sample twice (e.g. SWGS) will it have an A/B already or do we need to add that
        
    @staticmethod
    def parse_test_for_pipelines(test: str):
        if test == "WES":
            return "NonacusWES38"
        elif test == "TruSightCancer":
            return "IlluminaTruSightCancer"
        else:
            return test
    
    @staticmethod
    def parse_referral():
        pass
    
    @staticmethod
    def parse_sex(sex):
        """
        Convert M/F/unknown sex to 0/1/2 
        """
        if sex == "M":
            return "1"
        elif sex == "F":
            return "2"
        else:
            return "0"
    
    @staticmethod
    def parse_hpo_terms(hpo_terms):
        """
        Change HPO terms to pipe separated list for pipeline
        """
        # can be new lines mock this
        if len(hpo_terms) == 0:
            hpo_terms_parsed = "None"
        else:
            hpo_terms_parsed = "|".join(hpo_terms.split(";"))
            #TODO what if one HPO term
        return hpo_terms_parsed
    
    @staticmethod
    def parse_family_structure():
        pass
    
    def create_samplesheet_line(self):
        line = f"{self.lab_no},{self.worksheet},"





def open_glims_export(file):
    """
    Takes a csv file exported from GLIMS and reads in to memory
    """
    with open(file) as f:
        csv_dict_reader = csv.DictReader(f)
        glims_samples = []
        for line in csv_dict_reader:
            print(line)
            print(line["SEX"])
            l = GlimsSample(line)
            glims_samples.append(l)
        return glims_samples

test_tso = "/home/na282549/code/auto_qc/sample_sheet/glims/24-TSOSEQ-29.csv"
test_wes = "/home/na282549/code/auto_qc/sample_sheet/glims/24-WESSEQ-30.csv"

tso_samples = open_glims_export(test_tso)
for s in tso_samples:
    print(s.__dict__)

wes_samples = open_glims_export(test_wes)
for s in wes_samples:
    print(s.__dict__)    