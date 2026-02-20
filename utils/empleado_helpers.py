# utils/empleado_helpers.py
"""
Helpers para gestión segura de empleados.
Sistema moderno con tokens de activación en lugar de contraseñas temporales.
"""

import secrets
import string
import unicodedata
import logging
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import User


class UsernameGenerator:
    """Generador de usernames automáticos para empleados"""

    @staticmethod
    def remove_accents(text):
        """
        Convierte 'María' → 'Maria', 'José' → 'Jose'

        Args:
            text: String con posibles tildes

        Returns:
            String sin tildes
        """
        nfkd = unicodedata.normalize('NFKD', text)
        return ''.join([c for c in nfkd if not unicodedata.combining(c)])

    @staticmethod
    def generate(nombre, apellido):
        """
        Genera username automático: Primera letra nombre + apellido + contador

        Ejemplos:
            María López → MLOPEZ001
            José García → JGARCIA001
            Ana María Rodríguez → ARODRIGUEZ001

        Args:
            nombre: Primer nombre
            apellido: Primer apellido

        Returns:
            Username único generado (ej: MLOPEZ001)
        """
        logger = logging.getLogger('username_generator')

        # Normalizar y remover tildes
        nombre_clean = UsernameGenerator.remove_accents(nombre)
        apellido_clean = UsernameGenerator.remove_accents(apellido)

        # Generar base sin tildes
        base_username = f"{nombre_clean[0]}{apellido_clean}".upper()

        # Buscar el último número usado para este patrón
        similar_users = User.objects.filter(
            username__istartswith=base_username
        ).order_by('-username')

        if not similar_users.exists():
            counter = 1
        else:
            # Extraer el número más alto
            last_username = similar_users.first().username
            try:
                last_number = int(last_username.replace(base_username, ''))
                counter = last_number + 1
            except (ValueError, AttributeError):
                counter = 1

        username = f"{base_username}{counter:03d}"

        logger.info(
            f"Username generado: {username}",
            extra={'base': base_username, 'counter': counter}
        )

        return username


class PasswordGenerator:
    """
    Generador de contraseñas seguras.
    Solo para casos excepcionales - preferir sistema de tokens.
    """

    @staticmethod
    def generate_secure(length=12):
        """
        Genera contraseña segura aleatoria.

        ️ NOTA: Solo usar para casos excepcionales.
        Para nuevos empleados, usar ActivationTokenGenerator.

        Características:
        - Longitud configurable (default: 12, mínimo: 8)
        - Incluye mayúsculas, minúsculas, números y símbolos
        - Usa secrets module para criptográficamente seguro

        Args:
            length: Longitud de la contraseña (default: 12)

        Returns:
            String con contraseña generada

        Example:
            >>> PasswordGenerator.generate_secure()
            'aB3$xY9@mK2!'
        """
        if length < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres")

        # Alfabeto con letras, números y símbolos seguros
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"

        # Generar password
        password = ''.join(secrets.choice(alphabet) for _ in range(length))

        return password


class ActivationTokenGenerator:
    """
    Generador de tokens de activación seguros.
    Sistema moderno recomendado para onboarding de empleados.

    Ventajas sobre contraseñas temporales:
    - No hay contraseña que interceptar
    - Token de un solo uso
    - Expira automáticamente
    - El usuario elige su propia contraseña
    - Más seguro según NIST y OWASP
    """

    @staticmethod
    def generate(empleado, expiry_hours=24):
        """
        Genera token de activación único para un empleado.

        Args:
            empleado: Instancia de Empleado
            expiry_hours: Horas hasta expiración (default: 24)

        Returns:
            String con el token generado (32 caracteres URL-safe)

        Example:
            >>> token = ActivationTokenGenerator.generate(empleado)
            >>> # Token: "kJ8nH3mQ9pL2xZ7vB4cR6tY1wN5fG0sD"
        """
        from apps.seguridad.models import ActivationToken

        logger = logging.getLogger('activation_token')

        # Invalidar tokens anteriores del mismo empleado
        ActivationToken.objects.filter(
            empleado=empleado,
            usado=False
        ).update(usado=True)

        # Generar nuevo token criptográficamente seguro
        token = secrets.token_urlsafe(32)

        # Calcular fecha de expiración
        expires_at = timezone.now() + timedelta(hours=expiry_hours)

        # Crear registro en BD
        activation = ActivationToken.objects.create(
            empleado=empleado,
            token=token,
            expires_at=expires_at,
            usado=False
        )

        logger.info(
            f"Token de activación generado para {empleado.persona.full_name()}",
            extra={
                'empleado_id': empleado.id,
                'token_id': activation.id,
                'expires_at': expires_at.isoformat()
            }
        )

        return token

    @staticmethod
    def verify(token):
        """
        Verifica validez de un token de activación.

        Validaciones:
        - Token existe en BD
        - No ha sido usado
        - No ha expirado

        Args:
            token: String del token a verificar

        Returns:
            ActivationToken object si es válido, None si es inválido

        Example:
            >>> activation = ActivationTokenGenerator.verify(token)
            >>> if activation:
            >>>     empleado = activation.empleado
        """
        from apps.seguridad.models import ActivationToken

        logger = logging.getLogger('activation_token')

        try:
            activation = ActivationToken.objects.select_related(
                'empleado',
                'empleado__persona'
            ).get(
                token=token,
                usado=False,
                expires_at__gt=timezone.now()
            )

            logger.info(
                f"Token válido verificado",
                extra={
                    'empleado_id': activation.empleado.id,
                    'token_id': activation.id
                }
            )

            return activation

        except ActivationToken.DoesNotExist:
            logger.warning(
                f"Intento de uso de token inválido",
                extra={'token_hash': hash(token)}
            )
            return None

    @staticmethod
    def mark_as_used(activation):
        """
        Marca un token como usado (consumido).
        Previene reutilización del mismo token.

        Args:
            activation: Instancia de ActivationToken
        """
        logger = logging.getLogger('activation_token')

        activation.usado = True
        activation.fecha_uso = timezone.now()
        activation.save()

        logger.info(
            f"Token marcado como usado",
            extra={
                'empleado_id': activation.empleado.id,
                'token_id': activation.id
            }
        )


class OTPGenerator:
    """
    Generador de códigos OTP (One-Time Password).
    Para reset de contraseña por teléfono o SMS.
    """

    @staticmethod
    def generate(length=6):
        """
        Genera código numérico temporal.

        Usado para:
        - Reset de contraseña por teléfono
        - Verificación por SMS
        - 2FA (autenticación de dos factores)

        Args:
            length: Longitud del código (default: 6)

        Returns:
            String con código numérico

        Example:
            >>> otp = OTPGenerator.generate()
            >>> # OTP: "834729"
        """
        if length < 4 or length > 8:
            raise ValueError("OTP debe tener entre 4 y 8 dígitos")

        otp = ''.join([str(secrets.randbelow(10)) for _ in range(length)])
        return otp

    @staticmethod
    def generate_with_expiry(empleado, length=6, expiry_minutes=10):
        """
        Genera OTP y lo guarda en BD con expiración.

        Args:
            empleado: Instancia de Empleado
            length: Longitud del código (default: 6)
            expiry_minutes: Minutos hasta expiración (default: 10)

        Returns:
            String con el OTP generado
        """
        from apps.seguridad.models import OTPToken

        logger = logging.getLogger('otp_generator')

        # Invalidar OTPs anteriores del mismo empleado
        OTPToken.objects.filter(
            empleado=empleado,
            usado=False
        ).update(usado=True)

        # Generar nuevo OTP
        otp = OTPGenerator.generate(length)

        # Calcular fecha de expiración
        expires_at = timezone.now() + timedelta(minutes=expiry_minutes)

        # Crear registro en BD
        otp_token = OTPToken.objects.create(
            empleado=empleado,
            otp=otp,
            expires_at=expires_at,
            usado=False
        )

        logger.info(
            f"OTP generado para {empleado.persona.full_name()}",
            extra={
                'empleado_id': empleado.id,
                'otp_id': otp_token.id,
                'expires_at': expires_at.isoformat()
            }
        )

        return otp

    @staticmethod
    def verify(empleado, otp):
        """
        Verifica validez de un OTP para un empleado.

        Args:
            empleado: Instancia de Empleado
            otp: String con el código a verificar

        Returns:
            True si es válido, False si es inválido
        """
        from apps.seguridad.models import OTPToken

        logger = logging.getLogger('otp_generator')

        try:
            otp_token = OTPToken.objects.get(
                empleado=empleado,
                otp=otp,
                usado=False,
                expires_at__gt=timezone.now()
            )

            # Marcar como usado
            otp_token.usado = True
            otp_token.fecha_uso = timezone.now()
            otp_token.save()

            logger.info(
                f"OTP válido verificado",
                extra={'empleado_id': empleado.id, 'otp_id': otp_token.id}
            )

            return True

        except OTPToken.DoesNotExist:
            logger.warning(
                f"Intento de uso de OTP inválido",
                extra={'empleado_id': empleado.id}
            )
            return False