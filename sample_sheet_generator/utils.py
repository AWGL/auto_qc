import csv
import datetime

from collections import OrderedDict

from sample_sheet_generator.models import Assay

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
        self.urgency = sample_info["ROUTINE"]
        self.assay = self.get_assay(self.test, self.urgency)
        self.header_line = self.create_samplesheet_header()
        self.samplesheet_line = self.create_samplesheet_line()

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
        if len(hpo_terms) == 0:
            hpo_terms_parsed = "None"
        else:
            hpo_terms_parsed = "|".join(hpo_terms.split(";"))
        # add the rstrip as sometimes there's newlines involved
        return hpo_terms_parsed.rstrip()
    
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
        """
        Update the family position and make a placeholder family description field
        """
        
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
        
        #TODO if anything weird in these fields return nothing and an error message

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
        description_field = [f",{self.assay.pipeline_description}"]

        if self.assay.sex_in_desc:
            description_field.append(f"sex={self.parse_sex(self.sex)}")
        
        if self.assay.order_in_desc:
            description_field.append(f"order={self.position}")
        
        if self.assay.referral_in_desc:
            description_field.append(f"referral={self.parse_referral(self.reason_for_referral)}")
        
        # HPO terms and family structure for WES/WGS only. duos and trios have family/affected fields, singletons do not
        if self.test in ["WGS", "WES"]:

            if self.assay.hpo_in_desc:
                if self.parse_hpo_terms(self.hpo_terms) != "None":
                    description_field.append(f"hpoId={self.parse_hpo_terms(self.hpo_terms)}")

            if len(self.family_id) > 0:
                # get family position and info
                family_pos, family_description = self.parse_family_structure(self.family_id, self.family_pos)
                # update the family position for parsing later
                self.family_pos = family_pos
                # get affected status
                affected = self.parse_affected(self.affected)
                # update description
                description_field.append(f"{family_description};phenotype={affected}")

        # make the description field
        description_field = ";".join(description_field)
        
        # combine to one samplesheet line
        samplesheet_line = f"{common_fields}{sample_well_field}{index_fields}{additional_fields}{description_field}"
        
        return samplesheet_line
    

class WorksheetSamples:
    def __init__(self, glims_samples: list, sequencer: str):
        self.samples = glims_samples
        self.sequencer = sequencer
        self.tests = self.get_test()

    def get_test(self):
        """
        Get the test(s) in the samplesheet so the right header is used
        """
        tests = list(set([sample.test for sample in self.samples]))
        tests = "|".join(tests)
        return tests

    def get_header_line(self):
        """
        Gets the header line from the first sample. For split worksheets e.g. TSO500 DNA/RNA the header line is the same
        """
        header_line = self.samples[0].create_samplesheet_header()
        return header_line
    
    def get_samplesheet_lines(self):
        """
        Create all the samplesheet lines, updating the family structure where required
        """

        samplesheet_lines = []

        for sample in self.samples:

            samplesheet_line = sample.samplesheet_line
            # for probands, we need to update the description
            if sample.family_pos == "proband":

                # find the mother
                mother = [s for s in self.samples if s.family_id == sample.family_id and s.family_pos == "mother"]

                # find the father
                father = [s for s in self.samples if s.family_id == sample.family_id and s.family_pos == "father"]

                # for each parent, either replace or remove the text
                if len(mother) == 0:
                    samplesheet_line = samplesheet_line.replace(f"maternalId={sample.family_id}-mother","")
                else:
                    samplesheet_line = samplesheet_line.replace(f"maternalId={sample.family_id}-mother", f"maternalId={mother[0].lab_no}")
                if len(father) == 0:
                    samplesheet_line = samplesheet_line.replace(f"paternalId={sample.family_id}-father","")
                else:
                    samplesheet_line = samplesheet_line.replace(f"paternalId={sample.family_id}-father", f"paternalId={father[0].lab_no}")

                samplesheet_lines.append(samplesheet_line)
            
            # other family members can be left, and non-family samples don't need updating
            else:
                samplesheet_lines.append(samplesheet_line)
        
        return samplesheet_lines


class MainHeader:
    """
    Class containing functions common to standard and TSO500 samplesheets
    """
    def __init__(self, worksheet_samples: WorksheetSamples):
        self.assay = worksheet_samples.samples[0].test
        self.experiment_id = worksheet_samples.samples[0].worksheet
        self.sequencer = worksheet_samples.sequencer
        
        self.common_lines = []
        self.settings_lines = []
        self.data_line = []

    def merge_lines(self):
        all_lines = self.common_lines + self.settings_lines + [self.data_line]
        return all_lines


class StandardHeader(MainHeader):
    """
    Standard samplesheet header is used for everything except for TSO500
    """

    def __init__(self, worksheet_samples):
        super().__init__(worksheet_samples)
        self.common_lines =  [
            ["[Header]"],
            ["IEMFileVersion", "4"],
            ["InvestigatorName", "USERID"],
            ["ExperimentName", "EXP_ID"],
            ["Workflow", "GenerateFASTQ"],
            ["Application", "APP_ID"],
            ["Chemistry"],
            [],
            ["[Reads]"],
            ["151"],
            ["151"],
            []
        ]
        if self.assay == "WES":
            self.settings_lines = [
                ["[Settings]"],
                ["OverrideCycles", "OVERRIDE_ID"],
                []
            ]
        else:
            self.settings_lines = []
        self.data_line = ["[Data]"]

        # All MiSeq runs are single index and have 7 columns, everything else has 9
        if self.sequencer == "MiSeq":
            self.max_length = 7
        else:
            self.max_length = 9

    def replace_standard_text(self):
        """
        Replace the placeholder text in the main header with the correct information for each test
        """
        all_lines_merged = self.merge_lines()
        all_lines_formatted = []

        for list in all_lines_merged:
            formatted_list = []

            for item in list:
                # experiment ID is the worklist
                item.replace("EXP_ID", self.experiment_id)

                # app id is NovaSeqFASTQOnly for WGS/NovaSeq WES, NextSeqFASTQOnly for NextSeq WES and FASTQOnly for everything else
                if self.assay == "WES" and self.sequencer == "NextSeq":
                    app_id = "NextSeqFASTQOnly"
                elif self.assay in ["WES", "WGS"] and self.sequencer == "NovaSeq":
                    app_id = "NovaSeqFASTQOnly"
                else:
                    app_id = "FASTQOnly"
                item = item.replace("APP_ID", app_id)

                # override id only applies to WES
                if self.sequencer == "NextSeq":
                    override_id = "Y145;I8U9;I8;Y145"
                elif self.sequencer == "NovaSeq":
                    override_id = "Y151;I8U9;I8;Y151"
                item = item.replace("OVERRIDE_ID", override_id)

                #append line
                formatted_list.append(item)
            
            # pad out with the right number of commas
            formatted_list += [""] * (self.max_length - len(formatted_list))
            formatted_line = ",".join(formatted_list)

            all_lines_formatted.append(formatted_line)
        
        return all_lines_formatted


class TSOHeader(MainHeader):
    """
    TSO500 samplesheets are different to all the other samplesheets
    """

    def __init__(self, worksheet_samples):
        super().__init__(worksheet_samples)
        self.common_lines =  [
            ["[Header]"],
            ["IEMFileVersion", "4"],
            ["InvestigatorName", "USERID"],
            ["ExperimentName", "EXP_ID"],
            ["Date", "DDMMYYYY"],
            ["Workflow", "WORKFLOW"],
            ["Application", "APP_ID"],
            ["Assay", "ASSAY"],
            ["Description", "DESCRIPTION"],
            ["Chemistry"],
            [],
            ["[Reads]"],
            ["READS"],
            ["READS"],
            []
        ]
        self.settings_lines = [
            ["[Settings]"],
            ["AdapterRead1", "AGATCGGAAGAGCACACGTCTGAACTCCAGTCA"],
            ["AdapterRead2", "AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGT"],
            ["AdapterBehaviour", "trim"],
            ["MinimumTrimmedReadLength", "35"],
            ["OverrideCycles", "OVERRIDE_ID"],
            []
        ]
        self.data_line = ["[Data]"]

        # all the TSO samplesheets have 10 columns
        self.max_length = 10

    def replace_tso_text(self):
        all_lines_merged = self.merge_lines()
        all_lines_formatted = []

        for list in all_lines_merged:
            formatted_list = []

            for item in list:
                # experiment ID is the worklist
                item.replace("EXP_ID", self.experiment_id)

                # replace date placeholder with today's date
                today = datetime.date.today().strftime('%d/%m/%Y')
                item = item.replace("DDMMYYYY", today)

                # workflow is absent for ctDNA
                # app ID is NextSeq for TSO500 DNA/RNA, even though it's run on the NovaSeq
                # description is absent for ctDNA
                # DNA/RNA reads are 101, ctDNA is 151
                # override ID is different depending on read length. For both it says index reads are 8. They're not, but the app will break if you don't put 8.
                if self.assay == "TSO500CTDNA":
                    workflow = ""
                    application = "NovaSeq"
                    description = ""
                    reads = "151"
                    override = "U7N1Y143;I8;I8;U7N1Y143"
                else:
                    workflow = "GenerateFASTQ"
                    application = "NextSeqFASTQOnly"
                    description = self.experiment_id
                    reads = "101"
                    override = "U7N1Y93;I8;I8;U7N1Y93"
                item = item.replace("WORKFLOW", workflow)
                item = item.replace("APP_ID", application)
                item = item.replace("DESCRIPTION", description)
                item = item.replace("READS", reads)
                item = item.replace("OVERRIDE_ID", override)

                #append line
                formatted_list.append(item)

            # pad out with commas
            formatted_list += [""] * (self.max_length - len(formatted_list))
            formatted_line = ",".join(formatted_list)

            all_lines_formatted.append(formatted_line)
        
        return all_lines_formatted


def open_glims_export(file):
    """
    Takes a csv file exported from GLIMS and reads in to memory
    """
    #with open(file) as f:
    csv_dict_reader = csv.DictReader(file, delimiter="\t")
    glims_samples = []
    for line in csv_dict_reader:
        l = GlimsSample(line)
        glims_samples.append(l)
    return glims_samples

def create_samplesheet(worksheet_samples: WorksheetSamples, response):
    """
    Create the SampleSheet.csv for download
    """
    #main header lines
    if "TSO500" in worksheet_samples.tests:
        main_header_lines = TSOHeader(worksheet_samples).replace_tso_text()
    else:
        main_header_lines = StandardHeader(worksheet_samples).replace_standard_text()
    header_line = worksheet_samples.get_header_line()
    samplesheet_lines = worksheet_samples.get_samplesheet_lines()
    all_lines = main_header_lines + [header_line] + samplesheet_lines
    csv_writer = csv.writer(response)
    for line in all_lines:
        csv_writer.writerow(line.split(","))
