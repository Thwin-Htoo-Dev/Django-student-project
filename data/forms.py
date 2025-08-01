from django import forms
from .models import Student
from datetime import date
from django.core.exceptions import ValidationError
import re

class StudentForm(forms.ModelForm):
    phone = forms.CharField(
        max_length=13,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'type': 'tel',
            'placeholder': '+959xxxxxxxxx',
            'pattern': r'^\\+959\\d{7,9}$',  # updated to enforce proper client-side pattern
            'title': 'Phone number must start with +959 and be followed by 7 to 9 digits.',
        })
    )

    class Meta:
        model = Student
        fields = '__all__'
        widgets = {
            'studentid': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter name'
            }),
            'fathername': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Your Father name'
            }),
            'nrc': forms.TextInput(attrs={
                'class': 'form-control',
                'pattern': r'^\\d{1,2}/[A-Za-z]{3,10}\\((N|NA)\\)\\d{6}$',
                'title': 'Example: 1/AGaPa(N)224768',
                'placeholder': '1/AGaPa(N)224768',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Your Email'
            }),
            'state': forms.Select(attrs={'class': 'form-select'}),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Enter Your Address'
            }),
            'dob': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'placeholder': 'Enter Your Birthday'
            }),
            'major': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.pk:
            self.fields['nrc'].widget.attrs['autofocus'] = True
        else:
            self.fields['nrc'].initial = ''
            if not self.initial.get('phone'):
                self.fields['phone'].initial = '+959'

        self.fields['state'].required = True
        self.fields['state'].error_messages = {'required': 'Please select your state.'}
        self.fields['major'].required = True
        self.fields['major'].error_messages = {'required': 'Please select your major.'}

    def clean_nrc(self):
        nrc = self.cleaned_data.get('nrc')
        pattern = r'^\d{1,2}/[A-Za-z]{3,10}\((N|NA)\)\d{6}$'
        if not re.match(pattern, nrc):
            raise forms.ValidationError("Invalid NRC format. Example: 1/AGaPa(N)224768")
        return nrc

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Student.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This email already exists.")
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        pattern = r'^\+959\d{7,9}$'
        if not re.match(pattern, phone):
            raise ValidationError('Phone number must start with +959 and contain 7 to 9 digits.')
        return phone

    def clean_dob(self):
        dob = self.cleaned_data.get('dob')
        today = date.today()
        if not dob:
            raise forms.ValidationError("Date of birth is required.")
        age = (today - dob).days // 365
        if age < 16:
            raise forms.ValidationError("Age must be 16 years or older.")
        return dob

    def clean_state(self):
        state = self.cleaned_data.get('state')
        if not state:
            raise forms.ValidationError("Please select a valid state.")
        return state

    def clean_major(self):
        major = self.cleaned_data.get('major')
        if not major:
            raise forms.ValidationError("Please select a valid major.")
        return major


class ImportForm(forms.Form):
    importFile = forms.FileField()