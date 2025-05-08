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
    assay_type = forms.ModelMultipleChoiceField(
        queryset=AnalysisType.objects.all().order_by('analysis_type_id'),
        required=True,
        label="Assay Type",
        widget=forms.widgets.CheckboxSelectMultiple,
        help_text="Select one or more assay types to include in the export"
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
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        
        # Validate date range
        if start_date and end_date:
            if start_date > end_date:
                raise forms.ValidationError(
                    "Start date must be before or equal to end date."
                )
            
            # Optional: Warn about large date ranges
            date_diff = (end_date - start_date).days
            if date_diff > 90:
                self.add_warning(
                    "Large date range selected. The export may take longer to process and result in a large file."
                )
        
        return cleaned_data
    
    def add_warning(self, message):
        """Add a non-blocking warning message to the form"""
        if not hasattr(self, 'warnings_list'):
            self.warnings_list = []
        self.warnings_list.append(message)