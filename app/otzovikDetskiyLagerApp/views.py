from django.shortcuts import render
from .models import Role
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.http import HttpResponse


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

        data_processing_agreement_path = default_storage.save(f'media/public/{data_processing_agreement.name}',
                                                              data_processing_agreement)
        photos_paths = [default_storage.save(f'media/public/{photo.name}', photo) for photo in photos]
        video_path = default_storage.save(f'media/public/{video.name}', video)
        return HttpResponse('Form submitted successfully!')

    roles = Role.objects.all().values_list('name', flat=True)
    return render(request, 'index.html', {'roles': roles})
