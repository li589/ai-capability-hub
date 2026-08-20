# Guía de Escritura de Tesis de Medicina / Ciencias de la Vida

## Características de la Disciplina
- Énfasis en la medicina basada en evidencias, verificación experimental y datos clínicos
- Importancia de la ética de investigación, consentimiento informado y protección de privacidad
- Artículos de revistas > comunicaciones a congresos (revistas de primer nivel: NEJM/Lancet/JAMA/Nature Medicine/Cell)
- Normas de escritura estrictas: CONSORT, PRISMA, STROBE, entre otros

## Tipos de Investigación

### 1. Ensayo Clínico Aleatorizado (ECA)
- **Aplicable**: evaluación de eficacia de fármacos/intervenciones
- **Puntos clave de diseño**:
  - Método de aleatorización (simple/estratificado/bloques)
  - Cegamiento (simple/doble/triple)
  - Tipo de control (placebo/activo/sin tratamiento)
  - Cálculo del tamaño muestral (análisis de potencia)
- **Norma de reporte**: Declaración CONSORT 2010 + diagrama de flujo
- **Requisito de registro**: ClinicalTrials.gov o registro equivalente nacional

### 2. Estudio de Cohorte
- **Aplicable**: exploración etiológica, factores pronósticos
- **Tipos**: prospectivo / retrospectivo / bidireccional
- **Puntos clave de diseño**:
  - Definición clara de la exposición
  - Protocolo de seguimiento completo
  - Control de tasa de pérdida de seguimiento (<20%)
  - Control de factores de confusión
- **Norma de reporte**: Declaración STROBE

### 3. Estudio de Casos y Controles
- **Aplicable**: enfermedades raras, enfermedades con período de latencia prolongado
- **Puntos clave de diseño**:
  - Definición clara del caso (estándar de oro)
  - Selección adecuada de controles (hospital/comunidad/población)
  - Selección de factores de emparejamiento
  - Control del sesgo de memoria
- **Norma de reporte**: Declaración STROBE

### 4. Estudio Transversal
- **Aplicable**: encuesta de prevalencia, descripción de situación actual
- **Puntos clave de diseño**:
  - Método de muestreo (multietapa estratificado)
  - Tamaño muestral (estimación de prevalencia)
  - Fiabilidad y validez del instrumento de encuesta
- **Norma de reporte**: Declaración STROBE (extensión transversal)

### 5. Metaanálisis
- **Aplicable**: síntesis de evidencias, comparación de eficacia
- **Tipos**:
  - Metaanálisis de intervención (ECA)
  - Metaanálisis diagnóstico
  - Metaanálisis en red (NMA)
  - Metaanálisis de datos individuales (IPD)
- **Norma de reporte**: Declaración PRISMA 2020 + registro (PROSPERO)
- **Puntos clave del análisis**:
  - Prueba de heterogeneidad (estadístico I²)
  - Sesgo de publicación (funnel plot, prueba de Egger)
  - Análisis de sensibilidad
  - Calidad de la evidencia (clasificación GRADE)

### 6. Revisión Sistemática
- **Aplicable**: revisión exhaustiva de evidencias en un campo
- **Pasos**:
  1. Formular la pregunta PICO
  2. Desarrollar la estrategia de búsqueda (al menos 3 bases de datos)
  3. Selección de literatura (dos revisores de forma independiente)
  4. Extracción de datos (formulario estandarizado)
  5. Evaluación de calidad (Riesgo de sesgo Cochrane / RoB 2)
  6. Síntesis de evidencias (cualitativa/cuantitativa)
- **Norma de reporte**: PRISMA 2020

## Requisitos Éticos

### Revisión Ética
- **Aprobación del CEI (Comité de Ética en Investigación)**: obligatoria para toda investigación con seres humanos
- **Contenido de revisión**: protocolo de investigación, formulario de consentimiento informado, cualificaciones del investigador
- **Seguimiento**: anual / eventos adversos graves / modificaciones del protocolo

### Consentimiento Informado
- **Elementos**: propósito del estudio, procedimientos, riesgos, beneficios, alternativas, confidencialidad, voluntariedad, datos de contacto
- **Situaciones especiales**: excepción en emergencias, representante legal para personas incapacitadas
- **Documentación**: versión firmada + fecha + copia para el participante

### Protección de Privacidad
- **Desidentificación**: nombre → número, número de identificación → parcialmente oculto
- **Seguridad de almacenamiento**: cifrado, control de acceso, registro de auditoría
- **Seguridad en transmisión**: transmisión cifrada, principio de mínima necesidad
- **Período de retención**: al menos 5 años tras la finalización del estudio

## Métodos Estadísticos

### Estadística Básica
- **Descriptiva**: media ± desviación estándar, mediana (RIQ), frecuencia (%)
- **Prueba de normalidad**: Shapiro-Wilk, Kolmogorov-Smirnov
- **Comparación entre grupos**: prueba t, ANOVA, chi-cuadrado, pruebas de rangos

### Estadística Avanzada
- **Análisis de supervivencia**: curvas de Kaplan-Meier, prueba Log-rank, regresión de Cox
- **Análisis ROC**: área bajo la curva, punto de corte óptimo, sensibilidad/especificidad
- **Regresión logística**: univariante → multivariante, OR, IC 95%
- **Análisis multifactorial**: lineal/Logística/Cox, estrategia de selección de variables
- **Medidas repetidas**: modelos de efectos mixtos, GEE
- **Mediación/Moderación**: Bootstrap, prueba de Sobel

### Cálculo del Tamaño Muestral
- **Software**: G*Power, PASS, nQuery
- **Parámetros**: tamaño del efecto, α (0.05), β (0.1 o 0.2), tasa de abandono
- **Métodos**:
  - Comparación de dos grupos: fórmula de prueba t / chi-cuadrado
  - Análisis de supervivencia: cálculo por número de eventos
  - Prueba diagnóstica: requisitos de sensibilidad/especificidad
  - Diseño de equivalencia/no inferioridad: determinación del margen

## Plantilla de Estructura del Trabajo

### Investigación Original (Formato IMRAD)
```
1. Página de título: título, autores, afiliación, autor de correspondencia
2. Resumen: estructurado (objetivo, método, resultado, conclusión)
3. Introducción: antecedentes → problema → objetivo → hipótesis
4. Métodos:
   - Diseño / lugar / período
   - Participantes (criterios de inclusión/exclusión)
   - Intervención / definición de exposición
   - Criterios de valoración (principal/secundario)
   - Métodos estadísticos (software/versión/nivel de significancia)
5. Resultados:
   - Diagrama de flujo (CONSORT)
   - Tabla de características basales
   - Resultado principal (tamaño del efecto + IC + valor p)
   - Resultados secundarios
   - Análisis de subgrupos
   - Análisis de sensibilidad
6. Discusión:
   - Resumen de hallazgos principales
   - Comparación con investigaciones previas
   - Explicación del mecanismo
   - Significado clínico
   - Limitaciones (honestidad)
   - Direcciones futuras
7. Conclusiones: concisas, sin exageración
8. Agradecimientos / Declaraciones: financiación, conflicto de intereses, contribución de autores
9. Referencias: según normas de la revista (Vancouver/APA)
```

### Revisión Sistemática / Metaanálisis
```
1. Título: identificar claramente “Revisión sistemática” o “Metaanálisis”
2. Resumen: resumen estructurado PRISMA
3. Introducción: antecedentes → problema → objetivo (PICO)
4. Métodos:
   - Registro del protocolo (número PROSPERO)
   - Criterios de inclusión (PICOS)
   - Estrategia de búsqueda (estrategia completa en apéndice)
   - Proceso de selección (dos revisores independientes)
   - Extracción de datos (formulario estandarizado)
   - Evaluación de calidad (herramienta + versión)
   - Métodos estadísticos (indicador de efecto, heterogeneidad, sesgo de publicación)
5. Resultados:
   - Diagrama de flujo de búsqueda (PRISMA)
   - Tabla de características de estudios incluidos
   - Gráfico de evaluación de calidad
   - Forest plot
   - Funnel plot
   - Análisis de subgrupos
   - Análisis de sensibilidad
6. Discusión: resumen de evidencias, confiabilidad, limitaciones, investigación futura
7. Conclusiones: implicaciones para la práctica clínica
```

## Normas de Escritura

### Lista de Normas de Reporte
- **ECA**: CONSORT 2010 (lista de 25 ítems + diagrama de flujo)
- **Revisión sistemática/Metaanálisis**: PRISMA 2020 (lista de 27 ítems + diagrama de flujo)
- **Estudios observacionales**: STROBE (lista de 22 ítems)
- **Pruebas diagnósticas**: STARD (lista de 30 ítems)
- **Reportes de caso**: CARE (lista de 13 ítems)
- **Experimentos con animales**: ARRIVE (lista de 21 ítems)
- **Investigación cualitativa**: SRQR (lista de 21 ítems)
- **Evaluación económica**: CHEERS (lista de 24 ítems)

### Normas de Reporte Estadístico
- **Tamaño del efecto**: diferencia de medias (DM), diferencia de medias estandarizada (DME), OR, RR, HR
- **Precisión**: intervalo de confianza del 95% (IC)
- **Valor p**: valor p exacto (ej. P=0.032), no escribir “P<0.05”
- **Datos faltantes**: reportar tasa de faltantes y método de tratamiento
- **Software**: nombre + versión (ej. SPSS 26.0, R 4.2.1)

## Recomendaciones de Publicación

### Selección de Revista
- **Factor de impacto**: cuartiles JCR (Q1-Q4), clasificación CAS
- **Grado de coincidencia**: alcance, público objetivo, tipo de artículo
- **Plazos de revisión**: revisión inicial, revisión por pares, plazo total
- **Acceso abierto**: costos de APC, políticas de financiación
- **Lista de alerta**: evitar revistas en lista de alerta

### Materiales de Envío
- **Carta de presentación**: novedad, significado clínico, revisores recomendados
- **Contribución de autores**: taxonomía CRediT
- **Conflicto de intereses**: ninguno / declaración específica
- **Disponibilidad de datos**: ubicación de almacenamiento, forma de acceso
- **Aprobación ética**: número de aprobación ética, consentimiento informado

### Respuesta a Revisores
- **Actitud**: cortés, objetivo, sin justificaciones excesivas
- **Formato**: respuesta punto por punto (opinión del revisor → respuesta → ubicación del cambio)
- **Estrategia**: aceptar comentarios razonables, rechazar con fundamento, complementar experimentos/datos
- **Plazo**: responder a tiempo, solicitar prórroga con anticipación si es necesario

## Errores Comunes
1. Tamaño muestral insuficiente (potencia insuficiente)
2. Comparaciones múltiples sin corrección (falsos positivos)
3. Exceso en inferencia causal (correlación ≠ causalidad)
4. Desbalance basal (fallo de aleatorización)
5. Tratamiento inadecuado de datos faltantes (eliminación arbitraria)
6. Exceso de análisis de subgrupos (falsos positivos)
7. Descuido de factores de confusión (sesgo)
8. Selección errónea del método estadístico (usar prueba t con distribución no normal)
9. Tablas y figuras no normalizadas (ejes, leyendas, unidades)
10. Ausencia de descripción ética (no supera la revisión por pares)
