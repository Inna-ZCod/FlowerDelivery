from django import forms

class OrderForm(forms.Form):
    delivery_address = forms.CharField(label='Адрес доставки', max_length=255)
    additional_notes = forms.CharField(
        label='Дополнительные пожелания',
        widget=forms.Textarea,
        required=False
    )
