from django import forms
from .models import AcademicSession
class SessionForm(forms.ModelForm):
    class Meta:
        model = AcademicSession
        fields = ['label', 'course_code']
class UploadForm(forms.Form):
    session = forms.ModelChoiceField(queryset=AcademicSession.objects.order_by('-id'))
    kind = forms.ChoiceField(choices=[('workbook', 'Evaluation workbook (.xlsx)'), ('roster', 'Official student roster (.csv)'), ('assignments', 'Evaluator assignments (.csv)')])
    file = forms.FileField()
    def clean_file(self):
        f = self.cleaned_data['file']
        if f.size > 12 * 1024 * 1024: raise forms.ValidationError('Maximum upload is 12 MB.')
        return f
