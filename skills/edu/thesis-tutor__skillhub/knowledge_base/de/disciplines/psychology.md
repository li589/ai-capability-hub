# Leitfaden für das Verfassen wissenschaftlicher Arbeiten in Psychologie

## Fachspezifische Merkmale
- Betonung auf Versuchsdesign, statistischer Strenge und Theorievalidierung
- Wertschätzung für Ethikreview, informierte Zustimmung und Tierschutz
- Zeitschriftenartikel als Hauptform (Top-Journals: Psychological Science/JPSP/JEP/Developmental Psychology)
- Vorregistrierung (Preregistration) wird zunehmend wichtig
- Open-Science-Trend: Daten/Code/Material teilen

## Forschungstypen

### 1. Experimentelle Psychologie
- **Anwendung**: Kausalbeziehungen, kognitive Mechanismen, Verhaltensexperimente
- **Designtypen**:
  - Between-Subjects-Design: Verschiedene Probanden erhalten verschiedene Behandlungen
  - Within-Subjects-Design: Derselbe Proband erhält alle Behandlungen
  - Mixed Design: Sowohl Between- als auch Within-Variablen
- **Schlüsselelemente**:
  - Manipulation der unabhängigen Variablen (klar, effektiv, replizierbar)
  - Messung der abhängigen Variablen (Reaktionszeit, Genauigkeit, Eye-Tracking, ERP, fMRI)
  - Kontrolle von Störvariablen (Randomisierung, Balancierung, Maskierung)
  - Poweranalyse (G*Power: f=0.25 mittlerer Effekt, α=0.05, 1-β=0.80)
- **Berichterstattungsstandards**:
  - Hypothesenvorregistrierung (OSF, AsPredicted)
  - Vollständige Beschreibung des Versuchsablaufs (replizierbar)
  - Transparente Ausschlusskriterien (z.B. Reaktionszeit<200ms)
  - Ergänzende Bayes-Analyse (BF10)

### 2. Entwicklungspsychologie
- **Anwendung**: Lebensspannenentwicklung, Altersunterschiede, Längsschnittstudien
- **Designtypen**:
  - Querschnittsdesign: Verschiedene Altersgruppen gleichzeitig testen
  - Längsschnittdesign: Dieselbe Gruppe mehrfach testen
  - Sequenzdesign: Kombination aus Querschnitt und Längsschnitt
- **Schlüsselelemente**:
  - Altersgruppierung (theoriegetrieben: z.B. Piaget-Stufen)
  - Messinvarianz (Vergleichbarkeit über Altersgruppen)
  - Umgang mit Ausfällen (MAR/MCAR-Test, multiple Imputation)
  - Kohorteneffekte (historische Hintergrundunterschiede)
- **Besondere Überlegungen**:
  - Kinderethik: Elterliche Zustimmung + Kindliche Zustimmung (ab 7 Jahren)
  - Entwicklungsgerechtheit: Aufgabenschwierigkeit, Aufrechterhaltung der Aufmerksamkeit
  - Soziale Erwünschtheit: Kinder neigen stärker zur Anpassung

### 3. Sozialpsychologie
- **Anwendung**: Soziale Kognition, Einstellungen, Gruppenprozesse, zwischenmenschliche Beziehungen
- **Häufige Methoden**:
  - Fragebogen: Skalenmessung (Likert 5/7-stufig)
  - Experimentelle Methode: Situationsmanipulation (z.B. Varianten des Asch-Konformitätsexperiments)
  - Feldexperiment: Intervention in natürlichen Situationen
  - Archivanalyse: Historische Daten, Medieninhalte
- **Schlüsselelemente**:
  - Kontrolle sozialer Erwünschtheit (Anonymität, indirekte Messung, IAT)
  - Repräsentativität der Stichprobe (WEIRD-Problem: Western, Educated, Industrialized, Rich, Democratic)
  - Beachtung der Effektstärke (klein d=0.2, mittel d=0.5, groß d=0.8)
  - Replikationsexperimente (direkt/konzeptionell/systematisch)

### 4. Klinische Psychologie
- **Anwendung**: Psychische Störungen, Interventionseffekte, Bewertungsinstrumente
- **Designtypen**:
  - RCT: Goldstandard, Randomisierung in Behandlungs-/Kontrollgruppe
  - Single-Case-Experiment: ABA/Multi-Baseline-Design
  - Quasi-Experiment: Natürliche Gruppierung, Prä-Post-Messung
- **Schlüsselelemente**:
  - Diagnosekriterien (DSM-5/ICD-11)
  - Interventionsprotokoll (manualisiert, Fidelity-Check)
  - Endpunkte (Symptome, Funktionsfähigkeit, Lebensqualität)
  - Umgang mit Ausfällen (ITT/PP-Analyse)
- **Besondere Ethik**:
  - Schutz gefährdeter Gruppen (Patienten, Kinder, ältere Menschen)
  - Prinzip des minimalen Risikos
  - Datenschutz (DSGVO/Cybersicherheitsgesetz)

## Versuchsdesign

### Between- vs. Within-Subjects
| Dimension | Between-Subjects | Within-Subjects |
|-----------|------------------|-----------------|
| Vorteile | Keine Reihenfolge-/Übungseffekte | Kontrolle individueller Unterschiede, höhere Power |
| Nachteile | Mehr Probanden nötig, individuelle Unterschiede als Störfaktor | Reihenfolge-/Übungseffekte, Ermüdung |
| Anwendung | Behandlungen haben dauerhafte Wirkung | Behandlungen sind reversibel, hohe Power benötigt |
| Stichprobengröße | Pro Gruppe ≥30 (großer Effekt) | Gesamt ≥20 (großer Effekt) |

### Quasi-Experimentelle Designs
- **Ungleiche Gruppen Prä-Post-Test**: Keine Randomisierung, statistische Kontrolle nötig
- **Unterbrochene Zeitreihe**: Mehrfache Messungen, Vergleich vor/nach Intervention
- **Regression Discontinuity**: Schwellenwertbasierte Gruppierung
- **Nicht-Äquivalente Kontrollgruppe**: Matching statt Randomisierung

### Statistische Power
- **Berechnungstools**: G*Power, pwr-Paket, WebPower
- **Parameter**:
  - Effektstärke (d=0.2 klein/0.5 mittel/0.8 groß; f=0.1 klein/0.25 mittel/0.4 groß)
  - α-Niveau (0.05 oder 0.01)
  - Statistische Power (1-β=0.80 oder 0.90)
  - Testtyp (zweiseitig/ einseitig)
- **Empfehlungen**:
  - Kleiner Effekt: Pro Gruppe ≥64 (Power 0.80)
  - Mittlerer Effekt: Pro Gruppe ≥26
  - Großer Effekt: Pro Gruppe ≥16

## Statistische Methoden

### Grundlegende Analyse
- **t-Test**: Zweigruppenvergleich (unabhängig/gepaart)
- **Varianzanalyse (ANOVA)**: Mehrgruppenvergleich
  - Einfaktoriell: Eine unabhängige Variable
  - Mehrfaktoriell: Mehrere unabhängige Variablen + Interaktionseffekte
  - Wiederholte Messungen: Within-Subjects-Variablen
  - MANOVA: Mehrere abhängige Variablen
- **Chi-Quadrat-Test**: Zusammenhang kategorialer Variablen
- **Korrelationsanalyse**: Pearson/Spearman

### Fortgeschrittene Analyse
- **Regressionsanalyse**:
  - Lineare Regression: Kontinuierliche Prädiktion→Kontinuierliches Ergebnis
  - Logistische Regression: Kategoriales Ergebnis
  - Poisson-Regression: Zählergebnisse
  - Mehrfachregression: Verschachtelte Daten (Probanden→Klasse→Schule)
- **Strukturgleichungsmodell (SEM)**:
  - Konfirmatorische Faktorenanalyse (CFA): Messmodell
  - Pfadanalyse: Strukturmodell
  - Mehrgruppenvergleich: Messinvarianz (configural/metric/scalar)
- **Mehrebenenanalyse (HLM/MLM)**:
  - Random Intercept/Slope Modelle
  - Cross-Level-Interaktionen
  - 3+ Ebenen Verschachtelung
- **Latent Growth Model (LGM)**:
  - Lineares/nicht-lineares Wachstum
  - Wachstumsprädiktoren
  - Parallelprozessmodelle
- **Überlebensanalyse**: Zeit bis zum Eintreten eines Ereignisses

### Effektstärkenberichterstattung
- **Cohen's d**: Mittelwertdifferenz zwischen zwei Gruppen (klein 0.2/mittel 0.5/groß 0.8)
- **η² (Eta-Quadrat)**: Varianzaufklärungsanteil (klein 0.01/mittel 0.06/groß 0.14)
- **ω² (Omega-Quadrat)**: Unverzerrte Schätzung
- **r²**: Bestimmtheitsmaß
- **Odds Ratio (OR)**: Logistische Regression
- **Konfidenzintervall**: 95%-KI wichtiger als p-Wert

## Skalenverwendung

### Häufige Skalenquellen
- **APA PsycTests**: Offizielle psychologische Testdatenbank
- **Mental Measurements Yearbook**: Testbewertungen
- **Zeitschriftenanhänge**: Originalarbeiten enthalten oft vollständige Skalen
- **Handbücher**: z.B. BFI Big Five Persönlichkeitsinventar Handbuch

### Übersetzung-Rückübersetzung-Verfahren
1. Englisch→Deutsch (durch Zweisprachige)
2. Deutsch→Englisch (durch unabhängige Zweisprachige)
3. Vergleich von Original und Rückübersetzung
4. Expertenausschuss diskutiert Unterschiede
5. Pretest (30-50 Personen)
6. Reliabilitäts-/Validitätsprüfung

### Reliabilitäts-/Validitätsanforderungen
- **Reliabilität**:
  - Cronbachs α ≥ 0.70 (akzeptabel)
  - Split-Half-Reliabilität ≥ 0.70
  - Test-Retest-Reliabilität (2-4 Wochen Abstand) r ≥ 0.70
- **Validität**:
  - Inhaltsvalidität: Expertenbewertung
  - Konstruktvalidität: EFA/CFA, Faktorladungen ≥ 0.50
  - Kriteriumsvalidität: Korrelation mit externem Standard
  - Diskriminante Validität: AVE > Korrelationskoeffizient²

## Ethische Anforderungen

### APA-Ethische Prinzipien (5 Prinzipien)
1. **Wohltätigkeit und Nicht-Schaden**: Nutzen maximieren, Schaden minimieren
2. **Treue und Verantwortung**: Professionelle Standards, soziale Verantwortung
3. **Integrität**: Ehrlichkeit, Genauigkeit, kein Betrug
4. **Gerechtigkeit**: Faire Behandlung, Vermeidung von Vorurteilen
5. **Respekt**: Autonomie, Privatsphäre, Würde

### Informierte Zustimmung
- **Elemente**: Studienzweck, Verfahren, Risiken, Nutzen, Vertraulichkeit, Freiwilligkeit, Kontaktinformationen
- **Besondere Populationen**:
  - Kinder: Elterliche Zustimmung + Kindliche Zustimmung (ab 7 Jahren)
  - Kognitive Einschränkung: Gesetzlicher Vertreter
  - Gefangene: Zusätzlicher Schutz
- **Deception-Studien**: Nachträgliche Aufklärung (Debriefing)

### Tierexperimentelle Ethik
- **3R-Prinzipien**: Replacement (Ersatz), Reduction (Reduktion), Refinement (Verbesserung)
- **IACUC-Review**: Protokollgenehmigung, tierärztliche Aufsicht
- **Haltungsbedingungen**: Umweltanreicherung, soziale Bedürfnisse
- **Endpunkte**: Humane Endpunkte, Euthanasiekriterien

## Gliederungsvorlagen

### Experimentelle Studie
```
1. Einleitung
   - Theoretischer Hintergrund (Kernkonzepte)
   - Forschungsstand (Literaturlücke)
   - Forschungsfragen und Hypothesen (H1a, H1b...)
   - Theoretischer Beitrag und praktische Relevanz

2. Methode
   - Probanden (Rekrutierung, Screening, Stichprobengröße, Vergütung)
   - Design (2×3 Mixed Design, UV/AV)
   - Materialien/Stimuli (Herkunft, Entwicklung, Pretest)
   - Prozedur (Schritte, Randomisierung, Maskierung)
   - Datenanalyseplan (Vorregistrierungslink)

3. Ergebnisse
   - Deskriptive Statistik (M, SD, n)
   - Manipulationscheck (UV wirksam)
   - Hypothesentestung (ANOVA-Tabelle, Effektstärke, KI)
   - Zusätzliche Analysen (explorativ, Bayes)
   - Diagramme (Mittelwertplot, Interaktionsplot)

4. Diskussion
   - Hypothesenprüfungszusammenfassung
   - Theoretische Erklärung (Mechanismus)
   - Vergleich mit vorherigen Studien
   - Limitationen (Stichprobe, Methode, Generalisierung)
   - Zukünftige Richtungen (konkrete Hypothesen)
   - Fazit (prägnant)

5. Ergänzendes Material (online)
   - Vollständiger Fragebogen/Stimuli
   - Rohdaten (OSF)
   - Analysecode (R/Python)
```

## Open-Science-Praktiken

### Vorregistrierung
- **Plattformen**: OSF, AsPredicted, ClinicalTrials.gov
- **Inhalte**: Hypothesen, Design, Stichprobengröße, Analyseplan
- **Typen**:
  - Standardvorregistrierung: Vor Datenerhebung
  - Registered Report: Zeitschrift verpflichtet zur Veröffentlichung (unabhängig vom Ergebnis)
- **Vorteile**: Verhindert HARKing (Hypothesen nach Datenanalyse), erhöht Vertrauenswürdigkeit

### Datenteilen
- **Plattformen**: OSF, Figshare, Zenodo, GitHub
- **Inhalte**:
  - Rohdaten (anonymisiert)
  - Analysecode (replizierbar)
  - Studienmaterialien (Fragebögen, Stimuli)
- **Lizenzen**: CC0 (empfohlen), CC-BY

### Codeteilen
- **Anforderungen**: Ausführbar, kommentiert, mit README
- **Tools**: R Markdown, Jupyter Notebook
- **Versionskontrolle**: Git/GitHub

## Häufige Fehler
1. Unzureichende Stichprobengröße (Power<0.80)
2. Nicht korrigierte multiple Vergleiche (Bonferroni/FDR)
3. Within-Subjects-Design ohne Reihenfolgekontrolle (Lateinisches Quadrat/Randomisierung)
4. Effektstärke nicht berichtet (nur p-Wert)
5. Post-hoc-Hypothesen (HARKing)
6. Common Method Bias (gleichquellige Daten)
7. Niedrige Skalenreliabilität (α<0.70 trotzdem verwendet)
8. Überzogene Kausalschlussfolgerungen (Korrelationsdesign)
9. Kulturelle Unterschiede ignoriert (WEIRD-Stichprobe)
10. Fehlende Ethikbeschreibung (Review nicht bestehbar)
