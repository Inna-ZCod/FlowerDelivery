from django import forms
from django.contrib.auth.models import User
from .models import Review


# Форма для регистрации
class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Пароль")
    password_confirm = forms.CharField(widget=forms.PasswordInput, label="Подтверждение пароля")

    class Meta:
        model = User
        fields = ['username']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password != password_confirm:
            raise forms.ValidationError("Пароли не совпадают.")
        return cleaned_data


# Форма оформления заказа
class OrderForm(forms.Form):
    delivery_address = forms.CharField(label='Адрес доставки', max_length=255)
    additional_notes = forms.CharField(
        label='Дополнительные пожелания',
        widget=forms.Textarea,
        required=False
    )


# Форма для отзыва
class ReviewForm(forms.ModelForm):
    rating = forms.ChoiceField(
        choices=[(i, f"{i} ★") for i in range(1, 6)],  # Оценка от 1 до 5 звездочек
        widget=forms.Select(attrs={"class": "form-control"}),
        label = "Оценка"  # ✅ Заменяем "Rating" на "Оценка"
    )
    text = forms.CharField(
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        label="Текст отзыва"
    )

    class Meta:
        model = Review
        fields = ["rating", "text"]