# Guía Detallada de la Propuesta de Investigación

## Mapa de Ruta Técnico

### 1. ¿Qué es un mapa de ruta técnico?
El mapa de ruta técnico es una herramienta visual que muestra el camino completo desde el planteamiento del problema hasta la solución de la investigación. Ayuda a los expertos evaluadores a comprender rápidamente la lógica de tu investigación y también te ayuda a clarificar tu propio razonamiento.

### 2. Tipos de mapas de ruta técnicos

**Tipo 1: Diagrama de flujo (adecuado para investigación experimental/de ingeniería)**
```
Problema de investigación
    |
    v
Revisión de literatura → Marco teórico
    |
    v
Hipótesis de investigación
    |
    v
Diseño experimental / Recolección de datos
    |
    v
Análisis de datos
    |
    v
Verificación de resultados
    |
    v
Conclusiones y recomendaciones
```

**Tipo 2: Línea de tiempo (adecuado para investigación longitudinal/de desarrollo)**
```
Fase 1 (Mes 1-3)       Fase 2 (Mes 4-6)       Fase 3 (Mes 7-9)
    |                       |                       |
    v                       v                       v
Revisión bibliográfica  Recolección de datos    Redacción de tesis
Construcción teórica    Implementación          Revisión y
                        experimental            perfeccionamiento
```

**Tipo 3: Iterativo circular (adecuado para investigación-acción/diseño de investigación)**
```
       Planificar (Plan)
          |
          v
    Implementar (Do)
    /        \
Verificar (Check)  Reflexionar (Reflect)
    \        /
      Ajustar (Adjust)
          |
          v
      Nueva ronda de planificación
```

**Tipo 4: Ramificación en árbol (adecuado para investigación multimétodo/multicaso)**
```
              Problema central
                 |
    +------------+------------+
    |            |            |
Cuantitativa  Cualitativa   Mixta
    |            |            |
Encuesta     Entrevista    Triangulación
    |         en profundidad   |
Análisis     Análisis      Análisis
estadístico  temático      integrado
```

### 3. Herramientas para crear mapas de ruta técnicos

**Herramientas profesionales**:
- Visio: funcionalidad completa, adecuado para flujos complejos
- ProcessOn: en línea, amigable, rico en plantillas
- Draw.io (diagrams.net): gratuito, potente
- Lucidchart: colaboración en línea, adecuado para equipos

**Herramientas generales**:
- PowerPoint: suficiente para flujos simples
- Word: función SmartArt
- LaTeX: paquete TikZ (adecuado para composición académica)

**Herramientas de código**:
- Python: matplotlib, graphviz
- R: DiagrammeR, ggplot2
- Mermaid: estilo Markdown, adecuado para incrustar en documentos

### 4. Principios de diseño del mapa de ruta técnico

**Claridad**:
- Cada nodo tiene una etiqueta clara (verbo + sustantivo)
- Dirección de flechas explícita (unidireccional, bidireccional, circular)
- Evitar líneas cruzadas (usar capas o colores para diferenciar)

**Integridad**:
- Incluir la cadena completa desde el problema hasta la conclusión
- Marcar nodos clave (hitos)
- Marcar puntos de decisión (ej. "¿Se confirma la hipótesis?")

**Jerarquía**:
- Flujo principal: líneas gruesas, nodos grandes
- Subflujos: líneas delgadas, nodos pequeños
- Notas: líneas punteadas, color gris

**Estética**:
- Paleta de colores unificada (3-5 colores)
- Alineación (alineación cuadrícula)
- Espaciado (sin aglomeración)

### 5. Ejemplo: Mapa de ruta técnico de investigación cuantitativa

```
[Contexto de la investigación]
La educación en línea se ha desarrollado rápidamente, pero los resultados de aprendizaje son desiguales
         |
         v
[Revisión de literatura] → Identificar brecha de investigación: falta investigación sistemática sobre mecanismos de interacción
         |
         v
[Marco teórico] → Constructivismo social + Teoría de la carga cognitiva
         |
         v
[Hipótesis de investigación]
H1: La frecuencia de interacción docente-estudiante está positivamente correlacionada con el rendimiento académico
H2: La profundidad de la interacción entre estudiantes está positivamente correlacionada con el pensamiento crítico
H3: La calidad de la interacción media entre las funciones de la plataforma y los resultados de aprendizaje
         |
         v
[Diseño de investigación]
  |
  +-- Grupo experimental: usar nueva plataforma de interacción (n=150)
  |
  +-- Grupo de control: usar plataforma tradicional (n=150)
  |
  +-- Pre-test: motivación de aprendizaje, conocimientos previos
  |
  +-- Post-test: rendimiento académico, pensamiento crítico, satisfacción
         |
         v
[Recolección de datos]
  |
  +-- Registros de plataforma: frecuencia, duración y tipo de interacción
  |
  +-- Encuesta: percepción de calidad de interacción, experiencia de aprendizaje
  |
  +-- Calificaciones de pruebas: preguntas objetivas + subjetivas
  |
  +-- Entrevistas: comprensión en profundidad del mecanismo (n=20)
         |
         v
[Análisis de datos]
  |
  +-- Estadística descriptiva: características de la muestra, distribución de variables
  |
  +-- Estadística inferencial: prueba t, ANOVA, regresión
  |
  +-- Análisis de mediación: método Bootstrap
  |
  +-- Análisis cualitativo: codificación temática
         |
         v
[Verificación de resultados]
  |
  +-- Prueba de hipótesis: ¿Se confirman H1/H2/H3?
  |
  +-- Prueba de robustez: sustitución de variables, submuestra
  |
  +-- Triangulación: consistencia entre resultados cuantitativos y cualitativos
         |
         v
[Conclusiones y recomendaciones]
  |
  +-- Contribución teórica: perfeccionar la teoría de interacción en aprendizaje en línea
  |
  +-- Recomendaciones prácticas: diseño de plataforma, estrategias de enseñanza
  |
  +-- Limitaciones e investigación futura
```

## Análisis de Viabilidad

### 1. Dimensiones de viabilidad de la investigación

**Viabilidad teórica**:
- ¿El problema de investigación está respaldado teóricamente?
- ¿El marco teórico está consolidado?
- ¿Las hipótesis de investigación son deducibles?

**Viabilidad metodológica**:
- ¿El método de investigación es adecuado para el problema?
- ¿Los datos son accesibles?
- ¿Se dominan las técnicas de análisis?

**Viabilidad de recursos**:
- Tiempo: ¿El ciclo de investigación es razonable?
- Financiamiento: ¿Se requieren fondos adicionales?
- Equipamiento: ¿Se necesita equipo especial?
- Personal: ¿Se necesitan colaboradores?
- Datos: ¿Existen canales de acceso a los datos?

**Viabilidad personal**:
- Conocimientos: ¿Se poseen los fundamentos teóricos pertinentes?
- Habilidades: ¿Se dominan los métodos de investigación?
- Apoyo del director: ¿El director conoce el campo?
- Inversión de tiempo: ¿Se puede garantizar tiempo suficiente?

### 2. Marco de análisis de viabilidad

```
Análisis de viabilidad

1. Viabilidad teórica
   - Fundamento teórico: [nombre de la teoría] ha sido ampliamente aplicado en [campo], proporcionando un sólido respaldo para esta investigación
   - Brecha de investigación: Las investigaciones existentes se centran principalmente en X, pero prestan insuficiente atención a Y; esta investigación llena esta brecha
   - Conclusión de viabilidad: El marco teórico está consolidado, las hipótesis son deducibles; viabilidad teórica confirmada

2. Viabilidad metodológica
   - Método de investigación: [nombre del método] es el método estándar para abordar [problema de investigación]
   - Obtención de datos: [fuente de datos] ha confirmado su disponibilidad, o [método de recolección] ha sido validado
   - Técnica de análisis: [herramienta de análisis] ya se domina, o [curso de capacitación] está planificado
   - Conclusión de viabilidad: El método está consolidado, los datos son accesibles, la técnica es dominable; viabilidad metodológica confirmada

3. Viabilidad de recursos
   - Tiempo: Ciclo de investigación de [X meses], con cronograma detallado elaborado
   - Financiamiento: [fuente de financiamiento] asegurada, o no se requiere financiamiento adicional
   - Equipamiento: [nombre del equipo] disponible, o [fuente del equipo] confirmada
   - Personal: El director [nombre] conoce el campo; se ha contactado a [colaborador] quien ha aceptado colaborar
   - Datos: [canal de obtención de datos] confirmado, o [sujeto de estudio] ha aceptado participar
   - Conclusión de viabilidad: Recursos suficientes, o alternativas disponibles; viabilidad de recursos confirmada

4. Viabilidad personal
   - Conocimientos: Ha completado [nombre del curso], posee [fundamento teórico]
   - Habilidades: Domina [habilidad], ha completado [capacitación/curso]
   - Apoyo del director: La línea de investigación del director es [dirección], altamente pertinente a esta investigación
   - Inversión de tiempo: Puede dedicar [X horas] semanales; plan de gestión del tiempo elaborado
   - Conclusión de viabilidad: Las condiciones personales cumplen los requisitos de investigación; viabilidad personal confirmada

Conclusión general: Esta investigación es viable en las cuatro dimensiones: teórica, metodológica, de recursos y personal.
```

### 3. Ejemplo de análisis de viabilidad

**Ejemplo: Investigación de interacción en educación en línea**

```
1. Viabilidad teórica
   - Fundamento teórico: El constructivismo social (Vygotsky) y la teoría de la carga cognitiva (Sweller)
     han sido ampliamente aplicados en investigación de tecnología educativa, proporcionando un sólido
     respaldo teórico para esta investigación.
   - Brecha de investigación: Las investigaciones existentes se centran principalmente en el diseño
     funcional de plataformas de aprendizaje en línea, pero carecen de investigación sistemática
     sobre cómo los mecanismos de interacción influyen en los resultados de aprendizaje.
   - Conclusión de viabilidad: El marco teórico está consolidado, las hipótesis son deducibles;
     viabilidad teórica confirmada.

2. Viabilidad metodológica
   - Método de investigación: El diseño cuasiexperimental (grupo experimental vs. grupo de control)
     es el método estándar para verificar relaciones causales, adecuado para este problema de investigación.
   - Obtención de datos: Se ha llegado a un acuerdo de cooperación con la plataforma de educación
     en línea XX, permitiendo el acceso a datos de registros de aprendizaje; las encuestas se
     distribuirán a través de la plataforma, con una tasa de respuesta esperada >70%.
   - Técnica de análisis: Se domina SPSS y Mplus; se planea asistir a un curso de modelos de
     ecuaciones estructurales con AMOS.
   - Conclusión de viabilidad: El método está consolidado, los datos son accesibles, la técnica
     es dominable; viabilidad metodológica confirmada.

3. Viabilidad de recursos
   - Tiempo: Ciclo de investigación de 12 meses (2023.9-2024.8), con cronograma detallado elaborado.
   - Financiamiento: Se ha obtenido financiamiento del Fondo XX (50.000 yuanes), cubriendo gastos
     de encuestas, entrevistas y capacitación.
   - Equipamiento: Se dispone de computadora y software SPSS; no se requiere equipo adicional.
   - Personal: El director, Profesor XX, es un investigador destacado en tecnología educativa,
     con más de 10 publicaciones pertinentes; se ha contactado a la Facultad de Educación de la
     Universidad XX para colaboración, quien ha aceptado proporcionar el grupo de control.
   - Datos: La plataforma ha firmado el acuerdo de uso de datos; el comité de ética ha otorgado
     la aprobación.
   - Conclusión de viabilidad: Recursos suficientes; viabilidad de recursos confirmada.

4. Viabilidad personal
   - Conocimientos: Ha completado cursos de psicología educativa, estadística educativa y tecnología
     educativa, poseyendo una sólida base teórica.
   - Habilidades: Ha completado la capacitación avanzada en SPSS, dominando estadística descriptiva,
     inferencial y análisis de regresión; actualmente está aprendiendo modelos de ecuaciones estructurales.
   - Apoyo del director: El Profesor XX es un académico reconocido en el campo de la tecnología
     educativa, cuya línea de investigación es altamente pertinente a esta investigación; ha aceptado
     ser el director.
   - Inversión de tiempo: Puede dedicar 20 horas semanales; ha elaborado un plan detallado de
     gestión del tiempo.
   - Conclusión de viabilidad: Las condiciones personales cumplen los requisitos de investigación;
     viabilidad personal confirmada.

Conclusión general: Esta investigación es viable en las cuatro dimensiones: teórica, metodológica,
de recursos y personal, y puede ejecutarse según lo planificado.
```

## Plan de Contingencia de Riesgos

### 1. Identificación de riesgos comunes

**Riesgos de datos**:
- Riesgo: Dificultad en la recolección de datos (baja tasa de respuesta, muestra insuficiente)
- Riesgo: Problemas de calidad de datos (muchos valores faltantes, muchos valores atípicos)
- Riesgo: Cambios en los permisos de acceso a datos (retiro del socio colaborador, cierre de plataforma)

**Riesgos metodológicos**:
- Riesgo: Inaplicabilidad del método (hipótesis no confirmada, mal ajuste del modelo)
- Riesgo: Dificultades técnicas (errores de software, fallos en el análisis)
- Riesgo: Tiempo insuficiente (aprendizaje de nuevos métodos demasiado prolongado)

**Riesgos de recursos**:
- Riesgo: Financiamiento insuficiente (sobrecosto, gastos adicionales)
- Riesgo: Fallo de equipos (daño en computadora, vencimiento de software)
- Riesgo: Cambios de personal (director de viaje, retiro de colaborador)

**Riesgos personales**:
- Riesgo: Problemas de salud (enfermedad, fatiga)
- Riesgo: Conflictos de tiempo (cursos, exámenes, prácticas)
- Riesgo: Falta de motivación (meseta de progreso, procrastinación)

**Riesgos externos**:
- Riesgo: Cambios de política (requisitos institucionales, nuevas regulaciones éticas)
- Riesgo: Eventos imprevistos (pandemia, desastres naturales)
- Riesgo: Cambios tecnológicos (actualización de plataforma, cambio de formato de datos)

### 2. Matriz de evaluación de riesgos

```
Matriz de evaluación de riesgos

Riesgo                      Probabilidad(1-5)  Impacto(1-5)  Nivel    Estrategia de respuesta
---------------------------------------------------------------------------------------------
Baja tasa de respuesta         3               4           Alto     Distribución multicanal, incentivos
Muestra insuficiente           2               5           Alto     Ampliar muestreo, ajustar diseño
Método no aplicable            2               4           Medio    Método alternativo, pre-experimento
Sobrecosto de presupuesto      2               3           Medio    Reserva presupuestaria, solicitud adicional
Director de viaje              3               2           Bajo     Comunicación en línea, planificación anticipada
Problemas de salud             2               3           Medio    Gestión de salud, tiempo de reserva
Cambios de política            1               4           Bajo     Seguimiento de novedades, ajuste flexible
```

### 3. Estrategias de respuesta a riesgos

**Estrategias de prevención (reducir probabilidad)**:
- Recolección de datos: pretest del cuestionario, distribución multicanal, establecer recordatorios
- Tamaño de muestra: ampliar marco muestral, establecer estándar mínimo de muestra
- Aplicabilidad del método: verificación bibliográfica, pre-experimento, consultar a expertos
- Presupuesto: presupuesto detallado, reserva de 10-20%
- Salud: rutina regular, ejercicio periódico, tiempo flexible reservado

**Estrategias de mitigación (reducir impacto)**:
- Baja tasa de respuesta: aumentar tamaño de muestra, utilizar ajuste por ponderación
- Método no aplicable: preparar método alternativo, simplificar el modelo
- Sobrecosto: priorizar gastos esenciales, buscar financiamiento adicional
- Director de viaje: reuniones en línea, discutir cuestiones clave con anticipación
- Problemas de salud: avance por etapas, buscar ayuda de compañeros

**Estrategias de emergencia (después de que ocurra el riesgo)**:
- Tasa de respuesta <50%: ampliar marco muestral, cambiar a investigación cualitativa
- Muestra insuficiente: utilizar Bootstrap, métodos bayesianos
- Método completamente fallido:转向 investigación descriptiva, estudio de caso
- Presupuesto agotado: solicitar financiamiento de emergencia, buscar apoyo del director
- Enfermedad prolongada: solicitar prórroga, ajustar plan de investigación

**Estrategias de transferencia**:
- Recolección de datos:委托 a instituciones especializadas (requiere financiamiento)
- Análisis de datos: buscar consultoría estadística (generalmente gratuita en la universidad)
- Problemas técnicos: adquirir servicio de soporte técnico

### 4. Ejemplo de plan de contingencia

**Ejemplo: Baja tasa de respuesta de datos**

```
Riesgo: La tasa de respuesta de la encuesta es inferior a la esperada (<50%)

Medidas de prevención:
- Diseño del cuestionario: pretest con 10 personas, asegurar completitud en menos de 5 minutos
- Canales de distribución: correo + WeChat + aula + notificación de plataforma, cobertura multicanal
- Incentivos: los primeros 100 participantes en completar reciben recompensa XX (materiales de estudio, pequeños obsequios)
- Mecanismo de recordatorio: recordatorios a los 3, 7 y 14 días después de la distribución

Medidas de emergencia:
- Tasa de respuesta 40-50%: ampliar marco muestral, agregar 200 personas
- Tasa de respuesta 30-40%: aumentar incentivos, cambiar a sorteo (100% de premios)
- Tasa de respuesta <30%: cambiar a investigación cualitativa (20 entrevistas en profundidad)
- Tasa de respuesta <20%: discutir con el director, ajustar diseño de investigación

Indicadores de monitoreo:
- Número de respuestas diarias
- Tendencia de la tasa de respuesta
- Representatividad de la muestra (comparación con la población)
```

### 5. Redacción del plan de contingencia en la propuesta de investigación

```
[Plan de contingencia]

Esta investigación identifica los siguientes riesgos principales y establece los planes de contingencia correspondientes:

1. Riesgo de recolección de datos
   Descripción del riesgo: La tasa de respuesta de la encuesta podría ser inferior a la esperada.
   Medidas de prevención: Distribución multicanal (correo + WeChat + aula), establecer recordatorios, ofrecer incentivos.
   Medidas de emergencia: Si la tasa de respuesta <50%, ampliar el marco muestral o aumentar incentivos;
                          si <30%, cambiar a investigación cualitativa (entrevistas en profundidad).

2. Riesgo de aplicabilidad metodológica
   Descripción del riesgo: El modelo de ecuaciones estructurales podría no ajustarse adecuadamente.
   Medidas de prevención: Validación del modelo mediante pre-experimento, consultar a expertos en estadística.
   Medidas de emergencia: Si el ajuste del modelo es deficiente, utilizar métodos alternativos
                          (análisis de regresión, ANOVA) o simplificar el modelo.

3. Riesgo de tiempo
   Descripción del riesgo: La recolección de datos podría retrasarse, afectando el análisis posterior.
   Medidas de prevención: Elaborar cronograma detallado, reservar 2 meses de margen.
   Medidas de emergencia: Si el retraso supera 1 mes, solicitar prórroga de la tesis o simplificar el análisis.

4. Riesgo de recursos
   Descripción del riesgo: El presupuesto podría excederse.
   Medidas de prevención: Presupuesto detallado, reserva del 20%, priorizar gastos esenciales.
   Medidas de emergencia: Si hay exceso, solicitar financiamiento adicional o buscar apoyo del director.

Con los planes de contingencia anteriores, esta investigación puede gestionar eficazmente los riesgos potenciales y garantizar la finalización exitosa de la investigación.
```

## Plantilla de Estructura de la Propuesta de Investigación

### Estructura completa

```
1. Contexto e importancia de la investigación
   1.1 Contexto práctico (origen del problema)
   1.2 Contexto teórico (contexto académico)
   1.3 Importancia de la investigación (teórica + práctica)

2. Revisión de literatura
   2.1 Definición de conceptos clave
   2.2 Estado actual de la investigación nacional e internacional
   2.3 Evaluación de la investigación (brechas)

3. Objetivos y contenido de la investigación
   3.1 Objetivos de investigación (específicos y medibles)
   3.2 Contenido de la investigación (desarrollo por puntos)
   3.3 Hipótesis de investigación (si aplica)

4. Métodos de investigación y ruta técnica
   4.1 Métodos de investigación (metodología + métodos específicos)
   4.2 Mapa de ruta técnico (visualización)
   4.3 Instrumentos de investigación (cuestionarios, escalas, equipos)
   4.4 Plan de muestreo (población, muestra, método de muestreo)

5. Análisis de viabilidad
   5.1 Viabilidad teórica
   5.2 Viabilidad metodológica
   5.3 Viabilidad de recursos
   5.4 Viabilidad personal

6. Plan de contingencia de riesgos
   6.1 Identificación de riesgos
   6.2 Evaluación de riesgos
   6.3 Estrategias de respuesta

7. Plan de investigación y cronograma
   7.1 División de etapas
   7.2 Hitos
   7.3 Diagrama de Gantt

8. Resultados esperados y puntos de innovación
   8.1 Resultados esperados (tesis, patentes, software, etc.)
   8.2 Puntos de innovación (teóricos, metodológicos, de aplicación)

9. Referencias bibliográficas
```

### Sugerencias de distribución de palabras

| Sección | Licenciatura (3000-5000 palabras) | Maestría (8000-15000 palabras) | Doctorado (20000-30000 palabras) |
|------|-------------------|-------------------|---------------------|
| Contexto de investigación | 500-800 | 1000-2000 | 2000-3000 |
| Revisión de literatura | 1000-1500 | 3000-5000 | 8000-12000 |
| Objetivos de investigación | 300-500 | 500-1000 | 1000-2000 |
| Métodos de investigación | 500-800 | 1500-2500 | 3000-5000 |
| Análisis de viabilidad | 300-500 | 500-1000 | 1000-2000 |
| Plan de contingencia | 200-300 | 300-500 | 500-1000 |
| Cronograma | 200-300 | 300-500 | 500-1000 |
| Resultados esperados | 200-300 | 300-500 | 500-1000 |

## Preguntas Frecuentes y Soluciones

### P: ¿El mapa de ruta técnico es demasiado simple o demasiado complejo?
- Si es simple: agregar subprocesos, puntos de decisión, retroalimentación circular
- Si es complejo: combinar elementos similares, abstraer a nivel superior, incluir detalles en apéndices

### P: ¿El análisis de viabilidad parece una autoglorificación?
- Declaración objetiva: usar "ya se posee" o "ya confirmado" en lugar de "soy excelente"
- Reconocer limitaciones: "Aunque la experiencia en X es insuficiente, se ha compensado mediante Y"
- Citar evidencia: calificaciones de cursos, certificados de capacitación, publicaciones del director

### P: ¿El plan de contingencia parece un trámite?
- Ser específico: no escribir "posibles problemas", sino "la tasa de respuesta podría ser <50%"
- Cuantificar: probabilidad, impacto, umbral
- Ser operativo: no escribir "fortalecer la gestión", sino "enviar correo de recordatorio a los 3 días"

### P: ¿Los puntos de innovación son insuficientes?
- Redefinir: no se requiere "completamente nuevo", sino "nueva combinación", "nueva aplicación", "nueva perspectiva"
- Comparación explicativa: diferencias específicas con investigaciones existentes
- Expresión moderada: usar "intentar", "explorar", "mejorar" en lugar de "pionero", "revolucionario"

## Recursos Recomendados

1. **Herramientas de mapas de ruta técnicos**:
   - ProcessOn: www.processon.com
   - Draw.io: app.diagrams.net
   - Lucidchart: www.lucidchart.com

2. **Herramientas de gestión de proyectos**:
   - GanttProject: diagrama de Gantt gratuito
   - Microsoft Project: gestión profesional de proyectos
   - Excel: diagrama de Gantt simple (formato condicional)

3. **Herramientas de evaluación de riesgos**:
   - Plantilla de matriz de riesgos: plantilla Excel
   - Simulación Monte Carlo: @RISK, Crystal Ball

4. **Libros de referencia**:
   - *Diseño y métodos de investigación* (Bordens & Abbott)
   - *Guía de escritura de tesis* (Pan Maoyuan)
   - *Cómo escribir una propuesta de investigación* (Locke et al.)


# Guía de Revisión y Pulido de la Tesis

## Auto-revisión

### 1. Etapas de revisión

**Período de enfriamiento (1-3 días)**:
- Después de completar el borrador, dejar reposar 1-3 días antes de revisar
- Razón: La distancia genera objetividad, facilitando la detección de problemas
- Actividades: Leer literatura, procesar datos, descansar

**Primera ronda: Revisión estructural (macro)**
- Verificar la cadena lógica: introducción → métodos → resultados → discusión → conclusiones
- Verificar el equilibrio de capítulos: si la extensión de cada capítulo es razonable
- Verificar los niveles de encabezados: si son claros y consistentes
- Verificar las transiciones: si la coherencia entre capítulos y secciones es fluida

**Segunda ronda: Revisión de contenido (meso)**
- Verificar la argumentación: si cada párrafo tiene un argumento claro
- Verificar las evidencias: si las evidencias respaldan el argumento
- Verificar el razonamiento: si la lógica es rigurosa
- Verificar la redundancia: si hay contenido repetitivo
- Verificar omisiones: si falta contenido importante

**Tercera ronda: Revisión lingüística (micro)**
- Verificar la gramática: concordancia sujeto-verbo, tiempos verbales, artículos
- Verificar la ortografía: erratas, terminología técnica
- Verificar la puntuación: mezcla de signos de puntuación chinos y occidentales
- Verificar el formato: fuente, tamaño de letra, interlineado
- Verificar las citas: consistencia de formato, correspondencia

**Cuarta ronda: Pulido de detalles (exquisito)**
- Verificar las figuras y tablas: numeración, títulos, nitidez
- Verificar los datos: cifras, unidades, porcentajes
- Verificar las referencias bibliográficas: integridad, formato
- Verificar los apéndices: numeración, correspondencia

### 2. Lista de verificación para auto-revisión

**Lista de verificación estructural**:
- [ ] ¿El resumen incluye el objetivo, métodos, resultados y conclusiones de la investigación?
- [ ] ¿La introducción va de lo macro a lo micro, planteando claramente el problema de investigación al final?
- [ ] ¿La revisión de literatura tiene una clasificación clara y combina revisión con evaluación crítica?
- [ ] ¿La sección de métodos es lo suficientemente detallada como para ser replicable?
- [ ] ¿La sección de resultados presenta los datos objetivamente sin interpretarlos?
- [ ] ¿La sección de discusión interpreta los resultados, compara con la literatura y señala las limitaciones?
- [ ] ¿Las conclusiones responden a las preguntas de investigación sin introducir contenido nuevo?
- [ ] ¿La proporción de cada capítulo es razonable (introducción 10%, literatura 20%, métodos 15%, resultados 20%, discusión 25%, conclusiones 10%)?

**Lista de verificación de contenido**:
- [ ] ¿Cada párrafo tiene una oración temática?
- [ ] ¿Hay transiciones entre párrafos?
- [ ] ¿Hay contenido irrelevante?
- [ ] ¿Hay contenido repetido?
- [ ] ¿Falta literatura importante?
- [ ] ¿Los datos son los más recientes?
- [ ] ¿Las conclusiones contienen inferencias excesivas?

**Lista de verificación lingüística**:
- [ ] ¿Hay expresiones coloquiales?
- [ ] ¿Hay formulaciones vagas?
- [ ] ¿Hay formulaciones absolutas?
- [ ] ¿Hay oraciones largas y complejas (>30 palabras)?
- [ ] ¿Hay uso excesivo de voz pasiva?
- [ ] ¿Hay calcos del chino (Chinglish)?
- [ ] ¿La terminología es consistente?

### 3. Método de lectura en voz alta

**Procedimiento**:
- Leer en voz alta todo el texto de la tesis
- Alternativa: usar herramientas de texto a voz (lectura de Word, navegador Edge)

**Problemas que se detectan**:
- Oraciones difíciles de pronunciar: suenan mal, necesitan reescritura
- Vocabulario repetido: la misma palabra aparece consecutivamente, necesita sustitución
- Saltos lógicos: al terminar un párrafo no se entiende la conexión
- Problemas de tono: demasiado fuerte, demasiado débil, poco objetivo

### 4. Método de esquema inverso

**Procedimiento**:
- Al terminar de leer un párrafo, resumirlo en una sola oración
- Escribirlo en notas adhesivas o al margen del documento
- Al completar todos los párrafos, revisar solo las oraciones de resumen

**Verificación**:
- ¿Las oraciones de resumen forman una cadena lógica?
- ¿Hay oraciones de resumen que no coinciden con el título?
- ¿Hay párrafos consecutivos cuyos resúmenes son repetitivos?
- ¿Hay párrafos que no se pueden resumir (lo que indica contenido desordenado)?

## Gestión de la Retroalimentación del Director

### 1. Actitud correcta para recibir retroalimentación

**Actitud correcta**:
- El director es un colaborador, no un crítico
- La retroalimentación es una consulta gratuita de expertos
- Cada corrección mejora la calidad de la tesis
- El "no entiendo" del director suele ser el "no entiendo" del lector

**Actitudes a evitar**:
- Defensiva: "No estoy equivocado, es que el director no entendió"
- Resistente: "Tantos cambios, sería mejor reescribir"
- Procrastinadora: "Déjalo para después"
- Selectiva: "Solo cambio lo fácil, lo difícil lo ignoro"

### 2. Tipos de retroalimentación y cómo afrontarlos

**Tipo 1: Retroalimentación direccional**
- Característica: "Sugiero ajustar el marco de investigación" "Sugiero complementar con la teoría XX"
- Respuesta: reunirse con el director para confirmar la dirección específica, elaborar plan de corrección
- Nota: puede implicar una reescritura sustancial, abordar lo antes posible

**Tipo 2: Retroalimentación de contenido**
- Característica: "Las evidencias aquí son insuficientes" "Sugiero agregar datos XX"
- Respuesta: complementar con literatura, datos o casos, o eliminar ese argumento
- Nota: verificar la fuente de los datos para asegurar su fiabilidad

**Tipo 3: Retroalimentación estructural**
- Característica: "Sugiero fusionar los capítulos 2 y 3" "Sugiero reordenar los capítulos"
- Respuesta: elaborar un plan de reestructuración, ejecutar tras la confirmación del director
- Nota: usar la vista de esquema para operar, evitar pérdida de contenido

**Tipo 4: Retroalimentación lingüística**
- Característica: "Expresión poco clara" "Sugiero ser más conciso" "Errores gramaticales"
- Respuesta: corregir punto por punto, se puede solicitar ayuda de hablantes nativos o servicios de pulido
- Nota: unificar el estilo de corrección para evitar inconsistencias

**Tipo 5: Retroalimentación de formato**
- Característica: "Figuras y tablas no son estándar" "Formato de cita incorrecto"
- Respuesta:对照 la plantilla institucional, corregir ítem por ítem
- Nota: usar la función de estilos para evitar ajustes manuales

### 3. Flujo de trabajo para gestionar la retroalimentación

**Paso 1: Organizar la retroalimentación**
- Clasificar la retroalimentación: direccional / de contenido / estructural / lingüística / de formato
- Priorizar: debe corregirse / sugerido para corrección / opcional
- Indicar dificultad: fácil / media / difícil
- Elaborar tabla: contenido de retroalimentación | tipo | prioridad | dificultad | plan de corrección | estado

**Paso 2: Elaborar plan**
- Ordenar por prioridad: primero lo direccional, luego el contenido, finalmente el formato
- Alternar por dificultad: fácil + difícil alternados para evitar agotamiento
- Asignar tiempo: reservar tiempo para cada tipo de retroalimentación
- Reservar margen: 20% del tiempo total para imprevistos

**Paso 3: Ejecutar correcciones**
- Enfocarse en un tipo: procesar un solo tipo de retroalimentación a la vez
- Marcar completado: anotar "completado" tras la corrección
- Registrar problemas: documentar la razón cuando no se pueda corregir
- Mantener versiones: guardar nueva versión en cada ronda de corrección

**Paso 4: Verificación cruzada**
- Contrastar con la retroalimentación: verificar punto por punto que se corrigió
- Validación cruzada: comprobar si las correcciones introducen nuevos problemas
- Verificación global: comprobar si el texto completo es coherente tras las correcciones
- Enviar al director: adjuntar explicación de las correcciones

### 4. Redacción del informe de correcciones

```
Informe de correcciones

Estimado director:

Gracias por sus valiosas observaciones. He completado las siguientes correcciones, detalladas a continuación:

I. Correcciones direccional (3 ítems)
1. Sobre el ajuste del marco de investigación
   - Problema original: El marco de investigación era demasiado amplio
   - Plan de corrección: Centrar en la variable XX, eliminar la variable YY
   - Ubicación: Capítulo 1, Sección 3; Capítulo 3
   - Estado: Completado

2. ...

II. Correcciones de contenido (5 ítems)
1. Sobre la inclusión de la teoría XX
   - Problema original: La revisión de literatura carecía de la perspectiva de la teoría XX
   - Plan de corrección: Incluir la teoría XX (Capítulo 2, Sección 2,新增 500 palabras)
   - Nueva literatura: Smith (2020), Jones (2021)
   - Estado: Completado

2. ...

III. Correcciones estructurales (2 ítems)
...

IV. Correcciones lingüísticas (8 ítems)
...

V. Correcciones de formato (10 ítems)
...

Observaciones no corregidas y razones:
1. Sobre la eliminación del capítulo XX: Este capítulo es la base del análisis posterior, se sugiere mantenerlo
   (Confirmado en reunión con el director, quien同意 mantenerlo)

2. ...

El texto completo ha sido actualizado tras las correcciones, favor de revisar.

Estudiante: XXX
Fecha: XX de XXXX de 202X
```

## Revisión por Pares

### 1. Selección de revisores

**Criterios**:
- Del mismo campo: línea de investigación相近, capaz de comprender el contenido
- Perspectivas diferentes: orientación metodológica y teórica distinta, capaz de ofrecer nuevas perspectivas
- Con experiencia: estudiantes de posgrado avanzados, postdoctorados, profesores jóvenes
- Confiable: confidencial, constructivo, sin plagio

**Canales**:
- Compañeros del mismo director: hermanos académicos, compañeros de la misma cohorte
- Círculo académico: conocidos en conferencias, redes sociales
- Grupo de escritura: miembros de grupos de evaluación mutua periódica
- Servicios profesionales: algunas universidades ofrecen centros de escritura

### 2. Solicitud de revisión

**Plantilla de correo electrónico**:
```
Asunto: Solicitud de revisión de tesis - [Título de la tesis]

Estimado/a XX:

¡Saludos! Soy XXX, estudiante de posgrado de la Universidad XX, especialidad XX, actualmente redactando una tesis de maestría/doctorado sobre [tema de investigación].

He sabido que usted tiene una investigación profunda en [campo específico], y me gustaría invitarle a proporcionar comentarios de revisión sobre mi tesis. La investigación se centra en [problema central], utilizando [método], con hallazgos preliminares que indican [conclusión principal].

Si le es conveniente, me gustaría recibir su retroalimentación antes del [fecha]. Los aspectos clave de la revisión incluyen:
1. ¿Es razonable el marco de investigación?
2. ¿Es clara y replicable la sección de métodos?
3. ¿Es rigurosa la lógica argumentativa?
4. ¿Es precisa la expresión lingüística?

La tesis tiene aproximadamente [X mil palabras] y se enviará en formato Word.

Independientemente de su disponibilidad, ¡agradezco su consideración!

Atentamente,

XXX
[Datos de contacto]
```

### 3. Guía de revisión para el revisor

**Instrucciones para el revisor**:
```
¡Gracias por aceptar revisar mi tesis! A continuación se presenta la guía de revisión:

Información de la tesis:
- Título: [Título]
- Tipo: Tesis de maestría/doctorado
- Etapa: Borrador/borrador revisado/antes de la versión final
- Extensión: [X mil palabras]

Aspectos clave de la revisión (por orden de prioridad):
1. Estructura lógica: ¿La organización de capítulos es razonable? ¿Las transiciones son naturales?
2. Calidad argumentativa: ¿Los argumentos son claros? ¿Las evidencias son suficientes? ¿El razonamiento es riguroso?
3. Descripción de métodos: ¿Es lo suficientemente detallada para ser replicable? ¿Hay omisiones?
4. Revisión de literatura: ¿Es exhaustiva? ¿La clasificación es razonable? ¿La evaluación crítica es adecuada?
5. Expresión lingüística: ¿Hay oscuridad, redundancia o expresiones coloquiales?
6. Normas de formato: ¿Las figuras, tablas, citas y referencias son correctas?

Formato de retroalimentación:
- Evaluación general (200-500 palabras)
- Comentarios detallados (por capítulo o por tipo)
- Etiqueta de prioridad (alta/media/baja)

Fecha límite: Antes del [fecha]
Modalidad: Correo electrónico / WeChat / reunión presencial

¡Gracias de nuevo!
```

### 4. Gestión de los comentarios de revisión por pares

**Principios**:
- Todos los comentarios merecen consideración, incluso si no se adoptan
- La mayoría de comentarios deberían adoptarse, especialmente los planteados por varios revisores
- Los comentarios no adoptados deben tener razones充分, que pueden anotarse

**Flujo de trabajo**:
1. Recopilar todos los comentarios, clasificarlos y organizarlos
2. Anotar la frecuencia de aparición (planteados por varios = importante)
3. Elaborar plan de corrección
4. Ejecutar correcciones
5. Retroalimentar a los revisores (agradecer + explicar correcciones realizadas)

## Pulido Lingüístico

### 1. Técnicas de auto-pulido

**Simplificar**:
- Eliminar redundancias: "muy", "bastante", "realmente"
- Eliminar relleno: "es importante señalar que", "no hay duda de que"
- Eliminar repeticiones: no redefinir términos dentro de la misma sección
- Eliminar coloquialismos: usar vocabulario académico apropiado

**Fortalecer**:
- Verbos en lugar de sustantivos: "realizar un análisis" → "analizar"
- Voz activa en lugar de pasiva (con moderación): "Se encontró que" → "Encontramos que"
- Concreto en lugar de abstracto: "buenos resultados" → "los resultados mejoraron un 25%"
- Adjetivos fuertes en lugar de "muy + adjetivo"

**Coherencia**:
- Agregar conectores: "Además", "Sin embargo", "Por lo tanto", "En contraste"
- Agregar referencias: "Este hallazgo", "Estos resultados", "Ese enfoque"
- Agregar síntesis: oración de cierre al final del párrafo, oración de transición al final del capítulo

### 2. Herramientas de apoyo

**Correctores gramaticales**:
- Grammarly: detecta gramática, ortografía y estilo
- LanguageTool: código abierto, interfaz disponible en múltiples idiomas
- Writefull: especializado en escritura académica, basado en IA

**Correctores de estilo**:
- Hemingway Editor: detecta legibilidad, marca oraciones largas y complejas
- ProWritingAid: análisis integral de estilo
- Herramientas específicas según idioma

**Verificación de terminología**:
- Consistencia terminológica: búsqueda y reemplazo, asegurar uniformidad
- Precisión terminológica: comparar con literatura de autoridad
- Primera aparición del término: nombre completo + abreviatura

### 3. Servicios de pulido profesional

**Situaciones de aplicación**:
- Artículos en inglés para someter a revistas internacionales
- Muchos problemas lingüísticos, difícil de mejorar con auto-revisión
- Tiempo limitado, necesidad de pulido rápido

**Tipos de servicio**:
- Pulido lingüístico: gramática, ortografía, estilo ($0.03-0.08/palabra)
- Pulido profundo: lingüístico + sugerencias de contenido ($0.08-0.15/palabra)
- Pulido científico: lingüístico + precisión científica ($0.15-0.30/palabra)

**Criterios de selección**:
- Cualificaciones del editor: hablante nativo, formación en la disciplina
- Garantía de servicio: garantía de calidad, revisiones post-servicio
- Acuerdo de confidencialidad: firma de NDA
- Compromiso de tiempo: cumplimiento de plazos

**Servicios reconocidos**:
- Elsevier Language Services
- Springer Nature Author Services
- Wiley Editing Services
- Editage
- Medjaden
- Enago

### 4. Verificación post-pulido

**Verificaciones obligatorias**:
- ¿Los términos técnicos fueron alterados incorrectamente? (los términos técnicos suelen ser "corregidos" por palabras comunes)
- ¿Los datos fueron alterados? (cifras, unidades, porcentajes)
- ¿Las citas fueron alteradas? (nombre del autor, año, número de página)
- ¿La lógica fue alterada? (cambio de conectores que invierte la lógica)
- ¿El formato fue alterado? (posición de figuras/tablas, numeración)

**Recomendaciones**:
- Leer todo el texto después del pulido
- Contrastar con el original, verificar la información clave
- Pedir a un compañero que verifique

## Gestión de Versiones de Corrección

### 1. Normas de nomenclatura

**Fecha + versión**:
- Tesis_20230615_v1.docx
- Tesis_20230701_v2.docx
- Tesis_20230715_v3_Final.docx
- Tesis_20230720_v3_Final_Final.docx (¡Evitar!)

**Etapa + versión**:
- Tesis_Borrador_v1.docx
- Tesis_Revisión_Director1_v2.docx
- Tesis_Revisión_Director2_v3.docx
- Tesis_Pre-defensa_v4.docx
- Tesis_Versión_Final_v5.docx

### 2. Estrategia de respaldo

**Respaldo local**:
- Disco duro de la computadora (versión de trabajo)
- Disco duro externo (respaldo semanal)
- Memoria USB (respaldo de emergencia)

**Respaldo en la nube**:
- OneDrive / Google Drive / Dropbox (sincronización automática)
- Nube institucional (velocidad rápida en red educativa)
- Envío por correo electrónico (enviárselo a uno mismo)

**Herramientas de versiones**:
- Git / GitHub (adecuado para código + texto)
- Historial de versiones de Word (guardado automático)
- Copia manual (simple y confiable)

### 3. Registro de correcciones

**Contenido del registro**:
- Fecha de corrección
- Autor de la corrección (propia / director / revisor)
- Tipo de corrección (estructura / contenido / lenguaje / formato)
- Ubicación (capítulo / página)
- Razón de la corrección (retroalimentación / autodetección)

**Métodos de registro**:
- Propiedades del documento: Word → Archivo → Información → Propiedades
- Bitácora de correcciones: documento independiente
- Comentarios: función de comentarios de Word
- Comparación de versiones: Word → Revisar → Comparar

## Preguntas Frecuentes

### P: ¿Las correcciones empeoran el texto?
- Causa: correcciones excesivas, pérdida de perspectiva global
- Solución: imprimir todo el texto, leer en formato físico; o leer en voz alta
- Prevención: enfocar cada ronda de corrección en un solo tipo de problema

### P: ¿Las opiniones del director son contradictorias?
- Solución: comunicarse con el director para confirmar el orden de prioridad
- Estrategia: tomar como referencia el propio problema de investigación, explicar las decisiones
- Nota: registrar los resultados de la comunicación para evitar correcciones repetitivas

### P: ¿No hay suficiente tiempo para una corrección profunda?
- Prioridad: estructura > contenido > lenguaje > formato
- Estrategia: primero corregir errores graves (lagunas lógicas, errores fácticos), luego errores menores (pulido lingüístico)
- Solicitar ayuda: pedir a compañeros que ayuden con el ajuste de formato y la revisión lingüística

### P: ¿Se ha corregido muchas veces y sigue sin conformar?
- Aceptar: la tesis no puede ser perfecta, solo lo suficientemente buena
- Estándar: cumplir con los requisitos de graduación, aprobar la defensa
- Futuro: después de graduarse se puede seguir perfeccionando para publicación

## Recursos Recomendados

1. **Herramientas de corrección**:
   - Grammarly: grammarly.com
   - Hemingway Editor: hemingwayapp.com
   - ProWritingAid: prowritingaid.com

2. **Servicios de pulido**:
   - Elsevier Language Services
   - Springer Nature Author Services
   - Editage: www.editage.cn

3. **Libros sobre escritura**:
   - *Mientras escribo* (Stephen King)
   - *El estilo sense* (Steven Pinker)
   - *Guía de escritura académica* (Helen Sword)

4. **Estrategias de revisión**:
   - *La revisión: el arte de la escritura académica* (Wendy Bishop)
   - *Cómo revisar una tesis* (Booth et al.)


# Guía de Etapas del Proceso de Escritura de la Tesis

## Etapa 1: Diagnóstico de Selección del Tema

### Principios de selección del tema
- **Valor**: valor académico o valor práctico
- **Innovación**: nueva perspectiva, nuevo método, nuevos materiales, nuevas conclusiones
- **Viabilidad**: compatibilidad con el tiempo, los recursos y las capacidades disponibles
- **Claridad**: problema específico, límites bien definidos

### Métodos de selección del tema
1. **Impulsado por la literatura**: identificar brechas, contradicciones o vacíos
2. **Impulsado por problemas**: problemas encontrados en la práctica
3. **Impulsado por métodos**: nuevos métodos aplicados a problemas antiguos
4. **Impulsado por la interdisciplinariedad**: perspectiva transdisciplinaria

### Lista de verificación para la evaluación del tema
- [ ] ¿Se puede formular claramente el problema de investigación en una sola oración?
- [ ] ¿Existe literatura pertinente que lo respalde?
- [ ] ¿Los datos/materiales son accesibles?
- [ ] ¿Se puede completar en 6-12 meses?
- [ ] ¿El director lo aprueba?
- [ ] ¿Está alineado con la orientación formativa de la especialidad?

## Etapa 2: Propuesta de Investigación

### Estructura estándar
1. **Contexto de la investigación**
   - Contexto macro (social/académico)
   - Contexto micro (fenómeno específico)
   - Planteamiento del problema (del contexto al problema)

2. **Revisión de literatura**
   - Trayectoria de la investigación (cronológica/temática/metodológica)
   - Principales postulados (clasificación sistemática)
   - Insuficiencias de la investigación (análisis de brechas)
   - Posicionamiento de este trabajo (declaración de contribución)

3. **Contenido de la investigación**
   - Objetivos de investigación (general + específicos)
   - Preguntas de investigación (3-5 preguntas específicas)
   - Hipótesis de investigación (si aplica)
   - Ruta técnica (diagrama de flujo)

4. **Métodos de investigación**
   - Metodología (empírica/normativa/interpretativa)
   - Métodos específicos (cuantitativos/cualitativos/mixtos)
   - Fuentes de datos
   - Herramientas de análisis

5. **Puntos de innovación**
   - Innovación teórica
   - Innovación metodológica
   - Innovación en materiales
   - Innovación en argumentos

6. **Plan de investigación**
   - Hitos temporales (diagrama de Gantt)
   - Resultados esperados
   - Riesgos y respuestas

### Preparación para la defensa de la propuesta
- Presentación de 10-15 minutos
- Preparar respuestas para: ¿Por qué este tema? ¿Por qué este método? ¿Es viable?
- Registrar los comentarios del jurado, revisar después de la sesión

## Etapa 3: Construcción del Esquema

### Tipos de esquema
- **Tipo directorio**: niveles jerárquicos de títulos de capítulos y secciones
- **Tipo lógico**: relación progresiva entre argumentos
- **Tipo tarjetas**: contenido central de cada párrafo

### Elementos del esquema
- Argumento central de cada capítulo
- Evidencias/materiales/datos
- Relación lógica con los capítulos anterior y posterior
- Extensión estimada en palabras

### Verificación del esquema
- [ ] ¿La lógica es coherente?
- [ ] ¿Los niveles son claros?
- [ ] ¿Las proporciones son equilibradas?
- [ ] ¿Hay redundancia?
- [ ] ¿Se cubren todas las preguntas de investigación?

## Etapa 4: Escritura Capítulo por Capítulo

### Orden de redacción sugerido
1. **Escribir primero**: Revisión de literatura, Métodos de investigación (relativamente independientes)
2. **Escribir después**: Análisis de datos, Estudios de caso (trabajo central)
3. **Escribir luego**: Introducción, Conclusiones (requieren perspectiva global)
4. **Escribir al final**: Resumen, Palabras clave

### Estructura de cada capítulo
- **Párrafo introductorio**: Propósito del capítulo, relación con el texto completo, adelanto del contenido central
- **Párrafos de desarrollo**: Argumento + Evidencia + Análisis (estructura PEEL)
  - Point: Argumento
  - Evidence: Evidencia
  - Explanation: Explicación
  - Link: Retorno al argumento / transición al siguiente argumento
- **Párrafo de cierre**: Síntesis de hallazgos, enlace entre capítulos

### Técnicas de escritura
- **Escribir a hora fija**: Establecer un horario regular de escritura para crear un hábito
- **Primero completar, luego perfeccionar**: El borrador no necesita ser perfecto, primero hay que escribirlo
- **Escribir por párrafos**: Escribir un párrafo a la vez para reducir la presión
- **Marcar lo pendiente**: Usar la etiqueta TODO para los puntos inciertos

## Etapa 5: Revisión y Perfeccionamiento

### Lista de verificación para auto-revisión
- [ ] ¿Los argumentos son claros?
- [ ] ¿Las evidencias son suficientes?
- [ ] ¿La lógica es rigurosa?
- [ ] ¿El lenguaje es preciso?
- [ ] ¿El formato es correcto?
- [ ] ¿Las citas son completas?

### Niveles de revisión
1. **Macro**: Reestructuración, adición/eliminación de capítulos, reorganización lógica
2. **Meso**: Reorganización de párrafos, optimización de transiciones, fortalecimiento de la argumentación
3. **Micro**: Pulido de palabras y oraciones, normalización de puntuación, unificación de formato

### Gestión de la retroalimentación del director
- Distinguir entre "debe corregirse" y "se sugiere corregir"
- Comunicarse proactivamente cuando no se entienda algo
- Marcar los cambios tras la corrección
- Conservar el registro de las modificaciones

## Etapa 6: Normas de Formato

### Requisitos de formato comunes
- **Portada**: Formato unificado de la institución
- **Resumen**: En chino e inglés, 300-500 palabras
- **Índice**: Generación automática, tres niveles de títulos
- **Cuerpo del texto**:
  - Fuente: Song Ti / Times New Roman
  - Tamaño: Xiao Si (12pt)
  - Interlineado: 1.5 o valor fijo de 20 puntos
  - Márgenes: Superior e inferior 2.54cm, izquierdo y derecho 3.17cm
- **Figuras y tablas**:
  - Título de figura debajo, título de tabla encima
  - Numeración: Figura 1-1, Tabla 2-1
  - Indicación de la fuente
- **Referencias bibliográficas**:
  - Formato: GB/T 7714-2015
  - Tipos: Monografía [M], Artículo de revista [J], Tesis [D], Conferencia [C], Documento electrónico [EB/OL]

### Herramientas de composición
- **Word**: Función de estilos, listas multinivel, pies de figura
- **LaTeX**: Overleaf, plantillas
- **Gestión de referencias**: EndNote, Zotero, NoteExpress

## Etapa 7: Detección de Plagio y Defensa

### Preparación para la detección de plagio
- **Auto-revisión**: CNKI, VIP, Wanfang (sistema indicado por la institución)
- **Estrategias para reducir el índice de similitud**:
  - Sustitución por sinónimos (manteniendo la precisión académica)
  - Reestructuración de oraciones (conversión activa-pasiva)
  - Uso de tablas y figuras (convertir texto a tablas/figuras)
  - Normalización de citas (marcar citas textuales)
- **Precauciones**:
  - Conservar la terminología técnica
  - Reescribir descripciones de fórmulas
  - Textos de leyes / poesía clásica no se cuentan (pero deben citarse)
  - La lista de referencias no se cuenta

### Preparación para la defensa
- **Elaboración de la presentación (PPT)**:
  - 15-20 diapositivas
  - Problema de investigación, métodos, hallazgos, contribuciones
  - Priorizar gráficos, texto conciso
  - Preparar guión de presentación (no leer las diapositivas)

- **Preguntas típicas de defensa**:
  - ¿Por qué eligió este tema?
  - ¿Cuáles son los puntos de innovación?
  - ¿Qué limitaciones tiene el método?
  - ¿Cómo se explica un resultado determinado?
  - ¿Qué mejoraría si lo hiciera de nuevo?

- **Protocolo de defensa**:
  - Vestimenta formal
  - Control del tiempo (presentación de 15-20 minutos)
  - Responder a las críticas con humildad
  - Registrar las observaciones de corrección

### Después de la defensa
- Organizar las observaciones de corrección
- Confirmar con el director el alcance de las correcciones
- Entregar la versión corrigida dentro del plazo
- Verificación final de formato
- Entregar versión electrónica y versión impresa
