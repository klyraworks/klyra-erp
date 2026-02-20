# apis/inventario/categoria/categoria_viewset.py
import logging
import json
from django.db import transaction
from django.db.models import Count, Q
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError

from apis.core.ViewSetBase import TenantViewSet
from apis.core.response_handler import StandardResponse
from apps.core.decorators import requiere_permiso
from apps.inventario.models import Categoria, Producto
from .categoria_serializer import (
    CategoriaSerializer,
    CategoriaListSerializer,
    CategoriaSimpleSerializer,
    CategoriaTreeSerializer
)


class CategoriaViewSet(TenantViewSet):
    """
    ViewSet para gestión de Categorías de productos (jerárquicas)

    Endpoints:
        GET    /api/inventario/categorias/              - Listar categorías
        POST   /api/inventario/categorias/              - Crear categoría
        GET    /api/inventario/categorias/{id}/         - Detalle categoría
        PUT    /api/inventario/categorias/{id}/         - Actualizar categoría
        PATCH  /api/inventario/categorias/{id}/         - Actualizar parcial
        DELETE /api/inventario/categorias/{id}/         - Eliminar categoría
        POST   /api/inventario/categorias/{id}/activar/ - Reactivar categoría
        POST   /api/inventario/categorias/bulk_create/  - Crear múltiples categorías
        GET    /api/inventario/categorias/arbol/        - Vista de árbol jerárquico
        GET    /api/inventario/categorias/{id}/subcategorias/ - Listar subcategorías
        GET    /api/inventario/categorias/{id}/productos/ - Productos de la categoría
        GET    /api/inventario/categorias/principales/  - Solo categorías nivel 1

    Permisos:
        - ver_categorias: GET (list, retrieve)
        - crear_categorias: POST
        - editar_categorias: PUT, PATCH
        - eliminar_categorias: DELETE
        - ver_jerarquia_categorias: árbol, subcategorías
    """

    # ==================== CONFIGURACIÓN ====================
    logger = logging.getLogger('apps.inventario')
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer

    def get_serializer_class(self):
        """Serializer según acción"""
        if self.action == 'list':
            return CategoriaListSerializer
        elif self.action == 'arbol':
            return CategoriaTreeSerializer
        elif self.action in ['principales', 'subcategorias', 'bulk_create']:
            return CategoriaSimpleSerializer
        return CategoriaSerializer

    filterset_fields = ['nivel', 'categoria_padre', 'is_active']
    search_fields = ['nombre', 'codigo', 'descripcion']
    ordering_fields = ['nombre', 'codigo', 'nivel', 'created_at']
    ordering = ['nivel', 'nombre']

    # ==================== QUERYSET OPTIMIZADO ====================
    def get_queryset(self):
        """Queryset con joins optimizados"""
        queryset = super().get_queryset().select_related(
            'categoria_padre',
            'created_by',
            'updated_by'
        ).prefetch_related(
            'categorias_hijas'
        )

        # Anotar con conteos
        queryset = queryset.annotate(
            total_productos=Count('productos', filter=Q(productos__deleted_at__isnull=True)),
            total_subcategorias=Count('categorias_hijas', filter=Q(categorias_hijas__deleted_at__isnull=True,
                                                                   categorias_hijas__is_active=True))
        )

        return queryset

    # ==================== CRUD OPERATIONS ====================

    @requiere_permiso('ver_categorias')
    def list(self, request, *args, **kwargs):
        """Listar categorías con filtros"""
        try:
            queryset = self.filter_queryset(self.get_queryset())

            # Solo activas por defecto
            if request.query_params.get('incluir_inactivas') != 'true':
                queryset = queryset.filter(is_active=True)

            # Filtro por nivel
            nivel = request.query_params.get('nivel')
            if nivel:
                queryset = queryset.filter(nivel=nivel)

            # Filtro por categoría padre
            padre_id = request.query_params.get('padre_id')
            if padre_id:
                queryset = queryset.filter(categoria_padre_id=padre_id)

            # Solo raíces (sin padre)
            solo_raices = request.query_params.get('solo_raices')
            if solo_raices == 'true':
                queryset = queryset.filter(categoria_padre__isnull=True)

            # Búsqueda adicional
            search = request.query_params.get('search')
            if search:
                queryset = queryset.filter(
                    Q(codigo__icontains=search) |
                    Q(nombre__icontains=search) |
                    Q(descripcion__icontains=search)
                )

            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return StandardResponse.success(data=serializer.data)

        except Exception as e:
            self.logger.error(f"Error al listar categorías: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al obtener categorías",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @requiere_permiso('crear_categorias')
    def create(self, request, *args, **kwargs):
        """Crear nueva categoría"""
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            categoria = serializer.save()

            self.logger.info(
                f"Categoría creada | ID={categoria.id} | "
                f"Codigo={categoria.codigo} | Nombre={categoria.nombre} | "
                f"Nivel={categoria.nivel} | Usuario={request.user.id}"
            )

            return StandardResponse.success(
                data=CategoriaSerializer(categoria).data,
                mensaje="Categoría creada exitosamente",
                status_code=status.HTTP_201_CREATED
            )

        except ValidationError as e:
            self.logger.warning(f"Validación fallida: {e.detail}")
            return StandardResponse.validation_error(e.detail)
        except Exception as e:
            self.logger.error(f"Error al crear categoría: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al crear categoría",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @requiere_permiso('ver_categorias')
    def retrieve(self, request, *args, **kwargs):
        """Obtener detalle de categoría"""
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return StandardResponse.success(data=serializer.data)
        except Exception as e:
            self.logger.error(f"Error al obtener categoría: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al obtener categoría",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @requiere_permiso('editar_categorias')
    def update(self, request, *args, **kwargs):
        """Actualizar categoría completa"""
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()

            serializer = self.get_serializer(
                instance,
                data=request.data,
                partial=partial
            )
            serializer.is_valid(raise_exception=True)
            categoria = serializer.save()

            self.logger.info(
                f"Categoría actualizada | ID={categoria.id} | Usuario={request.user.id}"
            )

            return StandardResponse.success(
                data=CategoriaSerializer(categoria).data,
                mensaje="Categoría actualizada exitosamente"
            )

        except ValidationError as e:
            return StandardResponse.validation_error(e.detail)
        except Exception as e:
            self.logger.error(f"Error al actualizar: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al actualizar categoría",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @requiere_permiso('eliminar_categorias')
    def destroy(self, request, *args, **kwargs):
        """Eliminar categoría (soft delete)"""
        try:
            instance = self.get_object()

            # Validar que no tenga productos activos
            productos_activos = Producto.objects.filter(
                categoria=instance,
                is_active=True,
                deleted_at__isnull=True
            ).count()

            if productos_activos > 0:
                return StandardResponse.error(
                    mensaje=f"No se puede eliminar la categoría porque tiene {productos_activos} producto(s) asociado(s)",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            # Validar que no tenga subcategorías activas
            subcategorias_activas = instance.categorias_hijas.filter(
                is_active=True,
                deleted_at__isnull=True
            ).count()

            if subcategorias_activas > 0:
                return StandardResponse.error(
                    mensaje=f"No se puede eliminar la categoría porque tiene {subcategorias_activas} subcategoría(s)",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            # Soft delete
            self.perform_destroy(instance)

            self.logger.info(
                f"Categoría eliminada | ID={instance.id} | Codigo={instance.codigo} | "
                f"Usuario={request.user.id}"
            )

            return StandardResponse.success(
                mensaje="Categoría eliminada exitosamente",
                status_code=status.HTTP_204_NO_CONTENT
            )

        except Exception as e:
            self.logger.error(f"Error al eliminar: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al eliminar categoría",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ==================== CUSTOM ACTIONS ====================

    @action(detail=True, methods=['post'])
    @requiere_permiso('editar_categorias')
    def activar(self, request, pk=None):
        """Reactivar categoría desactivada"""
        try:
            categoria = self.get_object()

            if categoria.is_active:
                return StandardResponse.info(
                    mensaje="La categoría ya está activa",
                    data=CategoriaSerializer(categoria).data
                )

            categoria.is_active = True
            categoria.save(update_fields=['is_active', 'updated_at'])

            self.logger.info(
                f"Categoría reactivada | ID={categoria.id} | Codigo={categoria.codigo} | "
                f"Usuario={request.user.id}"
            )

            return StandardResponse.success(
                data=CategoriaSerializer(categoria).data,
                mensaje="Categoría reactivada exitosamente"
            )

        except Exception as e:
            self.logger.error(f"Error al activar categoría: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al activar categoría",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    @requiere_permiso('crear_categorias')
    def bulk_create(self, request):
        """
        Crear múltiples categorías en una sola operación

        IMPORTANTE: Procesa por niveles (padres primero)

        Body: Array de objetos categoría
        [
            {"nombre": "Electrónica", "descripcion": "..."},
            {"nombre": "Computadoras", "categoria_padre": "id_electronica"},
        ]
        """
        try:
            if not isinstance(request.data, list):
                return StandardResponse.error(
                    mensaje="Se esperaba un array de categorías",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            if len(request.data) == 0:
                return StandardResponse.error(
                    mensaje="El array no puede estar vacío",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            if len(request.data) > 100:
                return StandardResponse.error(
                    mensaje="No se pueden crear más de 100 categorías a la vez",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            categorias_creadas = []
            errores = []

            # Separar por niveles para procesamiento
            sin_padre = []
            con_padre = []

            for idx, cat_data in enumerate(request.data):
                if cat_data.get('categoria_padre'):
                    con_padre.append((idx, cat_data))
                else:
                    sin_padre.append((idx, cat_data))

            # Procesar primero las que no tienen padre
            for idx, categoria_data in sin_padre:
                try:
                    serializer = CategoriaSerializer(
                        data=categoria_data,
                        context={'request': request}
                    )
                    serializer.is_valid(raise_exception=True)
                    categoria = serializer.save()

                    categorias_creadas.append({
                        'id': str(categoria.id),
                        'codigo': categoria.codigo,
                        'nombre': categoria.nombre,
                        'nivel': categoria.nivel
                    })

                except ValidationError as e:
                    errores.append({
                        'index': idx,
                        'nombre': categoria_data.get('nombre', 'Sin nombre'),
                        'errores': e.detail
                    })
                except Exception as e:
                    self.logger.error(
                        f"Error crítico en bulk create | Index={idx} | Error={str(e)}",
                        exc_info=True
                    )
                    raise

            # Luego procesar las que tienen padre
            for idx, categoria_data in con_padre:
                try:
                    serializer = CategoriaSerializer(
                        data=categoria_data,
                        context={'request': request}
                    )
                    serializer.is_valid(raise_exception=True)
                    categoria = serializer.save()

                    categorias_creadas.append({
                        'id': str(categoria.id),
                        'codigo': categoria.codigo,
                        'nombre': categoria.nombre,
                        'nivel': categoria.nivel
                    })

                except ValidationError as e:
                    errores.append({
                        'index': idx,
                        'nombre': categoria_data.get('nombre', 'Sin nombre'),
                        'errores': e.detail
                    })
                except Exception as e:
                    self.logger.error(
                        f"Error crítico en bulk create | Index={idx} | Error={str(e)}",
                        exc_info=True
                    )
                    raise

            self.logger.info(
                f"Bulk create categorías | Creadas={len(categorias_creadas)} | "
                f"Errores={len(errores)} | Usuario={request.user.id}"
            )

            return StandardResponse.bulk_result(
                creados=categorias_creadas,
                errores=errores,
                recurso="categoría",
                recurso_genero="f"
            )

        except Exception as e:
            self.logger.error(f"Error en bulk create: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al crear categorías en lote",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    @requiere_permiso('ver_categorias')
    def arbol_expandido(self, request):
        """Todas las categorías con sus subcategorías (árbol expandido)"""
        try:
            categorias = self.get_queryset().order_by('-created_at')
            serializer = CategoriaTreeSerializer(categorias, many=True)

            return StandardResponse.success(data={
                'total_categorias': categorias.count(),
                'categorias': serializer.data
            })

        except Exception as e:
            self.logger.error(f"Error al obtener árbol expandido: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al obtener categoría",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    @requiere_permiso('ver_categorias')
    def estadisticas(self, request):
        """Estadísticas generales de categorías"""
        try:
            categorias = self.get_queryset()

            stats = {
                'total': categorias.count(),
                'por_nivel': {},
                'con_mas_productos': [],
                'sin_productos': categorias.annotate(
                    productos_count=Count('productos', filter=Q(productos__deleted_at__isnull=True))
                ).filter(productos_count=0).count()
            }

            for nivel in range(1, 6):
                count = categorias.filter(nivel=nivel).count()
                if count > 0:
                    stats['por_nivel'][f'nivel_{nivel}'] = count

            top_categorias = categorias.annotate(
                productos_count=Count('productos', filter=Q(productos__deleted_at__isnull=True))
            ).order_by('-productos_count')[:5]

            stats['con_mas_productos'] = [{
                'id': str(cat.id),
                'nombre': cat.nombre,
                'productos': cat.productos_count
            } for cat in top_categorias]

            return StandardResponse.success(data=stats)

        except Exception as e:
            self.logger.error(f"Error al obtener estadísticas: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al obtener estadísticas",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'], url_path='crear-con-subcategorias')
    @requiere_permiso('crear_categorias')
    def crear_con_subcategorias(self, request):
        """Crear categoría principal con sus subcategorías"""
        try:
            content_type = request.content_type

            if 'multipart/form-data' in content_type:
                try:
                    categoria_data = json.loads(request.data.get('categoria', '{}'))
                    subcategorias_nuevas = json.loads(request.data.get('subcategorias_nuevas', '[]'))
                    subcategorias_existentes = json.loads(request.data.get('subcategorias_existentes', '[]'))
                except (json.JSONDecodeError, TypeError) as e:
                    return StandardResponse.error(
                        mensaje=f'Error al parsear datos JSON: {str(e)}',
                        status_code=status.HTTP_400_BAD_REQUEST
                    )
                if 'imagen' in request.FILES:
                    categoria_data['imagen'] = request.FILES['imagen']
            else:
                categoria_data = request.data.get('categoria', {})
                subcategorias_nuevas = request.data.get('subcategorias_nuevas', [])
                subcategorias_existentes = request.data.get('subcategorias_existentes', [])

            with transaction.atomic():
                serializer = CategoriaSerializer(data=categoria_data, context={'request': request})
                serializer.is_valid(raise_exception=True)
                categoria_principal = serializer.save()

                subcategorias_creadas, subcategorias_enlazadas, errores = [], [], []

                for idx, sub_data in enumerate(subcategorias_nuevas):
                    try:
                        sub_data['categoria_padre'] = str(categoria_principal.id)
                        sub_serializer = CategoriaSerializer(data=sub_data, context={'request': request})
                        if sub_serializer.is_valid():
                            subcategoria = sub_serializer.save()
                            subcategorias_creadas.append({
                                'id': str(subcategoria.id),
                                'codigo': subcategoria.codigo,
                                'nombre': subcategoria.nombre,
                                'nivel': subcategoria.nivel
                            })
                        else:
                            errores.append(
                                {'index': idx, 'nombre': sub_data.get('nombre', ''), 'errores': sub_serializer.errors})
                    except Exception as e:
                        errores.append({'index': idx, 'nombre': sub_data.get('nombre', ''), 'error': str(e)})

                if subcategorias_existentes:
                    for cat in Categoria.objects.filter(id__in=subcategorias_existentes, is_active=True).exclude(
                            id=categoria_principal.id):
                        padre_temp, es_ciclo = categoria_principal.categoria_padre, False
                        while padre_temp:
                            if str(padre_temp.id) == str(cat.id):
                                es_ciclo = True
                                break
                            padre_temp = padre_temp.categoria_padre
                        if not es_ciclo:
                            cat.categoria_padre = categoria_principal
                            cat.nivel = categoria_principal.nivel + 1
                            cat.save()
                            subcategorias_enlazadas.append(
                                {'id': str(cat.id), 'nombre': cat.nombre, 'codigo': cat.codigo, 'nivel': cat.nivel})
                        else:
                            errores.append({'nombre': cat.nombre, 'error': 'Crearía un ciclo en la jerarquía'})

                return StandardResponse.success(
                    data={
                        'categoria': {'id': str(categoria_principal.id), 'codigo': categoria_principal.codigo,
                                      'nombre': categoria_principal.nombre, 'nivel': categoria_principal.nivel},
                        'subcategorias_creadas': subcategorias_creadas,
                        'subcategorias_enlazadas': subcategorias_enlazadas,
                        'total_subcategorias': len(subcategorias_creadas) + len(subcategorias_enlazadas),
                        **(({'errores_subcategorias': errores}) if errores else {})
                    },
                    mensaje=f"Categoría creada exitosamente{f' (con {len(errores)} errores en subcategorías)' if errores else ''}",
                    status_code=status.HTTP_201_CREATED
                )

        except ValidationError as e:
            return StandardResponse.validation_error(e.detail)
        except Exception as e:
            self.logger.error(f"Error al crear categoría con subcategorías: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje=f'Error al crear categoría: {str(e)}',
                status_code=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['patch'], url_path='actualizar-con-subcategorias')
    @requiere_permiso('editar_categorias')
    def actualizar_con_subcategorias(self, request, pk=None):
        """Actualizar categoría y gestionar subcategorías"""
        try:
            instance = self.get_object()
            content_type = request.content_type

            if 'multipart/form-data' in content_type:
                try:
                    categoria_data = json.loads(request.data.get('categoria', '{}'))
                    subcategorias_nuevas = json.loads(request.data.get('subcategorias_nuevas', '[]'))
                    subcategorias_existentes = json.loads(request.data.get('subcategorias_existentes', '[]'))
                except (json.JSONDecodeError, TypeError) as e:
                    return StandardResponse.error(
                        mensaje=f'Error al parsear datos JSON: {str(e)}',
                        status_code=status.HTTP_400_BAD_REQUEST
                    )
                if 'imagen' in request.FILES:
                    categoria_data['imagen'] = request.FILES['imagen']
            else:
                categoria_data = request.data.get('categoria', {})
                subcategorias_nuevas = request.data.get('subcategorias_nuevas', [])
                subcategorias_existentes = request.data.get('subcategorias_existentes', [])

            with transaction.atomic():
                serializer = CategoriaSerializer(instance, data=categoria_data, partial=True,
                                                 context={'request': request})
                serializer.is_valid(raise_exception=True)
                categoria_actualizada = serializer.save()

                subcategorias_creadas, subcategorias_enlazadas, errores = [], [], []

                for idx, sub_data in enumerate(subcategorias_nuevas):
                    try:
                        sub_data['categoria_padre'] = str(categoria_actualizada.id)
                        sub_serializer = CategoriaSerializer(data=sub_data, context={'request': request})
                        if sub_serializer.is_valid():
                            subcategoria = sub_serializer.save()
                            subcategorias_creadas.append({'id': str(subcategoria.id), 'codigo': subcategoria.codigo,
                                                          'nombre': subcategoria.nombre, 'nivel': subcategoria.nivel})
                        else:
                            errores.append(
                                {'index': idx, 'nombre': sub_data.get('nombre', ''), 'errores': sub_serializer.errors})
                    except Exception as e:
                        errores.append({'index': idx, 'nombre': sub_data.get('nombre', ''), 'error': str(e)})

                if subcategorias_existentes:
                    for cat in Categoria.objects.filter(id__in=subcategorias_existentes, is_active=True).exclude(
                            id=categoria_actualizada.id):
                        padre_temp, es_ciclo = categoria_actualizada.categoria_padre, False
                        while padre_temp:
                            if str(padre_temp.id) == str(cat.id):
                                es_ciclo = True
                                break
                            padre_temp = padre_temp.categoria_padre
                        if not es_ciclo:
                            cat.categoria_padre = categoria_actualizada
                            cat.nivel = categoria_actualizada.nivel + 1
                            cat.save()
                            subcategorias_enlazadas.append(
                                {'id': str(cat.id), 'nombre': cat.nombre, 'codigo': cat.codigo, 'nivel': cat.nivel})
                        else:
                            errores.append({'nombre': cat.nombre, 'error': 'Crearía un ciclo en la jerarquía'})

                return StandardResponse.success(
                    data={
                        'categoria': {'id': str(categoria_actualizada.id), 'codigo': categoria_actualizada.codigo,
                                      'nombre': categoria_actualizada.nombre, 'nivel': categoria_actualizada.nivel},
                        'subcategorias_creadas': subcategorias_creadas,
                        'subcategorias_enlazadas': subcategorias_enlazadas,
                        'total_subcategorias': len(subcategorias_creadas) + len(subcategorias_enlazadas),
                        **(({'errores_subcategorias': errores}) if errores else {})
                    },
                    mensaje="Categoría actualizada exitosamente"
                )

        except ValidationError as e:
            return StandardResponse.validation_error(e.detail)
        except Exception as e:
            self.logger.error(f"Error al actualizar categoría con subcategorías: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje=f'Error al actualizar: {str(e)}',
                status_code=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    @requiere_permiso('ver_jerarquia_categorias')
    def arbol(self, request):
        """Vista de árbol jerárquico completo"""
        try:
            # Solo categorías raíz (nivel 1)
            categorias_raiz = self.get_queryset().filter(
                categoria_padre__isnull=True,
                is_active=True
            ).order_by('nombre')

            serializer = CategoriaTreeSerializer(categorias_raiz, many=True)

            return StandardResponse.success(data={
                'total': categorias_raiz.count(),
                'arbol': serializer.data
            })

        except Exception as e:
            self.logger.error(f"Error al obtener árbol: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al obtener árbol de categorías",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    @requiere_permiso('ver_jerarquia_categorias')
    def subcategorias(self, request, pk=None):
        """Listar subcategorías directas de una categoría"""
        try:
            categoria = self.get_object()

            subcategorias = categoria.categorias_hijas.filter(
                is_active=True,
                deleted_at__isnull=True
            ).order_by('nombre')

            serializer = CategoriaSimpleSerializer(subcategorias, many=True)

            return StandardResponse.success(data={
                'categoria': {
                    'id': str(categoria.id),
                    'codigo': categoria.codigo,
                    'nombre': categoria.nombre,
                    'nivel': categoria.nivel
                },
                'total_subcategorias': subcategorias.count(),
                'subcategorias': serializer.data
            })

        except Exception as e:
            self.logger.error(f"Error al obtener subcategorías: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al obtener subcategorías",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    @requiere_permiso('ver_categorias')
    def productos(self, request, pk=None):
        """Ver productos de la categoría"""
        try:
            categoria = self.get_object()

            productos = Producto.objects.filter(
                categoria=categoria,
                is_active=True,
                deleted_at__isnull=True
            ).select_related('marca', 'unidad_medida').order_by('nombre')

            items = []
            for producto in productos:
                items.append({
                    'id': str(producto.id),
                    'codigo': producto.codigo,
                    'nombre': producto.nombre,
                    'marca': producto.marca.nombre if producto.marca else None,
                    'precio_venta': float(producto.precio_venta),
                    'stock_total': producto.stock_total,
                    'is_active': producto.is_active
                })

            return StandardResponse.success(data={
                'categoria': {
                    'id': str(categoria.id),
                    'codigo': categoria.codigo,
                    'nombre': categoria.nombre
                },
                'total_productos': len(items),
                'productos': items
            })

        except Exception as e:
            self.logger.error(f"Error al obtener productos: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al obtener productos de la categoría",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    @requiere_permiso('ver_categorias')
    def principales(self, request):
        """Listar solo categorías principales (nivel 1)"""
        try:
            categorias = self.get_queryset().filter(
                is_active=True,
                categoria_padre__isnull=True
            ).order_by('nombre')

            serializer = CategoriaSimpleSerializer(categorias, many=True)

            return StandardResponse.success(data={
                'total': categorias.count(),
                'categorias': serializer.data
            })

        except Exception as e:
            self.logger.error(f"Error al listar categorías: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al obtener categorías principales",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )