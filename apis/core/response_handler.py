# apis/core/response_handler.py
from rest_framework.response import Response
from rest_framework import status


class StandardResponse:
    """Handler estandarizado para respuestas de API"""

    @staticmethod
    def success(data=None, mensaje=None, status_code=status.HTTP_200_OK):
        """Respuesta exitosa"""
        return Response({
            'success': True,
            'data': data,
            'titulo': None,
            'mensaje': mensaje,
            'error': None,
            'info': None
        }, status=status_code)

    @staticmethod
    def error(mensaje, status_code=status.HTTP_400_BAD_REQUEST, detalles=None):
        """Respuesta de error general"""
        response_data = {
            'success': False,
            'data': None,
            'titulo': 'Error',
            'mensaje': mensaje,
            'error': 'error',
            'info': None
        }
        if detalles:
            response_data['detalles'] = detalles
        return Response(response_data, status=status_code)

    @staticmethod
    def info(mensaje, data=None, status_code=status.HTTP_200_OK):
        """Respuesta informativa (warnings, avisos)"""
        return Response({
            'success': True,
            'data': data,
            'titulo': None,
            'mensaje': None,
            'error': None,
            'info': mensaje
        }, status=status_code)

    @staticmethod
    def validation_error(errores):
        """
        Errores de validación de campos.

        Aplana automáticamente el primer mensaje encontrado en errores
        para que el frontend pueda mostrarlo directamente sin inspeccionar
        la estructura completa.

        Estructura de respuesta:
            titulo  → Título del alert ("Errores de validación")
            mensaje → Primer mensaje de error encontrado, listo para mostrar
            error   → Código de error ("validation_error")
            errores → Estructura completa para marcar campos en el formulario
        """
        return Response({
            'success': False,
            'data': None,
            'titulo': 'Errores de validación',
            'mensaje': StandardResponse._aplanar_errores(errores),
            'error': 'validation_error',
            'errores': errores,
            'info': None
        }, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def _aplanar_errores(errores) -> str:
        """
        Extrae el primer mensaje de error de la estructura de errores,
        sin importar qué tan anidada esté.

        Ejemplos:
            {'cedula': ['Cédula inválida']}
                → 'Cédula inválida'

            {'persona': {'cedula': ['Ya existe una persona con esta cédula']}}
                → 'Ya existe una persona con esta cédula'

            {'persona': {'cedula': 'Ya existe una persona con esta cédula'}}
                → 'Ya existe una persona con esta cédula'

            [ErrorDetail('Cédula inválida')]
                → 'Cédula inválida'

        Returns:
            str: Primer mensaje encontrado, o mensaje genérico si no se puede extraer
        """
        if isinstance(errores, str):
            return errores

        if isinstance(errores, list):
            if errores:
                return str(errores[0])
            return 'Revisa los campos del formulario.'

        if isinstance(errores, dict):
            for valor in errores.values():
                resultado = StandardResponse._aplanar_errores(valor)
                if resultado:
                    return resultado

        return 'Revisa los campos del formulario.'

    # ==================== BULK ====================
    @staticmethod
    def bulk_result(creados, errores, recurso="registros", recurso_genero="m",
                    status_success=status.HTTP_201_CREATED,
                    status_partial=status.HTTP_207_MULTI_STATUS,
                    status_fail=status.HTTP_400_BAD_REQUEST):
        """
        Respuesta estandarizada para operaciones bulk.

        Args:
            creados (list): Items creados exitosamente
            errores (list): Errores de validación
            recurso (str): Nombre del recurso (marcas, productos, etc.)
            recurso_genero (str): 'm' masculino, 'f' femenino
        """
        total_creados = len(creados)
        total_errores = len(errores)
        total_intentados = total_creados + total_errores
        ningun = "ningún" if recurso_genero == "m" else "ninguna"

        # Fallo total
        if total_creados == 0:
            return Response({
                'success': False,
                'data': None,
                'titulo': 'Error en operación masiva',
                'mensaje': f"No se pudo crear {ningun} {recurso}. {total_errores} errores de validación.",
                'error': 'bulk_error',
                'info': None,
                'detalles': {
                    'total_intentados': total_intentados,
                    'total_creados': 0,
                    'total_errores': total_errores,
                    'errores': errores
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Éxito parcial
        elif total_errores > 0:
            return Response({
                'success': True,
                'data': {
                    'total_intentados': total_intentados,
                    'total_creados': total_creados,
                    'total_errores': total_errores,
                    f'{recurso}': creados,
                    'errores': errores
                },
                'titulo': 'Operación parcial',
                'mensaje': f"{total_creados} {recurso} creados exitosamente. {total_errores} fallaron.",
                'error': None,
                'info': "Operación completada parcialmente. Revise los errores para más detalles."
            }, status=status_partial)

        # Éxito total
        else:
            return Response({
                'success': True,
                'data': {
                    'total_creados': total_creados,
                    'total_errores': 0,
                    f'{recurso}': creados
                },
                'titulo': None,
                'mensaje': f"{total_creados} {recurso} creados exitosamente",
                'error': None,
                'info': None
            }, status=status_success)