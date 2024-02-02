from django.shortcuts import render
from .models import Role


def index(request):
    roles = Role.objects.all().values_list('name', flat=True)
    return render(request, 'index.html', {'roles': roles})
