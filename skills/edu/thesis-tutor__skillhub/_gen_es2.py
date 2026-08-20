# -*- coding: utf-8 -*-
import os

base = r'd:\Skill Library\Thesis Tutor v4.0\knowledge_base\es\disciplines'

# File 2: management.md
content2 = """# Gu\u00eda de Escritura de Tesis de Gesti\u00f3n / Administraci\u00f3n de Empresas

## Caracter\u00edsticas de la Disciplina
- \u00c9nfasis en marcos te\u00f3ricos, verificaci\u00f3n emp\u00edrica e implicaciones gerenciales
- Importancia de fuentes de datos, medici\u00f3n de variables y tratamiento de endogeneidad
- Art\u00edculos en revistas principales (top journals: AMJ/SMJ/JOM/OS/MS)
- Estudios de caso bien aceptados (construcci\u00f3n/verificaci\u00f3n de teor\u00eda)

## Tipos de Investigaci\u00f3n

### 1. Estudio de Caso
- **Aplicable**: exploraci\u00f3n de nuevos fen\u00f3menos, construcci\u00f3n de teor\u00eda, procesos complejos
- **Tipos**:
  - Caso \u00fanico (extremo/t\u00edpico/longitudinal)
  - M\u00faltiples casos (replicaci\u00f3n/contraste/complementariedad)
- **Puntos clave de dise\u00f1o**:
  - Selecci\u00f3n de caso (muestreo te\u00f3rico, no aleatorio)
  - Recolecci\u00f3n de datos (entrevistas/archivo/observaci\u00f3n/m\u00faltiples fuentes)
  - Estrategia de an\u00e1lisis (coincidencia de patrones/construcci\u00f3n explicativa/secuencia temporal)
  - Garant\u00eda de fiabilidad (triangulaci\u00f3n/verificaci\u00f3n por miembros/auditor\u00eda)
- **Normas de reporte**:
  - Descripci\u00f3n rica del contexto (contextualizaci\u00f3n)
  - Cadena de evidencia clara (datos\u2192tablas\u2192conclusiones)
  - Di\u00e1logo con la literatura (confirmar/extender/desafiar)

### 2. Investigaci\u00f3n por Encuesta
- **Aplicable**: verificaci\u00f3n de hip\u00f3tesis con gran muestra, relaciones entre variables
- **Tipos**: transversal/longitudinal/panel
- **Puntos clave de dise\u00f1o**:
  - Marco muestral (accesibilidad de la poblaci\u00f3n objetivo)
  - Dise\u00f1o de cuestionario (escalas maduras + \u00edtems propios)
  - Recolecci\u00f3n de datos (en l\u00ednea/papel/mixto)
  - Sesgo de m\u00e9todo com\u00fan (factor \u00fanico de Harman/control procedural)
- **M\u00e9todos de an\u00e1lisis**:
  - Modelo de ecuaciones estructurales (SEM): AMOS/PLS/Mplus
  - Modelo lineal multinivel (HLM): datos anidados
  - Modelo de crecimiento latente (LGM): seguimiento longitudinal

### 3. Investigaci\u00f3n Experimental
- **Aplicable**: relaciones causales, mecanismos conductuales
- **Tipos**: laboratorio/campo/cuasi-experimento/experimento natural
- **Puntos clave de dise\u00f1o**:
  - Asignaci\u00f3n aleatoria (aleatorizaci\u00f3n simple/pareada)
  - Verificaci\u00f3n de manipulaci\u00f3n (si la variable independiente fue manipulada efectivamente)
  - Medici\u00f3n de la variable dependiente (objetiva/subjetiva/conductual)
  - Variables de control (exclusi\u00f3n de factores confusores)
- **M\u00e9todos de an\u00e1lisis**:
  - ANOVA/ANCOVA: comparaci\u00f3n entre grupos
  - Mediaci\u00f3n/moderaci\u00f3n: macro PROCESS
  - Multinivel: HLM

### 4. An\u00e1lisis de Datos Secundarios
- **Aplicable**: investigaci\u00f3n macro, datos de panel, estudios de eventos
- **Fuentes de datos**:
  - Empresas cotizadas: CSMAR, Wind, Guotai\u2019an
  - Datos de patentes: Oficina Nacional de Propiedad Intelectual, Derwent
  - Datos de reclutamiento: Zhilian, 51job
  - Redes sociales: Weibo, Zhihu, Maimai (web scraping)
- **M\u00e9todos de an\u00e1lisis**:
  - Modelos de datos de panel: efectos fijos/aleatorios/GMM
  - DID/PSM: inferencia causal
  - Estudio de eventos: c\u00e1lculo de CAR
  - An\u00e1lisis de texto: frecuencia de palabras, modelos de temas, an\u00e1lisis de sentimiento

## Marcos Te\u00f3ricos

### Teor\u00edas Com\u00fanmente Utilizadas
- **Visi\u00f3n Basada en Recursos (RBV)**: recursos VRIN\u2192ventaja competitiva
- **Teor\u00eda Institucional**: presiones institucionales regulatorias/normativas/cognitivas
- **Teor\u00eda de Agencia**: conflicto principal-agente\u2192mecanismos de gobernanza
- **Teor\u00eda de Stakeholders**: equilibrio de m\u00faltiples actores
- **Capacidades Din\u00e1micas**: percibir/capturar/reconfigurar
- **Aprendizaje Organizacional**: explorar/explotar, transformaci\u00f3n del conocimiento (SECI)
- **Teor\u00eda Upper Echelons**: caracter\u00edsticas de directivos\u2192selecci\u00f3n estrat\u00e9gica\u2192resultados organizacionales
- **Redes Sociales**: agujeros estructurales/centralidad/inserci\u00f3n
- **Teor\u00eda de Se\u00f1ales**: emisi\u00f3n de se\u00f1ales\u2192interpretaci\u00f3n de se\u00f1ales\u2192resultados
- **Teor\u00eda de Legitimidad**: legitimidad pragm\u00e1tica/moral/cognitiva

### Recomendaciones sobre Uso de Teor\u00edas
1. **No acumular teor\u00edas**: 1-2 teor\u00edas centrales son suficientes
2. **Clarificar la perspectiva te\u00f3rica**: qu\u00e9 explica, qu\u00e9 predice
3. **Vincular teor\u00eda e hip\u00f3tesis**: cada hip\u00f3tesis con respaldo te\u00f3rico
4. **Di\u00e1logo te\u00f3rico**: resultados consistentes/contradictorios/extendidos con las expectativas te\u00f3ricas

## Fuentes de Datos y Medici\u00f3n

### Dise\u00f1o de Cuestionario
- **Fuente de escalas**: preferir escalas maduras (validez y fiabilidad ya verificadas)
- **Traducci\u00f3n-retrotraducci\u00f3n**: escala en ingl\u00e9s\u2192espa\u00f1ol\u2192retrotraducci\u00f3n\u2192comparaci\u00f3n
- **N\u00famero de \u00edtems**: 3-7 por constructo (evitar fatiga)
- **\u00cdtems inversos**: incluir 2-3 (prevenir respuestas por defecto)
- **Pretest**: 30-50 personas, eliminar CITC<0.4

### Bases de Datos Comunes
- **CSMAR**: finanzas, gobernanza, accionariado de empresas cotizadas
- **Wind**: finanzas, macroeconom\u00eda, sectores
- **Guotai\u2019an**: econom\u00eda y finanzas, econom\u00eda regional
- **CEIC**: macroeconom\u00eda, datos sectoriales
- **Banco Mundial**: comparaci\u00f3n??, indicadores de desarrollo
- **Encuesta de Seguimiento de Hogares de China (CFPS)**: microdatos individuales
- **Encuesta de Seguimiento de Salud y Jubilaci\u00f3n de China (CHARLS)**: envejecimiento

### Medici\u00f3n de Variables
- **Variable independiente**: definici\u00f3n operacionalizada clara
- **Variable dependiente**: medici\u00f3n multidimensional (objetiva + subjetiva)
- **Variable mediadora**: explicaci\u00f3n del mecanismo
- **Variable moderadora**: condiciones de frontera
- **Variables de control**: excluir explicaciones alternativas

## M\u00e9todos de An\u00e1lisis

### Modelo de Ecuaciones Estructurales (SEM)
- **CB-SEM (AMOS/Mplus)**:
  - Gran muestra (>200)
  - An\u00e1lisis confirmatorio
  - Ajuste estricto del modelo (CFI>0.9, RMSEA<0.08, SRMR<0.08)
- **PLS-SEM (SmartPLS)**:
  - Aceptable con peque\u00f1as muestras
  - An\u00e1lisis exploratorio
  - Orientado a predicci\u00f3n (PLSpredict)

### Modelo Lineal Multinivel (HLM)
- **Aplicable**: datos anidados (empleado\u2192equipo\u2192organizaci\u00f3n)
- **Software**: HLM, Mplus, R (lme4)
- **Reporte**: ICC(1), ICC(2), rwg, efectos entre niveles

### An\u00e1lisis Comparativo Cualitativo (QCA)
- **Aplicable**: complejidad causal, combinaci\u00f3n de m\u00faltiples factores
- **Tipos**: crisp-set / fuzzy-set / mvQCA
- **Software**: fsQCA, R (paquete QCA)
- **Reporte**: tabla de verdad, consistencia, cobertura, soluci\u00f3n intermedia

### Tratamiento de Endogeneidad
- **Fuentes**: variables omitidas, causalidad inversa, error de medici\u00f3n, selecci\u00f3n de muestra
- **M\u00e9todos**:
  - Variables instrumentales (VI): MC2E
  - Diferencia en diferencias (DID): impacto de pol\u00edticas
  - Propensity Score Matching (PSM): emparejamiento de muestras
  - Regresi\u00f3n discontinua (RDD): cerca del umbral
  - Modelo de Heckman: selecci\u00f3n de muestra

## Plantilla de Estructura de Tesis

### Investigaci\u00f3n Emp\u00edrica (Cuantitativa)
```
1. Introducci\u00f3n
   - Contexto pr\u00e1ctico (fen\u00f3meno gerencial)
   - Brecha te\u00f3rica (di\u00e1logo con la literatura)
   - Pregunta de investigaci\u00f3n
   - Contribuci\u00f3n te\u00f3rica
   - Significado pr\u00e1ctico

2. Revisi\u00f3n de Literatura e Hip\u00f3tesis
   - Definici\u00f3n de constructos centrales
   - Literatura sobre efecto principal (A\u2192B)
   - Mecanismo de mediaci\u00f3n (A\u2192M\u2192B)
   - L\u00edmites de moderaci\u00f3n (W influye en A\u2192B)
   - Tabla resumen de hip\u00f3tesis

3. Dise\u00f1o de Investigaci\u00f3n
   - Muestra y procedimientos
   - Medici\u00f3n de variables (fuente de escala + fiabilidad)
   - Estrategia de an\u00e1lisis
   - Control del sesgo de m\u00e9todo com\u00fan

4. Resultados
   - Estad\u00edstica descriptiva + matriz de correlaciones
   - Modelo de medici\u00f3n (CFA/validez y fiabilidad)
   - Modelo estructural (coeficientes de ruta + significancia)
   - Efecto de mediaci\u00f3n (Bootstrap)
   - Efecto de moderaci\u00f3n (t\u00e9rmino de interacci\u00f3n/pendiente simple)
   - Prueba de robustez (medici\u00f3n alternativa/submuestra)

5. Discusi\u00f3n
   - Resumen de verificaci\u00f3n de hip\u00f3tesis
   - Contribuci\u00f3n te\u00f3rica (di\u00e1logo)
   - Implicaciones gerenciales (accionables)
   - Limitaciones (muestra/m\u00e9todo/causalidad)
   - Investigaci\u00f3n futura (direcciones concretas)
```

### Estudio de Caso (Cualitativo)
```
1. Introducci\u00f3n: fen\u00f3meno\u2192problema\u2192m\u00e9todo\u2192contribuci\u00f3n
2. Revisi\u00f3n de Literatura: perspectiva te\u00f3rica\u2192brecha\u2192marco
3. M\u00e9todo:
   - Selecci\u00f3n de caso (l\u00f3gica de muestreo te\u00f3rico)
   - Recolecci\u00f3n de datos (matriz de evidencia multisource)
   - An\u00e1lisis de datos (estrategia de codificaci\u00f3n)
   - Garant\u00eda de fiabilidad (triangulaci\u00f3n, etc.)
4. Descripci\u00f3n del caso: contexto\u2192proceso\u2192eventos clave
5. An\u00e1lisis transversal de casos: patrones\u2192proposiciones\u2192teor\u00eda
6. Discusi\u00f3n: contribuci\u00f3n\u2192implicaciones\u2192limitaciones\u2192futuro
```

## Errores Comunes
1. Marco te\u00f3rico d\u00e9bil (hip\u00f3tesis sin respaldo te\u00f3rico)
2. Descuido de la endogeneidad (inferencia causal no confiable)
3. Sesgo de m\u00e9todo com\u00fan (datos de fuente \u00fanica sin tratamiento)
4. Adaptaci\u00f3n arbitraria de escalas (destruir validez y fiabilidad)
5. Interpretaci\u00f3n err\u00f3nea del efecto de mediaci\u00f3n (mediaci\u00f3n completa \u2260 mediaci\u00f3n)
6. Error en gr\u00e1ficos de efecto de moderaci\u00f3n (direcci\u00f3n de pendiente simple)
7. Sesgo de selecci\u00f3n de muestra (generalizaci\u00f3n de muestreo por conveniencia)
8. Exceso de variables de control (controlar mediadores/moderadores)
9. Reporte selectivo de resultados (solo reportar resultados significativos)
10. Implicaciones gerenciales vac\u00edas (falta de accionabilidad)
"""

with open(os.path.join(base, 'management.md'), 'w', encoding='utf-8') as f:
    f.write(content2.lstrip())
print('management.md written')
