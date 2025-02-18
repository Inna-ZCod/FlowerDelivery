import pytest
from main.forms import ReviewForm

def test_review_form_valid():
    form = ReviewForm(data={"rating": 5, "text": "Отлично!"})
    assert form.is_valid()

def test_review_form_invalid():
    form = ReviewForm(data={"rating": 6, "text": ""})  # Неверный рейтинг
    assert not form.is_valid()