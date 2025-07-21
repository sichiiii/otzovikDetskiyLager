from django.contrib.auth.models import AbstractUser
from django.db import models

# Роли пользователей
class User(AbstractUser):
    ROLE_CHOICES = [
        ('organizer', 'Организатор'),
        ('expert', 'Эксперт'),
        ('participant', 'Участник'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    # email уже есть в AbstractUser

class GameSituation(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    limit = models.PositiveIntegerField(default=20)
    def __str__(self):
        return self.name

class Expert(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255)
    birth_date = models.DateField()
    phone = models.CharField(max_length=20)
    game_situation = models.ForeignKey(GameSituation, on_delete=models.SET_NULL, null=True, blank=True)
    # банковские реквизиты
    bik = models.CharField('БИК', max_length=9, blank=True)
    kor_account = models.CharField('Корр. счет', max_length=20, blank=True)
    ras_account = models.CharField('Расчетный счет', max_length=20, blank=True)
    inn = models.CharField('ИНН', max_length=12, blank=True)
    kpp = models.CharField('КПП', max_length=9, blank=True)
    bank_name = models.CharField('Наименование банка', max_length=255, blank=True)
    # банковские реквизиты и документы будут позже
    def __str__(self):
        return self.full_name

class Participant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255)
    birth_date = models.DateField()
    dou_name = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    dou_email = models.EmailField()
    dou_phone = models.CharField(max_length=20)
    mentor_name = models.CharField(max_length=255)
    mentor_phone = models.CharField(max_length=20)
    game_situation = models.ForeignKey(GameSituation, on_delete=models.SET_NULL, null=True, blank=True)
    has_volunteers = models.BooleanField(default=False)
    def __str__(self):
        return self.full_name

class Volunteer(models.Model):
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='volunteers')
    full_name = models.CharField(max_length=255)
    birth_date = models.DateField()
    def __str__(self):
        return self.full_name

class Document(models.Model):
    DOC_TYPE_CHOICES = [
        ('regulation', 'Положение'),
        ('consent_personal', 'Согласие на обработку ПД'),
        ('consent_photo', 'Согласие на фото/видео'),
        ('other', 'Другое'),
    ]
    owner_expert = models.ForeignKey(Expert, on_delete=models.CASCADE, null=True, blank=True)
    owner_participant = models.ForeignKey(Participant, on_delete=models.CASCADE, null=True, blank=True)
    doc_type = models.CharField(max_length=30, choices=DOC_TYPE_CHOICES)
    file = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

class Photo(models.Model):
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='photos')
    file = models.ImageField(upload_to='photos/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

class Video(models.Model):
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='videos')
    file = models.FileField(upload_to='videos/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

class FestivalStage(models.Model):
    name = models.CharField(max_length=100)
    start = models.DateTimeField()
    end = models.DateTimeField()
    def __str__(self):
        return self.name