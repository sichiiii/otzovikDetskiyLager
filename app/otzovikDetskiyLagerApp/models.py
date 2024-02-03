from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.db import models


class Role(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


@receiver(post_migrate)
def create_initial_data(sender, **kwargs):
    if sender.name == 'otzovikDetskiyLagerApp':
        if not Role.objects.exists():
            roles = [
                'Воспитатель',
                'Звукооператор',
                'Программист',
                'Инспектор ДПС',
                'Инструктор по физической культуре',
                'Кулинар',
                'Логопед',
                'Медицинская сестра',
                'Механик',
                'Музыкальный руководитель',
                'Овощевод',
                'Официант',
                'Парикмахер',
                'Педагог-психолог',
                'Пекарь',
                'Повар',
                'Продавец',
                'Скульптор',
                'Спасатель',
                'Строитель',
                'Фармацевт',
                'Флорист',
                'Химик',
                'Хореограф',
                'Швея',
            ]

            for role_name in roles:
                Role.objects.create(name='Я - ' + role_name)