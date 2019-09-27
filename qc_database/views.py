from django.shortcuts import render
from .models import *
# Create your views here.


def home(request):

	run_analyses = RunAnalysis.objects.all().order_by('start_date')


	return render(request, 'auto_qc/home.html', {'run_analyses': run_analyses})