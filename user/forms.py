from django import forms
from .models import User, MedicalDetails


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = '__all__'
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
            'password': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
        }



class MedicalDetailsForm(forms.ModelForm):
    class Meta:
        model = MedicalDetails
        fields = [
            'bloodGroup',
            'onGoingMedication',
            'chronicDisease',
            'knownAllergies',
            'familyHistory',
            'medicalReportpdf',
        ]
        def clean_medicalReportpdf(self):
            data = self.cleaned_data['medicalReportpdf']
            if not data:
                data = None
            return data