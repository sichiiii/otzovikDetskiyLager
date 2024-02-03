import os

from .models import Role
from django.conf import settings
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
import uuid


@csrf_exempt
def index(request):
    if request.method == 'POST':
        fio_child = request.POST.get('fio_child')
        city = request.POST.get('city')
        dou_number = request.POST.get('dou_number')
        mentor_fio = request.POST.get('mentor_fio')
        game_situation = request.POST.get('game_situation')
        data_processing_agreement = request.FILES.get('data_processing_agreement')
        photos = request.FILES.getlist('photos[]')
        video = request.FILES.get('video')

        form_folder_name = f'{game_situation}_{fio_child}_' + str(uuid.uuid4())
        form_folder = default_storage.get_available_name(os.path.join(settings.MEDIA_ROOT, form_folder_name))
        form_data_path = os.path.join(form_folder, 'form_data.txt')

        with default_storage.open(form_data_path, 'w') as file:
            file.write(f'ФИО ребенка: {fio_child}\n')
            file.write(f'Город/населенный пункт: {city}\n')
            file.write(f'Номер ДОУ: {dou_number}\n')
            file.write(f'ФИО педагога наставника: {mentor_fio}\n')
            file.write(f'Игровая ситуация: {game_situation}\n')

        default_storage.save(
            os.path.join(form_folder, fio_child + '_' + game_situation + os.path.splitext(data_processing_agreement.name)[1]),
            data_processing_agreement
        )

        photos_paths = []
        count = 0
        for photo in photos:
            photo_path = default_storage.save(
                os.path.join(form_folder, 'photos', fio_child + ' ' + game_situation + ' ' + '(' + str(count) + ')'
                             + os.path.splitext(photo.name)[1]),
                photo
            )
            photos_paths.append(photo_path)
            count += 1

        default_storage.save(
            os.path.join(form_folder, 'videos', fio_child + ' ' + game_situation + os.path.splitext(video.name)[1]),
            video
        )
        return render(request, 'success.html')

    roles = Role.objects.all().values_list('name', flat=True)
    return render(request, 'index.html', {'roles': roles})
