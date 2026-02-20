# apis/core/SerializerBase.py
from rest_framework import serializers
from apps.core.middleware.tenant_middleware import get_current_empresa
import pytz
from django.utils import timezone

class TenantSerializer(serializers.ModelSerializer):
    """Serializer base con manejo automático de empresa"""

    def get_empresa_from_context(self):
        """Obtiene empresa del contexto o del request"""
        # Prioridad 1: Empresa del contexto (middleware)
        empresa = get_current_empresa()
        if empresa:
            return empresa

        # Prioridad 2: Empresa del request
        request = self.context.get('request')
        if request and hasattr(request, 'empresa') and request.empresa:
            return request.empresa

        # Prioridad 3: Empresa del usuario
        if request and request.user.is_authenticated:
            if hasattr(request.user, 'empleado'):
                return request.empresa

        return None

    def get_fecha_empresa(self):
        # Obtener timezone de la empresa
        empresa = self.get_empresa_from_context()
        zona_horaria = pytz.timezone(empresa.timezone)

        # Obtener fecha actual en la zona horaria de la empresa
        fecha_empresa = timezone.now().astimezone(zona_horaria)
        return fecha_empresa

    def create(self, validated_data):
        """Auto-asigna empresa al crear"""
        if 'empresa' not in validated_data:
            empresa = self.get_empresa_from_context()
            if not empresa:
                raise serializers.ValidationError(
                    "No se pudo determinar la empresa. Usuario no asociado a ninguna empresa."
                )
            validated_data['empresa'] = empresa

        return super().create(validated_data)

    def to_representation(self, instance):
        """Oculta el campo empresa en la respuesta (ya lo saben por contexto)"""
        data = super().to_representation(instance)
        # Opcional: remover empresa de la respuesta
        # data.pop('empresa', None)
        return data