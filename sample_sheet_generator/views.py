from django.shortcuts import render
from django.db import transaction
from django.contrib.auth.decorators import login_required


########## home page ################
@transaction.atomic
@login_required
def home(request):
	"""
	Home page for sample sheet
	"""

	return render(request, 'sample_sheet_generator/home.html')