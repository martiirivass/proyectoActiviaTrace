## ADDED Requirements

### Requirement: Usuario puede importar calificaciones desde archivo LMS
El sistema SHALL permitir al usuario (PROFESOR sobre sus materias, COORDINADOR sobre cualquier materia) importar calificaciones desde un archivo exportado del LMS en formato `.xlsx` o `.csv`.

#### Scenario: Subir archivo válido con columnas numéricas y textuales
- **WHEN** el usuario sube un archivo `.xlsx` con encabezados que incluyen columnas terminadas en `(Real)` (numéricas) y columnas con valores textuales como "Satisfactorio"
- **THEN** el sistema parsea el archivo, detecta las columnas de actividad, infiere su tipo (numérica si termina en `(Real)`, textual en caso contrario), y retorna una vista previa con la lista de actividades detectadas

#### Scenario: Subir archivo con formato no soportado
- **WHEN** el usuario sube un archivo que no es `.xlsx` ni `.csv`
- **THEN** el sistema rechaza la operación con error 422 y mensaje "Formato no soportado. Use archivos .xlsx o .csv"

#### Scenario: Subir archivo sin columnas de actividad detectables
- **WHEN** el usuario sube un archivo válido pero ninguna columna es reconocida como actividad (numérica o textual)
- **THEN** el sistema retorna la vista previa con una lista vacía de actividades y un mensaje indicativo

#### Scenario: Vista previa incluye metadatos del alumno
- **WHEN** el archivo contiene columnas de metadatos (nombre, apellido, email)
- **THEN** el sistema las reconoce y las excluye de la lista de actividades detectadas, pero las incluye como datos de contexto del alumno

### Requirement: Usuario puede seleccionar actividades a incluir
El sistema SHALL permitir al usuario, después de la vista previa, seleccionar qué actividades detectadas desea incluir en la importación.

#### Scenario: Seleccionar actividades y confirmar importación
- **WHEN** el usuario envía una confirmación con `materia_id`, `cohorte_id`, la lista de actividades seleccionadas, y los datos parseados del archivo
- **THEN** el sistema crea registros de `Calificacion` para cada alumno × actividad seleccionada, computa el campo `aprobado` según el umbral vigente, y retorna el resumen con cantidad de registros creados

#### Scenario: Importación genera registro de auditoría
- **WHEN** el usuario confirma una importación de calificaciones
- **THEN** el sistema crea un registro de auditoría con acción `CALIFICACIONES_IMPORTAR`, incluyendo materia_id, cohorte_id, cantidad de filas afectadas, y el actor que realizó la importación

#### Scenario: Importación respeta aislamiento por tenant
- **WHEN** un usuario del Tenant A importa calificaciones
- **THEN** solo se crean registros con `tenant_id` del Tenant A, y usuarios del Tenant B no pueden acceder a esos datos

### Requirement: Sistema detecta columnas numéricas por sufijo (RN-01)
El sistema SHALL clasificar como columna de nota numérica toda columna cuyo encabezado termina en `(Real)`.

#### Scenario: Columna "TP1 (Real)" es detectada como numérica
- **WHEN** el archivo contiene una columna con encabezado "TP1 (Real)"
- **THEN** el sistema la clasifica como actividad numérica y los valores se parsean como decimales

#### Scenario: Columna sin sufijo "(Real)" no es numérica
- **WHEN** el archivo contiene una columna "Estado TP1"
- **THEN** el sistema no la clasifica como numérica; la clasifica como textual si contiene datos no vacíos

### Requirement: Sistema reconoce valores textuales aprobatorios (RN-02)
El sistema SHALL tratar los valores "Satisfactorio" y "Supera lo esperado" como nota textual aprobatoria.

#### Scenario: Alumno con "Satisfactorio" es marcado como aprobado
- **WHEN** se importa una calificación textual con valor "Satisfactorio"
- **THEN** el sistema computa `aprobado = true` para ese registro

#### Scenario: Alumno con "No satisfactorio" no es marcado como aprobado
- **WHEN** se importa una calificación textual con valor "No satisfactorio"
- **THEN** el sistema computa `aprobado = false` para ese registro

### Requirement: Sistema computa `aprobado` al importar
El sistema SHALL derivar el campo `aprobado` en el momento de crear cada `Calificacion`, según las reglas de E7.

#### Scenario: Nota numérica >= umbral → aprobado
- **WHEN** se importa una calificación con `nota_numerica = 75` y el umbral configurado para la materia es 60
- **THEN** el sistema computa `aprobado = true`

#### Scenario: Nota numérica < umbral → no aprobado
- **WHEN** se importa una calificación con `nota_numerica = 45` y el umbral configurado para la materia es 60
- **THEN** el sistema computa `aprobado = false`

#### Scenario: Solo nota textual aprobatoria → aprobado
- **WHEN** se importa una calificación sin `nota_numerica` pero con `nota_textual = "Supera lo esperado"`
- **THEN** el sistema computa `aprobado = true`

#### Scenario: Solo nota textual no aprobatoria → no aprobado
- **WHEN** se importa una calificación sin `nota_numerica` pero con `nota_textual = "No alcanzado"`
- **THEN** el sistema computa `aprobado = false`

### Requirement: Importación usa umbral configurado o default 60%
El sistema SHALL usar el umbral configurado en `UmbralMateria` para la asignación del docente que importa, o el defecto 60% si no existe configuración.

#### Scenario: Umbral configurado existe y se aplica
- **WHEN** el docente tiene un `UmbralMateria` con `umbral_pct = 75` para su asignación
- **THEN** la derivación de `aprobado` usa 75 como umbral

#### Scenario: Sin umbral configurado usa default 60
- **WHEN** el docente no tiene `UmbralMateria` configurado
- **THEN** la derivación de `aprobado` usa 60 como umbral

#### Scenario: Umbral de otro docente no afecta
- **WHEN** el Docente A tiene umbral 75 y el Docente B tiene umbral 50 para la misma materia
- **THEN** las calificaciones importadas por A usan umbral 75 y las de B usan umbral 50, sin interferencia
