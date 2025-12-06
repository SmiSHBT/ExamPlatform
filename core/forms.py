from django import forms
class UploadTestForm(forms.Form):
    title = forms.CharField(max_length=200)
    file = forms.FileField()
