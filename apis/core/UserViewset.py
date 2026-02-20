# apis/base/UserViewset.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apis.seguridad.empleado.empleado_serializer import EmpleadoListSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    user = request.user
    empleado = getattr(user, 'empleado', None)

    if empleado:
        # Usar el serializer existente para obtener toda la información del empleado
        empleado_data = EmpleadoListSerializer(empleado).data

        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'empleado': empleado_data
        })

    # Si no tiene empleado asociado, devolver solo info básica del usuario
    return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
    })