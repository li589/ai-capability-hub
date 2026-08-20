# Guía de Escritura de Tesis de Psicología

## Características de la Disciplina
- Énfasis en diseño experimental, rigor estadístico y verificación teórica
- Importancia de la revisión ética, consentimiento informado y bienestar animal
- Artículos de revistas como principal formato (revistas de primer nivel: Psychological Science/JPSP/JEP/Developmental Psychology)
- El preregistro (preregistration) es cada vez más importante
- Tendencia de ciencia abierta (Open Science): datos/código/materiales compartidos

## Tipos de Investigación

### 1. Psicología Experimental
- **Aplicable**: relaciones causales, mecanismos cognitivos, experimentos conductuales
- **Tipos de diseño**:
  - Diseño entre sujetos (Between-subjects): diferentes sujetos reciben diferentes tratamientos
  - Diseño intra-sujetos (Within-subjects): un mismo sujeto recibe todos los tratamientos
  - Diseño mixto (Mixed): incluye variables tanto entre como intra-sujetos
- **Elementos clave**:
  - Manipulación de la variable independiente (clara, efectiva, replicable)
  - Medición de la variable dependiente (tiempo de reacción, tasa de aciertos, eye tracking, ERP, fMRI)
  - Control de confusos (aleatorización, balanceo, enmascaramiento)
  - Análisis de potencia (G*Power: f=0.25 efecto mediano, α=0.05, 1-β=0.80)
- **Normas de reporte**:
  - Preregistro de hipótesis (OSF, AsPredicted)
  - Descripción completa del procedimiento experimental (replicable)
  - Criterios de exclusión transparentes (ej. tiempo de reacción<200ms)
  - Complemento con análisis bayesiano (BF10)

### 2. Psicología del Desarrollo
- **Aplicable**: desarrollo a lo largo de la vida, diferencias por edad, seguimiento longitudinal
- **Tipos de diseño**:
  - Diseño transversal: medición simultánea de diferentes grupos de edad
  - Diseño longitudinal: mediciones repetidas de un mismo grupo
  - Diseño secuencial: combinación de transversal y longitudinal
- **Elementos clave**:
  - Agrupación por edad (teóricamente fundamentada: ej. etapas de Piaget)
  - Equivalencia de medida (comparabilidad de instrumentos entre edades)
  - Manejo de desgaste (prueba MAR/MCAR, imputación múltiple)
  - Efecto de cohorte (diferencias contextuales época)
- **Consideraciones especiales**:
  - Ética con niños: consentimiento de padres + asentimiento del niño (a partir de 7 años)
  - Adecuación al desarrollo: dificultad de la tarea, mantenimiento de atención
  - Deseabilidad social: los niños tienden más a complacer

### 3. Psicología Social
- **Aplicable**: cognición social, actitudes, procesos grupales, relaciones interpersonales
- **Métodos frecuentes**:
  - Encuestas: medición con escalas (Likert de 5/7 puntos)
  - Experimental: manipulación situacional (ej. variantes del experimento de conformidad de Asch)
  - Experimento de campo: intervención en situación natural
  - Análisis de archivo: datos históricos, contenido mediático
- **Elementos clave**:
  - Control del sesgo de deseabilidad social (anonimato, medición indirecta, IAT)
  - Representatividad de la muestra (problema WEIRD: occidental, educado, industrializado, rico, democrático)
  - Atención al tamaño del efecto (pequeño d=0.2, mediano d=0.5, grande d=0.8)
  - Replicación de experimentos (directa / conceptual / sistemática)

### 4. Psicología Clínica
- **Aplicable**: trastornos psicológicos, eficacia de intervenciones, instrumentos de evaluación
- **Tipos de diseño**:
  - ECA: estándar de oro, asignación aleatoria a grupo de tratamiento/control
  - Experimento de sujeto único: diseño ABA / líneas base múltiples
  - Cuasi-experimental: agrupamiento natural, pretest-postest
- **Elementos clave**:
  - Criterios diagnósticos (DSM-5/CIE-11)
  - Protocolo de intervención (manualizado, verificación de fidelidad)
  - Criterios de valoración (síntomas, funcionamiento, calidad de vida)
  - Manejo de deserción (análisis ITT/PP)
- **Ética especial**:
  - Protección de poblaciones vulnerables (pacientes, niños, ancianos)
  - Principio de mínimo riesgo
  - Confidencialidad de datos (normativas de protección de datos)

## Diseño Experimental

### Entre Sujetos vs. Intra-Sujetos
| Dimensión | Entre Sujetos | Intra-Sujetos |
|-----------|--------------|---------------|
| Ventajas | Sin efectos de orden ni práctica | Control de diferencias individuales, mayor potencia estadística |
| Desventajas | Requiere más sujetos, confusión por diferencias individuales | Efectos de orden, práctica, fatiga |
| Aplicable | Cuando los tratamientos tienen efectos permanentes | Cuando los tratamientos son reversibles, se necesita alta potencia |
| Tamaño muestral | ≥30 por grupo (efecto grande) | ≥20 total (efecto grande) |

### Diseños Cuasi-Experimentales
- **Pretest-postest con grupos desiguales**: sin aleatorización, requiere control estadístico
- **Series temporales interrumpidas**: múltiples mediciones, comparación antes y después de la intervención
- **Regresión discontinua**: agrupamiento basado en umbral de variable continua
- **Grupo control no equivalente**: emparejamiento en lugar de aleatorización

### Potencia Estadística
- **Herramientas de cálculo**: G*Power, paquete pwr, WebPower
- **Parámetros**:
  - Tamaño del efecto (d=0.2 pequeño/0.5 mediano/0.8 grande; f=0.1 pequeño/0.25 mediano/0.4 grande)
  - Nivel α (0.05 o 0.01)
  - Potencia estadística (1-β=0.80 o 0.90)
  - Tipo de prueba (bilateral/unilateral)
- **Recomendaciones**:
  - Efecto pequeño: ≥64 por grupo (potencia 0.80)
  - Efecto mediano: ≥26 por grupo
  - Efecto grande: ≥16 por grupo

## Métodos Estadísticos

### Análisis Básicos
- **Prueba t**: comparación de dos grupos (independientes/pareados)
- **ANOVA**: comparación de múltiples grupos
  - Unidireccional: una variable independiente
  - Factorial: múltiples variables independientes + efecto de interacción
  - De medidas repetidas: variable intra-sujetos
  - MANOVA: múltiples variables dependientes
- **Chi-cuadrado**: asociación entre variables categóricas
- **Análisis de correlación**: Pearson/Spearman

### Análisis Avanzados
- **Análisis de regresión**:
  - Regresión lineal: predictor continuo → resultado continuo
  - Regresión logística: resultado categórico
  - Regresión de Poisson: resultado de conteo
  - Regresión multinivel: datos anidados (sujeto → aula → escuela)
- **Modelos de ecuaciones estructurales (SEM)**:
  - Análisis factorial confirmatorio (CFA): modelo de medición
  - Análisis de trayectorias: modelo estructural
  - Comparación multigrupo: equivalencia de medida (configural/métrica/escalar)
- **Modelos lineales multinivel (HLM/MLM)**:
  - Modelos de intercepto/pendiente aleatoria
  - Interacción entre niveles
  - Anidamiento de 3 o más niveles
- **Modelos de crecimiento latente (LGM)**:
  - Crecimiento lineal/no lineal
  - Predictores del crecimiento
  - Modelo de procesos paralelos
- **Análisis de supervivencia**: tiempo hasta el evento

### Reporte de Tamaño del Efecto
- **Cohen’s d**: diferencia de medias entre dos grupos (pequeño 0.2/mediano 0.5/grande 0.8)
- **η² (eta-cuadrado)**: proporción de varianza explicada (pequeño 0.01/mediano 0.06/grande 0.14)
- **ω² (omega-cuadrado)**: estimación insesgada
- **r²**: coeficiente de determinación
- **Odds ratio (OR)**: regresión logística
- **Intervalo de confianza**: IC 95% más importante que el valor p

## Uso de Escalas

### Fuentes Frecuentes de Escalas
- **APA PsycTests**: base de datos oficial de pruebas psicológicas
- **Mental Measurements Yearbook**: evaluación de pruebas
- **Apéndices de revistas**: los artículos originales suelen incluir la escala completa
- **Manuales**: ej. manual del Big Five Inventory (BFI)

### Procedimiento de Traducción y Retrotraducción
1. Inglés → idioma meta (traducción por bilingüe)
2. Idioma meta → inglés (retrotraducción por otro bilingüe independiente)
3. Comparación del original con la retrotraducción
4. Discusión de diferencias por comité de expertos
5. Prueba piloto (30-50 personas)
6. Validación de fiabilidad y validez

### Requisitos de Fiabilidad y Validez
- **Fiabilidad**:
  - Alfa de Cronbach ≥ 0.70 (aceptable)
  - Fiabilidad por mitades ≥ 0.70
  - Fiabilidad test-retest (intervalo 2-4 semanas) r ≥ 0.70
- **Validez**:
  - Validez de contenido: evaluación por expertos
  - Validez de constructo: EFA/CFA, carga factorial ≥ 0.50
  - Validez de criterio: correlación con estándar externo
  - Validez discriminante: AVE > correlación²

## Requisitos Éticos

### Principios Éticos de la APA (5 principios)
1. **Beneficencia y no maleficencia**: maximizar beneficios, minimizar daños
2. **Fidelidad y responsabilidad**: estándares profesionales, responsabilidad social
3. **Integridad**: honestidad, exactitud, sin fraude
4. **Justicia**: trato equitativo, evitar sesgos
5. **Respeto**: autonomía, privacidad, dignidad

### Consentimiento Informado
- **Elementos**: propósito del estudio, procedimientos, riesgos, beneficios, confidencialidad, voluntariedad, datos de contacto
- **Poblaciones especiales**:
  - Niños: consentimiento de padres + asentimiento del niño (a partir de 7 años)
  - Deterioro cognitivo: representante legal
  - Reclusos: protección adicional
- **Investigación con engaño**: explicación posterior (debriefing)

### Ética de Experimentación con Animales
- **Principio 3R**: Reemplazo (Replacement), Reducción (Reduction), Refinamiento (Refinement)
- **Revisión del IACUC**: aprobación del protocolo, supervisión veterinaria
- **Condiciones de alojamiento**: enriquecimiento ambiental, necesidades sociales
- **Punto final**: punto final humanitario, criterios de eutanasia

## Plantilla de Estructura del Trabajo

### Investigación Experimental
```
1. Introducción
   - Antecedentes teóricos (conceptos centrales)
   - Estado de la investigación (brecha en la literatura)
   - Pregunta de investigación e hipótesis (H1a, H1b...)
   - Contribución teórica y significado práctico

2. Método
   - Participantes (reclutamiento, selección, tamaño muestral, compensación)
   - Diseño (2×3 mixto, variables independientes/dependientes)
   - Materiales / estímulos (fuente, elaboración, prueba piloto)
   - Procedimiento (pasos, aleatorización, enmascaramiento)
   - Plan de análisis de datos (enlace de preregistro)

3. Resultados
   - Estadísticas descriptivas (M, SD, n)
   - Verificación de manipulación (VI efectiva)
   - Prueba de hipótesis (tabla ANOVA, tamaño del efecto, IC)
   - Análisis adicionales (exploratorio, bayesiano)
   - Tablas y figuras (gráfico de medias, gráfico de interacción)

4. Discusión
   - Resumen de verificación de hipótesis
   - Interpretación teórica (mecanismo)
   - Comparación con investigaciones previas
   - Limitaciones (muestra, método, generalización)
   - Direcciones futuras (hipótesis concretas)
   - Conclusión (concisa)

5. Materiales complementarios (en línea)
   - Cuestionario / estímulos completos
   - Datos crudos (OSF)
   - Código de análisis (R/Python)
```

## Prácticas de Ciencia Abierta

### Preregistro
- **Plataformas**: OSF, AsPredicted, ClinicalTrials.gov
- **Contenido**: hipótesis, diseño, tamaño muestral, plan de análisis
- **Tipos**:
  - Preregistro estándar: antes de la recolección de datos
  - Registered Reports: compromiso de publicación por la revista (independientemente de los resultados)
- **Beneficios**: prevenir HARKing (hipótesis post hoc), mejorar la credibilidad

### Compartición de Datos
- **Plataformas**: OSF, Figshare, Zenodo, GitHub
- **Contenido**:
  - Datos crudos (desidentificados)
  - Código de análisis (replicable)
  - Materiales de investigación (cuestionarios, estímulos)
- **Licencias**: CC0 (recomendado), CC-BY

### Compartición de Código
- **Requisitos**: ejecutable, con comentarios, con README
- **Herramientas**: R Markdown, Jupyter Notebook
- **Control de versiones**: Git/GitHub

## Errores Comunes
1. Tamaño muestral insuficiente (potencia<0.80)
2. Comparaciones múltiples sin corrección (Bonferroni/FDR)
3. Diseño intra-sujetos sin control de orden (cuadrado latino/aleatorización)
4. No reportar tamaño del efecto (solo valor p)
5. Hipótesis post hoc (HARKing)
6. Sesgo de método común (datos de la misma fuente)
7. Fiabilidad baja de la escala (alfa<0.70 aún en uso)
8. Inferencia causal excesiva (diseño correlacional)
9. Descuido de diferencias culturales (muestra WEIRD)
10. Ausencia de descripción ética (no supera la revisión por pares)
