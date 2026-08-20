# Leitfaden für das Verfassen wissenschaftlicher Arbeiten in Betriebswirtschaftslehre/Management

## Fachspezifische Merkmale
- Betonung auf theoretischen Rahmen, empirischer Validierung und Managementimplikationen
- Wertschätzung für Datenquellen, Variablenmessung und Endogenitätsbehandlung
- Zeitschriftenartikel als Hauptform (Top-Journals: AMJ/SMJ/JOM/OS/MS)
- Fallstudien beliebt (Theoriegenerierung/-prüfung)

## Forschungstypen

### 1. Fallstudien
- **Anwendung**: Phänomenexploration, Theoriegenerierung, komplexe Prozesse
- **Typen**:
  - Einzelfall (extrem/typisch/längsschnittlich)
  - Mehrfachfall (Replikation/Kontrast/Komplementarität)
- **Designprinzipien**:
  - Fallauswahl (theoretische Stichprobe, nicht zufällig)
  - Datenerhebung (Interviews/Archiv/Beobachtung/multi-method)
  - Analysestrategie (Musterabgleich/Interpretationsaufbau/Zeitreihen)
  - Reliabilitätssicherung (Triangulation/Mitgliederüberprüfung/Audit Trail)
- **Berichterstattung**:
  - Reichhaltige Kontextbeschreibung (Kontextualisierung)
  - Klare Evidenzkette (Daten→Diagramme→Schlussfolgerungen)
  - Dialog mit Literatur (Bestätigung/Erweiterung/Herausforderung)

### 2. Befragungsstudien
- **Anwendung**: Großstichproben-Hypothesenprüfung, Variablenbeziehungen
- **Typen**: Querschnitt/Längsschnitt/Panel
- **Designprinzipien**:
  - Stichprobenrahmen (Zielgesamtheit erreichbar)
  - Fragebogendesign (etablierte Skalen + eigene Items)
  - Datenerhebung (online/papiergestützt/gemischt)
  - Common Method Bias (Harman-Einfaktor/prozedurale Kontrolle)
- **Analysemethoden**:
  - Strukturgleichungsmodell (SEM): AMOS/PLS/Mplus
  - Mehrebenenanalyse (HLM): Hierarchische Daten
  - Latent Growth Model (LGM): Längsschnittverfolgung

### 3. Experimentelle Studien
- **Anwendung**: Kausalbeziehungen, Verhaltensmechanismen
- **Typen**: Labor/Feld/Quasi-Experiment/Natürliches Experiment
- **Designprinzipien**:
  - Randomisierung (echt/gepaart)
  - Manipulationscheck (unabhängige Variable wirksam?)
  - Abhängige Variablenmessung (objektiv/subjektiv/verhaltensbasiert)
  - Kontrollvariablen (Störfaktoren ausschließen)
- **Analysemethoden**:
  - ANOVA/ANCOVA: Gruppenvergleich
  - Mediation/Moderation: PROCESS-Makro
  - Mehrebenen: HLM

### 4. Sekundärdatenanalyse
- **Anwendung**: Makrostudien, Paneldaten, Ereignisstudien
- **Datenquellen**:
  - Börsennotierte Unternehmen: CSMAR, Wind, Guotaian
  - Patentdaten: Nationales Amt für geistiges Eigentum, Derwent
  - Rekrutierungsdaten: Zhilian, 51Job
  - Soziale Medien: Weibo, Zhihu, Maimai (Web Scraping)
- **Analysemethoden**:
  - Paneldatenmodelle: Fixed Effects/Random Effects/GMM
  - DID/PSM: Kausalschluss
  - Ereignisstudie: CAR-Berechnung
  - Textanalyse: Worthäufigkeit, Topic Modeling, Stimmungsanalyse

## Theoretische Rahmen

### Häufig verwendete Theorien
- **Resource-Based View (RBV)**: VRIN-Ressourcen→Wettbewerbsvorteil
- **Institutionelle Theorie**: Regulatorische/normative/kognitive institutionelle Drucks
- **Agenturtheorie**: Prinzipal-Agent-Konflikt→Governance-Mechanismen
- **Stakeholder-Theorie**: Multi-Akteurs-Gleichgewicht
- **Dynamic Capabilities**: Sensing/Seizing/Reconfiguring
- **Organisationales Lernen**: Exploration/Exploitation, Wissenstransformation (SECI)
- **Upper Echelons Theory**: Top-Management-Charakteristika→Strategische Wahl→Organisationsergebnisse
- **Soziale Netzwerke**: Strukturlöcher/Zentralität/Eingebettetheit
- **Signaltheorie**: Signalgebung→Signalinterpretation→Ergebnis
- **Legitimitätstheorie**: Pragmatische/morale/kognitive Legitimität

### Empfehlungen zur Theorieanwendung
1. **Keine Theorieanhäufung**: 1-2 Kerntheorien genügen
2. **Klare theoretische Perspektive**: Was erklären, was vorhersagen
3. **Theorie-Hypothesen-Abgleich**: Jede Hypothese theoretisch fundiert
4. **Theoriedialog**: Ergebnisse im Einklang/Widerspruch/Erweiterung zur Theorie

## Datenquellen und Messung

### Fragebogendesign
- **Skalenquellen**: Etablierte Skalen bevorzugen (Reliabilität/Validität geprüft)
- **Übersetzung-Rückübersetzung**: Englisch→Deutsch→Rückübersetzung→Vergleich
- **Anzahl der Items**: 3-7 pro Konstrukt (Müdigkeit vermeiden)
- **Invers gepolte Items**: 2-3 einstreuen (Standardreaktion verhindern)
- **Pretest**: 30-50 Personen, CITC<0.4 löschen

### Häufige Datenbanken
- **CSMAR**: Finanzen, Governance, Aktienbesitz börsennotierter Unternehmen
- **Wind**: Finanzen, Makro, Branchen
- **Guotaian**: Wirtschaft/Finanzen, Regionalwirtschaft
- **CEIC**: Makroökonomie, Branchendaten
- **Weltbank**: Ländervergleich, Entwicklungsindikatoren
- **China Family Panel Studies (CFPS)**: Mikroindividuen
- **China Health and Retirement Longitudinal Study (CHARLS)**: Alterung

### Variablenmessung
- **Unabhängige Variable**: Klare Operationalisierung
- **Abhängige Variable**: Mehrdimensionale Messung (objektiv+subjektiv)
- **Mediationsvariable**: Mechanismuserklärung
- **Moderationsvariable**: Grenzbedingungen
- **Kontrollvariablen**: Alternative Erklärungen ausschließen

## Analysemethoden

### Strukturgleichungsmodell (SEM)
- **CB-SEM (AMOS/Mplus)**:
  - Großstichprobe (>200)
  - Konfirmatorische Analyse
  - Strenger Modellfit (CFI>0.9, RMSEA<0.08, SRMR<0.08)
- **PLS-SEM (SmartPLS)**:
  - Kleine Stichprobe akzeptabel
  - Explorative Analyse
  - Prädiktionsorientiert (PLSpredict)

### Mehrebenenanalyse (HLM)
- **Anwendung**: Verschachtelte Daten (Mitarbeiter→Team→Organisation)
- **Software**: HLM, Mplus, R (lme4)
- **Berichterstattung**: ICC(1), ICC(2), rwg, Cross-Level-Effekte

### Qualitative Comparative Analysis (QCA)
- **Anwendung**: Kausalkomplexität, multifaktorielle Kombinationen
- **Typen**: crisp-set / fuzzy-set / mvQCA
- **Software**: fsQCA, R (QCA-Paket)
- **Berichterstattung**: Wahrheitstabelle, Konsistenz, Coverage, Intermediate Solution

### Endogenitätsbehandlung
- **Quellen**: Ausgelassene Variablen, umgekehrte Kausalität, Messfehler, Stichprobenauswahl
- **Methoden**:
  - Instrumentalvariablen (IV): 2SLS
  - Differences-in-Differences (DID): Politikschock
  - Propensity Score Matching (PSM): Stichprobenmatching
  - Regression Discontinuity Design (RDD): Schwellenwert
  - Heckman-Modell: Stichprobenauswahl

## Gliederungsvorlagen

### Empirische Studie (quantitativ)
```
1. Einleitung
   - Praktischer Hintergrund (Managementphänomen)
   - Theoretische Lücke (Literaturdialog)
   - Forschungsfrage
   - Theoretischer Beitrag
   - Praktische Relevanz

2. Literaturübersicht und Hypothesen
   - Definition der Kernkonstrukte
   - Literatur zum Haupeffekt (A→B)
   - Mediationsmechanismus (A→M→B)
   - Moderationsgrenze (W beeinflusst A→B)
   - Hypothesenzusammenfassungstabelle

3. Forschungsdesign
   - Stichprobe und Prozedur
   - Variablenmessung (Skalenherkunft + Reliabilität)
   - Analysestrategie
   - Common Method Bias Kontrolle

4. Ergebnisse
   - Deskriptive Statistik + Korrelationsmatrix
   - Messmodell (CFA/Reliabilität/Validität)
   - Strukturmodell (Pfadkoeffizienten + Signifikanz)
   - Mediationseffekt (Bootstrap)
   - Moderationseffekt (Interaktionsterm/einfache Steigung)
   - Robustheitstests (alternative Messung/Teilstichprobe)

5. Diskussion
   - Hypothesenprüfungszusammenfassung
   - Theoretischer Beitrag (Dialog)
   - Managementimplikationen (umsetzbar)
   - Limitationen (Stichprobe/Methode/Kausalität)
   - Zukünftige Forschung (konkrete Richtungen)
```

### Fallstudie (qualitativ)
```
1. Einleitung: Phänomen→Frage→Methode→Beitrag
2. Literaturübersicht: Theoretische Perspektive→Lücke→Rahmen
3. Methode:
   - Fallauswahl (theoretische Stichprobenlogik)
   - Datenerhebung (Multi-Quellen-Evidenzmatrix)
   - Datenanalyse (Kodierstrategie)
   - Reliabilitätssicherung (Triangulation etc.)
4. Falldarstellung: Hintergrund→Prozess→Schlüsselereignisse
5. Cross-Case-Analyse: Muster→Propositionen→Theorie
6. Diskussion: Beitrag→Implikationen→Limitationen→Zukunft
```

## Häufige Fehler
1. Schwacher theoretischer Rahmen (Hypothesen ohne theoretische Fundierung)
2. Endogenität wird ignoriert (Kausalschluss unzuverlässig)
3. Common Method Bias (gleichquellige Daten nicht behandelt)
4. Willkürliche Skalenmodifikation (zerstört Reliabilität/Validität)
5. Falsche Mediationseffektinterpretation (vollständige Mediation ≠ Mediation)
6. Falsches Moderationseffektdiagramm (Richtung der einfachen Steigung)
7. Stichprobenverzerrung (Bequemlichkeitsstichprobe verallgemeinern)
8. Überkontrolle von Variablen (Mediation/Moderation kontrollieren)
9. Selektive Ergebnisberichterstattung (nur signifikante Ergebnisse)
10. Leere Managementimplikationen (fehlende Umsetzbarkeit)
