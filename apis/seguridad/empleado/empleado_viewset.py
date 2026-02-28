# apis/seguridad/empleado/empleado_viewset.py
# ==================== IMPORTS ====================
# Standard library
import logging
import secrets
from datetime import timedelta
from django.conf import settings
# Local
from apis.core.ViewSetBase import TenantViewSet
from apis.core.response_handler import StandardResponse
from apps.core.decorators import requiere_permiso
from apps.core.models import Persona
from apps.rrhh.models import Departamento
from apps.seguridad.models import Empleado, ActivationToken, Rol
from django.contrib.auth.models import User
from django.db import transaction, models
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from utils.empleado_helpers import UsernameGenerator, ActivationTokenGenerator
from functions.services import EmailService
from apis.seguridad.empleado.empleado_serializer import (
    EmpleadoCreateSerializer,
    EmpleadoListSerializer,
    EmpleadoDetailSerializer,
    EmpleadoUpdateSerializer,
    CambiarEstadoSerializer,
    PersonaSerializer
)

class EmpleadoViewSet(TenantViewSet):
    """
    ViewSet para gestión de empleados.

    Endpoints:
        GET    /api/seguridad/empleados/                          - Listar empleados
        POST   /api/seguridad/empleados/                          - Crear empleado
        GET    /api/seguridad/empleados/{id}/                     - Detalle empleado
        PUT    /api/seguridad/empleados/{id}/                     - Actualizar empleado
        PATCH  /api/seguridad/empleados/{id}/                     - Actualizar parcial
        DELETE /api/seguridad/empleados/{id}/                     - Eliminar empleado
        POST   /api/seguridad/empleados/{id}/cambiar_estado/      - Cambiar estado
        POST   /api/seguridad/empleados/{id}/reenviar_activacion/ - Reenviar email
        GET    /api/seguridad/empleados/roles_disponibles/        - Roles de la empresa
        GET    /api/seguridad/empleados/departamentos_disponibles/ - Departamentos

    Permisos:
        - ver_empleados:      GET (list, retrieve)
        - crear_empleados:    POST
        - editar_empleados:   PUT, PATCH, cambiar_estado, reenviar_activacion
        - eliminar_empleados: DELETE
    """

    # ==================== CONFIGURACIÓN ====================
    logger = logging.getLogger('apps.seguridad')
    serializer_class = EmpleadoCreateSerializer
    queryset = Empleado.objects.all()

    def get_serializer_class(self):
        """Serializer según acción"""
        if self.action == 'list':
            return EmpleadoListSerializer
        elif self.action == 'retrieve':
            return EmpleadoDetailSerializer
        elif self.action in ('update', 'partial_update'):
            return EmpleadoUpdateSerializer
        elif self.action == 'cambiar_estado':
            return CambiarEstadoSerializer
        return EmpleadoCreateSerializer

    filterset_fields  = ['estado', 'departamento', 'rol']
    search_fields     = ['codigo', 'persona__nombre1', 'persona__apellido1', 'persona__cedula']
    ordering_fields   = ['codigo', 'persona__apellido1', 'fecha_contratacion', 'created_at']
    ordering          = ['persona__apellido1', 'persona__nombre1']

    # ==================== QUERYSET OPTIMIZADO ====================
    def get_queryset(self):
        """Queryset con select_related para evitar N+1 queries"""
        queryset = super().get_queryset().select_related(
            'persona',
            'usuario',
            'rol',
            'departamento',
            'created_by',
            'updated_by',
        )

        # Filtros adicionales via query params
        estado = self.request.query_params.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)

        solo_activos = self.request.query_params.get('activos')
        if solo_activos == 'true':
            queryset = queryset.filter(estado='activo')

        cuenta_activada = self.request.query_params.get('cuenta_activada')
        if cuenta_activada is not None:
            queryset = queryset.filter(cuenta_activada=cuenta_activada == 'true')

        return queryset

    # ==================== CRUD OPERATIONS ====================

    @requiere_permiso('ver_empleados')
    def list(self, request, *args, **kwargs):
        """Listar empleados con filtros y búsqueda"""
        try:
            queryset = self.filter_queryset(self.get_queryset())

            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return StandardResponse.success(data=serializer.data)

        except Exception as e:
            self.logger.error(f"Error al listar empleados: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al obtener empleados",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @requiere_permiso('crear_empleados')
    def create(self, request, *args, **kwargs):
        """
        Crear empleado completo.

        Flujo transaccional:
            1. Crear Persona
            2. Crear User con UsernameGenerator (si crear_acceso=True)
            3. Crear Empleado
            4. Generar ActivationToken con ActivationTokenGenerator
            5. Enviar email con link de activación vía EmailService (fuera del atomic)
        """
        serializer = EmpleadoCreateSerializer(
            data=request.data,
            context={'request': request}
        )

        if not serializer.is_valid():
            self.logger.warning(
                f"Validación fallida al crear empleado | "
                f"Errores={serializer.errors} | Usuario={request.user.id}"
            )
            return StandardResponse.validation_error(serializer.errors)

        validated = serializer.validated_data
        email_enviado = False

        try:
            with transaction.atomic():
                empleado, token = self._crear_empleado_completo(validated, request)

            # Envío fuera del atomic: un fallo de email no revierte la creación
            if token:
                email_enviado = self._enviar_email_activacion(empleado, token)

            self.logger.info(
                f"Empleado creado | ID={empleado.id} | Codigo={empleado.codigo} | "
                f"Username={empleado.usuario.username if empleado.usuario else 'sin acceso'} | "
                f"Usuario={request.user.id} | EmailEnviado={email_enviado}"
            )

            return StandardResponse.success(
                data={
                    **EmpleadoDetailSerializer(empleado).data,
                    'email_activacion_enviado': email_enviado,
                },
                mensaje=self._mensaje_creacion(empleado, email_enviado),
                status_code=status.HTTP_201_CREATED
            )

        except Exception as e:
            self.logger.error(
                f"Error al crear empleado | Cedula={validated.get('persona', {}).get('cedula')} | "
                f"Error={str(e)}",
                exc_info=True
            )
            return StandardResponse.error(
                mensaje="Error al crear empleado",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @requiere_permiso('ver_empleados')
    def retrieve(self, request, *args, **kwargs):
        """Detalle completo de un empleado"""
        try:
            empleado = self.get_object()
            return StandardResponse.success(
                data=EmpleadoDetailSerializer(empleado).data
            )

        except Exception as e:
            self.logger.error(f"Error al obtener empleado: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al obtener empleado",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @requiere_permiso('editar_empleados')
    def update(self, request, *args, **kwargs):
        """Actualizar datos del empleado"""
        try:
            partial  = kwargs.pop('partial', False)
            empleado = self.get_object()

            serializer = EmpleadoUpdateSerializer(
                empleado,
                data=request.data,
                partial=partial,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)

            empleado = serializer.save(updated_by=request.user)

            self.logger.info(
                f"Empleado actualizado | ID={empleado.id} | Usuario={request.user.id}"
            )

            return StandardResponse.success(
                data=EmpleadoDetailSerializer(empleado).data,
                mensaje="Empleado actualizado exitosamente"
            )

        except Exception as e:
            self.logger.error(f"Error al actualizar empleado: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al actualizar empleado",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @requiere_permiso('editar_empleados')
    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    @requiere_permiso('eliminar_empleados')
    def destroy(self, request, *args, **kwargs):
        """Soft delete del empleado — solo si no está activo"""
        try:
            empleado = self.get_object()

            if empleado.estado == 'activo':
                return StandardResponse.error(
                    mensaje="No se puede eliminar un empleado activo. Cambie su estado primero.",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            empleado.soft_delete(request.user)

            self.logger.info(
                f"Empleado eliminado (soft) | ID={empleado.id} | Usuario={request.user.id}"
            )

            return StandardResponse.success(
                mensaje="Empleado eliminado exitosamente",
                status_code=status.HTTP_204_NO_CONTENT
            )

        except Exception as e:
            self.logger.error(f"Error al eliminar empleado: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al eliminar empleado",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ==================== CUSTOM ACTIONS ====================

    @action(detail=True, methods=['post'])
    @requiere_permiso('editar_empleados')
    def cambiar_estado(self, request, pk=None):
        """
        Cambiar estado del empleado.

        Body:
            {
                "estado": "inactivo",
                "observaciones": "Motivo del cambio"
            }
        """
        try:
            empleado = self.get_object()
            serializer = CambiarEstadoSerializer(
                data=request.data,
                context={'empleado': empleado}
            )
            serializer.is_valid(raise_exception=True)

            estado_anterior = empleado.estado
            empleado.estado = serializer.validated_data['estado']
            empleado.save(update_fields=['estado', 'updated_at'])

            self.logger.info(
                f"Estado cambiado | Empleado={empleado.id} | "
                f"{estado_anterior} → {empleado.estado} | Usuario={request.user.id}"
            )

            return StandardResponse.success(
                data={
                    'estado_anterior': estado_anterior,
                    'estado_nuevo': empleado.estado,
                    'empleado': EmpleadoDetailSerializer(empleado).data,
                },
                mensaje=f"Estado actualizado a '{empleado.get_estado_display()}'"
            )

        except Exception as e:
            self.logger.error(f"Error al cambiar estado: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al cambiar estado del empleado",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    @requiere_permiso('editar_empleados')
    def reenviar_activacion(self, request, pk=None):
        """
        Reenvía email de activación al empleado.
        ActivationTokenGenerator invalida tokens anteriores automáticamente.
        """
        try:
            empleado = self.get_object()

            if not empleado.usuario:
                return StandardResponse.error(
                    mensaje="Este empleado no tiene usuario del sistema asignado.",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            if empleado.cuenta_activada:
                return StandardResponse.info(
                    mensaje="La cuenta de este empleado ya fue activada."
                )

            # ActivationTokenGenerator.generate() invalida tokens anteriores internamente
            token = ActivationTokenGenerator.generate(empleado, expiry_hours=48)
            email_enviado = self._enviar_email_activacion(empleado, token)

            self.logger.info(
                f"Activación reenviada | Empleado={empleado.id} | "
                f"EmailEnviado={email_enviado} | Usuario={request.user.id}"
            )

            return StandardResponse.success(
                data={'email_enviado': email_enviado},
                mensaje=(
                    f"Email de activación enviado a {empleado.persona.email}"
                    if email_enviado else
                    f"Token generado para {empleado.get_full_name()} pero falló el envío del email."
                )
            )

        except Exception as e:
            self.logger.error(f"Error al reenviar activación: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al reenviar email de activación",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    @requiere_permiso('ver_empleados')
    def roles_disponibles(self, request):
        """Lista roles activos disponibles para asignar a empleados"""
        try:
            roles = Rol.objects.filter(
                empresa=request.empresa,
                is_active=True,
                deleted_at__isnull=True
            ).values('id', 'codigo', 'nombre', 'descripcion').order_by('nombre')

            return StandardResponse.success(data={
                'total': roles.count(),
                'roles': list(roles)
            })

        except Exception as e:
            self.logger.error(f"Error al obtener roles: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al obtener roles disponibles",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    @requiere_permiso('ver_empleados')
    def departamentos_disponibles(self, request):
        """Lista departamentos activos disponibles"""
        try:
            departamentos = Departamento.objects.filter(
                empresa=request.empresa,
                is_active=True,
                deleted_at__isnull=True
            ).values('id', 'codigo', 'nombre').order_by('nombre')

            return StandardResponse.success(data={
                'total': departamentos.count(),
                'departamentos': list(departamentos)
            })

        except Exception as e:
            self.logger.error(f"Error al obtener departamentos: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al obtener departamentos disponibles",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    @requiere_permiso('ver_empleados')
    def buscar(self, request):
        """
        Búsqueda rápida de empleados para selects y autocompletes.

        Query params:
            q: Texto a buscar (nombre, apellido, cédula, username, puesto)

        Ejemplo:
            GET api/seguridad/empleados/buscar/?q=carlos
        """
        try:
            query = request.query_params.get('q', '').strip()

            if not query:
                return StandardResponse.success(data={'results': []})

            empleados = self.get_queryset().filter(
                models.Q(persona__nombre1__icontains=query) |
                models.Q(persona__nombre2__icontains=query) |
                models.Q(persona__apellido1__icontains=query) |
                models.Q(persona__apellido2__icontains=query) |
                models.Q(persona__cedula__icontains=query) |
                models.Q(usuario__username__icontains=query) |
                models.Q(puesto__nombre__icontains=query)
            ).filter(
                estado='activo'
            )[:20]  # Limitar resultados para performance

            serializer = EmpleadoListSerializer(empleados, many=True)

            return StandardResponse.success(data={
                'results': serializer.data,
                'total': len(serializer.data)
            })

        except Exception as e:
            self.logger.error(f"Error en búsqueda de empleados: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al buscar empleados",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ==================== MÉTODOS AUXILIARES ====================

    def _crear_empleado_completo(self, validated_data, request):
        """
        Crea la cadena completa Persona → User → Empleado → ActivationToken
        dentro de una transacción atómica.

        Returns:
            tuple: (Empleado, str token | None)
        """
        empresa      = request.empresa
        persona_data = validated_data['persona']
        crear_acceso = validated_data.get('crear_acceso', True)
        puesto       = validated_data['puesto']

        # 1. Crear Persona
        persona = Persona.objects.create(
            empresa=empresa,
            **persona_data
        )

        # 2. Crear User del sistema
        usuario = None
        if crear_acceso:
            usuario = self._crear_usuario_sistema(persona)

        # 3. Crear Empleado
        empleado = Empleado.objects.create(
            empresa=empresa,
            persona=persona,
            usuario=usuario,
            puesto=puesto,
            salario=validated_data['salario'],
            fecha_contratacion=validated_data['fecha_contratacion'],
            estado=validated_data.get('estado', 'activo'),
            rol_id=validated_data.get('rol_id'),
            departamento_id=validated_data.get('departamento_id'),
            debe_cambiar_password=True,
            cuenta_activada=False,
            created_by=request.user,
        )

        # 4. Generar token de activación (retorna str, invalida anteriores)
        token = None
        if usuario:
            token = ActivationTokenGenerator.generate(empleado, expiry_hours=48)

        return empleado, token

    def _crear_usuario_sistema(self, persona):
        """
        Crea el User de Django con contraseña inutilizable.
        Username generado con UsernameGenerator: nombre[0] + apellido + correlativo.

        Ejemplos:
            Carlos Mendoza → CMENDOZA001
            María López    → MLOPEZ001

        Returns:
            User
        """
        username = UsernameGenerator.generate(
            nombre=persona.nombre1,
            apellido=persona.apellido1
        )

        usuario = User.objects.create(
            username=username,
            email=persona.email or '',
            first_name=persona.nombre1 or '',
            last_name=persona.apellido1 or '',
            is_active=False,  # Se activa cuando el empleado confirma el link
        )
        usuario.set_unusable_password()
        usuario.save()

        return usuario

    def _enviar_email_activacion(self, empleado, token):
        """
        Envía email de activación usando EmailService con template HTML.
        Captura excepciones sin propagar para no bloquear la creación.

        Args:
            empleado: Instancia de Empleado
            token: String del token (retornado por ActivationTokenGenerator.generate)

        Returns:
            bool: True si el email fue enviado exitosamente
        """
        try:
            empresa = empleado.empresa
            dominio = f"{empresa.subdominio}.{settings.PARENT_DOMAIN}"
            activation_url = f"http://{dominio}:3000/activar-cuenta/{token}"

            exito, _ = EmailService.send_notification(
                employee=empleado,
                subject_text="Activa tu cuenta en el sistema",
                title=f"¡Bienvenido al {empleado.empresa.nombre_comercial}!",
                subtitle="Tu cuenta ha sido creada exitosamente",
                message=(
                    f"Hola {empleado.persona.nombre1}, tu cuenta está lista. "
                    f"Haz clic en el botón para activarla y definir tu contraseña. "
                    f"Este enlace expira en 48 horas."
                ),
                cta_text="Activar mi cuenta",
                cta_url=activation_url
            )

            return exito

        except Exception as e:
            self.logger.error(
                f"Fallo envío email activación | Empleado={empleado.id} | Error={str(e)}",
                exc_info=True
            )
            return False

    def _mensaje_creacion(self, empleado, email_enviado):
        """Genera mensaje amigable de confirmación según resultado del email"""
        nombre = empleado.get_full_name()
        if email_enviado:
            return (
                f"Empleado '{nombre}' creado exitosamente. "
                f"Se envió email de activación a {empleado.persona.email}."
            )
        elif empleado.usuario:
            return (
                f"Empleado '{nombre}' creado. "
                f"No se pudo enviar el email de activación; use 'Reenviar activación'."
            )
        return f"Empleado '{nombre}' creado exitosamente sin acceso al sistema."