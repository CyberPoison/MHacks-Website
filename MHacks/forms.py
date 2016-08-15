from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.admin.widgets import AdminFileWidget
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from MHacks.widgets import ArrayFieldSelectMultiple

from models import MHacksUser, Application
from utils import validate_url


class LoginForm(AuthenticationForm):
    username = forms.EmailField(label='Email', max_length=254)
    password = forms.CharField(label='Password', max_length=128, strip=False, widget=forms.PasswordInput)
    password.longest = True

    def confirm_login_allowed(self, user):
        if not user.email_verified:
            error = forms.ValidationError('Email not verified.', code='unverified')
            error.user_pk = urlsafe_base64_encode(force_bytes(user.pk))
            raise error
        if not user.is_active:
            raise forms.ValidationError(
                self.error_messages['inactive'],
                code='inactive',
            )


class RegisterForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super(UserCreationForm, self).__init__(*args, **kwargs)
        self.fields['password2'].label = "Confirm Password"
        self.fields['password2'].longest = True

    class Meta:
        model = MHacksUser
        fields = ('first_name', 'last_name', "email",)


class ApplicationForm(forms.ModelForm):
    gender_other = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'placeholder': 'Other/Other/Other'}))
    gender_other.label = ''
    gender_other.required = False

    race_other = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'placeholder': 'Enter your race'}))
    race_other.label = ''
    race_other.required = False

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')

        super(ApplicationForm, self).__init__(*args, **kwargs)

        self.fields['school'].cols = 10
        self.fields['is_high_school'].cols = 2
        self.fields['is_high_school'].end_row = True
        self.fields['birthday'].end_row = True

        self.fields['major'].end_row = True
        self.fields['grad_date'].end_row = True

        self.fields['race'].cols = 6
        self.fields['gender'].cols = 6
        self.fields['birthday'].demographic = True
        self.fields['race'].previous = True

        self.fields['github'].cols = 6
        self.fields['devpost'].cols = 6
        self.fields['devpost'].end_row = True

        self.fields['personal_website'].cols = 6
        self.fields['resume'].cols = 6
        self.fields['resume'].end_row = True

        self.fields['num_hackathons'].cols = 6
        self.fields['num_hackathons'].end_row = True
        self.fields['num_hackathons'].interests = True

        self.fields['cortex'].short = True

        self.fields['github'].required = False
        self.fields['devpost'].required = False
        self.fields['personal_website'].required = False

        # if the user is from UMich, exclude the short answer and reimbursement/travel fields
        if self.user and 'umich.edu' in self.user.email:
            for key in ['passionate', 'coolest_thing', 'other_info', 'needs_reimbursement', 'can_pay', 'from_city', 'from_state']:
                del self.fields[key]

    class Meta:
        from application_lists import TECH_OPTIONS
        model = Application

        # use all fields except for these
        exclude = ['user', 'deleted', 'score', 'reimbursement', 'submitted']

        labels = {
            'school': 'School or University',
            "grad_date": 'Expected graduation date',
            'birthday': 'Date of birth',
            'is_high_school': 'Are you in high school?',
            'github': '',
            'devpost': '',
            'personal_website': '',
            'cortex': '',
            'passionate': 'Tell us about a project that you worked on and why you\'re proud of it. This doesn\'t have to be a hack! (150 words max)',
            'coolest_thing': 'What do you hope to take away from MHacks 8? (150 words max)',
            'other_info': 'Anything else you want to tell us?',
            'num_hackathons': 'How many hackathons have you attended? (Put 0 if this is your first!)',
            'can_pay': 'How much of the travel costs can you pay?',
            'mentoring': 'Are you interested in mentoring other hackers?',
            'needs_reimbursement': 'Will you be needing travel reimbursement to attend MHacks?',
            'from_city': 'Which city will you be traveling from?',
            'from_state': 'Which state will you be traveling from?',
            'gender': 'Preferred gender pronouns'
        }

        widgets = {
            "grad_date": forms.TextInput(attrs={'placeholder': 'DD/MM/YYYY', 'class': 'form-control input-md'}),
            'cortex': ArrayFieldSelectMultiple(attrs={'class': 'checkbox-inline checkbox-style'}, choices=TECH_OPTIONS),
            'birthday': forms.TextInput(attrs={'placeholder': 'DD/MM/YYYY', 'class': 'form-control input-md'}),
            'school': forms.TextInput(attrs={'placeholder': 'University of ...', 'class': 'form-control input-md'}),
            'major': forms.Select(attrs={'class': 'select_style'}),
            'gender': forms.Select(attrs={'class': 'select_style'}),
            'race': forms.Select(attrs={'class': 'select_style'}),
            'github': forms.TextInput(attrs={'placeholder': 'GitHub', 'class': 'form-control input-md'}),
            'devpost': forms.TextInput(attrs={'placeholder': 'Devpost', 'class': 'form-control input-md'}),
            'personal_website': forms.TextInput(attrs={'placeholder': 'Personal Website', 'class': 'form-control input-md'}),
            'other_info': forms.Textarea(attrs={'class': 'textfield form-control'}),
            'coolest_thing': forms.Textarea(attrs={'class': 'textfield form-control'}),
            'passionate': forms.Textarea(attrs={'class': 'textfield form-control'}),
            'resume': AdminFileWidget(attrs={'class': 'input-md form-control'})
        }

    # custom validator for urls
    def clean_github(self):
        data = self.cleaned_data['github']
        validate_url(data, 'github.com')
        return data

    def clean_devpost(self):
        data = self.cleaned_data['devpost']
        validate_url(data, 'devpost.com')
        return data

    def clean_gender_other(self):
        from application_lists import GENDER_PRONOUNS

        gender_other = self.cleaned_data['gender_other']
        gender = self.cleaned_data['gender']

        if gender == 'other':
            if gender_other and gender_other.count('/') == 2:
                GENDER_PRONOUNS.append((gender_other, gender_other))
                self.cleaned_data['gender'] = gender_other
            else:
                raise forms.ValidationError('Please enter your gender pronouns (e.g. She/Her/Hers).')

        return gender_other

    def clean_race_other(self):
        from application_lists import RACES

        race_other = self.cleaned_data['race_other']
        race = self.cleaned_data['race']

        if race == 'other':
            if race_other:
                RACES.append((race_other, race_other))
                self.cleaned_data['race'] = race_other
            else:
                raise forms.ValidationError('Please enter your race.')

        return race_other
