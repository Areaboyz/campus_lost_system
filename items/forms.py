from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.utils.text import slugify
from .models import LostFoundItem, StudentProfile


class CampusAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label='Username or campus email')

    def clean(self):
        identifier = self.cleaned_data.get('username', '').strip()
        if '@' in identifier:
            username = User.objects.filter(email__iexact=identifier).values_list('username', flat=True).first()
            if username:
                self.cleaned_data['username'] = username
        return super().clean()


class StudentRegistrationForm(UserCreationForm):
    username = forms.CharField(required=False, widget=forms.HiddenInput())
    full_name = forms.CharField(label='Full Name', max_length=150)
    email = forms.EmailField(label='Email Address', required=True)
    phone_number = forms.CharField(label='Phone Number', required=True, max_length=30)
    register_purpose = forms.ChoiceField(label='Why are you registering?', choices=StudentProfile.PURPOSE_CHOICES)
    search_category = forms.ChoiceField(
        label='Primary item category of interest',
        choices=[('', '-- Choose Category to Search --'), *StudentProfile.CATEGORY_CHOICES],
        required=False,
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('email',)

    def clean_full_name(self):
        full_name = ' '.join(self.cleaned_data['full_name'].split())
        if len(full_name.split()) < 2:
            raise forms.ValidationError('Enter your first and last name.')
        return full_name

    def clean_username(self):
        # Keep Django's required username internally, deriving it from the email
        # so new students only need to provide their full name and email.
        base = slugify(self.data.get('email', '').split('@')[0])[:140] or 'student'
        candidate = base
        suffix = 1
        while User.objects.filter(username__iexact=candidate).exists():
            candidate = f'{base}{suffix}'
            suffix += 1
        return candidate

    def clean_email(self):
        email = self.cleaned_data['email'].strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        first_name, *last_names = self.cleaned_data['full_name'].split()
        user.first_name = first_name
        user.last_name = ' '.join(last_names)
        if commit:
            user.save()
            StudentProfile.objects.create(
                user=user,
                phone_number=self.cleaned_data['phone_number'],
                register_purpose=self.cleaned_data['register_purpose'],
                search_category=self.cleaned_data['search_category'],
            )
        return user


class ProfileSettingsForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=False, label='First name', widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=150, required=False, label='Last name', widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=False, label='Email address', widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter an email address'}))

    class Meta:
        model = StudentProfile
        fields = ('first_name', 'last_name', 'email', 'emergency_contact_name', 'emergency_contact_phone', 'profile_picture')
        widgets = {
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.FileInput(attrs={'class': 'profile-picture-input', 'accept': 'image/*'}),
        }

    def __init__(self, *args, user, **kwargs):
        self.user = user
        profile, _created = StudentProfile.objects.get_or_create(user=user)
        super().__init__(*args, instance=profile, **kwargs)
        self.fields['first_name'].initial = user.first_name
        self.fields['last_name'].initial = user.last_name

    def clean_email(self):
        email = self.cleaned_data['email'].strip()
        if email and User.objects.filter(email__iexact=email).exclude(pk=self.user.pk).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def save(self, commit=True):
        profile = super().save(commit=False)
        self.user.first_name = self.cleaned_data['first_name'].strip()
        self.user.last_name = self.cleaned_data['last_name'].strip()
        if self.cleaned_data['email']:
            self.user.email = self.cleaned_data['email']
        if commit:
            self.user.save()
            profile.save()
        return profile


class LostFoundItemForm(forms.ModelForm):
    class Meta:
        model = LostFoundItem
        fields = [
            'title',
            'description',
            'category',
            'status',
            'location',
            # 'image',  <-- COMMENT THIS LINE OUT FOR NOW
        ]
        widgets = {
            'title': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Item Title'}
            ),
            'description': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4,
                    'placeholder': 'Detailed description...',
                }
            ),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'location': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Where was it lost/found?',
                }
            ),
            # 'image': forms.ClearableFileInput(attrs={'class': 'form-control-file'}), <-- COMMENT OUT
        }
