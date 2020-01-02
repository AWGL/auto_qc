from django.shortcuts import render, get_object_or_404, redirect
from .models import *
from .forms import *
from .utils.slack import message_slack
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction


@transaction.atomic
@login_required
def home(request):
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

	form = RunAnalysisSignOffForm(run_analysis_id= run_analysis.pk, comment =run_analysis.comment)
	reset_form = ResetRunForm(run_analysis_id= run_analysis.pk)
	sensitivity_form = SensitivityForm(instance = run_analysis)



	if request.method == 'POST':

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
				run_analysis.save()

				# message run status to slack
				message_slack(
					status_message +
					f'```Run ID:          {run_analysis.run}\n' + 
					f'Worksheet ID:    {run_analysis.get_worksheets()}\n' + 
					f'Panel:           {run_analysis.analysis_type}\n' + 
					f'Pipeline:        {run_analysis.pipeline}\n' + 
					f'Signed off by:   {run_analysis.signoff_user}\n' +
					f'Comments:        {run_analysis.comment}\n' +
					f'QC link:         http://10.59.210.245:5000/run_analysis/{run_analysis.pk}/```'
				)

				return redirect('home')

		# if the user resets the run analysis to be watched
		elif 'reset-form' in request.POST:

			reset_form = ResetRunForm(run_analysis_id= run_analysis.pk)

			run_analysis.manual_approval = False
			run_analysis.watching = True
			run_analysis.signoff_user = None
			run_analysis.save()

			return redirect('home')

		elif 'sensitivity-form' in request.POST:

			sensitivity_form = SensitivityForm(request.POST, instance=run_analysis)

			if sensitivity_form.is_valid():

				sensitivity_form.save()
				run_analysis.sensitivity_user = request.user
				run_analysis.save()


	return render(request, 'auto_qc/view_run_analysis.html', {'run_analysis': run_analysis,
															 'sample_analyses': sample_analyses,
															 'run_level_qualities': run_level_qualities,
															 'auto_qc': auto_qc,
															 'min_q30_score': min_q30_score,
															 'max_contamination_score': max_contamination_score,
															 'max_ntc_contamination_score': max_ntc_contamination_score,
															 'form': form,
															 'reset_form': reset_form,
															 'sensitivity_form': sensitivity_form,
															 'checks_to_do': checks_to_do})

@transaction.atomic
@login_required
def view_archived_run_analysis(request):
	"""
	View run analyses which are not being watched,

	"""
	run_analyses = RunAnalysis.objects.filter(watching=False).order_by('-run')

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

			return redirect('home')

		else:

			form = UserCreationForm()
			return render(request, 'auto_qc/signup.html', {'form': form, 'warning' : ['Could not create an account.']})

	else:

		form = UserCreationForm()
		return render(request, 'auto_qc/signup.html', {'form': form, 'warning': []})
