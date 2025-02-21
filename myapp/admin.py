from django.contrib import admin
from .models import Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'position', 'examiner')  # Добавьте поле в список отображаемых полей
    list_editable = ('examiner',)  # Позволяет редактировать поле прямо из списка
    search_fields = ('user__username', 'position')  # Поиск по имени пользователя и должности