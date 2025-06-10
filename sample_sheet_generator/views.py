from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import render

from io import TextIOWrapper
import subprocess

from sample_sheet_generator.utils import open_glims_export, WorksheetSamples, create_samplesheet, create_samplesheet_webserver
from sample_sheet_generator.forms import UploadForm

########## home page ################
@transaction.atomic
@login_required
def home_samplesheetgenerator(request):
	"""
	Home page for sample sheet
	"""

	upload_form = UploadForm()
	context = {
		"form": upload_form,
		"warnings": [],
	}

	if request.POST:

		samplesheet_upload_file = request.FILES["upload_file"]
		samplesheet_upload_formatted = TextIOWrapper(samplesheet_upload_file)
		sequencer = request.POST["sequencer"]
		
		glims_samples = open_glims_export(samplesheet_upload_formatted)
		worksheet_samples = WorksheetSamples(glims_samples, sequencer)

		if "download-samplesheet" in request.POST:
			response = HttpResponse(content_type = "text/csv")
			response['Content-Disposition'] = 'attachment; filename="SampleSheet.csv"'
			create_samplesheet(worksheet_samples, response)
			return response
		
		elif "download-webserver" in request.POST:
			initial_path = f'{settings.SSGEN_DOWNLOAD}/{sequencer}/'
			#make worksheet sub-directory
			worksheet = worksheet_samples.worksheet
			cmd = f'mkdir -p {initial_path}/{worksheet}'
			subprocess.check_output(cmd, shell=True, executable='/bin/bash')
			final_path = f'{initial_path}/{worksheet}/SampleSheet.csv'
			create_samplesheet_webserver(worksheet_samples, final_path)
	
	return render(request, 'sample_sheet_generator/home.html', context)
