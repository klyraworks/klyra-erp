from rest_framework import serializers
from apps.core.models import Persona
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
import secrets
import string

class PersonaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Persona
        fields = ['id', 'nombre1', 'nombre2', 'apellido1', 'apellido2', 'email', 'telefono', 'direccion', 'cedula', 'pasaporte', 'fecha_nacimiento']

    def validate_cedula(self, value):
        """Validar que la cédula no esté en uso y tenga 10 dígitos"""
        if Persona.objects.filter(document_number=value).exists():
            raise serializers.ValidationError("Ya existe una Persona con esta cédula")
        if len(value) != 10 or not value.isdigit():
            raise serializers.ValidationError("La cédula debe tener exactamente 10 dígitos")
        return value

    def validate_email(self, value):
        """Validar email único"""
        if Persona.objects.filter(email=value).exists():
            raise serializers.ValidationError("Ya existe una Persona con este email")
        return value
