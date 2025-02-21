from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


class UploadedFile(models.Model):
    DIRECTION_CHOICES = [
        ('техническая', 'Техническа'),
        ('естественно-научная', 'Естественно-научная'),
    ]

    file = models.FileField(upload_to='uploads/')
    original_name = models.CharField(max_length=255, blank=True)
    name = models.CharField(max_length=255, blank=True)
    tag = models.CharField(max_length=100, blank=True)
    direction = models.CharField(max_length=100, choices=DIRECTION_CHOICES, blank=True, verbose_name="Направление")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    approved = models.BooleanField(default=False)
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected = models.BooleanField(default=False)
    rejected_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True, verbose_name="Причина отклонения")
    rating = models.IntegerField(null=True, blank=True, verbose_name="Рейтинг")
    download_count = models.PositiveIntegerField(default=0, verbose_name="Количество скачиваний")  # Новое поле

    def save(self, *args, **kwargs):
        if not self.original_name:
            self.original_name = self.file.name
        if not self.name:
            self.name = self.original_name
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name or self.file.name

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    position = models.CharField(max_length=100, null=True, blank=True, verbose_name="Должность")
    examiner = models.BooleanField(default=False, verbose_name="Экзаменатор")
    technical_examiner = models.BooleanField(default=False, verbose_name="Технический экзаменатор")
    scientific_examiner = models.BooleanField(default=False, verbose_name="Естественно-научный экзаменатор")

    def __str__(self):
        return f'Профиль {self.user.username}'

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


class Comment(models.Model):
    file = models.ForeignKey(UploadedFile, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'Комментарий от {self.author.username} к файлу {self.file.name}'