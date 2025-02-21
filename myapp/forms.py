from django import forms
from .models import UploadedFile
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile
from .models import Comment

class UploadFileForm(forms.ModelForm):
    TAG_CHOICES = [
        ('дополнительная общеразвивающая программа', 'Дополнительная общеразвивающая программа'),
        ('программа тематической профильной смены', 'Программа тематической профильной смены'),
        ('учебно-методический комплекс (УМК) к программе', 'Учебно-методический комплекс (УМК) к программе'),
        ('кейс', 'Кейс'),
        ('игра/квиз/квест', 'Игра/Квиз/Квест'),
        ('мастер-класс', 'Мастер-класс'),
        ('открытое занятие', 'Открытое занятие'),
        ('методическая разработка/Методист для педагогов', 'Методическая разработка/Методист для педагогов'),
        ('методические рекомендации', 'Методические рекомендации'),
    ]

    DIRECTION_CHOICES = [
        ('техническая', 'Техническая'),
        ('естественно-научная', 'Естественно-научная'),
    ]

    tag = forms.ChoiceField(
        choices=TAG_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'tag-input'}),
        label="Выберите тег"
    )

    direction = forms.ChoiceField(
        choices=DIRECTION_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'direction-input'}),
        label="Выберите направление"
    )

    class Meta:
        model = UploadedFile
        fields = ['file', 'tag', 'direction']

class UserSystem(UserCreationForm):
    email = forms.EmailField(required=True, label="Email")
    phone = forms.CharField(required=True, label="Номер телефона")
    position = forms.CharField(required=True, label="Должность")

    class Meta:
        model = User
        fields = ("username", "email", "phone", "position", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].help_text = None 
        self.fields['password2'].help_text = None  
        self.fields['password1'].error_messages = {
            'password_too_short': 'Пароль должен содержать не менее 8 символов.',
            'password_too_common': 'Пароль слишком простой.',
            'password_entirely_numeric': 'Пароль не может состоять только из цифр.',
            'password_too_similar': 'Пароль слишком похож на другую личную информацию.',
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            profile = Profile.objects.get(user=user)
            profile.phone = self.cleaned_data["phone"]
            profile.position = self.cleaned_data["position"]
            profile.save()
        return user
    
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']