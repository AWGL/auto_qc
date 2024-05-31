import csv
from collections import OrderedDict

from sample_sheet_generator.models import Assay

## sample well in current sample sheet is actually the index well

class GlimsSample:
    #TODO update init to just run all the functions
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
        self.urgency = sample_info["ROUTINE"]
        self.assay = self.get_assay(self.test, self.urgency)

    @staticmethod
    def parse_lab_no(lab_no: str, test: str):
        """
        For assays with 2 NTCs on a sheet (BRCA/CRM and TSO500 DNA/RNA) we need to rename the NTCs to be unique
        """
        tests_to_check = ["TSO500DNA", "TSO500RNA", "GeneReadBRCA", "GeneReadCRM"]
        if "NTC" in lab_no and any(test_to_check in test for test_to_check in tests_to_check):
            return f"{lab_no}-{test}"
        else:
            return lab_no
        #TODO if loading a sample twice (e.g. SWGS) will it have an A/B already or do we need to add that
    
    @staticmethod
    def parse_worksheet(test: str, worksheet: str):
        """
        For any paired assay going in to SVD, we need to rename the worksheets to be unique
        Also going to do this for ctDNA or it'll look different to everything else going in to SVD
        #TODO later SWGS
        """
        # Get assay name from lims name
        assay_obj = Assay.objects.get(lims_test=test)
        assay = assay_obj.assay
        
        tests_to_check = ["TSO500DNA", "TSO500RNA", "ctDNA", "BRCA", "CRM"]
        if any(test_to_check in assay for test_to_check in tests_to_check):
            return f"{worksheet}-{assay}"
        else:
            return worksheet
    
    @staticmethod
    def parse_referral(referral):
        # This is gonna be a big one. for now, change commas to pipes so the csv doesn't mess up
        referral = referral.replace(",", "|")
        # If no referral field, set null for the pipelines that will otherwise crash
        if referral == "":
            referral = "null"
        return referral
    
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
        return hpo_terms_parsed
    
    @staticmethod
    def parse_affected(affected):
        """
        Change the affected field to PED format for pipeline
        """
        if affected.lower() in ["2", "affected"]:
            affected = "2"
        elif affected.lower() in ["1", "unaffected"]:
            affected = "1"
        elif affected.lower() in ["0", "missing"]:
            affected = "0"
        else:
            # affected is missing
            affected = "-9"
        return affected

    @staticmethod
    def parse_family_structure(family_id: str, family_pos: str):
        #TODO check what's being put in LIMS
        
        # if it's a singleton we don't need a family structure
        if family_id.lower() in ["", "none", "na", "n/a"]:
            return None
        
        # otherwise, we have a family
        # reformat family_id to match VariantBank nomenclature
        if family_id.isdigit():
            family_id = f"FAM00{family_id}"

        # now we want to set up the family string as much as possible
        # for probands we'll use a placeholder for parents which will be replaced when samplesheet is compiled and checked
        if family_pos.lower() == "proband":
            family_pos = "proband"
            family_description = f"familyId={family_id};paternalId={family_id}-father;maternalId={family_id}-mother"
        
        elif family_pos.lower() in ["mum", "mother"]:
            family_pos = "mother"
            family_description = f"familyId={family_id}"
        
        elif family_pos.lower() in ["dad", "father"]:
            family_pos = "father"
            family_description = f"familyId={family_id}"
        
        return family_pos, family_description
        
    @staticmethod
    def get_assay(test: str, urgency: str):
        """
        Get the assay object
        """
        try:
            # for urgent WGS samples, we want to return FastWGS
            if test == "WGS" and urgency == "U":
                assay = Assay.objects.get(pk="FastWGS")
            else:
                assay = Assay.objects.get(lims_test=test)
            return assay
        except Assay.DoesNotExist:
            raise Exception("This test is not configured - contact bioinformatics.")

    def create_samplesheet_header(self):
        """
        All samplesheets share some fields:
        Sample_ID,Sample_Plate,Sample_Well,Description
        Indexes differ and TSO has some extra fields needed for the app
        """
        # some fields are common to all sample sheets
        common_fields = "Sample_ID,Sample_Plate,Sample_Well"

        # sort the index fields
        if self.assay.index_fields == "1":
            # single index
            index_fields = ",I7_Index_ID,index"

        elif self.assay.index_fields == "2":
            # dual index
            index_fields = ",I7_Index_ID,index,I5_Index_ID,index2"

        elif self.assay.index_fields == "T":
            # TSO500 app indexes
            index_fields = ",Index_ID,index,index2"
        
        else:
            # error we need indexes set up properly
            raise Exception("This test is not configured correctly - contact bioinformatics.")

        # add any additional fields required
        # nothing by default
        additional_fields = ""

        if self.assay.sample_name_field:
            additional_fields += ",Sample_Name"
        
        if self.assay.pair_id_field:
            additional_fields += ",Pair_ID"
        
        if self.assay.sample_type_field:
            additional_fields += ",Sample_Type"

        if self.assay.sample_project_field:
            additional_fields += ",Sample_Project"

        # all sample sheets have a description field
        description_field = ",Description"

        # create the header
        samplesheet_header = f"{common_fields}{index_fields}{additional_fields}{description_field}"
        
        return samplesheet_header
    
    def create_samplesheet_line(self):
        """
        Create a line for the samplesheet.
        """
        
        # Sample_ID and Sample_Plate (worksheet) same for all assays
        common_fields = f"{self.parse_lab_no(self.lab_no, self.test)},{self.parse_worksheet(self.test, self.worksheet)}"

        # Sample_Well is either position or index ID depending on the assay
        if self.assay.sample_well_field == "P":
            sample_well_field = f",{self.position}"
        elif self.assay.sample_well_field == "I":
            sample_well_field = f",{self.index_well}"    

        # Index fields differ depending no the assay
        if self.assay.index_fields == "1":
            # single index
            index_fields = f",{self.i7_index},{self.i7_seq}"

        elif self.assay.index_fields == "2":
            # dual index
            index_fields = f",{self.i7_index},{self.i7_seq},{self.i5_index},{self.i5_seq}"

        elif self.assay.index_fields == "T":
            # TSO500 app indexes
            index_fields = f",{self.i7_index},{self.i7_seq},{self.i5_seq}"
        
        else:
            # error we need indexes set up properly
            raise Exception("This test is not configured correctly - contact bioinformatics.")
        
        # add any additional fields required
        # nothing by default
        additional_fields = ""

        if self.assay.sample_name_field:
            # Sample Name is Sample ID
            additional_fields += f",{self.lab_no}"
        
        if self.assay.pair_id_field:
            # Pair ID is also Sample ID
            additional_fields += f",{self.lab_no}"
        
        if self.assay.sample_type_field:
            # only for TSO500
            if self.test == "TSO500RNA":
                additional_fields += ",RNA"
            elif self.test == "TSO500DNA" or self.test == "TSO500CTDNA":
                additional_fields += ",DNA"

        if self.assay.sample_project_field:
            # this is always blank
            additional_fields += ","

        # Description field varies by assay but all start with pipeline etc. from fixtures
        description_field = f",{self.assay.pipeline_description}"

        if self.assay.sex_in_desc:
            description_field += f";sex={self.parse_sex(self.sex)}"
        
        if self.assay.order_in_desc:
            description_field += f";order={self.position}"
        
        if self.assay.referral_in_desc:
            description_field += f";referral={self.parse_referral(self.reason_for_referral)}"
        
        if self.assay.hpo_in_desc:
            description_field += f";hpoId={self.parse_hpo_terms(self.hpo_terms)}"

        if self.assay.family_in_desc:
            # for WES/WGS only. duos and trios have family/affected fields, singletons do not
            family_info = self.parse_family_structure(self.family_id, self.family_pos)
            if family_info:
                # get family position and info
                family_pos, family_description = family_info
                # update the family position for parsing later
                self.family_pos = family_pos
                # get affected status
                affected = self.parse_affected(self.affected)
                # update description
                description_field += f";{family_description};phenotype={affected}"
        
        # combine to one samplesheet line
        samplesheet_line = f"{common_fields}{sample_well_field}{index_fields}{additional_fields}{description_field}"
        return samplesheet_line




def open_glims_export(file):
    """
    Takes a csv file exported from GLIMS and reads in to memory
    """
    with open(file) as f:
        csv_dict_reader = csv.DictReader(f, delimiter="\t")
        glims_samples = []
        for line in csv_dict_reader:
            l = GlimsSample(line)
            glims_samples.append(l)
        return glims_samples

test_tso = "/home/na282549/code/auto_qc/glims/24-TSOSEQ-29.tsv"
test_wes = "/home/na282549/code/auto_qc/glims/24-WESSEQ-30.tsv"

tso_samples = open_glims_export(test_tso)
for s in tso_samples:
    s.create_samplesheet_line()
#for s in tso_samples:
    #print(s.__dict__)

wes_samples = open_glims_export(test_wes)
#for s in wes_samples:
    #print(s.__dict__)    