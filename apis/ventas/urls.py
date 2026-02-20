# urls.py - Módulo Ventas
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apis.ventas.cliente.cliente_viewset import ClienteViewSet
from apis.inventario.producto.producto_viewset import ProductoViewSet
from apis.ventas.venta.venta_viewset import VentaViewSet
from apis.ventas.pago.pago_viewset import PagoViewSet

router = DefaultRouter()
router.register('clientes', ClienteViewSet)
router.register('productos', ProductoViewSet)
router.register('ventas', VentaViewSet)
router.register('pagos', PagoViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]
