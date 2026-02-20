# utils/validators.py
"""
Validadores reutilizables para serializers.
Funciones puras sin efectos secundarios ni acceso directo a modelos.
"""

import re
import unicodedata
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import EmailValidator
from rest_framework.exceptions import ValidationError


class EcuadorianValidators:
    """Validadores específicos para datos ecuatorianos"""

    @staticmethod
    def validate_cedula_format(value):
        """
        Valida formato de cédula ecuatoriana (10 dígitos).
        NO valida unicidad - eso debe hacerse en el serializer.

        Args:
            value: String con la cédula

        Returns:
            String normalizado (sin espacios)

        Raises:
            ValidationError: Si el formato es inválido
        """
        if not value:
            raise ValidationError("La cédula es requerida")

        value = value.strip()

        if not re.match(r'^\d{10}$', value):
            raise ValidationError("La cédula debe tener 10 dígitos")

        return value

    @staticmethod
    def validate_ruc_format(value):
        """
        Valida formato de RUC ecuatoriano (13 dígitos).
        NO valida unicidad - eso debe hacerse en el serializer.

        Args:
            value: String con el RUC

        Returns:
            String normalizado

        Raises:
            ValidationError: Si el formato es inválido
        """
        if not value:
            raise ValidationError("El RUC es requerido")

        value = value.strip()

        if not re.match(r'^\d{13}$', value):
            raise ValidationError("El RUC debe tener 13 dígitos")

        return value

    @staticmethod
    def validate_ruc_matches_cedula(ruc, cedula):
        """
        Valida que el RUC inicie con el número de cédula.
        Para personas naturales con RUC.

        Args:
            ruc: RUC completo (13 dígitos)
            cedula: Cédula (10 dígitos)

        Raises:
            ValidationError: Si no coinciden
        """
        if len(ruc) == 13 and len(cedula) == 10:
            if ruc[:10] != cedula:
                raise ValidationError("El RUC debe iniciar con el número de cédula")

    @staticmethod
    def validate_telefono_format(value):
        """
        Valida formato de teléfono ecuatoriano.
        Formato: 0 + 9 dígitos (total 10 dígitos)

        Args:
            value: String con el teléfono

        Returns:
            String normalizado

        Raises:
            ValidationError: Si el formato es inválido
        """
        if not value:
            raise ValidationError("El teléfono es requerido")

        value = value.strip()

        if not re.match(r'^0\d{9}$', value):
            raise ValidationError(
                "El teléfono debe tener 10 dígitos y empezar con 0"
            )

        return value


class TextNormalizers:
    """Utilidades para normalización de texto"""

    @staticmethod
    def remove_accents(text):
        """
        Elimina tildes y caracteres especiales.
        'María' → 'Maria', 'José' → 'Jose'

        Args:
            text: String a normalizar

        Returns:
            String sin tildes
        """
        nfkd = unicodedata.normalize('NFKD', text)
        return ''.join([c for c in nfkd if not unicodedata.combining(c)])

    @staticmethod
    def normalize_email(value):
        """
        Normaliza y valida email:
        - Convierte a minúsculas
        - Elimina espacios
        - Elimina tildes y caracteres especiales
        - Valida formato

        Args:
            value: Email a normalizar

        Returns:
            Email normalizado

        Raises:
            ValidationError: Si el formato es inválido
        """
        if not value:
            return value

        # Limpiar y normalizar
        value = value.strip().lower()

        # Normalizar Unicode (ñ -> n, á -> a)
        value = unicodedata.normalize('NFKD', value)
        value = value.encode('ASCII', 'ignore').decode('ASCII')

        # Validar formato
        validator = EmailValidator()
        try:
            validator(value)
        except DjangoValidationError:
            raise ValidationError("Ingrese un email válido")

        return value

    @staticmethod
    def normalize_text(value):
        """
        Normaliza texto:
        - Elimina espacios extra
        - Elimina tildes y caracteres especiales

        Args:
            value: Texto a normalizar

        Returns:
            Texto normalizado
        """
        if not value:
            return value

        # Eliminar espacios extra
        value = ' '.join(value.strip().split())

        # Eliminar tildes y caracteres especiales
        value = TextNormalizers.remove_accents(value)

        return value


class BusinessValidators:
    """Validadores de reglas de negocio generales"""

    @staticmethod
    def validate_positive_amount(value, field_name="valor"):
        """
        Valida que un monto sea positivo.

        Args:
            value: Número a validar
            field_name: Nombre del campo para el mensaje de error

        Raises:
            ValidationError: Si es negativo
        """
        if value < 0:
            raise ValidationError(f"El {field_name} no puede ser negativo")
        return value

    @staticmethod
    def validate_positive_integer(value, field_name="valor"):
        """
        Valida que un entero sea positivo.

        Args:
            value: Número a validar
            field_name: Nombre del campo para el mensaje de error

        Raises:
            ValidationError: Si es negativo o no es entero
        """
        if not isinstance(value, int) or value < 0:
            raise ValidationError(f"El {field_name} debe ser un entero positivo")
        return value

    @staticmethod
    def validate_percentage(value, field_name="porcentaje"):
        """
        Valida que un porcentaje esté entre 0 y 100.

        Args:
            value: Número a validar
            field_name: Nombre del campo para el mensaje de error

        Raises:
            ValidationError: Si está fuera de rango
        """
        if value < 0 or value > 100:
            raise ValidationError(f"El {field_name} debe estar entre 0 y 100")
        return value

    @staticmethod
    def validate_minimum_age(fecha_nacimiento, edad_minima=18):
        """
        Valida edad mínima basada en fecha de nacimiento.

        Args:
            fecha_nacimiento: Date object
            edad_minima: Edad mínima requerida

        Raises:
            ValidationError: Si no cumple la edad mínima
        """
        from datetime import date

        if not fecha_nacimiento:
            raise ValidationError("La fecha de nacimiento es requerida")

        hoy = date.today()
        edad = hoy.year - fecha_nacimiento.year - (
                (hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day)
        )

        if edad < edad_minima:
            raise ValidationError(
                f"Debe ser mayor de {edad_minima} años (edad actual: {edad})"
            )

        if edad > 100:
            raise ValidationError("La fecha de nacimiento no es válida")

        return fecha_nacimiento

    @staticmethod
    def validate_minimum_salary(value, minimo=460):
        """
        Valida salario mínimo legal.

        Args:
            value: Salario a validar
            minimo: Salario mínimo legal

        Raises:
            ValidationError: Si es menor al mínimo
        """
        if value is None:
            raise ValidationError("El salario es requerido")

        if value <= 0:
            raise ValidationError("El salario debe ser mayor a 0")

        if value < minimo:
            raise ValidationError(
                f"El salario no puede ser menor al mínimo legal (${minimo})"
            )

        return value

    @staticmethod
    def validate_past_date(value, field_name="fecha"):
        """
        Valida que una fecha no sea futura.

        Args:
            value: Date a validar
            field_name: Nombre del campo para el mensaje

        Raises:
            ValidationError: Si es fecha futura
        """
        from datetime import date

        if not value:
            raise ValidationError(f"La {field_name} es requerida")

        if value > date.today():
            raise ValidationError(f"La {field_name} no puede ser futura")

        return value


class SerializerHelpers:
    """Helpers comunes para serializers"""

    @staticmethod
    def extract_person_fields(validated_data):
        """
        Extrae campos de Persona del validated_data.
        Útil para serializers que manejan Persona + otra entidad.

        Args:
            validated_data: Dict con datos validados

        Returns:
            Dict con solo los campos de Persona
        """
        person_fields = [
            'nombre1', 'nombre2', 'apellido1', 'apellido2', 'cedula',
            'pasaporte', 'email', 'telefono', 'direccion', 'fecha_nacimiento'
        ]

        return {
            field: validated_data.pop(field)
            for field in person_fields
            if field in validated_data
        }

    @staticmethod
    def build_address_representation(direccion):
        """
        Construye representación enriquecida de dirección.

        Args:
            direccion: Objeto SubRegion

        Returns:
            Dict con información de la dirección
        """
        if not direccion:
            return None

        return {
            'id': direccion.id,
            'name': direccion.name,
            'region': direccion.region.name if direccion.region else '',
            'country': direccion.country.name if direccion.country else ''
        }


# ============== EJEMPLO DE USO ==============

"""
# En tu serializer:

from utils.validators import (
    EcuadorianValidators,
    TextNormalizers,
    BusinessValidators,
    SerializerHelpers
)

class ClienteSerializer(serializers.ModelSerializer):

    def validate_cedula(self, value):
        # Validar formato (reutilizable)
        value = EcuadorianValidators.validate_cedula_format(value)

        # Validar unicidad (específico del modelo)
        if self.instance and self.instance.persona.cedula == value:
            return value

        persona = Persona.objects.filter(cedula=value).first()
        if persona and hasattr(persona, 'cliente'):
            raise ValidationError(f"La cédula {value} ya está registrada")

        return value

    def validate_email(self, value):
        return TextNormalizers.normalize_email(value)

    def validate_telefono(self, value):
        return EcuadorianValidators.validate_telefono_format(value)

    def validate_limite_credito(self, value):
        return BusinessValidators.validate_positive_amount(
            value, 
            "límite de crédito"
        )

    def _extract_person_data(self, validated_data):
        return SerializerHelpers.extract_person_fields(validated_data)
"""