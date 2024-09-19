from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from django.conf import settings
from django.http import HttpResponse

from qc_database.models import *
from qc_database.forms import *
from qc_database.utils.kpi import make_kpi_excel

from rest_framework import generics
from .models import SampleAnalysis, RunAnalysis
from .serializers import SampleAnalysisSerializer, RunAnalysisSerializer

from datetime import datetime as dt


@transaction.atomic
@login_required
def home_auto_qc(request):
	"""
	Return a list of active run analysis objects

	"""

	run_analyses = RunAnalysis.objects.filter(watching=True).order_by('-run')

	return render(request, 'auto_qc/home.html', {'run_analyses': run_analyses})


@transaction.atomic
@login_required
def view_run_analysis(request, pk):
	"""	
	View a specific run analysis object

	"""

	run_analysis = get_object_or_404(RunAnalysis, pk=pk)

	sample_analyses = SampleAnalysis.objects.filter(
		run = run_analysis.run,
		pipeline = run_analysis.pipeline,
		analysis_type = run_analysis.analysis_type
	).order_by('worksheet', 'sample')

	relatedness = RelatednessQuality.objects.filter(run_analysis = run_analysis)

	run_level_qualities = InteropRunQuality.objects.filter(run = run_analysis.run)

	auto_qc = run_analysis.passes_auto_qc()

	min_q30_score = round(run_analysis.min_q30_score * 100)
	max_contamination_score = round(sample_analyses[0].contamination_cutoff*100, 1)
	max_ntc_contamination_score = round(sample_analyses[0].ntc_contamination_cutoff, 1)

	checks_to_do = run_analysis.auto_qc_checks

	if checks_to_do == None:

		checks_to_do = []

	else:
		
		checks_to_do = checks_to_do.split(',')

	reset_form = ResetRunForm(run_analysis_id= run_analysis.pk)
	sensitivity_form = SensitivityForm(instance = run_analysis)

	if request.method == 'POST':

		if 'samplefail' in request.POST:

			entry_list = []

			for entry in request.POST:

				entry_list.append(entry)

			for sample in sample_analyses:

				if str(sample.pk) in entry_list:

					SampleAnalysis.objects.filter(sample=sample.sample, run=run_analysis.run, pipeline=run_analysis.pipeline,  analysis_type = run_analysis.analysis_type).update(sample_status='Pass')

				else:

					SampleAnalysis.objects.filter(sample=sample.sample, run=run_analysis.run, pipeline=run_analysis.pipeline,  analysis_type = run_analysis.analysis_type).update(sample_status='Fail')

		if 'run_status' in request.POST:

			status = request.POST['run_status']

			if status == 'Pass':

				approval = RunAnalysis.objects.get(pk=run_analysis.pk)
				approval.manual_approval = True
				approval.watching = False
				approval.signoff_user = request.user
				approval.signoff_date = dt.now()
				approval.save()

			elif status == 'Fail':

				failure = RunAnalysis.objects.get(pk=run_analysis.pk)
				failure.manual_approval = False
				failure.watching = False
				failure.signoff_user = request.user
				failure.signoff_date = dt.now()
				failure.save()
				
				if 'samplefail' in request.POST:
					entry_list = []
					for entry in request.POST:
						entry_list.append(entry)
					for sample in sample_analyses:
						if str(sample.pk) in entry_list:
							SampleAnalysis.objects.filter(sample=sample.sample).update(sample_status='Fail')

		if 'run_status_comment' in request.POST:

			run_comment = request.POST['run_status_comment']
			
			comment = RunAnalysis.objects.get(pk=run_analysis.pk)
			comment.comment = run_comment
			comment.save()

			return redirect('home_auto_qc')

		# if the user submitted the signoff form
		if 'run-analysis-signoff-form' in request.POST:

			form = RunAnalysisSignOffForm(request.POST, run_analysis_id= run_analysis.pk, comment =run_analysis.comment)

			if form.is_valid():

				approval = form.cleaned_data['approval']
				comment = form.cleaned_data['comment']

				if approval == 'Pass':

					run_analysis.manual_approval = True
					status_message = f':heavy_check_mark: *{run_analysis.analysis_type} run {run_analysis.get_worksheets()} has passed QC*\n'

				else:

					run_analysis.manual_approval = False
					status_message = f':x: *{run_analysis.analysis_type} run {run_analysis.get_worksheets()} has failed QC*\n'

				run_analysis.comment = comment
				run_analysis.watching = False
				run_analysis.signoff_user = request.user
				run_analysis.signoff_date = dt.now()
				run_analysis.save()

				return redirect('home_auto_qc')

		# if the user resets the run analysis to be watched
		elif 'reset-form' in request.POST:

			reset_form = ResetRunForm(run_analysis_id= run_analysis.pk)

			run_analysis.manual_approval = False
			run_analysis.watching = True
			run_analysis.signoff_user = None
			run_analysis.signoff_date = None
			run_analysis.save()

			return redirect('home_auto_qc')

	return render(request, 'auto_qc/view_run_analysis.html', {'run_analysis': run_analysis,
															 'sample_analyses': sample_analyses,
															 'run_level_qualities': run_level_qualities,
															 'auto_qc': auto_qc,
															 'min_q30_score': min_q30_score,
															 'max_contamination_score': max_contamination_score,
															 'max_ntc_contamination_score': max_ntc_contamination_score,
															 'reset_form': reset_form,
															 'sensitivity_form': sensitivity_form,
															 'checks_to_do': checks_to_do,
															 'relatedness': relatedness,
															 'cpf_warning': 60.0})


@transaction.atomic
@login_required
def view_archived_run_analysis(request):
	"""
	View run analyses which are not being watched,

	"""
	run_analyses = RunAnalysis.objects.filter(watching=False).order_by('-run').select_related('pipeline','analysis_type', 'run')

	return render(request, 'auto_qc/archived_run_analysis.html', {'run_analyses': run_analyses})


@transaction.atomic
def signup(request):
	"""
	Allow users to sign up
	User accounts are inactive by default - an admin must activate it using the admin page.
	"""

	if request.method == 'POST':

		form = UserCreationForm(request.POST)

		if form.is_valid():

			form.save()
			
			username = form.cleaned_data.get('username')
			raw_password = form.cleaned_data.get('password1')
			user = authenticate(username=username, password=raw_password)
			user.is_active = False
			user.save()

			return redirect('home_auto_qc')

		else:

			form = UserCreationForm()
			return render(request, 'auto_qc/signup.html', {'form': form, 'warning' : ['Could not create an account.']})

	else:

		form = UserCreationForm()
		return render(request, 'auto_qc/signup.html', {'form': form, 'warning': []})

@transaction.atomic
@login_required
def search(request):
	"""
	Allow user to search for samples, worksheets
	"""

	form = SearchForm()

	results = None

	if request.method == 'POST':

		form = SearchForm(request.POST)

		if form.is_valid():

			query = form.cleaned_data['search']
			
			if form.cleaned_data['search_type'] == 'Sample':

				try:

					queried_sample = Sample.objects.get(sample_id = query)

				except:

					return render(request, 'auto_qc/search.html', {'form': form, 'results': None})

				results = SampleAnalysis.objects.filter(sample=queried_sample)

				return render(request, 'auto_qc/search.html', {'form': form, 'results': results})

			elif form.cleaned_data['search_type'] == 'Worksheet':

				try:

					queried_sample = WorkSheet.objects.get(worksheet_id = query)

				except:

					return render(request, 'auto_qc/search.html', {'form': form, 'results': None})

				results = SampleAnalysis.objects.filter(worksheet=queried_sample)

				return render(request, 'auto_qc/search.html', {'form': form, 'results': results})

	return render(request, 'auto_qc/search.html', {'form': form, 'results': results})

@transaction.atomic
@login_required
def ngs_kpis(request):
	"""
	Query NGS runs between 2 dates and output excel sheet for tech team
	"""
	form = KpiDateForm()

	if request.POST:

		form = KpiDateForm(request.POST)

		if form.is_valid():
			# get data from form
			cleaned_data = form.cleaned_data
			start_date = cleaned_data['start_date']
			end_date = cleaned_data['end_date']

			# query all runs between input dates
			runs = Run.objects.filter(instrument_date__range=(start_date, end_date)).order_by('instrument_date', 'experiment')
			
			# setup download button for openpyxl file
			response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheet.sheet')
			output_name = f'attachment; filename="KPI_{start_date}_{end_date}.xlsx"'
			response['Content-Disposition'] = output_name

			# loops through runs and make list of required data
			wb = make_kpi_excel(runs)
			wb.save(response)
			return response

	return render(request, 'auto_qc/ngs_kpis.html', {'form': form})

class SampleAnalysisList(generics.ListAPIView):
	queryset = SampleAnalysis.objects.all()
	serializer_class = SampleAnalysisSerializer


class RunAnalysisList(generics.ListAPIView):
	queryset = RunAnalysis.objects.all()
	serializer_class = RunAnalysisSerializer





