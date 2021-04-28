from django import forms
from django.forms.widgets import FileInput
from django.contrib.auth import authenticate
from crowdsourcedtagging.models import *
from django.utils.translation import gettext_lazy as _

MAX_UPLOAD_SIZE = 2500000


class UploadImageForm(forms.Form):
    task_name = forms.CharField(max_length=200, label=_("Task Name"))
    task_description = forms.CharField(max_length=200, label=_("Task Description"))
    task_number = forms.IntegerField(min_value=1, max_value=100, label=_("Number of Results to be Collected"))
    task_money = forms.FloatField(min_value=0.01, label=_("Total Money for the Task"))
    task_content = forms.CharField(max_length=65536, label=_("Image URLs"),
                                   widget=forms.Textarea(
                                       attrs={"placeholder": _("Please use enter to separate the image links.")}))


class UploadPOSForm(forms.Form):
    task_name = forms.CharField(max_length=200, label=_("Task Name"))
    task_description = forms.CharField(max_length=200, label=_("Task Description"))
    task_number = forms.IntegerField(min_value=1, max_value=100, label=_("Number of Results to be Collected"))
    task_money = forms.FloatField(min_value=0.01, label=_("Total Money for the Task"))
    task_content = forms.CharField(max_length=65536, label=_("Content"), widget=forms.Textarea)


class AddMoneyForm(forms.Form):
    amount = forms.FloatField(min_value=0.01, label=_("Enter amount"),
                              widget=forms.NumberInput(attrs={'id': 'amount'}))
    add_time = models.DateTimeField(_('date published'), auto_now_add=True)


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('profile_picture',)
        labels = {
            "profile_picture": _("Profile Picture")
        }
        widgets = {
            'profile_picture': FileInput
        }

    def clean(self):
        cleaned_data = super(ProfileForm, self).clean()
        return cleaned_data

    def clean_profile_picture(self):
        avatar = self.cleaned_data['profile_picture']
        if not avatar or not hasattr(avatar, 'content_type'):
            raise forms.ValidationError(_('You must upload a picture'))
        if not avatar.content_type or not avatar.content_type.startswith('image'):
            raise forms.ValidationError(_('File type is not image'))
        if avatar.size > MAX_UPLOAD_SIZE:
            raise forms.ValidationError(_('File too big (max size is ') + MAX_UPLOAD_SIZE + _('bytes'))
        return avatar


class InformationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'date_joined', 'last_login',)
        labels = {
            "username": _("User Name"),
            "email": _("Email Address"),
            "first_name": _("First Name"),
            "last_name": _("Last Name"),
            "You Joined in:": _("Date Joined"),
            "Your Last Login is ": _("Last Login"),
        }
        exclude = ('email',)
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_username', 'readonly': 'readonly'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'id': 'id_email', 'readonly': 'readonly'}),
            "first_name": forms.TextInput(
                attrs={'class': 'form-control', 'id': 'id_first_name', 'readonly': 'readonly'}),
            "last_name": forms.TextInput(attrs={'class': 'form-control', 'id': 'id_last_name', 'readonly': 'readonly'}),
            "date_joined": forms.DateTimeInput(
                attrs={'class': 'form-control', 'id': 'date_joined', 'readonly': 'readonly'}),
            "last_login": forms.DateTimeInput(
                attrs={'class': 'form-control', 'id': 'last_login', 'readonly': 'readonly'}),
        }

    def clean(self):
        cleaned_data = super(InformationForm, self).clean()
        # username = self.cleaned_data['username']
        # email = self.cleaned_data['email']
        # first_name = self.cleaned_data['first_name']
        # last_name = self.cleaned_data['last_name']
        return cleaned_data


class LoginForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'

    username = forms.CharField(max_length=32, label=_("Username"))
    password = forms.CharField(max_length=32, label=_("Password"), widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super(LoginForm, self).clean()
        username = cleaned_data['username']
        password = cleaned_data['password']
        user = authenticate(username=username, password=password)
        if not user:
            raise forms.ValidationError(_("No such username and password combination."))
        return cleaned_data


class RegisterForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'

    username = forms.CharField(max_length=32, label=_("Username"))
    password = forms.CharField(max_length=32, label=_("Password"), widget=forms.PasswordInput)
    confirm_password = forms.CharField(max_length=32, label=_("Confirm Password"), widget=forms.PasswordInput)
    email = forms.CharField(max_length=32, label=_("E-mail"), widget=forms.EmailInput)

    def clean(self):
        cleaned_data = super(RegisterForm, self).clean()
        password1 = cleaned_data['password']
        password2 = cleaned_data['confirm_password']
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(_("Passwords don't match."))
        return cleaned_data

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username__exact=username):
            raise forms.ValidationError(_("Username is already taken."))
        return username
