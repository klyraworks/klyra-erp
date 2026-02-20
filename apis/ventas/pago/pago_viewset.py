# apis/ventas/venta/pago_viewset.py

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.ventas.models import Pago
from apis.ventas.pago.pago_serializer import PagoSerializer
from apis.core.ViewSetBase import TenantViewSet

class PagoViewSet(TenantViewSet):
    """ViewSet para gestionar Pagos de ventas"""

    queryset = Pago.objects.filter(is_active=True)
    serializer_class = PagoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return super().get_queryset()


