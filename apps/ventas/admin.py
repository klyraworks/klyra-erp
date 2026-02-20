# apps/ventas/admin.py
from django.contrib import admin
from apps.ventas.models import Cliente, DetalleVenta, DetalleCotizacion, Cotizacion, Venta, Pago

admin.site.register(Cliente)
admin.site.register(DetalleVenta)
admin.site.register(DetalleCotizacion)
admin.site.register(Cotizacion)
admin.site.register(Venta)
admin.site.register(Pago)