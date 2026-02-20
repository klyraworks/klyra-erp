# urls.py - Módulo Inventario
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apis.inventario.producto.producto_viewset import ProductoViewSet
from apis.inventario.categoria.categoria_viewset import CategoriaViewSet
from apis.inventario.marca.marca_viewset import MarcaViewSet
from apis.inventario.unidad_medida.unidad_medida_viewset import UnidadMedidaViewSet
from apis.inventario.movimiento.movimiento_viewset import MovimientoInventarioViewSet
from apis.inventario.bodega.bodega_viewset import BodegaViewSet
from apis.inventario.stock.stock_viewset import StockViewSet
from apis.inventario.ubicacion.ubicacion_viewset import UbicacionViewSet


router = DefaultRouter()
router.register(r'bodegas', BodegaViewSet, basename='bodega')
router.register(r'marcas', MarcaViewSet, basename='marca')
router.register(r'categorias', CategoriaViewSet, basename='categoria')
router.register(r'productos', ProductoViewSet)
router.register(r'unidades-medida', UnidadMedidaViewSet)
router.register(r'movimientos-inventario', MovimientoInventarioViewSet)
router.register(r'stock', StockViewSet)
router.register(r'ubicaciones', UbicacionViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]
