import csv

from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist

from sample_sheet_generator.models import Assay, Referral

def parse_referral(referral):
    """
    Takes a referral and parses it to the needed format in the pipeline (lower case, underscores)
    """
    referral = referral.split(" ")
    referral = [r.lower() for r in referral]
    referral = "_".join(referral)
    return referral

class Command(BaseCommand):

    """
    Add referrals to the samplesheet generator through csv import
    All referrals on a given csv will be added to the assay(s) mentioned
    The 'pipeline_referral' description should correspond exactly to how the assay is run in the pipeline
    """

    def add_arguments(self, parser):
        parser.add_argument("--referrals_csv", help="csv containing referrals for a given assay", nargs=1, required=True)
        parser.add_argument("--assays", help="a list of the assays to add these referrals to", nargs="+", required=True)

    def handle(self, *args, **options):

        # read in csv
        referrals_csv = options["referrals_csv"]
        assays = options["assays"]

        with open(referrals_csv) as f:
            csv_reader = csv.DictReader(f)

            for line in csv_reader:
                print(list(line.keys()))
                if list(line.keys()) != ["referral_code", "pipeline_referral"]:
                    raise ValueError("Unexpected CSV format - check and try again!")

                referral_code = line["referral_code"]
                referral_for_pipeline = parse_referral(line["pipeline_referral"])
                referral_obj, created = Referral.objects.get_or_create(referral_code=referral_code, referral_for_pipeline=referral_for_pipeline)

                # add to assay
                for assay in assays:
                    try:
                        assay_obj = Assay.objects.get(assay=assay)
                        referral_obj.assay.add(assay_obj)
                        referral_obj.save()
                        print(f"Adding {referral_code} to {assay}")
                    except ObjectDoesNotExist:
                        all_assays = Assay.objects.all()
                        assays = [assay.assay for assay in all_assays]
                        raise ObjectDoesNotExist(f"{assay} not configured - do this first and try again! Assays configured for {' '.join(assays)}")
                    
        print(f"Uploaded referrals from {referrals_csv}")