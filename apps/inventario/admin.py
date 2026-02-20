from django.contrib import admin

from apps.inventario.models import (Producto, Categoria, UnidadMedida, Marca, MovimientoInventario, AjusteInventario,
                                    Bodega, DetalleAjuste, DetalleMovimiento, Stock, DetalleConteo,
                                    DetalleTransferencia, TransferenciaBodega, Ubicacion, ConteoFisico,
                                    UnidadConversion, KitComponente)

# Register your models here.
admin.site.register(Producto)
admin.site.register(Categoria)
admin.site.register(UnidadMedida)
admin.site.register(Marca)
admin.site.register(MovimientoInventario)
admin.site.register(AjusteInventario)
admin.site.register(Bodega)
admin.site.register(DetalleAjuste)
admin.site.register(DetalleMovimiento)
admin.site.register(Stock)
admin.site.register(DetalleConteo)
admin.site.register(DetalleTransferencia)
admin.site.register(TransferenciaBodega)
admin.site.register(Ubicacion)
admin.site.register(ConteoFisico)
admin.site.register(UnidadConversion)
admin.site.register(KitComponente)