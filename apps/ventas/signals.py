# apps/ventas/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction, models
import logging

from apps.ventas.models import Pago, Venta
from decimal import Decimal

logger = logging.getLogger('venta_signals')


@receiver(post_save, sender=Pago)
def actualizar_saldo_venta_al_registrar_pago(sender, instance, created, **kwargs):
    """
    Signal: Actualiza el saldo y crédito cuando se registra un pago.

    NO modifica el estado de la venta (borrador/confirmada/facturada/anulada).
    El estado_pago se calcula automáticamente en el modelo basado en saldo_pendiente.
    """
    if not created:
        return

    venta = instance.venta
    try:
        with transaction.atomic():
            # 1. Calcular nuevo saldo
            total_pagado = venta.pagos.aggregate(
                total=models.Sum('monto')
            )['total'] or Decimal('0.00')

            saldo_anterior = venta.saldo_pendiente
            nuevo_saldo = venta.total - total_pagado

            # 2. Liberar crédito si es venta a crédito
            if venta.tipo_pago == 'credito' and saldo_anterior != nuevo_saldo:
                diferencia = saldo_anterior - nuevo_saldo
                if diferencia > 0:
                    venta.cliente.liberar_credito(diferencia)
                    venta.cliente.save(update_fields=['credito_disponible'])

                    logger.info(
                        f"Crédito liberado por pago: {venta.cliente.get_nombre_facturacion()}",
                        extra={
                            'cliente_id': str(venta.cliente.id),
                            'monto_liberado': float(diferencia),
                            'credito_disponible': float(venta.cliente.credito_disponible)
                        }
                    )

            # 3. Actualizar solo el saldo pendiente
            # NO tocar el estado - se mantiene como estaba
            # estado_pago se calcula automáticamente en el modelo
            venta.saldo_pendiente = nuevo_saldo
            venta.save(update_fields=['saldo_pendiente', 'updated_at'])

            logger.info(
                f"Saldo actualizado: Venta {venta.numero}",
                extra={
                    'venta_id': str(venta.id),
                    'pago_id': str(instance.id),
                    'monto_pago': float(instance.monto),
                    'saldo_anterior': float(saldo_anterior),
                    'saldo_nuevo': float(nuevo_saldo),
                    'estado': venta.estado,
                    'estado_pago': venta.estado_pago  # Se calcula automáticamente
                }
            )

    except Exception as e:
        logger.exception(
            f"Error en signal de pago para venta {venta.numero}: {str(e)}",
            extra={'venta_id': str(venta.id), 'pago_id': str(instance.id)}
        )


@receiver(post_delete, sender=Pago)
def revertir_saldo_al_eliminar_pago(sender, instance, **kwargs):
    """
    Signal: Revierte el saldo y el crédito al eliminar un pago.

    NO modifica el estado de la venta (se mantiene en su estado documental).
    El estado_pago se recalcula automáticamente en el modelo.
    """
    venta = instance.venta
    try:
        with transaction.atomic():
            # 1. Recalcular saldo total
            total_pagado = venta.pagos.aggregate(
                total=models.Sum('monto')
            )['total'] or Decimal('0.00')

            saldo_anterior = venta.saldo_pendiente
            nuevo_saldo = venta.total - total_pagado

            # 2. Si es crédito, re-ocupar el crédito del cliente
            if venta.tipo_pago == 'credito':
                diferencia = nuevo_saldo - saldo_anterior
                if diferencia > 0:
                    venta.cliente.reducir_credito(diferencia)
                    venta.cliente.save(update_fields=['credito_disponible'])

                    logger.info(
                        f"Crédito re-ocupado al eliminar pago: {venta.cliente.get_nombre_facturacion()}",
                        extra={
                            'cliente_id': str(venta.cliente.id),
                            'monto_reducido': float(diferencia),
                            'credito_disponible': float(venta.cliente.credito_disponible)
                        }
                    )

            # 3. Actualizar solo el saldo pendiente
            # NO tocar el estado - se mantiene como estaba
            # estado_pago se calcula automáticamente en el modelo
            venta.saldo_pendiente = nuevo_saldo
            venta.save(update_fields=['saldo_pendiente', 'updated_at'])

            logger.info(
                f"Saldo revertido tras eliminar pago: Venta {venta.numero}",
                extra={
                    'venta_id': str(venta.id),
                    'pago_eliminado_id': str(instance.id),
                    'monto_pago': float(instance.monto),
                    'saldo_anterior': float(saldo_anterior),
                    'saldo_nuevo': float(nuevo_saldo),
                    'estado': venta.estado,
                    'estado_pago': venta.estado_pago  # Se calcula automáticamente
                }
            )

    except Exception as e:
        logger.exception(
            f"Error al revertir saldo para venta {venta.numero}: {str(e)}",
            extra={'venta_id': str(venta.id), 'pago_eliminado_id': str(instance.id)}
        )