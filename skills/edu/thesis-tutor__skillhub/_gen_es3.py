# -*- coding: utf-8 -*-
import os

base = r'd:\Skill Library\Thesis Tutor v4.0\knowledge_base\es\disciplines'

# File 3: medical.md
content3 = """# Gu\u00eda de Escritura de Tesis de Medicina / Ciencias de la Vida

## Caracter\u00edsticas de la Disciplina
- \u00c9nfasis en medicina basada en evidencia, verificaci\u00f3n experimental y datos cl\u00ednicos
- Importancia de la revisi\u00f3n \u00e9tica, consentimiento informado y protecci\u00f3n de privacidad
- Art\u00edculos en revistas > conferencias (top journals: NEJM/Lancet/JAMA/Nature Medicine/Cell)
- Normas de escritura estrictas: CONSORT, PRISMA, STROBE, etc.

## Tipos de Investigaci\u00f3n

### 1. Ensayo Cl\u00ednico Aleatorizado (ECA)
- **Aplicable**: evaluaci\u00f3n de eficacia de medicamentos/intervenciones
- **Puntos clave de dise\u00f1o**:
  - M\u00e9todo de aleatorizaci\u00f3n (simple/estratificado/bloques)
  - Cegamiento (simple/doble/triple)
  - Tipo de control (placebo/activo/ninguno)
  - C\u00e1lculo de tama\u00f1o de muestra (an\u00e1lisis de potencia)
- **Normas de reporte**: Declaraci\u00f3n CONSORT 2010 + diagrama de flujo
- **Requisitos de registro**: ClinicalTrials.gov o Registro de Ensayos Cl\u00ednicos de China

### 2. Estudio de Cohorte
- **Aplicable**: exploraci\u00f3n de etiolog\u00eda, factores pron\u00f3sticos
- **Tipos**: prospectivo/retrospectivo/bidireccional
- **Puntos clave de dise\u00f1o**:
  - Definici\u00f3n clara de exposici\u00f3n
  - Protocolo de seguimiento completo
  - Control de tasa de p\u00e9rdida de seguimiento (<20%)
  - Control de factores de confusi\u00f3n
- **Normas de reporte**: Declaraci\u00f3n STROBE

### 3. Estudio de Casos y Controles
- **Aplicable**: enfermedades raras, enfermedades con per\u00edodo de latencia prolongado
- **Puntos clave de dise\u00f1o**:
  - Definici\u00f3n clara de caso (est\u00e1ndar de oro)
  - Selecci\u00f3n razonable de controles (hospital/comunidad/poblaci\u00f3n)
  - Selecci\u00f3n de factores de emparejamiento
  - Control de sesgo de memoria
- **Normas de reporte**: Declaraci\u00f3n STROBE

### 4. Estudio Transversal
- **Aplicable**: encuesta de prevalencia, descripci\u00f3n de situaci\u00f3n
- **Puntos clave de dise\u00f1o**:
  - M\u00e9todo de muestreo (multietapa estratificado)
  - Tama\u00f1o de muestra (estimaci\u00f3n de prevalencia)
  - Validez y fiabilidad de instrumentos de encuesta
- **Normas de reporte**: Declaraci\u00f3n STROBE (extensi\u00f3n transversal)

### 5. Metaan\u00e1lisis
- **Aplicable**: s\u00edntesis de evidencia, comparaci\u00f3n de eficacia
- **Tipos**:
  - Metaan\u00e1lisis de intervenciones (ECA)
  - Metaan\u00e1lisis diagn\u00f3stico
  - Metaan\u00e1lisis en red (NMA)
  - Metaan\u00e1lisis de datos individuales (IPD)
- **Normas de reporte**: Declaraci\u00f3n PRISMA 2020 + registro (PROSPERO)
- **Puntos clave de an\u00e1lisis**:
  - Prueba de heterogeneidad (estad\u00edstico I\u00b2)
  - Sesgo de publicaci\u00f3n (funnel plot, prueba de Egger)
  - An\u00e1lisis de sensibilidad
  - Calidad de evidencia (clasificaci\u00f3n GRADE)

### 6. Revisi\u00f3n Sistem\u00e1tica
- **Aplicable**: revisi\u00f3n integral de evidencia en un campo
- **Pasos**:
  1. Formular pregunta PICO
  2. Desarrollar estrategia de b\u00fasqueda (al menos 3 bases de datos)
  3. Seleccionar literatura (dos revisores independientes)
  4. Extraer datos (formulario estandarizado)
  5. Evaluar calidad (riesgo de sesgo Cochrane/RoB 2)
  6. Sintetizar evidencia (cualitativa/cuantitativa)
- **Normas de reporte**: PRISMA 2020

## Requisitos \u00c9ticos

### Revisi\u00f3n \u00c9tica
- **Aprobaci\u00f3n del CEI/CIE**: obligatoria para toda investigaci\u00f3n con seres humanos
- **Contenido de revisi\u00f3n**: protocolo de investigaci\u00f3n, formulario de consentimiento informado, cualificaciones del investigador
- **Seguimiento**: anual/eventos adversos graves/modificaciones de protocolo

### Consentimiento Informado
- **Elementos**: prop\u00f3sito del estudio, procedimientos, riesgos, beneficios, alternativas, confidencialidad, voluntariedad, datos de contacto
- **Situaciones especiales**: excepciones en emergencias, representante legal para personas incapaces
- **Documentaci\u00f3n**: versi\u00f3n firmada + fecha + copia para el participante

### Protecci\u00f3n de Privacidad
- **Desidentificaci\u00f3n**: nombre\u2192c\u00f3digo, n\u00famero de identificaci\u00f3n\u2192parcialmente oculto
- **Seguridad de almacenamiento**: cifrado, control de acceso, registro de auditor\u00eda
- **Seguridad en transmisi\u00f3n**: transmisi\u00f3n cifrada, principio de m\u00ednima necesidad
- **Per\u00edodo de retenci\u00f3n**: al menos 5 a\u00f1os despu\u00e9s de finalizar el estudio

## M\u00e9todos Estad\u00edsticos

### Estad\u00edstica B\u00e1sica
- **Descriptiva**: media \u00b1 desviaci\u00f3n est\u00e1ndar, mediana (RIQ), frecuencia (%)
- **Prueba de normalidad**: Shapiro-Wilk, Kolmogorov-Smirnov
- **Comparaci\u00f3n entre grupos**: prueba t, ANOVA, chi-cuadrado, prueba de rangos

### Estad\u00edstica Avanzada
- **An\u00e1lisis de supervivencia**: curvas de Kaplan-Meier, prueba de Log-rank, regresi\u00f3n de Cox
- **An\u00e1lisis ROC**: \u00e1rea bajo la curva, punto de corte \u00f3ptimo, sensibilidad/especificidad
- **Regresi\u00f3n log\u00edstica**: univariante\u2192multivariante, OR, IC 95%
- **An\u00e1lisis multifactorial**: lineal/Logistic/Cox, estrategia de selecci\u00f3n de variables
- **Mediciones repetidas**: modelos de efectos mixtos, GEE
- **Mediaci\u00f3n/moderaci\u00f3n**: m\u00e9todo Bootstrap, prueba de Sobel

### C\u00e1lculo de Tama\u00f1o de Muestra
- **Software**: G*Power, PASS, nQuery
- **Par\u00e1metros**: tama\u00f1o del efecto, \u03b1 (0.05), \u03b2 (0.1 o 0.2), tasa de deserci\u00f3n
- **M\u00e9todos**:
  - Comparaci\u00f3n de dos grupos: f\u00f3rmula de prueba t/chi-cuadrado
  - An\u00e1lisis de supervivencia: c\u00e1lculo de n\u00famero de eventos
  - Prueba diagn\u00f3stica: requisitos de sensibilidad/especificidad
  - Dise\u00f1o de equivalencia/no inferioridad: determinaci\u00f3n del margen

## Plantilla de Estructura de Tesis

### Investigaci\u00f3n Original (Formato IMRAD)
```
1. P\u00e1gina de t\u00edtulo: t\u00edtulo, autores, afiliaci\u00f3n, autor de correspondencia
2. Resumen: estructurado (objetivo, m\u00e9todo, resultado, conclusi\u00f3n)
3. Introducci\u00f3n: antecedentes\u2192problema\u2192objetivo\u2192hip\u00f3tesis
4. M\u00e9todos:
   - Dise\u00f1o/lugar/per\u00edodo
   - Participantes (criterios de inclusi\u00f3n/exclusi\u00f3n)
   - Intervenci\u00f3n/definici\u00f3n de exposici\u00f3n
   - Variables de resultado (primarias/secundarias)
   - M\u00e9todos estad\u00edsticos (software/versi\u00f3n/nivel de significancia)
5. Resultados:
   - Diagrama de flujo (CONSORT)
   - Tabla de caracter\u00edsticas basales
   - Resultados principales (tama\u00f1o del efecto + IC + valor P)
   - Resultados secundarios
   - An\u00e1lisis de subgrupos
   - An\u00e1lisis de sensibilidad
6. Discusi\u00f3n:
   - Resumen de hallazgos principales
   - Comparaci\u00f3n con investigaciones previas
   - Explicaci\u00f3n del mecanismo
   - Significado cl\u00ednico
   - Limitaciones (franqueza)
   - Direcciones futuras
7. Conclusi\u00f3n: concisa, sin exagerar
8. Agradecimientos/declaraciones: financiaci\u00f3n, conflictos de inter\u00e9s, contribuciones de autores
9. Referencias: seg\u00fan requisitos de la revista (Vancouver/APA)
```

### Revisi\u00f3n Sistem\u00e1tica/Metaan\u00e1lisis
```
1. T\u00edtulo: identificar claramente "revisi\u00f3n sistem\u00e1tica" o "metaan\u00e1lisis"
2. Resumen: resumen estructurado PRISMA
3. Introducci\u00f3n: antecedentes\u2192problema\u2192objetivo (PICO)
4. M\u00e9todos:
   - Registro de protocolo (n\u00famero PROSPERO)
   - Criterios de inclusi\u00f3n (PICOS)
   - Estrategia de b\u00fasqueda (estrategia completa en ap\u00e9ndice)
   - Proceso de selecci\u00f3n (dos revisores independientes)
   - Extracci\u00f3n de datos (formulario estandarizado)
   - Evaluaci\u00f3n de calidad (herramienta + versi\u00f3n)
   - M\u00e9todos estad\u00edsticos (indicador de efecto, heterogeneidad, sesgo de publicaci\u00f3n)
5. Resultados:
   - Diagrama de flujo de b\u00fasqueda (PRISMA)
   - Tabla de caracter\u00edsticas de estudios incluidos
   - Gr\u00e1fico de resultados de evaluaci\u00f3n de calidad
   - Forest plot
   - Funnel plot
   - An\u00e1lisis de subgrupos
   - An\u00e1lisis de sensibilidad
6. Discusi\u00f3n: s\u00edntesis de evidencia, confiabilidad, limitaciones, investigaci\u00f3n futura
7. Conclusi\u00f3n: implicaciones para la pr\u00e1ctica
```

## Normas de Escritura

### Lista de Verificaci\u00f3n de Normas de Reporte
- **ECA**: CONSORT 2010 (lista de 25 \u00edtems + diagrama de flujo)
- **Revisi\u00f3n sistem\u00e1tica/Meta**: PRISMA 2020 (lista de 27 \u00edtems + diagrama de flujo)
- **Estudio observacional**: STROBE (lista de 22 \u00edtems)
- **Prueba diagn\u00f3stica**: STARD (lista de 30 \u00edtems)
- **Reporte de caso**: CARE (lista de 13 \u00edtems)
- **Experimento animal**: ARRIVE (lista de 21 \u00edtems)
- **Investigaci\u00f3n cualitativa**: SRQR (lista de 21 \u00edtems)
- **Evaluaci\u00f3n econ\u00f3mica**: CHEERS (lista de 24 \u00edtems)

### Normas de Reporte Estad\u00edstico
- **Tama\u00f1o del efecto**: diferencia de medias (DM), diferencia de medias estandarizada (DME), OR, RR, HR
- **Precisi\u00f3n**: intervalo de confianza del 95% (IC)
- **Valor P**: valor P exacto (ej. P=0.032), no escribir "P<0.05"
- **Datos faltantes**: reportar tasa de faltantes, m\u00e9todo de tratamiento
- **Software**: nombre + versi\u00f3n (ej. SPSS 26.0, R 4.2.1)

## Consejos de Publicaci\u00f3n

### Selecci\u00f3n de Revista
- **Factor de impacto**: clasificaci\u00f3n JCR (Q1-Q4), clasificaci\u00f3n de la Academia China de Ciencias
- **Grado de correspondencia**: alcance, p\u00fablico lector, tipo de art\u00edculo
- **Per\u00edodo de revisi\u00f3n**: revisi\u00f3n inicial, revisi\u00f3n por pares, per\u00edodo total
- **Acceso abierto**: costos de APC, pol\u00edticas de financiaci\u00f3n
- **Lista de alerta**: evitar revistas en la lista de alerta de la Academia China de Ciencias

### Material de Env\u00edo
- **Carta de presentaci\u00f3n**: puntos de innovaci\u00f3n, significado cl\u00ednico, revisores recomendados
- **Contribuciones de autores**: taxonom\u00eda CRediT
- **Conflictos de inter\u00e9s**: ninguno/declarar espec\u00edficamente
- **Disponibilidad de datos**: ubicaci\u00f3n de almacenamiento, forma de acceso
- **Aprobaci\u00f3n \u00e9tica**: n\u00famero de aprobaci\u00f3n \u00e9tica, consentimiento informado

### Respuesta a Revisores
- **Actitud**: cort\u00e9s, objetivo, sin excusas
- **Formato**: respuesta punto por punto (opini\u00f3n del revisor\u2192respuesta\u2192ubicaci\u00f3n de modificaci\u00f3n)
- **Estrategia**: aceptar opiniones razonables, rechazar con fundamento, complementar experimentos/datos
- **Plazo**: responder a tiempo, comunicar con anticipaci\u00f3n si se necesita extensi\u00f3n

## Errores Comunes
1. Tama\u00f1o de muestra insuficiente (potencia insuficiente)
2. Comparaciones m\u00faltiples sin correcci\u00f3n (falsos positivos)
3. Inferencia causal excesiva (correlaci\u00f3n \u2260 causalidad)
4. Desbalance basal (falla de aleatorizaci\u00f3n)
5. Manejo inadecuado de datos faltantes (eliminaci\u00f3n arbitraria)
6. Exceso de an\u00e1lisis de subgrupos (falsos positivos)
7. Descuido de factores de confusi\u00f3n (sesgo)
8. Selecci\u00f3n err\u00f3nea de m\u00e9todos estad\u00edsticos (usar prueba t en datos no normales)
9. Gr\u00e1ficos no estandarizados (ejes, leyendas, unidades)
10. Falta de descripci\u00f3n \u00e9tica (no pasar revisi\u00f3n de pares)
"""

with open(os.path.join(base, 'medical.md'), 'w', encoding='utf-8') as f:
    f.write(content3.lstrip())
print('medical.md written')
