from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

class UploadForm(forms.Form):
    """
    Form to upload GLIMS csv
    """
    
    SEQUENCER_CHOICES = (
        ("NovaSeq", "NovaSeq"),
        ("NextSeq", "NextSeq"),
        ("MiSeq", "MiSeq")
    )

    upload_file = forms.FileField(label="1. Upload your tsv")
    sequencer = forms.ChoiceField(choices=SEQUENCER_CHOICES, label="2. Select the sequencer")
    
    def __init__(self, *args, **kwargs):
        super(UploadForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "POST"
        self.helper.add_input(
            Submit("submit", "Create Samplesheet", css_class="btn btn-info w-100")
            )
