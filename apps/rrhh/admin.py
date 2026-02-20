# apps/rrhh/admin.py
from django.contrib import admin
from apps.rrhh.models import Departamento, Nomina, PeriodoNomina, Asistencia, Ausencia, Evaluacion, HistorialPuesto

admin.site.register(Departamento)
admin.site.register(Nomina)
admin.site.register(PeriodoNomina)
admin.site.register(Asistencia)
admin.site.register(Ausencia)
admin.site.register(Evaluacion)
admin.site.register(HistorialPuesto)