# # apps/ventas/services/venta_service.py
# from decimal import Decimal
# from django.db import transaction
# from apps.ventas.models import Venta
#
#
# class VentaService:
#     """Servicio para operaciones complejas de ventas"""
#
#     @staticmethod
#     @transaction.atomic
#     def confirmar_con_inventario(venta, bodega):
#         """Confirma venta y reduce inventario"""
#         # Validar stock
#         for detalle in venta.detalles.all():
#             if detalle.producto.stock < detalle.cantidad:
#                 raise ValueError(f'Stock insuficiente para {detalle.producto.nombre}')
#
#         # Crear movimiento
#         from apps.inventario.services import MovimientoService
#         movimiento = MovimientoService.crear_salida(
#             venta=venta,
#             bodega=bodega
#         )
#
#         # Reducir crédito si aplica
#         if venta.tipo_pago == 'credito':
#             venta.cliente.reducir_credito(venta.total)
#
#         # Cambiar estado
#         venta.estado = 'confirmada'
#         venta.save(update_fields=['estado', 'updated_at'])
#
#         return movimiento
#
#     @staticmethod
#     @transaction.atomic
#     def facturar(venta):
#         """Genera factura electrónica"""
#         from apps.ventas.services import FacturacionService
#
#         if venta.estado != 'confirmada':
#             raise ValueError('Solo se pueden facturar ventas confirmadas')
#
#         return FacturacionService.generar_factura(venta)
#
#     @staticmethod
#     @transaction.atomic
#     def anular(venta, motivo):
#         """Anula venta y reversa procesos"""
#         if venta.estado == 'anulada':
#             raise ValueError('La venta ya está anulada')
#
#         if venta.estado == 'facturada' and venta.esta_autorizada_sri():
#             raise ValueError('Debe generar Nota de Crédito para facturas autorizadas')
#
#         # Reversa inventario
#         if venta.estado in ['confirmada', 'facturada']:
#             from apps.inventario.services import MovimientoService
#             MovimientoService.reversar_salida(venta.numero)
#
#             # Liberar crédito
#             if venta.tipo_pago == 'credito':
#                 venta.cliente.liberar_credito(venta.total)
#
#         # Anular
#         venta.estado = 'anulada'
#         venta.saldo_pendiente = Decimal('0.00')
#         venta.observaciones = f"{venta.observaciones}\n\nANULADA: {motivo}".strip()
#         venta.save()
#
#         return venta