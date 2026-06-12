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