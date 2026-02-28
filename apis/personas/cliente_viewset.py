# apis/personas/cliente_viewset

import logging
from decimal import Decimal
from apps.core.models import Persona

from django.db import transaction
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import action

from apis.core.ViewSetBase import TenantViewSet
from apis.core.response_handler import StandardResponse
from apps.core.decorators import requiere_permiso
from apps.personas.models import Cliente
from apis.personas.cliente_serializer import (
    ClienteCreateSerializer,
    ClienteDetailSerializer,
    ClienteListSerializer,
    ClienteUpdateSerializer,
    SaldoCreditoSerializer,
)


class ClienteViewSet(TenantViewSet):
    """
    ViewSet para gestión de clientes.

    Endpoints:
        GET    /api/personas/clientes/                    - Listar
        POST   /api/personas/clientes/                    - Crear
        GET    /api/personas/clientes/{id}/               - Detalle
        PUT    /api/personas/clientes/{id}/               - Actualizar
        PATCH  /api/personas/clientes/{id}/               - Actualizar parcial
        DELETE /api/personas/clientes/{id}/               - Eliminar
        GET    /api/personas/clientes/buscar/             - Búsqueda para selects
        PATCH  /api/personas/clientes/{id}/cambiar_estado/ - Activar/Desactivar
        GET    /api/personas/clientes/{id}/saldo_credito/  - Consultar saldo de crédito
        GET    /api/personas/clientes/consumidor_final/    - Obtener consumidor final

    Permisos:
        - ver_cliente:      GET (list, retrieve, buscar, saldo_credito, consumidor_final)
        - crear_cliente:    POST
        - editar_cliente:   PUT, PATCH, cambiar_estado
        - eliminar_cliente: DELETE
        - gestionar_credito: saldo_credito
    """

    # ==================== CONFIGURACIÓN ====================
    logger           = logging.getLogger('apis.persona')
    queryset         = Cliente.objects.all()
    serializer_class = ClienteDetailSerializer

    def get_serializer_class(self):
        if self.action == 'list':
            return ClienteListSerializer
        elif self.action == 'retrieve':
            return ClienteDetailSerializer
        elif self.action in ('update', 'partial_update'):
            return ClienteUpdateSerializer
        return ClienteDetailSerializer

    filterset_fields = ['tipo', 'tipo_identificacion', 'is_active']
    search_fields    = ['razon_social', 'identificacion', 'codigo']
    ordering_fields  = ['razon_social', 'codigo', 'created_at']
    ordering         = ['razon_social']

    # ==================== QUERYSET OPTIMIZADO ====================

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'persona',
            'created_by',
            'updated_by',
        )

        tipo = self.request.query_params.get('tipo')
        if tipo:
            queryset = queryset.filter(tipo=tipo)

        tipo_identificacion = self.request.query_params.get('tipo_identificacion')
        if tipo_identificacion:
            queryset = queryset.filter(tipo_identificacion=tipo_identificacion)

        activo = self.request.query_params.get('activo')
        if activo is not None:
            queryset = queryset.filter(is_active=activo.lower() == 'true')

        return queryset

    # ==================== CRUD OPERATIONS ====================

    @requiere_permiso('ver_cliente')
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return StandardResponse.success(data=serializer.data)

        except Exception as e:
            self.logger.error(f"Error al listar clientes: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al obtener clientes",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @requiere_permiso('crear_cliente')
    def create(self, request, *args, **kwargs):
        serializer = ClienteCreateSerializer(
            data=request.data, context={'request': request}
        )
        if not serializer.is_valid():
            self.logger.warning(
                f"Validación fallida al crear cliente | Errores={serializer.errors} | Usuario={request.user.id}"
            )
            return StandardResponse.validation_error(serializer.errors)

        try:
            with transaction.atomic():
                cliente = self._crear_cliente(serializer.validated_data, request)

            self.logger.info(
                f"Cliente creado | ID={cliente.id} | Codigo={cliente.codigo} | Usuario={request.user.id}"
            )
            return StandardResponse.success(
                data=ClienteDetailSerializer(cliente, context={'request': request}).data,
                mensaje="Cliente creado exitosamente",
                status_code=status.HTTP_201_CREATED
            )

        except Exception as e:
            self.logger.error(f"Error al crear cliente: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al crear cliente",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @requiere_permiso('ver_cliente')
    def retrieve(self, request, *args, **kwargs):
        try:
            instancia = self.get_object()
            return StandardResponse.success(
                data=ClienteDetailSerializer(instancia, context={'request': request}).data
            )
        except Exception as e:
            self.logger.error(f"Error al obtener cliente: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al obtener cliente",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @requiere_permiso('editar_cliente')
    def update(self, request, *args, **kwargs):
        try:
            partial   = kwargs.pop('partial', False)
            instancia = self.get_object()
            serializer = ClienteUpdateSerializer(
                instancia, data=request.data,
                partial=partial, context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            instancia = serializer.save()

            self.logger.info(
                f"Cliente actualizado | ID={instancia.id} | Usuario={request.user.id}"
            )
            return StandardResponse.success(
                data=ClienteDetailSerializer(instancia, context={'request': request}).data,
                mensaje="Cliente actualizado exitosamente"
            )

        except Exception as e:
            self.logger.error(f"Error al actualizar cliente: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al actualizar cliente",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @requiere_permiso('editar_cliente')
    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    @requiere_permiso('eliminar_cliente')
    def destroy(self, request, *args, **kwargs):
        try:
            instancia = self.get_object()

            if instancia.es_consumidor_final():
                return StandardResponse.error(
                    mensaje="No se puede eliminar el consumidor final.",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            self.perform_destroy(instancia)
            self.logger.info(
                f"Cliente eliminado | ID={instancia.id} | Usuario={request.user.id}"
            )
            return StandardResponse.success(
                mensaje="Cliente eliminado exitosamente",
                status_code=status.HTTP_204_NO_CONTENT
            )

        except Exception as e:
            self.logger.error(f"Error al eliminar cliente: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al eliminar cliente",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ==================== CUSTOM ACTIONS ====================

    @action(detail=False, methods=['get'])
    @requiere_permiso('ver_cliente')
    def buscar(self, request):
        """
        Búsqueda para selects y autocompletes.
        GET /api/personas/clientes/buscar/?q=texto
        """
        try:
            query = request.query_params.get('q', '').strip()
            if not query:
                return StandardResponse.success(data={'results': [], 'total': 0})

            resultados = self.get_queryset().filter(
                Q(razon_social__icontains=query) |
                Q(identificacion__icontains=query) |
                Q(codigo__icontains=query)
            ).filter(is_active=True)[:20]

            serializer = ClienteListSerializer(resultados, many=True, context={'request': request})
            return StandardResponse.success(data={
                'results': serializer.data,
                'total':   len(serializer.data)
            })

        except Exception as e:
            self.logger.error(f"Error en búsqueda de clientes: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al buscar clientes",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['patch'])
    @requiere_permiso('editar_cliente')
    def cambiar_estado(self, request, pk=None):
        """
        Activa o desactiva un cliente.
        PATCH /api/personas/clientes/{id}/cambiar_estado/
        """
        try:
            instancia = self.get_object()

            if instancia.es_consumidor_final():
                return StandardResponse.error(
                    mensaje="No se puede desactivar el consumidor final.",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            instancia.is_active = not instancia.is_active
            instancia.updated_by = request.user
            instancia.save(update_fields=['is_active', 'updated_by', 'updated_at'])

            estado = "activado" if instancia.is_active else "desactivado"
            self.logger.info(
                f"Cliente {estado} | ID={instancia.id} | Usuario={request.user.id}"
            )
            return StandardResponse.success(
                data={'is_active': instancia.is_active},
                mensaje=f"Cliente {estado} exitosamente"
            )

        except Exception as e:
            self.logger.error(f"Error al cambiar estado del cliente: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al cambiar estado del cliente",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    @requiere_permiso('gestionar_credito')
    def saldo_credito(self, request, pk=None):
        """
        Consulta saldo de crédito de un cliente.
        GET /api/personas/clientes/{id}/saldo_credito/
        """
        try:
            instancia = self.get_object()
            serializer = SaldoCreditoSerializer(instancia)
            return StandardResponse.success(data=serializer.data)

        except Exception as e:
            self.logger.error(f"Error al consultar saldo de crédito: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al consultar saldo de crédito",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    @requiere_permiso('ver_cliente')
    def consumidor_final(self, request):
        """
        Obtiene el consumidor final de la empresa (singleton).
        GET /api/personas/clientes/consumidor_final/
        """
        try:
            cliente = Cliente.get_consumidor_final(request.empresa)
            return StandardResponse.success(
                data=ClienteDetailSerializer(cliente, context={'request': request}).data
            )
        except Exception as e:
            self.logger.error(f"Error al obtener consumidor final: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al obtener consumidor final",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ==================== MÉTODOS AUXILIARES ====================

    def _crear_cliente(self, validated_data: dict, request) -> Cliente:
        persona_id = validated_data.pop('persona_id', None)
        persona_data = validated_data.pop('persona_data', None)

        if persona_data:
            persona = Persona.objects.create(empresa=request.empresa, **persona_data)
            persona_id = persona.id

        cliente = Cliente(
            empresa=request.empresa,
            created_by=request.user,
            persona_id=persona_id,
            **validated_data
        )
        cliente.save()
        return cliente