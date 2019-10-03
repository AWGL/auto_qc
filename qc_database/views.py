from django.shortcuts import render, get_object_or_404
from .models import *
# Create your views here.


def home(request):

	run_analyses = RunAnalysis.objects.all().order_by('start_date')


	return render(request, 'auto_qc/home.html', {'run_analyses': run_analyses})


def view_run_analysis(request, pk):

	run_analysis = get_object_or_404(RunAnalysis, pk=pk)

	sample_analyses = SampleAnalysis.objects.filter(run = run_analysis.run,
													pipeline = run_analysis.pipeline,
													analysis_type=run_analysis.analysis_type )

	run_level_qualities = InteropRunQuality.objects.filter(run =run_analysis.run)

	return render(request, 'auto_qc/view_run_analysis.html', {'run_analysis': run_analysis,
															 'sample_analyses': sample_analyses,
															 'run_level_qualities': run_level_qualities})