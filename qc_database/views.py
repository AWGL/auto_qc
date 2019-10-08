from django.shortcuts import render, get_object_or_404, redirect
from .models import *
from .forms import *

# Create your views here.


def home(request):

	run_analyses = RunAnalysis.objects.filter(watching=True).order_by('start_date')


	return render(request, 'auto_qc/home.html', {'run_analyses': run_analyses})


def view_run_analysis(request, pk):

	run_analysis = get_object_or_404(RunAnalysis, pk=pk)

	sample_analyses = SampleAnalysis.objects.filter(run = run_analysis.run,
													pipeline = run_analysis.pipeline,
													analysis_type=run_analysis.analysis_type )

	run_level_qualities = InteropRunQuality.objects.filter(run =run_analysis.run)

	auto_qc = run_analysis.passes_auto_qc()

	min_q30_score = round(run_analysis.min_q30_score * 100)

	max_contamination_score = round(sample_analyses[0].contamination_cutoff*100, 1)

	max_ntc_contamination_score = round(sample_analyses[0].ntc_contamination_cutoff, 1)


	if request.method == 'POST':

		form = RunAnalysisSignOffForm(request.POST, run_analysis_id= run_analysis.pk)

		if form.is_valid():

			approval = form.cleaned_data['approval']
			comment = form.cleaned_data['comment']

			if approval == 'Pass':

				run_analysis.manual_approval = True

			else:

				run_analysis.manual_approval = False

			run_analysis.comment = comment
			run_analysis.watching = False
			run_analysis.save()

			return redirect('home')

	else:

		form = RunAnalysisSignOffForm(run_analysis_id= run_analysis.pk)

	return render(request, 'auto_qc/view_run_analysis.html', {'run_analysis': run_analysis,
															 'sample_analyses': sample_analyses,
															 'run_level_qualities': run_level_qualities,
															 'auto_qc': auto_qc,
															 'min_q30_score': min_q30_score,
															 'max_contamination_score': max_contamination_score,
															 'max_ntc_contamination_score': max_ntc_contamination_score,
															 'form': form})

def view_archived_run_analysis(request):

	run_analyses = RunAnalysis.objects.filter(watching=False).order_by('start_date')

	return render(request, 'auto_qc/home.html', {'run_analyses': run_analyses})