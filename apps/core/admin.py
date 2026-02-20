# apps/base/admin.py
from django.contrib import admin
from apps.core.models import Persona

admin.site.register(Persona)