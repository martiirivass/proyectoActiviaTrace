"""
RESERVADO para C-04: Matriz de permisos RBAC fino
- Permisos por modulo:accion
- Matriz rol x permiso
- require_permission dependency

Asignación actual de permisos:

| Permiso                 | ADMIN | COORDINADOR | PROFESOR | TUTOR | NEXO | ALUMNO |
|-------------------------|-------|-------------|----------|-------|------|--------|
| encuentros:gestionar    |   ✓   |      ✓      |    ✓     |   ✓   |      |        |
"""

# Constantes de permisos del sistema
# Formato: modulo:accion
ENCUENTROS_GESTIONAR: str = "encuentros:gestionar"
COLOQUIOS_GESTIONAR: str = "coloquios:gestionar"
COLOQUIOS_RESERVAR: str = "coloquios:reservar"
AVISOS_PUBLICAR: str = "avisos:publicar"
AVISOS_VER: str = "avisos:ver"
TAREAS_GESTIONAR: str = "tareas:gestionar"
TAREAS_ADMIN: str = "tareas:admin"

# Liquidaciones y honorarios
GRILLA_SALARIAL_VER: str = "grilla-salarial:ver"
GRILLA_SALARIAL_CREAR: str = "grilla-salarial:crear"
GRILLA_SALARIAL_EDITAR: str = "grilla-salarial:editar"
GRILLA_SALARIAL_ELIMINAR: str = "grilla-salarial:eliminar"
LIQUIDACIONES_VER: str = "liquidaciones:ver"
LIQUIDACIONES_CALCULAR: str = "liquidaciones:calcular"
LIQUIDACIONES_CERRAR: str = "liquidaciones:cerrar"
LIQUIDACIONES_EXPORTAR: str = "liquidaciones:exportar"
LIQUIDACIONES_HISTORIAL: str = "liquidaciones:historial"
FACTURAS_GESTIONAR: str = "facturas:gestionar"