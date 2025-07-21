import os
import uuid
import io
import zipfile
from django.http import HttpResponse, JsonResponse, StreamingHttpResponse
from django.utils.text import slugify

from django.conf import settings
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.contrib import messages
from django.core.mail import send_mail
from .forms import ExpertRegistrationForm, ParticipantRegistrationForm, LoginForm
from .models import Participant, Document, Photo, Video, Volunteer
from .forms import DocumentUploadForm, PhotoUploadForm, VideoUploadForm, VolunteerForm
from django.contrib.auth.decorators import login_required
from .forms import ExpertProfileForm
from .models import Expert
from django.contrib.auth.decorators import user_passes_test
from .models import FestivalStage
from django.utils import timezone
from django.db.models import Count
from django.views.decorators.http import require_POST
from django.contrib.auth import logout
from unidecode import unidecode


def organizer_required(view_func):
    decorated_view_func = user_passes_test(lambda u: u.is_authenticated and hasattr(u, 'role') and u.role == 'organizer')(view_func)
    return decorated_view_func

@organizer_required
def organizer_cabinet(request):
    from collections import defaultdict
    # Эксперты по игровым ситуациям
    experts_by_game = defaultdict(list)
    for expert in Expert.objects.select_related('game_situation').all():
        if expert.game_situation:
            experts_by_game[expert.game_situation.name].append(expert)
    # Участники по игровым ситуациям
    participants_by_game = defaultdict(list)
    for participant in Participant.objects.select_related('game_situation').all():
        if participant.game_situation:
            participants_by_game[participant.game_situation.name].append(participant)
    return render(request, 'organizer_cabinet.html', {
        'experts_by_game': dict(experts_by_game),
        'participants_by_game': dict(participants_by_game),
    })


@csrf_exempt
def index(request):
    # Получаем этапы фестиваля
    stages = {s.name: s for s in FestivalStage.objects.all()}
    now = timezone.now()
    # Для примера: ищем этапы по ключам
    stage_names = [
        'Прием заявок',
        'Прием конкурсных работ',
        'Отборочный этап',
        'Финал',
    ]
    context = {'stages': stages, 'now': now, 'stage_names': stage_names}
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
        form_folder = default_storage.get_available_name(os.path.join(settings.COMPETITORS_URL, form_folder_name))
        os.mkdir('competitors/' + form_folder_name)
        form_data_path = os.path.join(form_folder, 'form_data.txt')

        with default_storage.open(form_data_path, 'w') as file:
            file.write(f'ФИО ребенка: {fio_child}\n')
            file.write(f'Город/населенный пункт: {city}\n')
            file.write(f'Номер ДОУ: {dou_number}\n')
            file.write(f'ФИО педагога наставника: {mentor_fio}\n')
            file.write(f'Игровая ситуация: {game_situation}\n')

        try:
            default_storage.save(
                os.path.join(form_folder, fio_child + '_' + game_situation + os.path.splitext(data_processing_agreement.name)[1]),
                data_processing_agreement
            )
        except:
            pass

        photos_paths = []
        count = 0
        for photo in photos:
            photo_path = default_storage.save(
                os.path.join(form_folder, 'photos',
                             f'{fio_child}_{game_situation}_{count}{os.path.splitext(photo.name)[1]}'),
                photo
            )
            photos_paths.append(photo_path)
            count += 1

        default_storage.save(
            os.path.join(form_folder, 'videos', fio_child + ' ' + game_situation + os.path.splitext(video.name)[1]),
            video
        )
        return render(request, 'success.html')

    return render(request, 'index.html', context)


def success(request):
    return render(request, 'success.html')


def register_expert(request):
    # Проверка этапа
    stage = get_stage('Прием заявок')
    now = timezone.now()
    if not stage or not (stage.start <= now <= stage.end):
        return render(request, 'register_expert.html', {'form': None, 'stage_closed': True, 'stage': stage})

    if request.method == 'POST':
        form = ExpertRegistrationForm(request.POST)
        if form.is_valid():
            expert, login, password = form.save()
            # Отправка email
            send_mail(
                'Регистрация эксперта',
                f'Ваш логин: {login}\nВаш пароль: {password}',
                settings.DEFAULT_FROM_EMAIL,
                [form.cleaned_data['email']],
                fail_silently=False,
            )
            messages.success(request, 'Регистрация успешна! Логин и пароль отправлены на email.')
            return redirect('login')
    else:
        form = ExpertRegistrationForm()
    return render(request, 'register_expert.html', {'form': form, 'stage_closed': False, 'stage': stage})

def get_stage(name):
    return FestivalStage.objects.filter(name=name).first()


def register_participant(request):
    # Проверка этапа
    stage = get_stage('Прием заявок')
    now = timezone.now()
    if not stage or not (stage.start <= now <= stage.end):
        return render(request, 'register_participant.html', {'form': None, 'stage_closed': True, 'stage': stage})

    if request.method == 'POST':
        form = ParticipantRegistrationForm(request.POST)
        if form.is_valid():
            # Лимит по игровой ситуации
            game_situation = form.cleaned_data['game_situation']
            limit = game_situation.limit if game_situation else 20
            count = Participant.objects.filter(game_situation=game_situation).count()
            if count >= limit:
                form.add_error('game_situation', f'Лимит участников ({limit}) по этой игровой ситуации достигнут!')
            else:
                participant, login, password = form.save()
                send_mail(
                    'Регистрация участника',
                    f'Ваш логин: {login}\nВаш пароль: {password}',
                    settings.DEFAULT_FROM_EMAIL,
                    [form.cleaned_data['email']],
                    fail_silently=False,
                )
                messages.success(request, 'Регистрация успешна! Логин и пароль отправлены на email.')
                return redirect('login')
    else:
        form = ParticipantRegistrationForm()
    return render(request, 'register_participant.html', {'form': form, 'stage_closed': False, 'stage': stage})

def login_view(request):
    from django.contrib.auth import login, authenticate
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            # Редирект в кабинет по роли
            if user.role == 'organizer':
                return redirect('organizer_cabinet')
            elif user.role == 'expert':
                return redirect('expert_cabinet')
            elif user.role == 'participant':
                return redirect('participant_cabinet')
            else:
                return redirect('index')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('index')

@login_required
def participant_cabinet(request):
    participant = Participant.objects.get(user=request.user)
    documents = Document.objects.filter(owner_participant=participant)
    photos = Photo.objects.filter(participant=participant)
    videos = Video.objects.filter(participant=participant)
    volunteers = Volunteer.objects.filter(participant=participant)

    doc_form = DocumentUploadForm()
    photo_form = PhotoUploadForm()
    video_form = VideoUploadForm()
    volunteer_form = VolunteerForm()

    # Проверка этапа загрузки работ
    stage = get_stage('Прием конкурсных работ')
    now = timezone.now()
    upload_open = stage and (stage.start <= now <= stage.end)

    # Проверка заполненности анкеты
    required_fields = [
        participant.full_name,
        participant.birth_date,
        participant.dou_name,
        participant.city,
        participant.dou_email,
        participant.dou_phone,
        participant.mentor_name,
        participant.mentor_phone,
        participant.game_situation,
    ]
    profile_complete = all(required_fields)

    # Проверка обязательных документов
    required_doc_types = ['consent_personal', 'consent_photo']
    doc_types_uploaded = set(doc.doc_type for doc in documents)
    docs_complete = all(dt in doc_types_uploaded for dt in required_doc_types)

    allow_upload_media = profile_complete and docs_complete

    # AJAX upload handlers
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        if request.method == 'POST' and 'upload_document' in request.POST and upload_open:
            doc_form = DocumentUploadForm(request.POST, request.FILES)
            if doc_form.is_valid():
                doc = doc_form.save(commit=False)
                doc.owner_participant = participant
                doc.save()
                return JsonResponse({'message': 'Документ загружен!', 'reload': True})
            else:
                return JsonResponse({'message': doc_form.errors.as_text()}, status=400)
        if request.method == 'POST' and 'upload_photo' in request.POST and upload_open and allow_upload_media:
            if photos.count() >= 8:
                return JsonResponse({'message': 'Можно загрузить не более 8 фото!'}, status=400)
            photo_form = PhotoUploadForm(request.POST, request.FILES)
            if photo_form.is_valid():
                photo = photo_form.save(commit=False)
                photo.participant = participant
                photo.save()
                return JsonResponse({'message': 'Фото загружено!', 'reload': True})
            else:
                return JsonResponse({'message': photo_form.errors.as_text()}, status=400)
        if request.method == 'POST' and 'upload_video' in request.POST and upload_open and allow_upload_media:
            if videos.count() >= 1:
                return JsonResponse({'message': 'Можно загрузить только одно видео!'}, status=400)
            video_form = VideoUploadForm(request.POST, request.FILES)
            if video_form.is_valid():
                video = video_form.save(commit=False)
                video.participant = participant
                video.save()
                return JsonResponse({'message': 'Видео загружено!', 'reload': True})
            else:
                return JsonResponse({'message': video_form.errors.as_text()}, status=400)
        return JsonResponse({'message': 'Некорректный запрос'}, status=400)

    # Обычная обработка (без AJAX)
    # Загрузка документа
    if request.method == 'POST' and 'upload_document' in request.POST and upload_open:
        doc_form = DocumentUploadForm(request.POST, request.FILES)
        if doc_form.is_valid():
            doc = doc_form.save(commit=False)
            doc.owner_participant = participant
            doc.save()
            messages.success(request, 'Документ загружен!')
            return redirect('participant_cabinet')

    # Загрузка фото (до 8)
    if request.method == 'POST' and 'upload_photo' in request.POST and upload_open and allow_upload_media:
        if photos.count() >= 8:
            messages.error(request, 'Можно загрузить не более 8 фото!')
        else:
            photo_form = PhotoUploadForm(request.POST, request.FILES)
            if photo_form.is_valid():
                photo = photo_form.save(commit=False)
                photo.participant = participant
                photo.save()
                messages.success(request, 'Фото загружено!')
                return redirect('participant_cabinet')

    # Загрузка видео (1, до 3Гб)
    if request.method == 'POST' and 'upload_video' in request.POST and upload_open and allow_upload_media:
        if videos.count() >= 1:
            messages.error(request, 'Можно загрузить только одно видео!')
        else:
            video_form = VideoUploadForm(request.POST, request.FILES)
            if video_form.is_valid():
                video = video_form.save(commit=False)
                video.participant = participant
                video.save()
                messages.success(request, 'Видео загружено!')
                return redirect('participant_cabinet')

    # Добавление волонтёра (до 5)
    if request.method == 'POST' and 'add_volunteer' in request.POST and upload_open and allow_upload_media:
        if volunteers.count() >= 5:
            messages.error(request, 'Можно добавить не более 5 волонтёров!')
        else:
            volunteer_form = VolunteerForm(request.POST)
            if volunteer_form.is_valid():
                volunteer = volunteer_form.save(commit=False)
                volunteer.participant = participant
                volunteer.save()
                messages.success(request, 'Волонтёр добавлен!')
                return redirect('participant_cabinet')

    return render(request, 'participant_cabinet.html', {
        'participant': participant,
        'documents': documents,
        'photos': photos,
        'videos': videos,
        'volunteers': volunteers,
        'doc_form': doc_form,
        'photo_form': photo_form,
        'video_form': video_form,
        'volunteer_form': volunteer_form,
        'upload_open': upload_open,
        'stage': stage,
        'allow_upload_media': allow_upload_media,
        'profile_complete': profile_complete,
        'docs_complete': docs_complete,
    })

@require_POST
def delete_participant_file(request):
    from django.shortcuts import get_object_or_404
    participant = Participant.objects.get(user=request.user)
    file_type = request.POST.get('file_type')
    file_id = request.POST.get('file_id')
    # Проверка этапа
    stage = get_stage('Прием конкурсных работ')
    now = timezone.now()
    upload_open = stage and (stage.start <= now <= stage.end)
    if not upload_open:
        return JsonResponse({'message': 'Удаление недоступно вне этапа приёма работ.'}, status=403)
    if file_type == 'photo':
        obj = get_object_or_404(Photo, id=file_id, participant=participant)
    elif file_type == 'video':
        obj = get_object_or_404(Video, id=file_id, participant=participant)
    elif file_type == 'document':
        obj = get_object_or_404(Document, id=file_id, owner_participant=participant)
    else:
        return JsonResponse({'message': 'Некорректный тип файла.'}, status=400)
    obj.file.delete(save=False)
    obj.delete()
    return JsonResponse({'message': 'Файл удалён!', 'reload': True})

@require_POST
@login_required
def delete_expert_file(request):
    from django.shortcuts import get_object_or_404
    expert = Expert.objects.get(user=request.user)
    file_type = request.POST.get('file_type')
    file_id = request.POST.get('file_id')
    if file_type == 'document':
        obj = get_object_or_404(Document, id=file_id, owner_expert=expert)
    else:
        return JsonResponse({'message': 'Некорректный тип файла.'}, status=400)
    obj.file.delete(save=False)
    obj.delete()
    return JsonResponse({'message': 'Файл удалён!', 'reload': True})

@login_required
def expert_cabinet(request):
    expert = Expert.objects.get(user=request.user)
    documents = Document.objects.filter(owner_expert=expert)
    doc_form = DocumentUploadForm()
    profile_form = ExpertProfileForm(instance=expert)

    # Проверка этапа приёма работ
    stage = get_stage('Прием конкурсных работ')
    now = timezone.now()
    access_open = stage and (now > stage.end)
    participants = []
    if access_open and expert.game_situation:
        participants = Participant.objects.filter(game_situation=expert.game_situation)

    # Редактирование анкеты и реквизитов
    if request.method == 'POST' and 'save_profile' in request.POST:
        profile_form = ExpertProfileForm(request.POST, instance=expert)
        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, 'Анкета и реквизиты обновлены!')
            return redirect('expert_cabinet')

    # Загрузка документа
    if request.method == 'POST' and 'upload_document' in request.POST:
        doc_form = DocumentUploadForm(request.POST, request.FILES)
        if doc_form.is_valid():
            doc = doc_form.save(commit=False)
            doc.owner_expert = expert
            doc.save()
            messages.success(request, 'Документ загружен!')
            return redirect('expert_cabinet')

    return render(request, 'expert_cabinet.html', {
        'expert': expert,
        'documents': documents,
        'doc_form': doc_form,
        'profile_form': profile_form,
        'access_open': access_open,
        'participants': participants,
        'stage': stage,
    })

def zipfile_generator(file_tuples):
    import io
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for abs_path, arcname, content in file_tuples:
            if abs_path and os.path.exists(abs_path):
                try:
                    zf.write(abs_path, arcname)
                except Exception:
                    continue
            elif content is not None:
                zf.writestr(arcname, content)
    zf.close()
    buf.seek(0)
    yield from buf

@organizer_required
def download_all_zip(request):
    from .models import Expert, Participant
    file_tuples = []
    # Эксперты
    for expert in Expert.objects.select_related('game_situation').all():
        if expert.game_situation:
            base = f"эксперты/{slugify(unidecode(str(expert.game_situation.name)))}/{slugify(unidecode(str(expert.full_name)))}_{expert.id}/"
            # info.txt для эксперта
            info = f"ФИО: {expert.full_name}\nДата рождения: {expert.birth_date}\nТелефон: {expert.phone}\nEmail: {expert.user.email if expert.user else ''}\nИгровая ситуация: {expert.game_situation.name if expert.game_situation else ''}"
            file_tuples.append((None, base + "info.txt", info))
            for doc in expert.document_set.all():
                if doc.file:
                    file_tuples.append((doc.file.path, base + f"{doc.get_doc_type_display()}_{doc.id}.pdf", None))
    # Участники
    for participant in Participant.objects.select_related('game_situation').all():
        if participant.game_situation:
            base = f"участники/{slugify(unidecode(str(participant.game_situation.name)))}/{slugify(unidecode(str(participant.full_name)))}_{participant.id}/"
            # info.txt для участника
            info = f"ФИО: {participant.full_name}\nДата рождения: {participant.birth_date}\nДОУ: {participant.dou_name}\nГород: {participant.city}\nEmail ДОУ: {participant.dou_email}\nТелефон ДОУ: {participant.dou_phone}\nПедагог-наставник: {participant.mentor_name}\nТелефон педагога: {participant.mentor_phone}\nИгровая ситуация: {participant.game_situation.name if participant.game_situation else ''}"
            file_tuples.append((None, base + "info.txt", info))
            for doc in participant.document_set.all():
                if doc.file:
                    file_tuples.append((doc.file.path, base + f"{doc.get_doc_type_display()}_{doc.id}.pdf", None))
            for i, photo in enumerate(participant.photos.all(), 1):
                if photo.file:
                    ext = photo.file.name.split('.')[-1]
                    file_tuples.append((photo.file.path, base + f"фото{i}.{ext}", None))
            for video in participant.videos.all():
                if video.file:
                    ext = video.file.name.split('.')[-1]
                    file_tuples.append((video.file.path, base + f"видео.{ext}", None))
            for v in participant.volunteers.all():
                vinfo = f"волонтер_{slugify(unidecode(str(v.full_name)))}_{v.birth_date}.txt"
                content = f"ФИО: {v.full_name}\nДата рождения: {v.birth_date}"
                file_tuples.append((None, base + vinfo, content))
    response = StreamingHttpResponse(zipfile_generator(file_tuples), content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename=festival_all_materials.zip'
    return response

@organizer_required
def download_game_zip(request, game_type, game_name):
    from .models import Expert, Participant
    file_tuples = []
    if game_type == 'experts':
        for expert in Expert.objects.filter(game_situation__name=game_name):
            base = f"эксперты/{slugify(unidecode(str(game_name)))}/{slugify(unidecode(str(expert.full_name)))}_{expert.id}/"
            info = f"ФИО: {expert.full_name}\nДата рождения: {expert.birth_date}\nТелефон: {expert.phone}\nEmail: {expert.user.email if expert.user else ''}\nИгровая ситуация: {expert.game_situation.name if expert.game_situation else ''}"
            file_tuples.append((None, base + "info.txt", info))
            for doc in expert.document_set.all():
                if doc.file:
                    file_tuples.append((doc.file.path, base + f"{doc.get_doc_type_display()}_{doc.id}.pdf", None))
    elif game_type == 'participants':
        for participant in Participant.objects.filter(game_situation__name=game_name):
            base = f"участники/{slugify(unidecode(str(game_name)))}/{slugify(unidecode(str(participant.full_name)))}_{participant.id}/"
            info = f"ФИО: {participant.full_name}\nДата рождения: {participant.birth_date}\nДОУ: {participant.dou_name}\nГород: {participant.city}\nEmail ДОУ: {participant.dou_email}\nТелефон ДОУ: {participant.dou_phone}\nПедагог-наставник: {participant.mentor_name}\nТелефон педагога: {participant.mentor_phone}\nИгровая ситуация: {participant.game_situation.name if participant.game_situation else ''}"
            file_tuples.append((None, base + "info.txt", info))
            for doc in participant.document_set.all():
                if doc.file:
                    file_tuples.append((doc.file.path, base + f"{doc.get_doc_type_display()}_{doc.id}.pdf", None))
            for i, photo in enumerate(participant.photos.all(), 1):
                if photo.file:
                    ext = photo.file.name.split('.')[-1]
                    file_tuples.append((photo.file.path, base + f"фото{i}.{ext}", None))
            for video in participant.videos.all():
                if video.file:
                    ext = video.file.name.split('.')[-1]
                    file_tuples.append((video.file.path, base + f"видео.{ext}", None))
            for v in participant.volunteers.all():
                vinfo = f"волонтер_{slugify(unidecode(str(v.full_name)))}_{v.birth_date}.txt"
                content = f"ФИО: {v.full_name}\nДата рождения: {v.birth_date}"
                file_tuples.append((None, base + vinfo, content))
    response = StreamingHttpResponse(zipfile_generator(file_tuples), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename={game_type}_{game_name}_materials.zip'
    return response