# Guía para la redacción de trabajos académicos en Ciencias de la Computación (CS)

## Características de la disciplina
- Énfasis en la innovación algorítmica, implementación de sistemas y validación experimental
- Importancia del código abierto, conjuntos de datos y reproducibilidad
- Artículos de conferencia > artículos de revista (conferencias top: CVPR/ICML/NeurIPS/SIGCOMM/SOSP)

## Direcciones de investigación

### Áreas populares
1. **Inteligencia Artificial/Aprendizaje Automático**
   - Optimización de eficiencia de grandes modelos (aceleración de inferencia, compresión de modelos)
   - Aprendizaje multimodal (fusión visión-lenguaje-audio)
   - Seguridad y alineación de IA (RLHF, pruebas de equipo rojo)
   - Aprendizaje federado y computación con privacidad

2. **Sistemas y Redes**
   - Sistemas nativos en la nube (Serverless, microservicios)
   - Computación en el borde e IoT
   - Ciberseguridad (arquitectura de confianza cero, detección de amenazas)
   - Consistencia en sistemas distribuidos

3. **Ingeniería de Software**
   - Inteligencia de código (generación de código, detección de defectos)
   - DevOps y AIOps
   - Seguridad de la cadena de suministro de software
   - Plataformas de código bajo/sin código

4. **Ciencia de Datos**
   - Análisis de series temporales
   - Aplicaciones de redes neuronales de grafos
   - Gobernanza y calidad de datos
   - Procesamiento de flujo en tiempo real

### Criterios de evaluación de temas
- **Innovación**: nuevo problema o nueva solución o nueva perspectiva
- **Factibilidad**: completable en 6-12 meses
- **Valor**: reconocimiento académico o industrial
- **Datos/Código**: disponibilidad de recursos públicos

## Plantilla de estructura del trabajo

### Tesis de grado
`
1. Introducción (contexto de investigación, definición del problema, resumen de contribuciones)
2. Trabajo relacionado (revisión clasificada, identificación de brechas)
3. Diseño del método/sistema (diagrama de arquitectura, pseudocódigo del algoritmo, diagrama de flujo)
4. Experimentos/Implementación (conjuntos de datos, métricas, experimentos comparativos, ablación)
5. Análisis de resultados (tablas y gráficos, significancia estadística, estudio de caso)
6. Discusión (limitaciones, trabajo futuro)
7. Conclusión
`

### Tesis de maestría
Adicional:
- Fundamentos teóricos (definiciones formales, demostración de teoremas)
- Experimentos más completos (múltiples conjuntos de datos, múltiples líneas base, ejecución prolongada)
- Despliegue del sistema (pruebas en entorno real, estudios con usuarios)

## Puntos clave de redacción

### Descripción de algoritmos
- Usar pseudocódigo (no código real)
- Análisis de complejidad temporal/espacial
- Demostración de convergencia (para problemas de optimización)

### Diseño experimental
- Selección de línea base: métodos clásicos + SOTA
- Métricas de evaluación: Accuracy/F1/Latency/Throughput
- Pruebas de significancia: t-test o Wilcoxon
- Experimentos de ablación: verificar la necesidad de cada componente

### Especificaciones de tablas y figuras
- Usar gráficos vectoriales (PDF/SVG)
- Colores amigables para daltónicos
- Barras de error (múltiples ejecuciones)
- Tablas con tres líneas

## Errores comunes
1. **Experimentos insuficientes**: solo 1-2 conjuntos de datos, falta comparación
2. **Afirmaciones excesivas**: "primera propuesta", "óptimo" (requiere demostración)
3. **Código no reproducible**: falta configuración de entorno, semillas aleatorias
4. **Revisión de trabajo relacionado**: debe incluir análisis crítico
5. **Introducción vacía**: debe especificar qué problema se resuelve

## Herramientas recomendadas
- **Gestión de experimentos**: Weights & Biases, MLflow
- **Visualización**: Matplotlib, Seaborn, Plotly
- **Versionado de código**: Git + GitHub
- **Escritura**: Overleaf (LaTeX)
- **Referencias**: Zotero + Better BibTeX

## Recomendaciones de envío
- **Conferencias**: atención a fechas límite, completar 2 meses antes
- **Revistas**: ciclo de revisión largo, adecuado para trabajo sistemático
- **arXiv**: publicación rápida, establecer prioridad

## Precauciones para verificación de plagio
- Fragmentos de código no se contabilizan en la verificación (en la mayoría de sistemas)
- Descripciones de fórmulas usar palabras propias
- Pseudocódigo algorítmico acepta cierta repetición
- Descripciones de configuración experimental pueden estandarizarse