from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate

from libraryaccess.models import Student

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(max_length=60, help_text='Required. Add a valid email address')

    class Meta:
        model = Student
        fields = ("email", "username", "forename", "surname", "password1", "password2")

    def clean_forename(self):
        if self.is_valid():
            forename = self.cleaned_data['forename'].lower()
            return forename

    def clean_surname(self):
        if self.is_valid():
            surname = self.cleaned_data['surname'].lower()
            return surname



class AccountAuthenticationForm(forms.ModelForm):

    password = forms.CharField(label='Password', widget=forms.PasswordInput)

    class Meta:
        model = Student
        fields = ('email', 'password')

    def clean(self):
        if self.is_valid():
            email = self.cleaned_data['email']
            password = self.cleaned_data['password']
            if not authenticate(email=email, password=password):
                raise forms.ValidationError("Invalid login")



class AccountUpdateForm(forms.ModelForm):
    yearGroup_choices = [(7, '7'), (8, '8'), (9, '9'), (10, '10'), (11, '11'), (12, '12'), (13, '13')]
    yearGroup = forms.IntegerField(label='What year group are you in: ', widget=forms.Select(choices=yearGroup_choices), required=False)
    formCode = forms.CharField(max_length = 3, label='What form are you in', required=False)
    studentID = forms.IntegerField(label='What is your student ID number', required=False)

    class Meta:
        model = Student
        fields = ('username', 'forename', 'surname', 'yearGroup', 'formCode', 'studentID')

    def clean_username(self):
        if self.is_valid():
            username = self.cleaned_data['username']
            try:
                account = Student.objects.exclude(pk=self.instance.pk).get(username=username)
            except Student.DoesNotExist:
                return username
            raise forms.ValidationError('Username "%s" is already in use.' % account.username)

    def clean_studentID(self):
        if self.is_valid():
            studentID = self.cleaned_data['studentID']
            try:
                account = Student.objects.exclude(pk=self.instance.pk).get(studentID=studentID)
            except Student.DoesNotExist:
                return studentID
            raise forms.ValidationError('studentID "%s" is already in use.' % account.studentID)

    def clean_forename(self):
        if self.is_valid():
            forename = self.cleaned_data['forename'].lower()
            return forename

    def clean_surname(self):
        if self.is_valid():
            surname = self.cleaned_data['surname'].lower()
            return surname
