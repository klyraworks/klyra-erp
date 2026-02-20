from django.core.exceptions import ValidationError
import re

# VARIABLES GLOBALES
PASAPORTE_REGEX = r'^[A-Z][0-9]{8}$'

def validar_cedula_ecuatoriana(value):
    ced = value.strip()

    # Debe tener 10 dígitos
    if not ced.isdigit() or len(ced) != 10:
        raise ValidationError("La cédula debe tener 10 dígitos numéricos.")

    provincia = int(ced[0:2])
    if provincia < 1 or provincia > 24:
        raise ValidationError("El código de provincia es inválido.")

    numeros = list(map(int, ced))
    verificador_proporcionado = numeros[-1]

    suma = 0
    for i in range(9):
        dig = numeros[i]
        if i % 2 == 0:  # posiciones impares humanas (1,3,5...) -> índices 0,2,4...
            dig *= 2
            if dig >= 10:
                dig -= 9
        suma += dig

    verificador_calculado = 10 - (suma % 10)
    if verificador_calculado == 10:
        verificador_calculado = 0

    if verificador_calculado != verificador_proporcionado:
        raise ValidationError("Cédula ecuatoriana inválida.")


def validar_pasaporte(value):
    pas = value.strip().upper()

    if not re.match(PASAPORTE_REGEX, pas):
        raise ValidationError("Formato de pasaporte inválido. Ej: P12345678")

