# apis/ventas/cliente/cliente_serializer.py
from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.ventas.models import Cliente
from apps.core.models import Persona
from apis.core.personas.persona_serializer import PersonaSerializer
from cities_light.models import SubRegion
from apis.core.SerializerBase import TenantSerializer

# Importar validadores reutilizables
from utils.validators import (
    EcuadorianValidators,
    TextNormalizers,
    BusinessValidators,
    SerializerHelpers
)

import logging


class ClienteSerializer(TenantSerializer):
    """
    Serializer para gestión completa de clientes en el ERP.
    Los clientes son DATOS del negocio, NO usuarios del sistema.

    Soporta dos tipos de cliente:
    - Natural: Persona física con cédula
    - Jurídica: Empresa con RUC y razón social
    """

    # READ-ONLY
    persona = PersonaSerializer(read_only=True)

    # WRITE-ONLY - Datos de Persona
    nombre1 = serializers.CharField(write_only=True)
    nombre2 = serializers.CharField(write_only=True, required=False, allow_blank=True)
    apellido1 = serializers.CharField(write_only=True)
    apellido2 = serializers.CharField(write_only=True, required=False, allow_blank=True)
    cedula = serializers.CharField(write_only=True)
    pasaporte = serializers.CharField(write_only=True, required=False, allow_blank=True)
    email = serializers.CharField(write_only=True, required=False, allow_blank=True)
    telefono = serializers.CharField(write_only=True)
    direccion = serializers.PrimaryKeyRelatedField(queryset=SubRegion.objects.all(), write_only=True)
    fecha_nacimiento = serializers.DateField(write_only=True, required=False, allow_null=True)

    # CAMPOS ACTUALIZADOS: Usar identificacion y tipo_identificacion
    ruc = serializers.CharField(write_only=True, required=False, allow_blank=True)
    razon_social = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Cliente
        fields = [
            'id', 'persona',
            'tipo', 'tipo_identificacion', 'identificacion', 'razon_social',
            'limite_credito', 'descuento_porcentaje',
            'email_facturacion', 'telefono_facturacion', 'direccion',
            # Write-only fields
            'nombre1', 'nombre2', 'apellido1', 'apellido2', 'cedula',
            'pasaporte', 'email', 'telefono', 'fecha_nacimiento', 'ruc'
        ]
        read_only_fields = ['id', 'persona', 'tipo_identificacion', 'identificacion']
        extra_kwargs = {
            'ruc': {'required': False, 'allow_blank': True},
            'razon_social': {'required': False, 'allow_blank': True}
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger('cliente_service')

    # ==================== SERIALIZATION ====================

    def to_representation(self, instance):
        """Agrega información enriquecida en la respuesta"""
        data = super().to_representation(instance)

        if instance.persona:
            data['persona'] = {
                'id': instance.persona.id,
                'cedula': instance.persona.cedula,
                'nombre_completo': instance.persona.full_name(),
                'email': instance.persona.email,
                'telefono': instance.persona.telefono
            }

            # Usar helper para dirección
            data['persona']['ciudad'] = SerializerHelpers.build_address_representation(
                instance.persona.ciudad
            )

        data['estado'] = 'Activo' if instance.is_active else 'Inactivo'

        # Nombre completo según tipo de cliente
        data['nombre_completo'] = instance.get_nombre_facturacion()

        # Información de crédito disponible
        data['credito_disponible'] = float(instance.credito_disponible)

        return data

    # ==================== VALIDATIONS ====================

    def validate_cedula(self, value):
        """
        Valida cédula:
        1. Formato (reutilizable)
        2. Unicidad como cliente EN LA MISMA EMPRESA
        """
        # Validar formato
        value = EcuadorianValidators.validate_cedula_format(value)

        # Validar unicidad solo en la empresa actual
        if self.instance and self.instance.persona.cedula == value:
            return value

        empresa = self.get_empresa_from_context()
        if not empresa:
            raise ValidationError("No se pudo determinar la empresa")

        persona_existente = Persona.objects.filter(cedula=value).first()
        if persona_existente:
            # Verificar si ya es cliente de ESTA empresa
            if Cliente.objects.filter(persona=persona_existente, empresa=empresa).exists():
                raise ValidationError(f"La cédula {value} ya está registrada como cliente en esta empresa")

        return value

    def validate_ruc(self, value):
        """
        Valida RUC:
        1. Formato (reutilizable)
        2. Unicidad EN LA MISMA EMPRESA
        """
        if not value:
            return value

        # Validar formato
        value = EcuadorianValidators.validate_ruc_format(value)

        # Validar unicidad en la empresa actual
        if self.instance and self.instance.identificacion == value:
            return value

        empresa = self.get_empresa_from_context()
        if not empresa:
            raise ValidationError("No se pudo determinar la empresa")

        if Cliente.objects.filter(identificacion=value, empresa=empresa).exists():
            raise ValidationError(f"El RUC {value} ya está registrado en esta empresa")

        return value

    def validate_tipo(self, value):
        """Valida el tipo de cliente"""
        if value not in ['natural', 'juridica']:
            raise ValidationError("Tipo debe ser 'natural' o 'juridica'")
        return value

    def validate_limite_credito(self, value):
        """Valida límite de crédito usando validador reutilizable"""
        return BusinessValidators.validate_positive_amount(value, "límite de crédito")

    def validate_descuento_porcentaje(self, value):
        """Valida porcentaje de descuento usando validador reutilizable"""
        return BusinessValidators.validate_percentage(value, "descuento")

    def validate_email(self, value):
        """Normaliza y valida email usando validador reutilizable"""
        return TextNormalizers.normalize_email(value)

    def validate_telefono(self, value):
        """Valida teléfono usando validador reutilizable"""
        if not value:  # Opcional para clientes
            return value
        return EcuadorianValidators.validate_telefono_format(value)

    # ==================== CROSS-FIELD VALIDATION ====================

    def validate(self, attrs):
        """Validaciones cruzadas y mapeo de campos legacy a nuevos"""
        tipo = attrs.get('tipo', 'natural')
        ruc = attrs.get('ruc', '').strip()
        cedula = attrs.get('cedula', '').strip()

        # MAPEO: Determinar tipo_identificacion e identificacion según tipo de cliente
        if tipo == 'juridica':
            # Persona jurídica DEBE tener RUC
            if not ruc:
                raise ValidationError({
                    'ruc': 'El RUC es obligatorio para personas jurídicas'
                })

            razon_social = attrs.get('razon_social', '').strip()
            if not razon_social:
                raise ValidationError({
                    'razon_social': 'La razón social es obligatoria para personas jurídicas'
                })

            # Establecer tipo_identificacion e identificacion
            attrs['tipo_identificacion'] = 'ruc'
            attrs['identificacion'] = ruc

        elif tipo == 'natural':
            if ruc:
                # Natural con RUC: validar que coincida con cédula
                try:
                    EcuadorianValidators.validate_ruc_matches_cedula(ruc, cedula)
                except ValidationError as e:
                    raise ValidationError({'ruc': str(e)})

                attrs['tipo_identificacion'] = 'ruc'
                attrs['identificacion'] = ruc
            else:
                # Natural sin RUC: usar solo cédula
                attrs['tipo_identificacion'] = 'cedula'
                attrs['identificacion'] = cedula

        # Limpiar el campo ruc del dict (ya no se usa en el modelo)
        attrs.pop('ruc', None)

        return attrs

    # ==================== DATA EXTRACTION ====================

    def _extract_person_data(self, validated_data):
        """Extrae campos de Persona usando helper reutilizable"""
        return SerializerHelpers.extract_person_fields(validated_data)

    def _extract_cliente_data(self, validated_data):
        """Extrae solo los campos que pertenecen al modelo Cliente"""
        cliente_fields = [
            'tipo', 'tipo_identificacion', 'identificacion', 'razon_social',
            'limite_credito', 'descuento_porcentaje',
            'email_facturacion', 'telefono_facturacion', 'direccion'
        ]

        cliente_data = {}
        for field in cliente_fields:
            if field in validated_data:
                cliente_data[field] = validated_data[field]

        return cliente_data

    # ==================== CREATE ====================

    def create(self, validated_data):
        """
        Crea cliente con persona en transacción atómica.
        NO crea usuario - los clientes son datos del negocio.
        """
        person_data = self._extract_person_data(validated_data)
        cliente_data = self._extract_cliente_data(validated_data)
        empresa = self.get_empresa_from_context()

        try:
            with transaction.atomic():
                # Crear o reutilizar Persona
                cedula = person_data.get('cedula')
                persona = Persona.objects.filter(cedula=cedula).first()

                if persona:
                    for field, value in person_data.items():
                        setattr(persona, field, value)
                    persona.save()
                    self.logger.info(f"Persona existente reutilizada: {persona.id}")
                else:
                    persona = Persona.objects.create(**person_data)
                    self.logger.info(f"Persona creada: {persona.id}")

                # Mapear email y teléfono para facturación si no se proporcionaron
                if 'email_facturacion' not in cliente_data and person_data.get('email'):
                    cliente_data['email_facturacion'] = person_data['email']

                if 'telefono_facturacion' not in cliente_data and person_data.get('telefono'):
                    cliente_data['telefono_facturacion'] = person_data['telefono']

                # Preparar datos para crear cliente
                cliente_data['persona'] = persona

                # Usar super() para asignar empresa automáticamente
                cliente = super().create(cliente_data)

                self.logger.info(
                    f"Cliente creado: {cliente.id} - {cliente.identificacion}",
                    extra={
                        'cliente_id': cliente.id,
                        'identificacion': cliente.identificacion,
                        'tipo': cliente.tipo,
                        'tipo_identificacion': cliente.tipo_identificacion,
                        'nombre': cliente.get_nombre_facturacion()
                    }
                )

                return cliente

        except Exception as e:
            self.logger.exception(f"Error creando cliente: {str(e)}")
            raise ValidationError(f"Error al crear cliente: {str(e)}")

    # ==================== UPDATE ====================

    def update(self, instance, validated_data):
        """Actualiza cliente con tracking de cambios"""
        person_data = self._extract_person_data(validated_data)
        cliente_data = self._extract_cliente_data(validated_data)

        try:
            with transaction.atomic():
                updates = []

                # 1. Actualizar Persona
                if person_data:
                    for field, value in person_data.items():
                        if getattr(instance.persona, field) != value:
                            setattr(instance.persona, field, value)
                    instance.persona.save()
                    updates.append('persona')

                # 2. Actualizar Cliente
                cambios_criticos = {}
                for field, value in cliente_data.items():
                    old_value = getattr(instance, field)
                    if old_value != value:
                        if field in ['limite_credito', 'descuento_porcentaje']:
                            cambios_criticos[field] = {
                                'anterior': str(old_value),
                                'nuevo': str(value)
                            }
                        setattr(instance, field, value)
                        updates.append(field)

                if updates:
                    instance.save()

                    log_data = {
                        'cliente_id': instance.id,
                        'cambios': updates
                    }

                    if cambios_criticos:
                        log_data['cambios_criticos'] = cambios_criticos

                    self.logger.info(
                        f"Cliente {instance.id} actualizado",
                        extra=log_data
                    )

        except Exception as e:
            self.logger.exception(f"Error actualizando cliente: {str(e)}")
            raise ValidationError(f"Error al actualizar cliente: {str(e)}")

        return instance

"""
Ejemplo de JSON para crear cliente natural:
{
    "tipo": "natural",
    "nombre1": "Juan",
    "apellido1": "Pérez",
    "cedula": "0102030405",
    "email": "jperez@example.com",
    "telefono": "0998765432",
    "direccion": 5,
    "limite_credito": "1000.00",
    "descuento_porcentaje": "5.00"
}
"""