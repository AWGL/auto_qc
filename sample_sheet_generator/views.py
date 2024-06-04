from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import render

from io import TextIOWrapper

from sample_sheet_generator.utils import open_glims_export, WorksheetSamples, create_samplesheet
from sample_sheet_generator.forms import UploadForm

########## home page ################
@transaction.atomic
@login_required
def home(request):
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
		
		response = HttpResponse(content_type = "text/csv")
		response['Content-Disposition'] = 'attachment; filename="SampleSheet.csv"'
		create_samplesheet(worksheet_samples, response)
		return response
	
	return render(request, 'sample_sheet_generator/home.html', context)