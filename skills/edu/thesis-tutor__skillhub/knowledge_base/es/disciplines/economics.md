# Guía para la redacción de trabajos académicos en Economía

## Características de la disciplina
- Énfasis en modelos teóricos, análisis empíricos e implicaciones de política
- Importancia de la calidad de datos, estrategias de identificación y pruebas de robustez
- Predominio de artículos de revista (Top 5: AER/QJE/JPE/Econometrica/RES)

## Direcciones de investigación

### Microeconomía
1. **Economía Laboral**
   - Retorno de la educación, prima de habilidades
   - Salario mínimo, efectos en el empleo
   - Trabajo remoto, economía de plataformas

2. **Organización Industrial**
   - Antimonopolio en economía de plataformas
   - Fijación de precios en mercados digitales
   - Entrada/salida de empresas

3. **Economía Pública**
   - Efectos de políticas tributarias
   - Diseño de seguridad social
   - Competencia fiscal local

### Macroeconomía
1. **Crecimiento Económico**
   - Productividad total de factores
   - Crecimiento impulsado por innovación
   - Transformación estructural

2. **Política Monetaria**
   - Efectos de la flexibilización cuantitativa
   - Monedas digitales (CBDC)
   - Mecanismos de transmisión de tasas de interés

3. **Finanzas Internacionales**
   - Fluctuaciones cambiarias
   - Flujos de capital
   - Cadenas globales de valor

### Economía del Desarrollo
- Evaluación de efectos de reducción de pobreza precisa
- Inclusión financiera digital
- Cambio climático y agricultura
- Migración y urbanización

## Plantilla de estructura del trabajo

### Artículo empírico (el más común)
`
1. Introducción (pregunta de investigación, contribuciones, adelanto de hallazgos principales)
2. Revisión de literatura (contexto teórico, avances empíricos, posicionamiento del artículo)
3. Contexto institucional/marco teórico (situación local, predicciones teóricas)
4. Datos y estadísticas descriptivas (fuente de datos, definición de variables, características de la muestra)
5. Estrategia empírica (método de identificación, especificación del modelo, tratamiento de endogeneidad)
6. Resultados de referencia (regresión principal, interpretación de coeficientes, significancia económica)
7. Pruebas de robustez (variables alternativas, submuestras, placebo)
8. Análisis de mecanismos (efectos mediación, análisis de heterogeneidad)
9. Conclusiones y recomendaciones de política
`

### Artículo teórico
- Especificación del modelo (supuestos, estructura de juego, concepto de equilibrio)
- Análisis de equilibrio (existencia, unicidad, estática comparativa)
- Análisis de bienestar (eficiencia, efectos distributivos)
- Simulación numérica (calibración, contrafactual)

## Puntos clave de redacción

### Estrategia empírica
- **Estrategia de identificación**:
  - RCT (experimento aleatorio)
  - Experimento natural (DID, RDD, IV)
  - Métodos de emparejamiento (PSM, control sintético)

- **Tratamiento de endogeneidad**:
  - Variables omitidas (efectos fijos, variables de control)
  - Causalidad inversa (variables instrumentales, GMM)
  - Error de medición (múltiples indicadores, ecuaciones estructurales)

### Especificaciones de tablas de regresión
- Reportar progresivamente: referencia → con controles → con efectos fijos
- Errores estándar entre paréntesis (agrupados al nivel apropiado)
- Marcas de significancia: * p<0.1, ** p<0.05, *** p<0.01
- R², tamaño de muestra, estadístico F

### Significancia económica
- No solo reportar significancia estadística, sino explicar el significado económico
- Comparar con referencia: proporción del efecto respecto a la media
- Análisis costo-beneficio

## Fuentes de datos
- **Macro**: Oficina Nacional de Estadísticas, Banco Mundial, FMI, Penn World Table
- **Micro**: CHFS, CFPS, CHARLS, CGSS, base de datos de empresas industriales
- **Finanzas**: CSMAR, Wind, Bloomberg
- **Política**: informes de trabajo del gobierno, ministerio de finanzas, banco central

## Errores comunes
1. **Regresión espuria**: regresión directa de series temporales no estacionarias
2. **Sesgo de selección**: selección inadecuada de muestra
3. **Control excesivo**: controlar variables mediadoras
4. **Multicolinealidad**: VIF > 10
5. **Significancia falsa**: p-hacking, no reportar resultados negativos

## Herramientas recomendadas
- **Procesamiento de datos**: Stata (principal), R, Python (pandas)
- **Análisis de regresión**: Stata (reghdfe, ivreg2), R (fixest)
- **Visualización**: ggplot2, Stata coefplot
- **Gestión de literatura**: Zotero, Mendeley
- **Escritura**: LaTeX (Overleaf) o Word

## Recomendaciones de envío
- **Revistas chinas**: "Estudios Económicos", "Mundo de la Gestión", "Economía (trimestral)"
- **Revistas en inglés**: seleccionar por campo (JDE, JLE, serie AEJ)
- **Documentos de trabajo**: NBER, IZA, CEPR (establecer prioridad)

## Precauciones para verificación de plagio
- Descripciones empíricas (fuente de datos, definición de variables) pueden estandarizarse
- Derivaciones de modelos teóricos usar palabras propias
- La sección de revisión de literatura es la más propensa a repetición, requiere reformulación
- Recomendaciones de política combinar con datos más recientes