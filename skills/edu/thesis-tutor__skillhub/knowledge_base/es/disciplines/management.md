# Guía de Escritura de Tesis de Administración / Gestión Empresarial

## Características de la Disciplina
- Énfasis en marcos teóricos, verificación empírica e implicaciones gerenciales
- Importancia de fuentes de datos, medición de variables y tratamiento de endogeneidad
- Artículos de revistas como principal formato (revistas de primer nivel: AMJ/SMJ/JOM/OS/MS)
- Estudios de caso bien valorados (construcción/verificación teórica)

## Tipos de Investigación

### 1. Estudio de Caso
- **Aplicable**: exploración de nuevos fenómenos, construcción teórica, procesos complejos
- **Tipos**:
  - Caso único (extremo / típico / longitudinal)
  - Múltiples casos (replicación / comparación / complementariedad)
- **Puntos clave de diseño**:
  - Selección de caso (muestreo teórico, no aleatorio)
  - Recopilación de datos (entrevistas / archivos / observación / múltiples fuentes)
  - Estrategia de análisis (patrones coincidentes / construcción de explicaciones / secuencia temporal)
  - Garantía de fiabilidad (triangulación / verificación por miembros / auditoría)
- **Normas de reporte**:
  - Descripción contextual rica (contextualización)
  - Cadena de evidencia clara (datos → tablas → conclusiones)
  - Diálogo con la literatura (confirmar / ampliar / desafiar)

### 2. Investigación por Encuesta
- **Aplicable**: verificación de hipótesis con grandes muestras, relaciones entre variables
- **Tipos**: transversal / longitudinal / panel
- **Puntos clave de diseño**:
  - Marco de muestreo (accesibilidad a la población objetivo)
  - Diseño del cuestionario (escalas validadas + ítems propios)
  - Recopilación de datos (en línea / papel / mixto)
  - Sesgo de método común (factor único de Harman / control procedimental)
- **Métodos de análisis**:
  - Modelos de ecuaciones estructurales (SEM): AMOS/PLS/Mplus
  - Modelos lineales multinivel (HLM): datos anidados
  - Modelos de crecimiento latente (LGM): seguimiento longitudinal

### 3. Investigación Experimental
- **Aplicable**: relaciones causales, mecanismos conductuales
- **Tipos**: laboratorio / campo / cuasi-experimental / experimento natural
- **Puntos clave de diseño**:
  - Asignación aleatoria (aleatorización simple / pareada)
  - Verificación de manipulación (si la variable independiente es efectiva)
  - Medición de la variable dependiente (objetiva / subjetiva / conductual)
  - Control de variables (exclusión de factores confusos)
- **Métodos de análisis**:
  - ANOVA/ANCOVA: comparación entre grupos
  - Mediador / Moderador: macro PROCESS
  - Multinivel: HLM

### 4. Análisis de Datos Secundarios
- **Aplicable**: investigación macro, datos de panel, estudios de eventos
- **Fuentes de datos**:
  - Empresas cotizadas: CSMAR, Wind, GT (GuoTaiAn)
  - Datos de patentes: Oficina Nacional de Propiedad Intelectual, Derwent
  - Datos de contratación: Zhilian, 51job
  - Redes sociales: Weibo, Zhihu, Maimai (web scraping)
- **Métodos de análisis**:
  - Modelos de datos de panel: efectos fijos / aleatorios / GMM
  - DID/PSM: inferencia causal
  - Estudio de eventos: cálculo de CAR
  - Análisis de texto: frecuencia de palabras, modelos temáticos, análisis de sentimiento

## Marcos Teóricos

### Teorías Frecuentemente Utilizadas
- **Visión basada en recursos (RBV)**: recursos VRIN → ventaja competitiva
- **Teoría institucional**: presiones institucionales regulatorias / normativas / cognitivas
- **Teoría de agencia**: conflicto principal-agente → mecanismos de gobernanza
- **Teoría de los grupos de interés**: equilibrio entre múltiples actores
- **Capacidades dinámicas**: percibir / captar / transformar
- **Aprendizaje organizacional**: explorar / explotar, transformación del conocimiento (SECI)
- **Teoría del escalafón superior**: características directivas → elecciones estratégicas → resultados organizacionales
- **Redes sociales**: agujeros estructurales / centralidad / incrustación
- **Teoría de señales**: envío de señales → interpretación de señales → resultados
- **Teoría de legitimidad**: legitimidad pragmática / moral / cognitiva

### Recomendaciones sobre el Uso de Teorías
1. **No acumular teorías**: 1-2 teorías centrales son suficientes
2. **Clarificar la perspectiva teórica**: qué se explica, qué se predice
3. **Vincular teoría e hipótesis**: cada hipótesis con soporte teórico
4. **Diálogo teórico**: resultados consistentes / contradictorios / extensivos con la teoría

## Fuentes de Datos y Medición

### Diseño del Cuestionario
- **Fuente de escalas**: priorizar escalas validadas (fiabilidad y validez ya comprobadas)
- **Traducción y retrotraducción**: escala en inglés → español → retrotraducción → comparación
- **Número de ítems**: 3-7 por constructo (evitar fatiga)
- **Ítems inversos**: incluir 2-3 (prevenir respuesta por defecto)
- **Prueba piloto**: 30-50 personas, eliminar si CITC<0.4

### Bases de Datos Frecuentes
- **CSMAR**: finanzas, gobernanza y accionariado de empresas cotizadas
- **Wind**: finanzas, macroeconomía, sectores
- **GT (GuoTaiAn)**: economía y finanzas, economía regional
- **CEIC**: macroeconomía, datos sectoriales
- **Banco Mundial**: comparación transnacional, indicadores de desarrollo
- **CFPS (China Family Panel Studies)**: individuos micro
- **CHARLS (China Health and Retirement Longitudinal Study)**: envejecimiento

### Medición de Variables
- **Variable independiente**: definición operacional clara
- **Variable dependiente**: medición multidimensional (objetiva + subjetiva)
- **Variable mediadora**: explicación del mecanismo
- **Variable moderadora**: condiciones de frontera
- **Variables de control**: exclusión de explicaciones alternativas

## Métodos de Análisis

### Modelos de Ecuaciones Estructurales (SEM)
- **CB-SEM (AMOS/Mplus)**:
  - Gran muestra (>200)
  - Análisis confirmatorio
  - Ajuste estricto del modelo (CFI>0.9, RMSEA<0.08, SRMR<0.08)
- **PLS-SEM (SmartPLS)**:
  - Aceptable con muestras pequeñas
  - Análisis exploratorio
  - Orientado a la predicción (PLSpredict)

### Modelos Lineales Multinivel (HLM)
- **Aplicable**: datos anidados (empleados → equipos → organizaciones)
- **Software**: HLM, Mplus, R (lme4)
- **Reporte**: ICC(1), ICC(2), rwg, efectos entre niveles

### Análisis Cualitativo Comparativo (QCA)
- **Aplicable**: complejidad causal, combinaciones multifactoriales
- **Tipos**: crisp-set / fuzzy-set / mvQCA
- **Software**: fsQCA, R (paquete QCA)
- **Reporte**: tabla de verdad, consistencia, cobertura, solución intermedia

### Tratamiento de Endogeneidad
- **Fuentes**: variables omitidas, causalidad inversa, error de medición, selección de muestra
- **Métodos**:
  - Variables instrumentales (VI): MC2E
  - Diferencia en diferencias (DID): choque político
  - Propensity Score Matching (PSM): emparejamiento de muestra
  - Regresión discontinua (RDD): cerca del umbral
  - Modelo de Heckman: selección de muestra

## Plantilla de Estructura del Trabajo

### Investigación Empírica (Cuantitativa)
```
1. Introducción
   - Contexto práctico (fenómeno gerencial)
   - Brecha teórica (diálogo con la literatura)
   - Pregunta de investigación
   - Contribución teórica
   - Significado práctico

2. Revisión de Literatura e Hipótesis
   - Definición de constructos centrales
   - Literatura sobre el efecto principal (A→B)
   - Mecanismo de mediación (A→M→B)
   - Frontera de moderación (W afecta A→B)
   - Tabla resumen de hipótesis

3. Diseño de Investigación
   - Muestra y procedimiento
   - Medición de variables (fuente de escala + fiabilidad)
   - Estrategia de análisis
   - Control del sesgo de método común

4. Resultados
   - Estadísticas descriptivas + matriz de correlación
   - Modelo de medición (CFA/fiabilidad y validez)
   - Modelo estructural (coeficientes de trayectoria + significancia)
   - Efecto de mediación (Bootstrap)
   - Efecto de moderación (término de interacción/pendiente simple)
   - Prueba de robustez (medición alternativa/submuestra)

5. Discusión
   - Resumen de verificación de hipótesis
   - Contribución teórica (diálogo)
   - Implicaciones gerenciales (operativas)
   - Limitaciones (muestra/método/causalidad)
   - Investigación futura (direcciones concretas)
```

### Estudio de Caso (Cualitativo)
```
1. Introducción: fenómeno → problema → método → contribución
2. Revisión de literatura: perspectiva teórica → brecha → marco
3. Método:
   - Selección de caso (lógica de muestreo teórico)
   - Recopilación de datos (matriz de evidencia multisource)
   - Análisis de datos (estrategia de codificación)
   - Garantía de fiabilidad (triangulación, etc.)
4. Descripción del caso: contexto → proceso → eventos clave
5. Análisis transversal de casos: patrones → proposiciones → teoría
6. Discusión: contribución → implicaciones → limitaciones → futuro
```

## Errores Comunes
1. Marco teórico débil (hipótesis sin soporte teórico)
2. Descuido de la endogeneidad (inferencia causal poco fiable)
3. Sesgo de método común (datos homólogos sin tratamiento)
4. Adaptación arbitraria de escalas (se comprometen fiabilidad y validez)
5. Interpretación errónea del efecto de mediación (mediación completa ≠ mediación)
6. Gráfico erróneo del efecto moderador (dirección de la pendiente simple)
7. Sesgo de selección de muestra (generalización con muestreo por conveniencia)
8. Exceso de variables de control (controlar mediador/moderador)
9. Reporte selectivo de resultados (solo resultados significativos)
10. Implicaciones gerenciales vacías (falta de operatividad)
