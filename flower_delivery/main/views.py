from django.shortcuts import render
from .models import Product

def home(request):
    return render(request, 'main/home.html')

def catalog(request):
    products = Product.objects.all()
    return render(request, 'main/catalog.html', {'products': products})
