# -*- coding: utf-8 -*-
import os

base = r'd:\Skill Library\Thesis Tutor v4.0\knowledge_base\es\disciplines'

# File 4: psychology.md
content4 = """# Gu\u00eda de Escritura de Tesis de Psicolog\u00eda

## Caracter\u00edsticas de la Disciplina
- \u00c9nfasis en dise\u00f1o experimental, rigor estad\u00edstico y verificaci\u00f3n te\u00f3rica
- Importancia de la revisi\u00f3n \u00e9tica, consentimiento informado y bienestar animal
- Art\u00edculos en revistas principales (top journals: Psychological Science/JPSP/JEP/Developmental Psychology)
- Pre-registro (Preregistration) cada vez m\u00e1s importante
- Tendencia de ciencia abierta (Open Science): compartici\u00f3n de datos/c\u00f3digo/materiales

## Tipos de Investigaci\u00f3n

### 1. Psicolog\u00eda Experimental
- **Aplicable**: relaciones causales, mecanismos cognitivos, experimentos conductuales
- **Tipos de dise\u00f1o**:
  - Dise\u00f1o entre sujetos (Between-subjects): diferentes sujetos reciben diferentes tratamientos
  - Dise\u00f1o intra-sujetos (Within-subjects): el mismo sujeto recibe todos los tratamientos
  - Dise\u00f1o mixto (Mixed): combina variables entre e intra-sujetos
- **Elementos clave**:
  - Manipulaci\u00f3n de la variable independiente (clara, efectiva, reproducible)
  - Medici\u00f3n de la variable dependiente (tiempo de reacci\u00f3n, tasa de aciertos, seguimiento ocular, ERP, fMRI)
  - Control de factores confusores (aleatorizaci\u00f3n, balanceo, enmascaramiento)
  - An\u00e1lisis de potencia (G*Power: f=0.25 efecto mediano, \u03b1=0.05, 1-\u03b2=0.80)
- **Normas de reporte**:
  - Pre-registro de hip\u00f3tesis (OSF, AsPredicted)
  - Descripci\u00f3n completa del procedimiento experimental (reproducible)
  - Criterios de exclusi\u00f3n transparentes (ej. tiempo de reacci\u00f3n <200ms)
  - Complemento con an\u00e1lisis bayesiano (BF10)

### 2. Psicolog\u00eda del Desarrollo
- **Aplicable**: desarrollo a lo largo de la vida, diferencias por edad, seguimiento longitudinal
- **Tipos de dise\u00f1o**:
  - Dise\u00f1o transversal: diferentes grupos de edad evaluados simult\u00e1neamente
  - Dise\u00f1o longitudinal: el mismo grupo evaluado m\u00faltiples veces
  - Dise\u00f1o secuencial: combinaci\u00f3n de transversal y longitudinal
- **Elementos clave**:
  - Agrupamiento por edad (basado en teor\u00eda: ej. etapas de Piaget)
  - Equivalencia de medici\u00f3n (comparabilidad de instrumentos entre edades)
  - Manejo de deserci\u00f3n (prueba MAR/MCAR, imputaci\u00f3n m\u00faltiple)
  - Efecto de cohorte (diferencias por contexto \u00e9poca)
- **Consideraciones especiales**:
  - \u00c9tica con ni\u00f1os: consentimiento de padres + asentimiento del ni\u00f1o (mayores de 7 a\u00f1os)
  - Adecuaci\u00f3n al desarrollo: dificultad de la tarea, mantenimiento de atenci\u00f3n
  - Deseabilidad social: los ni\u00f1os tienden m\u00e1s a complacer

### 3. Psicolog\u00eda Social
- **Aplicable**: cognici\u00f3n social, actitudes, procesos grupales, relaciones interpersonales
- **M\u00e9todos comunes**:
  - Cuestionarios: medici\u00f3n con escalas (Likert de 5/7 puntos)
  - Experimentos: manipulaci\u00f3n situacional (ej. variantes del experimento de conformidad de Asch)
  - Experimentos de campo: intervenci\u00f3n en situaciones naturales
  - An\u00e1lisis de archivo: datos hist\u00f3ricos, contenido medi\u00e1tico
- **Elementos clave**:
  - Control del sesgo de deseabilidad social (anonimato, medici\u00f3n indirecta, IAT)
  - Representatividad de la muestra (problema WEIRD: Western, Educated, Industrialized, Rich, Democratic)
  - Atenci\u00f3n al tama\u00f1o del efecto (peque\u00f1o d=0.2, mediano d=0.5, grande d=0.8)
  - Replicaci\u00f3n de experimentos (directa/conceptual/sistem\u00e1tica)

### 4. Psicolog\u00eda Cl\u00ednica
- **Aplicable**: trastornos psicol\u00f3gicos, efectividad de intervenciones, instrumentos de evaluaci\u00f3n
- **Tipos de dise\u00f1o**:
  - ECA: est\u00e1ndar de oro, asignaci\u00f3n aleatoria a grupo de tratamiento/control
  - Experimento de sujeto \u00fanico: dise\u00f1o ABA/l\u00edneas base m\u00faltiples
  - Cuasi-experimento: agrupamiento natural, pre-test/post-test
- **Elementos clave**:
  - Criterios diagn\u00f3sticos (DSM-5/CIE-11)
  - Protocolo de intervenci\u00f3n (manualizado, verificaci\u00f3n de fidelidad)
  - Variables de resultado (s\u00edntomas, funcionamiento, calidad de vida)
  - Manejo de deserci\u00f3n (an\u00e1lisis ITT/PP)
- **Consideraciones \u00e9ticas especiales**:
  - Protecci\u00f3n de poblaciones vulnerables (pacientes, ni\u00f1os, ancianos)
  - Principio de riesgo m\u00ednimo
  - Confidencialidad de datos (Ley de Ciberseguridad)

## Dise\u00f1o Experimental

### Entre-sujetos vs Intra-sujetos
| Dimensi\u00f3n | Entre-sujetos | Intra-sujetos |
|------|--------|--------|
| Ventajas | Sin efectos de orden/pr\u00e1ctica | Control de diferencias individuales, mayor potencia estad\u00edstica |
| Desventajas | Necesita m\u00e1s sujetos, confusi\u00f3n por diferencias individuales | Efectos de orden/pr\u00e1ctica/fatiga |
| Aplicable | Cuando los tratamientos tienen efectos permanentes | Cuando los tratamientos son reversibles, se necesita alta potencia |
| Tama\u00f1o de muestra | \u226530 por grupo (efecto grande) | \u226520 total (efecto grande) |

### Dise\u00f1os Cuasi-Experimentales
- **Pre-test/post-test con grupos no equivalentes**: sin aleatorizaci\u00f3n, requiere control estad\u00edstico
- **Series temporales interrumpidas**: m\u00faltiples observaciones, comparaci\u00f3n antes/despu\u00e9s de la intervenci\u00f3n
- **Regresi\u00f3n discontinua**: agrupamiento basado en umbral de variable continua
- **Grupo control no equivalente**: emparejamiento en lugar de aleatorizaci\u00f3n

### Potencia Estad\u00edstica
- **Herramientas de c\u00e1lculo**: G*Power, paquete pwr, WebPower
- **Par\u00e1metros**:
  - Tama\u00f1o del efecto (d=0.2 peque\u00f1o/0.5 mediano/0.8 grande; f=0.1 peque\u00f1o/0.25 mediano/0.4 grande)
  - Nivel \u03b1 (0.05 o 0.01)
  - Potencia estad\u00edstica (1-\u03b2=0.80 o 0.90)
  - Tipo de prueba (bilateral/unilateral)
- **Recomendaciones**:
  - Efecto peque\u00f1o: \u226564 por grupo (potencia 0.80)
  - Efecto mediano: \u226526 por grupo
  - Efecto grande: \u226516 por grupo

## M\u00e9todos Estad\u00edsticos

### An\u00e1lisis B\u00e1sico
- **Prueba t**: comparaci\u00f3n de dos grupos (independientes/pareados)
- **ANOVA**: comparaci\u00f3n de m\u00faltiples grupos
  - Unidireccional: una variable independiente
  - Factorial: m\u00faltiples variables independientes + efectos de interacci\u00f3n
  - Medidas repetidas: variable intra-sujetos
  - MANOVA: m\u00faltiples variables dependientes
- **Chi-cuadrado**: asociaci\u00f3n entre variables categ\u00f3ricas
- **Correlaci\u00f3n**: Pearson/Spearman

### An\u00e1lisis Avanzado
- **An\u00e1lisis de regresi\u00f3n**:
  - Regresi\u00f3n lineal: predictor continuo\u2192resultado continuo
  - Regresi\u00f3n log\u00edstica: resultado categ\u00f3rico
  - Regresi\u00f3n de Poisson: resultado de conteo
  - Regresi\u00f3n multinivel: datos anidados (sujeto\u2192aula\u2192escuela)
- **Modelo de Ecuaciones Estructurales (SEM)**:
  - An\u00e1lisis Factorial Confirmatorio (AFC): modelo de medici\u00f3n
  - An\u00e1lisis de ruta: modelo estructural
  - Comparaci\u00f3n multigrupo: equivalencia de medici\u00f3n (configural/m\u00e9trica/escalar)
- **Modelo Lineal Multinivel (HLM/MLM)**:
  - Modelo de intercepto/pendiente aleatoria
  - Interacciones entre niveles
  - Anidamiento de 3 o m\u00e1s niveles
- **Modelo de Crecimiento Latente (LGM)**:
  - Crecimiento lineal/no lineal
  - Predictores del crecimiento
  - Modelo de procesos paralelos
- **An\u00e1lisis de supervivencia**: tiempo hasta el evento

### Reporte de Tama\u00f1o del Efecto
- **Cohen's d**: diferencia de medias entre dos grupos (peque\u00f1o 0.2/mediano 0.5/grande 0.8)
- **\u03b7\u00b2 (eta-cuadrado)**: proporci\u00f3n de varianza explicada (peque\u00f1o 0.01/mediano 0.06/grande 0.14)
- **\u03c9\u00b2 (omega-cuadrado)**: estimaci\u00f3n insesgada
- **r\u00b2**: coeficiente de determinaci\u00f3n
- **Odds ratio (OR)**: regresi\u00f3n log\u00edstica
- **Intervalo de confianza**: IC 95% m\u00e1s importante que valor P

## Uso de Escalas

### Fuentes Comunes de Escalas
- **APA PsycTests**: base de datos oficial de pruebas psicol\u00f3gicas
- **Mental Measurements Yearbook**: evaluaci\u00f3n de pruebas
- **Ap\u00e9ndices de revistas**: art\u00edculos originales suelen incluir escala completa
- **Manuales**: ej. manual de personalidad Big Five (BFI)

### Procedimiento de Traducci\u00f3n-Retrotraducci\u00f3n
1. Ingl\u00e9s\u2192espa\u00f1ol (traducci\u00f3n por biling\u00fce)
2. Espa\u00f1ol\u2192ingl\u00e9s (retrotraducci\u00f3n por biling\u00fce independiente)
3. Comparar versi\u00f3n original con retrotraducci\u00f3n
4. Comit\u00e9 de expertos discute diferencias
5. Pretest (30-50 personas)
6. Prueba de validez y fiabilidad

### Requisitos de Validez y Fiabilidad
- **Fiabilidad**:
  - Alfa de Cronbach \u2265 0.70 (aceptable)
  - Fiabilidad de split-half \u2265 0.70
  - Fiabilidad test-retest (intervalo 2-4 semanas) r \u2265 0.70
- **Validez**:
  - Validez de contenido: evaluaci\u00f3n por expertos
  - Validez de constructo: AFC, cargas factoriales \u2265 0.50
  - Validez de criterio: correlaci\u00f3n con est\u00e1ndar externo
  - Validez discriminante: AVE > correlaci\u00f3n\u00b2

## Requisitos \u00c9ticos

### Principios \u00c9ticos APA (5 principios)
1. **Beneficencia y no maleficencia**: maximizar beneficios, minimizar da\u00f1os
2. **Fidelidad y responsabilidad**: est\u00e1ndares profesionales, responsabilidad social
3. **Integridad**: honestidad, precisi\u00f3n, sin fraude
4. **Justicia**: trato equitativo, evitar sesgos
5. **Respeto**: autonom\u00eda, privacidad, dignidad

### Consentimiento Informado
- **Elementos**: prop\u00f3sito del estudio, procedimientos, riesgos, beneficios, confidencialidad, voluntariedad, datos de contacto
- **Poblaciones especiales**:
  - Ni\u00f1os: consentimiento de padres + asentimiento del ni\u00f1o (mayores de 7 a\u00f1os)
  - Deterioro cognitivo: representante legal
  - Reclusos: protecci\u00f3n adicional
- **Estudios con enga\u00f1o**: explicaci\u00f3n posterior (debriefing)

### \u00c9tica en Experimentos con Animales
- **Principios 3R**: Reemplazo (Replacement), Reducci\u00f3n (Reduction), Refinamiento (Refinement)
- **Revisi\u00f3n IACUC**: aprobaci\u00f3n de protocolo, supervisi\u00f3n veterinaria
- **Condiciones de cr\u00eda**: enriquecimiento ambiental, necesidades sociales
- **Definici\u00f3n de punto final**: punto final humanitario, criterios de eutanasia

## Plantilla de Estructura de Tesis

### Investigaci\u00f3n Experimental
```
1. Introducci\u00f3n
   - Antecedentes te\u00f3ricos (conceptos centrales)
   - Estado actual de la investigaci\u00f3n (brecha en la literatura)
   - Pregunta e hip\u00f3tesis de investigaci\u00f3n (H1a, H1b...)
   - Contribuci\u00f3n te\u00f3rica y significado pr\u00e1ctico

2. M\u00e9todo
   - Sujetos (reclutamiento, selecci\u00f3n, tama\u00f1o de muestra, compensaci\u00f3n)
   - Dise\u00f1o (2\u00d73 mixto, variables independientes/dependientes)
   - Materiales/est\u00edmulos (fuente, elaboraci\u00f3n, pretest)
   - Procedimiento (pasos, aleatorizaci\u00f3n, enmascaramiento)
   - Plan de an\u00e1lisis de datos (enlace de pre-registro)

3. Resultados
   - Estad\u00edstica descriptiva (M, DT, n)
   - Verificaci\u00f3n de manipulaci\u00f3n (variable independiente efectiva)
   - Prueba de hip\u00f3tesis (tabla ANOVA, tama\u00f1o del efecto, IC)
   - An\u00e1lisis adicionales (exploratorio, bayesiano)
   - Gr\u00e1ficos (medias, interacciones)

4. Discusi\u00f3n
   - Resumen de verificaci\u00f3n de hip\u00f3tesis
   - Explicaci\u00f3n te\u00f3rica (mecanismo)
   - Comparaci\u00f3n con investigaciones previas
   - Limitaciones (muestra, m\u00e9todo, generalizaci\u00f3n)
   - Direcciones futuras (hip\u00f3tesis concretas)
   - Conclusi\u00f3n (concisa)

5. Material complementario (en l\u00ednea)
   - Cuestionario/est\u00edmulos completos
   - Datos originales (OSF)
   - C\u00f3digo de an\u00e1lisis (R/Python)
```

## Pr\u00e1cticas de Ciencia Abierta

### Pre-registro
- **Plataformas**: OSF, AsPredicted, ClinicalTrials.gov
- **Contenido**: hip\u00f3tesis, dise\u00f1o, tama\u00f1o de muestra, plan de an\u00e1lisis
- **Tipos**:
  - Pre-registro est\u00e1ndar: antes de la recolecci\u00f3n de datos
  - Registered Reports: la revista se compromete a publicar (independientemente de resultados)
- **Beneficios**: prevenci\u00f3n de HARKing (hip\u00f3tesis post hoc), mayor credibilidad

### Compartici\u00f3n de Datos
- **Plataformas**: OSF, Figshare, Zenodo, GitHub
- **Contenido**:
  - Datos originales (desidentificados)
  - C\u00f3digo de an\u00e1lisis (reproducible)
  - Materiales de investigaci\u00f3n (cuestionarios, est\u00edmulos)
- **Licencias**: CC0 (recomendada), CC-BY

### Compartici\u00f3n de C\u00f3digo
- **Requisitos**: ejecutable, comentado, con README
- **Herramientas**: R Markdown, Jupyter Notebook
- **Control de versiones**: Git/GitHub

## Errores Comunes
1. Tama\u00f1o de muestra insuficiente (potencia <0.80)
2. Comparaciones m\u00faltiples sin correcci\u00f3n (Bonferroni/FDR)
3. Dise\u00f1o intra-sujetos sin control de orden (latino/cuadrado/aleatorio)
4. No reportar tama\u00f1o del efecto (solo valor P)
5. Hip\u00f3tesis post hoc (HARKing)
6. Sesgo de m\u00e9todo com\u00fan (datos de fuente \u00fanica)
7. Fiabilidad baja de la escala (\u03b1<0.70 a\u00fan en uso)
8. Inferencia causal excesiva (dise\u00f1o correlacional)
9. Descuido de diferencias culturales (muestra WEIRD)
10. Falta de descripci\u00f3n \u00e9tica (no pasar revisi\u00f3n de pares)
"""

with open(os.path.join(base, 'psychology.md'), 'w', encoding='utf-8') as f:
    f.write(content4.lstrip())
print('psychology.md written')
