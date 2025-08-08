from django import forms
from .models import Expert, Participant, User, Document, Photo, Video, Volunteer
from django.contrib.auth.forms import AuthenticationForm
from django.utils.crypto import get_random_string
from datetime import datetime

class ExpertRegistrationForm(forms.ModelForm):
    email = forms.EmailField(label='Электронная почта')
    birth_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label='Дата рождения')

    class Meta:
        model = Expert
        fields = ['full_name', 'birth_date', 'phone', 'game_situation']
        labels = {
            'full_name': 'ФИО',
            'birth_date': 'Дата рождения',
            'phone': 'Телефон',
            'game_situation': 'Игровая ситуация',
        }

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data

    def save(self, commit=True):
        # Генерация логина и пароля
        full_name = self.cleaned_data['full_name']
        birth_date = self.cleaned_data['birth_date']
        initials = ''.join([x[0].upper() for x in full_name.split()[1:]])
        last_name = full_name.split()[0]
        login = f"{initials}{last_name}".replace(' ', '')
        password = f"{login}{birth_date.day}"
        email = self.cleaned_data['email']
        user = User.objects.create_user(username=login, email=email, password=password, role='expert')
        expert = super().save(commit=False)
        expert.user = user
        if commit:
            expert.save()
        return expert, login, password

class ParticipantRegistrationForm(forms.ModelForm):
    email = forms.EmailField(label='Электронная почта')
    birth_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label='Дата рождения')

    class Meta:
        model = Participant
        fields = ['full_name', 'birth_date', 'dou_name', 'city', 'dou_email', 'dou_phone', 'mentor_name', 'mentor_phone', 'game_situation', 'has_volunteers']
        labels = {
            'full_name': 'ФИО',
            'birth_date': 'Дата рождения',
            'dou_name': 'ДОУ',
            'city': 'Город',
            'dou_email': 'Email ДОУ',
            'dou_phone': 'Телефон ДОУ',
            'mentor_name': 'Педагог-наставник',
            'mentor_phone': 'Телефон педагога',
            'game_situation': 'Игровая ситуация',
            'has_volunteers': 'Есть волонтёры',
        }

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data

    def save(self, commit=True):
        # Генерация логина и пароля
        full_name = self.cleaned_data['full_name']
        birth_date = self.cleaned_data['birth_date']
        last_name = full_name.split()[-1]
        login = f"{last_name}{birth_date.strftime('%d%m%Y')}"
        password = login
        email = self.cleaned_data['email']
        user = User.objects.create_user(username=login, email=email, password=password, role='participant')
        participant = super().save(commit=False)
        participant.user = user
        if commit:
            participant.save()
        return participant, login, password

class LoginForm(AuthenticationForm):
    username = forms.CharField(label='Логин')
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput)

class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['doc_type', 'file']
        labels = {
            'doc_type': 'Тип документа',
            'file': 'Файл (PDF)',
        }
    def clean_file(self):
        file = self.cleaned_data['file']
        if not file.name.lower().endswith('.pdf'):
            raise forms.ValidationError('Только PDF-файлы!')
        return file

class PhotoUploadForm(forms.ModelForm):
    class Meta:
        model = Photo
        fields = ['file']
        labels = {
            'file': 'Фотография (JPG, PNG)',
        }
    def clean_file(self):
        file = self.cleaned_data['file']
        if not file.name.lower().endswith(('.jpg', '.jpeg', '.png')):
            raise forms.ValidationError('Только изображения JPG, JPEG, PNG!')
        return file

class VideoUploadForm(forms.ModelForm):
    class Meta:
        model = Video
        fields = ['file']
        labels = {
            'file': 'Видео (MP4, AVI, MOV, MKV)',
        }
    def clean_file(self):
        file = self.cleaned_data['file']
        if not file.name.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
            raise forms.ValidationError('Только видеофайлы!')
        if file.size > 3 * 1024 * 1024 * 1024:
            raise forms.ValidationError('Максимальный размер видео — 3 Гб!')
        return file

class VolunteerForm(forms.ModelForm):
    birth_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label='Дата рождения')
    class Meta:
        model = Volunteer
        fields = ['full_name', 'birth_date']
        labels = {
            'full_name': 'ФИО',
            'birth_date': 'Дата рождения',
        }

class ExpertProfileForm(forms.ModelForm):
    class Meta:
        model = Expert
        fields = ['full_name', 'birth_date', 'phone', 'game_situation', 'bik', 'kor_account', 'ras_account', 'inn', 'kpp', 'bank_name']
        labels = {
            'full_name': 'ФИО',
            'birth_date': 'Дата рождения',
            'phone': 'Телефон',
            'game_situation': 'Игровая ситуация',
            'bik': 'БИК',
            'kor_account': 'Корр. счет',
            'ras_account': 'Расчетный счет',
            'inn': 'ИНН',
            'kpp': 'КПП',
            'bank_name': 'Наименование банка',
        }

    def clean_bik(self):
        bik = self.cleaned_data['bik']
        if bik and len(bik) != 9:
            raise forms.ValidationError('БИК должен содержать 9 цифр')
        return bik
    def clean_kor_account(self):
        val = self.cleaned_data['kor_account']
        if val and len(val) != 20:
            raise forms.ValidationError('Корр. счет должен содержать 20 цифр')
        return val
    def clean_ras_account(self):
        val = self.cleaned_data['ras_account']
        if val and len(val) != 20:
            raise forms.ValidationError('Расчетный счет должен содержать 20 цифр')
        return val
    def clean_inn(self):
        val = self.cleaned_data['inn']
        if val and len(val) not in (10, 12):
            raise forms.ValidationError('ИНН должен содержать 10 или 12 цифр')
        return val
    def clean_kpp(self):
        val = self.cleaned_data['kpp']
        if val and len(val) != 9:
            raise forms.ValidationError('КПП должен содержать 9 цифр')
        return val 