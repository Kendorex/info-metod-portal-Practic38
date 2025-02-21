from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('upload/', views.upload_file, name='upload'),
    path('search/', views.search_file, name='search'),
    path('about/', views.about, name='about'),
    path('download/<int:file_id>/', views.download_file, name='download'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'), 
    path('logout/', views.custom_logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('approve-files/', views.approve_files, name='approve_files'),  # Одобрение файлов
    path('approve-file/<int:file_id>/', views.approve_file, name='approve_file'),  # Одобрение конкретного файла
    path('reject_file/<int:file_id>/', views.reject_file, name='reject_file'),
    path('delete_file/<int:file_id>/', views.delete_file, name='delete_file'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('file/<int:file_id>/', views.file_detail, name='file_detail'),
    path('file/<int:file_id>/add_comment/', views.add_comment, name='add_comment'),
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
]