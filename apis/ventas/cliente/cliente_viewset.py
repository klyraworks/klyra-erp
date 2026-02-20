# apis/ventas/cliente/cliente_viewset.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.db.models import Q, Sum, Count

from apps.ventas.models import Cliente
from apis.ventas.cliente.cliente_serializer import ClienteSerializer
from apis.core.ViewSetBase import TenantViewSet
from utils.mixins.permissions import PermissionCheckMixin

import logging


class ClienteViewSet(PermissionCheckMixin, TenantViewSet):
    """
    ViewSet para gestionar Clientes del ERP.

    Los clientes son DATOS del negocio (no usuarios del sistema).
    Representan a las personas/empresas que compran productos.

    Permisos:
    - view_cliente: Ver clientes (Vendedor, Supervisor, Gerente)
    - add_cliente: Crear clientes (Vendedor, Supervisor, Gerente)
    - change_cliente: Editar clientes (Vendedor, Supervisor, Gerente)
    - delete_cliente: Eliminar clientes (Solo Supervisor y Gerente)
    - ver_historial_compras: Ver historial de compras (Supervisor, Gerente)
    - gestionar_credito: Gestionar límite de crédito (Solo Gerente)
    """
    queryset = Cliente.objects.select_related('persona', 'persona__direccion').all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger('cliente_viewset')

    # ==================== QUERYSET OPTIMIZADO ====================

    def get_queryset(self):
        """
        Optimizar queries y filtrar por empresa del usuario
        """

        return super().get_queryset()

    # ==================== CRUD OPERATIONS ====================

    def list(self, request, *args, **kwargs):
        """
        Listar clientes con filtros.
        Permiso: view_cliente
        """
        try:
            self.verificar_permiso('view_cliente')

            queryset = self.filter_queryset(self.get_queryset())

            # Filtro por tipo de cliente
            tipo = request.query_params.get('tipo', None)
            if tipo in ['natural', 'juridica']:
                queryset = queryset.filter(tipo=tipo)

            # Filtro por estado activo
            activo = request.query_params.get('is_active', None)
            if activo is not None:
                activo_bool = activo.lower() in ['true', '1', 'yes', 'verdadero']
                queryset = queryset.filter(is_active=activo_bool)

            # Filtro por búsqueda general
            search = request.query_params.get('search', None)
            if search:
                queryset = queryset.filter(
                    Q(ruc__icontains=search) |
                    Q(razon_social__icontains=search) |
                    Q(persona__nombre1__icontains=search) |
                    Q(persona__apellido1__icontains=search) |
                    Q(persona__cedula__icontains=search) |
                    Q(persona__email__icontains=search)
                )

            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

        except PermissionDenied as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            self.logger.error(f"Error listando clientes: {str(e)}", extra={
                'action': 'list_clientes',
                'error': str(e)
            })
            return Response(
                {'error': 'Error al obtener la lista de clientes'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def create(self, request, *args, **kwargs):
        """
        Crear un nuevo cliente.
        Permiso: add_cliente
        """
        try:
            self.verificar_permiso('add_cliente')

            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            cliente = serializer.save()

            self.logger.info(
                f"Cliente creado por {request.user.username}: {cliente.id}",
                extra={
                    'cliente_id': cliente.id,
                    'ruc': cliente.ruc,
                    'tipo': cliente.tipo,
                    'creado_por': request.user.username,
                    'action': 'create_cliente'
                }
            )

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        except PermissionDenied as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            self.logger.error(f"Error creando cliente: {str(e)}", extra={
                'action': 'create_cliente',
                'error': str(e),
                'request_data': request.data
            })
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def retrieve(self, request, *args, **kwargs):
        """
        Obtener un cliente específico.
        Permiso: view_cliente
        """
        try:
            self.verificar_permiso('view_cliente')

            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)

        except PermissionDenied as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except Cliente.DoesNotExist:
            return Response(
                {'error': 'Cliente no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            self.logger.error(f"Error obteniendo cliente: {str(e)}", extra={
                'action': 'retrieve_cliente',
                'error': str(e)
            })
            return Response(
                {'error': 'Error al obtener el cliente'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def update(self, request, *args, **kwargs):
        """
        Actualizar completamente un cliente.
        Permiso: change_cliente
        """
        try:
            self.verificar_permiso('change_cliente')

            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            cliente = serializer.save()

            self.logger.info(
                f"Cliente actualizado por {request.user.username}: {cliente.id}",
                extra={
                    'cliente_id': cliente.id,
                    'actualizado_por': request.user.username,
                    'action': 'update_cliente'
                }
            )

            return Response(serializer.data)

        except PermissionDenied as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except Cliente.DoesNotExist:
            return Response(
                {'error': 'Cliente no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            self.logger.error(f"Error actualizando cliente: {str(e)}", extra={
                'action': 'update_cliente',
                'error': str(e)
            })
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def partial_update(self, request, *args, **kwargs):
        """
        Actualizar parcialmente un cliente.
        Permiso: change_cliente
        """
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        Eliminar un cliente (soft delete).
        Permiso: delete_cliente
        """
        try:
            self.verificar_permiso(
                'delete_cliente',
                'Solo Supervisores y Gerentes pueden eliminar clientes'
            )

            instance = self.get_object()
            cliente_id = instance.id
            ruc = instance.ruc

            # Soft delete: desactivar en lugar de eliminar
            instance.is_active = False
            instance.save()

            self.logger.info(
                f"Cliente desactivado por {request.user.username}: {cliente_id}",
                extra={
                    'cliente_id': cliente_id,
                    'ruc': ruc,
                    'desactivado_por': request.user.username,
                    'action': 'delete_cliente'
                }
            )

            return Response(
                {'message': 'Cliente desactivado exitosamente'},
                status=status.HTTP_200_OK
            )

        except PermissionDenied as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except Cliente.DoesNotExist:
            return Response(
                {'error': 'Cliente no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            self.logger.error(f"Error eliminando cliente: {str(e)}", extra={
                'action': 'delete_cliente',
                'error': str(e)
            })
            return Response(
                {'error': 'Error al eliminar el cliente'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ==================== CUSTOM ACTIONS ====================

    @action(detail=False, methods=['get'], url_path='buscar')
    def buscar(self, request):
        """
        Buscar clientes por término de búsqueda.
        GET /api/clientes/buscar/?q=termino
        Permiso: view_cliente
        """
        try:
            self.verificar_permiso('view_cliente')

            query = request.query_params.get('q', '').strip()

            if not query:
                return Response(
                    {'error': 'Parámetro de búsqueda "q" es requerido'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            clientes = self.get_queryset().filter(
                Q(ruc__icontains=query) |
                Q(razon_social__icontains=query) |
                Q(persona__nombre1__icontains=query) |
                Q(persona__apellido1__icontains=query) |
                Q(persona__cedula__icontains=query) |
                Q(persona__email__icontains=query)
            )

            serializer = self.get_serializer(clientes, many=True)

            return Response({
                'count': clientes.count(),
                'results': serializer.data
            })

        except PermissionDenied as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            self.logger.error(f"Error buscando clientes: {str(e)}", extra={
                'action': 'buscar_clientes',
                'error': str(e),
                'query': query
            })
            return Response(
                {'error': 'Error al buscar clientes'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], url_path='activar')
    def activar(self, request, pk=None):
        """
        Activar un cliente.
        POST /api/clientes/{id}/activar/
        Permiso: delete_cliente
        """
        try:
            self.verificar_permiso('delete_cliente')

            cliente = self.get_object()
            cliente.is_active = True
            cliente.save()

            self.logger.info(
                f"Cliente activado por {request.user.username}: {cliente.id}",
                extra={
                    'cliente_id': cliente.id,
                    'activado_por': request.user.username,
                    'action': 'activar_cliente'
                }
            )

            serializer = self.get_serializer(cliente)
            return Response({
                'message': 'Cliente activado exitosamente',
                'cliente': serializer.data
            })

        except PermissionDenied as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except Cliente.DoesNotExist:
            return Response(
                {'error': 'Cliente no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            self.logger.error(f"Error activando cliente: {str(e)}", extra={
                'action': 'activar_cliente',
                'error': str(e)
            })
            return Response(
                {'error': 'Error al activar el cliente'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'], url_path='historial-compras')
    def historial_compras(self, request, pk=None):
        """
        Ver historial de compras de un cliente.
        GET /api/clientes/{id}/historial-compras/
        Permiso: ver_historial_compras
        """
        try:
            self.verificar_permiso(
                'ver_historial_compras',
                'No tienes permiso para ver el historial de compras'
            )

            cliente = self.get_object()

            # Obtener estadísticas de compras
            from apps.ventas.models import Venta

            ventas = Venta.objects.filter(cliente=cliente).order_by('-fecha')

            estadisticas = ventas.aggregate(
                total_compras=Count('id'),
                monto_total=Sum('total'),
                monto_pendiente=Sum('saldo_pendiente')
            )

            # Últimas 10 compras
            ultimas_ventas = ventas[:10].values(
                'id', 'fecha', 'total', 'estado', 'saldo_pendiente'
            )

            return Response({
                'cliente': {
                    'id': cliente.id,
                    'nombre': cliente.razon_social or cliente.persona.full_name(),
                    'ruc': cliente.ruc,
                },
                'estadisticas': estadisticas,
                'ultimas_compras': list(ultimas_ventas)
            })

        except PermissionDenied as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            self.logger.error(f"Error obteniendo historial: {str(e)}", extra={
                'action': 'historial_compras',
                'error': str(e)
            })
            return Response(
                {'error': 'Error al obtener el historial de compras'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], url_path='gestionar-credito')
    def gestionar_credito(self, request, pk=None):
        """
        Gestionar límite de crédito del cliente.
        POST /api/clientes/{id}/gestionar-credito/
        Body: {"limite_credito": 5000.00}
        Permiso: gestionar_credito (Solo Gerente)
        """
        try:
            self.verificar_permiso(
                'gestionar_credito',
                'Solo Gerentes de Ventas pueden gestionar límites de crédito'
            )

            cliente = self.get_object()
            nuevo_limite = request.data.get('limite_credito')

            if nuevo_limite is None:
                return Response(
                    {'error': 'Se requiere el campo "limite_credito"'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                nuevo_limite = float(nuevo_limite)
                if nuevo_limite < 0:
                    raise ValueError("El límite no puede ser negativo")
            except ValueError as e:
                return Response(
                    {'error': f'Límite de crédito inválido: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            limite_anterior = cliente.limite_credito
            cliente.limite_credito = nuevo_limite
            cliente.save()

            self.logger.info(
                f"Límite de crédito actualizado por {request.user.username}",
                extra={
                    'cliente_id': cliente.id,
                    'limite_anterior': float(limite_anterior),
                    'limite_nuevo': nuevo_limite,
                    'modificado_por': request.user.username,
                    'action': 'gestionar_credito'
                }
            )

            return Response({
                'message': 'Límite de crédito actualizado exitosamente',
                'limite_anterior': float(limite_anterior),
                'limite_nuevo': float(cliente.limite_credito),
                'cliente': self.get_serializer(cliente).data
            })

        except PermissionDenied as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            self.logger.error(f"Error gestionando crédito: {str(e)}", extra={
                'action': 'gestionar_credito',
                'error': str(e)
            })
            return Response(
                {'error': 'Error al gestionar el límite de crédito'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )