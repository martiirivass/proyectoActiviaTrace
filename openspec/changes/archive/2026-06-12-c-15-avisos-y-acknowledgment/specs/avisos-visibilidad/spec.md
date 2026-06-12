## ADDED Requirements

### Requirement: Usuario ve solo avisos que aplican a su contexto (RN-20)
El sistema SHALL filtrar los avisos visibles para cada usuario según la combinación de: alcance del aviso, contexto del usuario (materias/cohortes asociadas), rol del usuario, y estado activo. Los avisos fuera de su ventana de vigencia (inicio_en/fin_en) no se muestran (RN-18).

#### Scenario: ALUMNO ve avisos globales y de su cohorte
- **WHEN** ALUMNO autenticado consulta GET /api/avisos
- **THEN** el sistema retorna solo avisos con alcance Global + alcance PorCohorte de su cohorte + alcance PorRol a ALUMNO, dentro de vigencia

#### Scenario: PROFESOR ve avisos de su materia
- **WHEN** PROFESOR autenticado con asignación a Materia A consulta GET /api/avisos
- **THEN** el sistema retorna avisos Global + PorMateria para Materia A + PorRol a PROFESOR

#### Scenario: Aviso fuera de vigencia no se muestra
- **WHEN** hay un aviso con fin_en en el pasado y un usuario consulta GET /api/avisos
- **THEN** el aviso vencido no aparece en el listado

#### Scenario: Aviso con inicio_en futuro no se muestra
- **WHEN** hay un aviso con inicio_en en el futuro y un usuario consulta GET /api/avisos
- **THEN** el aviso no aparece hasta que llegue su fecha de inicio

### Requirement: Orden de presentación por prioridad (orden)
El sistema SHALL ordenar los avisos visibles por el campo `orden` (ascendente). A igual orden, por fecha de creación descendente.

#### Scenario: Avisos ordenados por prioridad
- **WHEN** existen avisos con orden=1, orden=3, orden=2
- **THEN** el listado muestra primero orden=1, luego orden=2, luego orden=3

### Requirement: Aviso inactivo no se muestra a nadie
El sistema SHALL ocultar los avisos con activo=false de todos los listados, independientemente de alcance y vigencia.

#### Scenario: Aviso inactivo no visible
- **WHEN** COORDINADOR crea un aviso con activo=false y un usuario consulta GET /api/avisos
- **THEN** el aviso no aparece en el listado
