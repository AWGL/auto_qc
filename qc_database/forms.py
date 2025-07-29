from django import forms
from .models import  *
from django.urls import reverse
from crispy_forms.bootstrap import Field
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, HTML
from django.forms import ModelForm
import datetime



class ResetRunForm(forms.Form):
	"""
	Form for resetting a run analysis
	"""

	def __init__(self, *args, **kwargs):
		
		self.run_analysis_id = kwargs.pop('run_analysis_id')

		super(ResetRunForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper()
		self.helper.form_id = 'reset-form'
		self.helper.label_class = 'col-lg-2'
		self.helper.field_class = 'col-lg-8'
		self.helper.form_method = 'post'
		self.helper.add_input(Submit('reset-form', 'Move To Pending', css_class='btn-success'))
		self.helper.form_class = 'form-horizontal'
		self.helper.layout = Layout(
		)


class SensitivityForm(ModelForm):

	class Meta:
		model = RunAnalysis
		fields = ['sensitivity', 'sensitivity_lower_ci', 'sensitivity_higher_ci']


	def __init__(self, *args, **kwargs):
		
		super(SensitivityForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper()
		self.helper.form_id = 'reset-form'
		self.helper.label_class = 'col-lg-2'
		self.helper.field_class = 'col-lg-8'
		self.helper.form_method = 'post'
		self.helper.add_input(Submit('sensitivity-form', 'Submit Sensitivity', css_class='btn-success'))
		self.helper.form_class = 'form-horizontal'
		self.helper.layout = Layout(

		)


class SearchForm(forms.Form):
	"""
	Form for searching
	"""

	search = forms.CharField(widget=forms.Textarea(attrs={'rows':1}))
	search_type = forms.ChoiceField(choices =(('Sample', 'Sample'), ('Worksheet', 'Worksheet')))

	def __init__(self, *args, **kwargs):
		
		super(SearchForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper()
		self.helper.form_id = 'search-form'
		self.helper.label_class = 'col-lg-2'
		self.helper.field_class = 'col-lg-8'
		self.helper.form_method = 'post'
		self.helper.add_input(Submit('reset-form', 'Search', css_class='btn-success'))
		self.helper.form_class = 'form-horizontal'
		self.helper.layout = Layout(
			Field('search', title=False),
			Field('search_type', title=False),
		)

class KpiDateForm(forms.Form):
	"""
	Form to input two dates, used to pull KPI data for NGS runs between the dates
	"""
	current_year = datetime.datetime.now().year
	current_month = datetime.datetime.now().month
	last_year = current_year - 1
	last_month = current_month - 1

	# choices for year dropdown box
	YEAR_CHOICES = range(2019, (current_year + 1))

	# default to first and last day of previous month
	if current_month == 1:
		# It's January so we want December last year
		INITIAL_START_DATE = datetime.date(last_year, 12, 1)
		INITIAL_END_DATE = datetime.date(last_year, 12, 31)
	else:
		INITIAL_START_DATE = datetime.date(current_year, last_month, 1)
		INITIAL_END_DATE = datetime.date(current_year, current_month, 1) - datetime.timedelta(days=1)

	start_date = forms.DateField(
		initial=INITIAL_START_DATE,
		widget=forms.SelectDateWidget(years=YEAR_CHOICES)
	)
	end_date = forms.DateField(
		initial=INITIAL_END_DATE,
		widget=forms.SelectDateWidget(years=YEAR_CHOICES)
	)


class DataDownloadForm(forms.Form):
	"""
	Form to download sample analysis data with options to choose assay types,
	data models and date range
	"""
	assay_type = forms.ModelMultipleChoiceField(
		queryset=AnalysisType.objects.all().distinct().order_by('analysis_type_id'),
		required=True,
		label="Assay Type",
		widget=forms.widgets.CheckboxSelectMultiple,
		help_text="Select one or more assay types to include in the export"
	)
	
	# This field will be populated dynamically via JavaScript
	data_models = forms.MultipleChoiceField(
		required=False,
		label="Data Models to Include",
		widget=forms.widgets.CheckboxSelectMultiple,
		help_text="Select which data models to include in the export (updates based on selected assay types)",
		choices=[]  # Will be populated dynamically
	)
	
	start_date = forms.DateField(
		widget=forms.DateInput(attrs={'type': 'date'}),
		required=True,
		label="Start Date",
		initial=datetime.date.today() - datetime.timedelta(days=30),  # Default to last 30 days
		help_text="Select the starting date for samples to include"
	)
	
	end_date = forms.DateField(
		widget=forms.DateInput(attrs={'type': 'date'}),
		required=True,
		label="End Date",
		initial=datetime.date.today(),  # Default to today
		help_text="Select the ending date for samples to include"
	)
	

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.helper = FormHelper()
		self.helper.form_method = 'post'
		self.helper.add_input(Submit('submit', 'Export CSV', css_class='btn btn-primary'))
		self.helper.add_input(Submit('submit', 'Generate Plot', css_class='btn btn-primary'))

		# Set choices for data_models if it's in POST data
		if args and isinstance(args[0], dict) and 'data_models' in args[0]:
			choices = [(model, model) for model in args[0].getlist('data_models')]
			self.fields['data_models'].choices = choices
	
	def clean(self):
		cleaned_data = super().clean()
		# If data_models is provided but not in available choices, don't raise validation error
		if 'data_models' in self.data and not cleaned_data.get('data_models'):
			cleaned_data['data_models'] = []
		
		return cleaned_data
	
	def add_warning(self, message):
		"""Add a non-blocking warning message to the form"""
		if not hasattr(self, 'warnings_list'):
			self.warnings_list = []
		self.warnings_list.append(message)