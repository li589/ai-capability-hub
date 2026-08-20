# Guía general para la redacción de trabajos académicos en Ingeniería

## Características de la disciplina
- Énfasis en la orientación a problemas, innovación en soluciones y validación experimental
- Importancia de la reproducibilidad, parámetros completos y condiciones límite
- Artículos de conferencia + artículos de revista con igual importancia (conferencias top: serie IEEE/serie ACM)
- Alta calidad exigida en tablas y figuras (planos de ingeniería, figuras de simulación, fotos reales)

## Tipos de investigación

### 1. Investigación de diseño
- **Aplicable a**: diseño de nuevos sistemas/nuevas estructuras/nuevos algoritmos
- **Elementos clave**:
  - Análisis de requisitos (funcional/restricciones de rendimiento)
  - Diseño de solución (arquitectura/módulos/interfaz)
  - Argumentación de viabilidad (teórica/prototipo de simulación)
  - Evaluación de rendimiento (comparativo/pruebas de referencia)
- **Estructura del trabajo**: problema → solución → implementación → validación → discusión

### 2. Investigación experimental
- **Aplicable a**: experimentos físicos, pruebas de rendimiento, verificación de fiabilidad
- **Elementos clave**:
  - Plataforma experimental (equipos/entorno/condiciones)
  - Diseño experimental (variables/niveles/repeticiones)
  - Adquisición de datos (sensores/tasa de muestreo/precisión)
  - Análisis de resultados (incertidumbre/error/estadística)
- **Estructura del trabajo**: objetivo → método → experimento → resultados → análisis

### 3. Investigación de simulación
- **Aplicable a**: simulación numérica, análisis computacional, verificación virtual
- **Elementos clave**:
  - Establecimiento del modelo (geométrico/físico/matemático)
  - Generación de malla (tipo/densidad/calidad)
  - Condiciones límite (cargas/restricciones/contacto)
  - Configuración de resolución (algoritmo/convergencia/precisión)
  - Verificación de resultados (comparación con experimentos/comparación con literatura)
- **Estructura del trabajo**: problema → modelado → resolución → verificación → aplicación

### 4. Investigación de optimización
- **Aplicable a**: optimización de parámetros, optimización estructural, optimización de programación
- **Elementos clave**:
  - Objetivo de optimización (un objetivo/múltiples objetivos)
  - Variables de diseño (continuas/discretas/mixtas)
  - Restricciones (igualdad/desigualdad)
  - Algoritmo de optimización (gradual/heurístico/metaheurístico)
  - Análisis de convergencia (curva de iteración/estabilidad)
- **Estructura del trabajo**: problema → modelado → algoritmo → experimento → comparación

## Plantilla de estructura del trabajo

### Tesis de grado
`
1. Introducción
   - Contexto de investigación (necesidades de ingeniería, estado actual de la tecnología)
   - Estado de la investigación nacional e internacional (revisión clasificada)
   - Objetivo y significado de la investigación
   - Organización del trabajo

2. Fundamentos teóricos/trabajo relacionado
   - Definición de conceptos clave
   - Derivación de teorías fundamentales
   - Resumen de métodos existentes (tabla comparativa de ventajas y desventajas)

3. Diseño de solución/propuesta de método
   - Arquitectura general (diagrama del sistema)
   - Diseño detallado (diagrama de descomposición de módulos)
   - Algoritmos clave (pseudocódigo/diagrama de flujo)
   - Explicación de puntos de innovación

4. Experimentos/simulación/implementación
   - Plataforma experimental/entorno de simulación
   - Configuración de parámetros (lista completa)
   - Diseño experimental (diseño de grupo de control)
   - Proceso de implementación (pasos clave)

5. Resultados y análisis
   - Resultados principales (prioridad en tablas y figuras)
   - Análisis comparativo (con métodos existentes)
   - Análisis de sensibilidad de parámetros
   - Análisis de incertidumbre/error
   - Discusión (explicación del mecanismo)

6. Conclusiones y perspectivas
   - Principales contribuciones (1.2.3.)
   - Limitaciones
   - Trabajo futuro
`

### Tesis de maestría/artículo de revista
Adicional:
- Derivaciones teóricas más detalladas
- Verificación experimental más completa (múltiples escenarios/múltiples conjuntos de datos)
- Análisis de mecanismo más profundo
- Comparaciones más amplias (métodos SOTA)
- Análisis de complejidad (temporal/espacial)

## Especificaciones de tablas y figuras

### Planos de ingeniería
- **Planos CAD**: especificaciones de tipo de línea (línea gruesa continua/línea fina continua/línea punteada/línea de centro)
- **Acotación**: completa, clara, sin omisiones
- **Tolerancias y ajustes**: acotación razonable (grado IT)
- **Acotación de materiales**: designación, estado, tratamiento térmico
- **Requisitos técnicos**: rugosidad superficial, tolerancias geométricas

### Figuras de resultados de simulación
- **Diagramas de contorno**: escala de color clara, rango razonable, unidades etiquetadas
- **Gráficos de curvas**: etiquetas de ejes, unidades, leyenda, cuadrícula
- **Gráficos vectoriales**: dirección de flechas, proporción de tamaño, ampliación de áreas clave
- **Gráficos comparativos**: misma escala, mismo ángulo de vista, mismos parámetros

### Fotografías de objetos reales
- **Resolución**: superior a 300dpi
- **Fondo**: simple, sin interferir con el sujeto principal
- **Etiquetas**: indicación de componentes clave, referencia de dimensiones
- **Múltiples ángulos**: general + parcial + detalle

### Diagramas de sistema/diagramas de flujo
- **Jerarquía clara**: nivel de sistema → nivel de módulo → nivel de unidad
- **Interfaces claras**: flujo de señales, flujo de datos, flujo de control
- **Símbolos estándar**: conforme a estándares IEEE/GB
- **Especificaciones de color**: diferenciación funcional (entrada/procesamiento/salida/retroalimentación)

## Fórmulas y algoritmos

### Especificaciones de fórmulas
- **Numeración**: (1), (2), (3)..., alineación a la derecha
- **Referencias**: "como se muestra en la fórmula (3)"
- **Derivaciones**: no omitir pasos clave, citar teoremas requiere etiquetado
- **Símbolos**: definición en primera aparición, consistente en todo el documento
- **Unidades**: unidades SI, consistencia dimensional

### Pseudocódigo de algoritmos
- **Formato**: estructurado, indentación, comentarios
- **Entrada/Salida**: parámetros claros, valores de retorno
- **Complejidad**: etiquetar complejidad temporal/espacial
- **Pasos clave**: resaltar en negrita/comentar

`
Algoritmo 1: Algoritmo XXX
Entrada: parámetro1, parámetro2, ...
Salida: resultado
1. Inicializar...
2. para i = 1 hasta n hacer
3.   Calcular...
4.   si condición entonces
5.     Actualizar...
6.   fin si
7. fin para
8. devolver resultado
`

## Herramientas recomendadas

### Modelado y simulación
- **MATLAB/Simulink**: control, señales, cálculo numérico
- **ANSYS**: estructuras, fluidos, electromagnético, multifísica
- **SolidWorks/CATIA**: modelado 3D, ensamblaje, planos de ingeniería
- **AutoCAD**: planos 2D de ingeniería, diagramas eléctricos
- **COMSOL**: simulación de acoplamiento multifísico
- **ABAQUS**: análisis no lineal, mecánica de materiales

### Programación y algoritmos
- **Python**: análisis de datos, aprendizaje automático, automatización
- **C/C++**: computación de alto rendimiento, sistemas en tiempo real
- **LabVIEW**: sistemas de medición y control, instrumentos virtuales
- **Programación PLC**: control industrial, automatización

### Visualización de datos
- **Origin**: gráficos científicos, ajuste de curvas
- **Tecplot**: postprocesamiento CFD, diagramas de contorno
- **Paraview**: visualización de código abierto, datos a gran escala
- **MATLAB**: gráficos integrados, personalización

## Errores comunes
1. Configuración de parámetros incompleta (faltan parámetros clave)
2. Condiciones límite no claras (afectan la reproducibilidad de resultados)
3. Baja calidad de tablas y figuras (baja resolución, etiquetas poco claras)
4. Comparación injusta (diferentes condiciones, diferentes conjuntos de datos)
5. Falta de análisis de error (incertidumbre no evaluada)
6. Descripción vaga de puntos de innovación (sin comparación con métodos existentes)
7. Saltos en la derivación teórica (omisión de pasos clave)
8. Baja reproducibilidad experimental (entorno/equipos no registrados)
9. Generalización excesiva en conclusiones (más allá de las condiciones experimentales)
10. Planos de ingeniería no estandarizados (errores en tipos de línea/acotación/tolerancias)