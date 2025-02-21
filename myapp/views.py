from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .forms import UploadFileForm, UserSystem
from .models import UploadedFile, Profile
from django.http import FileResponse, Http404
import os
import mimetypes
from urllib.parse import quote
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
import logging
from django.core.files.storage import default_storage
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from .models import Comment, UploadedFile
from .forms import CommentForm


def home(request):
    return render(request, 'home.html')

logger = logging.getLogger(__name__)


@login_required
def edit_profile(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        position = request.POST.get('position')

        user = request.user
        user.username = username
        user.email = email
        user.save()

        profile = user.profile
        profile.phone = phone
        profile.position = position
        profile.save()

        return JsonResponse({
            'success': True,
            'username': user.username,
            'email': user.email,
            'phone': profile.phone,
            'position': profile.position
        })

    return redirect('profile')


def get_user_info(request, user_id):
    user = get_object_or_404(User, id=user_id)
    profile = user.profile
    data = {
        'username': user.username,
        'email': user.email,
        'position': profile.position,
        'phone': profile.phone,
    }
    return JsonResponse(data)

@login_required
def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            files = request.FILES.getlist('file')
            tag = form.cleaned_data.get('tag', '')
            direction = form.cleaned_data.get('direction', '')

            for file in files:
                uploaded_file = UploadedFile(
                    file=file,
                    tag=tag,
                    direction=direction,
                    uploaded_by=request.user,
                    approved=False,
                    rejected=False
                )
                uploaded_file.save()
                send_upload_email(request.user.email, file.name)

            return redirect('home')
    else:
        form = UploadFileForm()
    return render(request, 'upload.html', {'form': form})

def send_upload_email(user_email, file_name):
    subject = 'Файл загружен на Информационно-методический портал "Практик38"'
    message = f'Вы успешно загрузили файл "{file_name}" на Информационно-методический портал "Практик38".\n\nФайл будет проверен, и вы получите уведомление о результатах.'
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [user_email]
    
    send_mail(subject, message, email_from, recipient_list)

def download_file(request, file_id):
    uploaded_file = get_object_or_404(UploadedFile, id=file_id)
    file = uploaded_file.file 

    # Проверяем, существует ли файл на диске
    if not file or not os.path.exists(file.path):
        raise Http404("Файл не найден")
    uploaded_file.download_count += 1
    uploaded_file.save()

    filename = uploaded_file.original_name
    if not filename:
        filename = os.path.basename(file.name)

    content_type, _ = mimetypes.guess_type(filename)
    if content_type is None:
        content_type = 'application/octet-stream'
    encoded_filename = quote(filename)

    response = FileResponse(file.open('rb'), content_type=content_type)
    response['Content-Disposition'] = f'attachment; filename="{encoded_filename}"'
    return response


def file_detail(request, file_id):
    file = get_object_or_404(UploadedFile, id=file_id)
    comments = file.comments.all()
    return render(request, 'file_detail.html', {'file': file, 'comments': comments})

def search_file(request):
    query = request.GET.get('q')
    selected_direction = request.GET.get('direction')
    selected_tag = request.GET.get('tag')


    files = UploadedFile.objects.filter(approved=True)
    if query:
        files = files.filter(name__icontains=query) | files.filter(tag__icontains=query)

    if selected_direction:
        files = files.filter(direction=selected_direction)

    if selected_tag:
        files = files.filter(tag=selected_tag)


    files = files.order_by('-rating')
    for file in files:
        file.rating_percentage = file.rating * 1 
    directions = UploadedFile.objects.values_list('direction', flat=True).distinct()
    tags = UploadedFile.objects.values_list('tag', flat=True).distinct()

    return render(request, 'search.html', {
        'files': files,
        'query': query,
        'directions': directions,
        'tags': tags,
        'selected_direction': selected_direction,
        'selected_tag': selected_tag,
    })

def about(request):
    return render(request, 'about.html')

def register(request):
    if request.method == 'POST':
        form = UserSystem(request.POST)
        if form.is_valid():
            user = form.save() 
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')


            raw_password = form.cleaned_data.get('password1')  # Получаем пароль из формы
            user = authenticate(username=username, password=raw_password)  # Аутентифицируем пользователя
            login(request, user)


            send_registration_email(email, username)

            messages.success(request, f'Аккаунт создан для {username}!')
            return redirect('home') 
    else:
        form = UserSystem()
    return render(request, 'register.html', {'form': form})

def send_registration_email(user_email, username):
    subject = 'Регистрация на Информационно-методическом портале "Практик38"'
    message = f'Здравствуйте, {username}!\n\nВы успешно зарегистрировались на Информационно-методическом портале "Практик38".\n\nСпасибо за регистрацию!'
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [user_email]
    
    send_mail(subject, message, email_from, recipient_list)

@login_required
def profile(request):
    user = request.user
    files_pending = UploadedFile.objects.filter(uploaded_by=user, approved=False, rejected=False)
    files_approved = UploadedFile.objects.filter(uploaded_by=user, approved=True)
    files_rejected = UploadedFile.objects.filter(uploaded_by=user, rejected=True)

    context = {
        'user': user,
        'files_pending': files_pending,
        'files_approved': files_approved,
        'files_rejected': files_rejected,
    }
    return render(request, 'profile.html', context)

@login_required
def approve_files(request):
    if not request.user.profile.examiner and not request.user.is_superuser:
        return redirect('home')  # Если пользователь не экзаменатор и не администратор, перенаправляем его на главную страницу

    profile = request.user.profile

    # Если пользователь администратор, показываем все файлы
    if request.user.is_superuser:
        files_to_approve = UploadedFile.objects.filter(approved=False, rejected=False)
    else:
        # Определяем направление экзаменатора
        if profile.technical_examiner:
            direction = 'техническое'
        elif profile.scientific_examiner:
            direction = 'естественно-научное'
        else:
            direction = None

        if direction:
            files_to_approve = UploadedFile.objects.filter(approved=False, rejected=False, direction=direction)
        else:
            files_to_approve = UploadedFile.objects.none()  # Если направление не указано, показываем пустой список

    return render(request, 'approve_files.html', {'files': files_to_approve})


@login_required
def approve_file(request, file_id):
    if not request.user.profile.examiner:
        return redirect('home')

    if request.method == 'POST':
        file_to_approve = get_object_or_404(UploadedFile, id=file_id)
        rating = request.POST.get('rating', None)

        file_to_approve.approved = True
        file_to_approve.approved_at = timezone.now()
        file_to_approve.rejected = False
        file_to_approve.rejected_at = None
        file_to_approve.rating = rating 
        file_to_approve.save()

        send_status_email(file_to_approve.uploaded_by.email, 'approved', file_to_approve.name)

        messages.success(request, f'Файл "{file_to_approve.name}" успешно одобрен.')
        return redirect('approve_files')

    return redirect('approve_files')

@login_required
def reject_file(request, file_id):
    if not request.user.profile.examiner:
        return redirect('home')

    if request.method == 'POST':
        file_to_reject = get_object_or_404(UploadedFile, id=file_id)
        rejection_reason = request.POST.get('rejection_reason', '')

        file_to_reject.rejected = True
        file_to_reject.rejected_at = timezone.now()
        file_to_reject.approved = False
        file_to_reject.approved_at = None
        file_to_reject.rejection_reason = rejection_reason
        file_to_reject.save()

        send_status_email(file_to_reject.uploaded_by.email, 'rejected', file_to_reject.name, rejection_reason)

        return redirect('approve_files')

    return redirect('approve_files')

@login_required
def delete_file(request, file_id):
    file_to_delete = get_object_or_404(UploadedFile, id=file_id)

    if not (request.user.is_superuser or request.user == file_to_delete.uploaded_by):
        return redirect('home')

    if file_to_delete.file:
        if default_storage.exists(file_to_delete.file.name):
            default_storage.delete(file_to_delete.file.name)

    file_to_delete.delete()

    messages.success(request, f'Файл "{file_to_delete.name}" успешно удален.')
    return redirect('search')

def send_status_email(user_email, status, file_name, rejection_reason=None):
    subject = f'Статус вашего файла: {file_name}'
    if status == 'approved':
        message = f'Ваш файл "{file_name}" был одобрен на Информационно-методическом портале "Практик38".\n\nСпасибо за ваш вклад!'
    elif status == 'rejected':
        message = f'Ваш файл "{file_name}" был отклонен на Информационно-методическом портале "Практик38".\n\nПричина: {rejection_reason}\n\nПожалуйста, исправьте указанные замечания и загрузите файл снова.'
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [user_email]
    
    send_mail(subject, message, email_from, recipient_list)

def custom_logout(request):
    logout(request)
    return redirect('home')


@login_required
def add_comment(request, file_id):
    file = get_object_or_404(UploadedFile, id=file_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.file = file
            comment.author = request.user
            comment.save()
            return redirect('file_detail', file_id=file.id)
    else:
        form = CommentForm()
    return render(request, 'add_comment.html', {'form': form, 'file': file})

@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if request.user == comment.author or request.user.profile.examiner:
        comment.delete()
    return redirect('file_detail', file_id=comment.file.id)

