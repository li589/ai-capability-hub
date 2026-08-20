# Leitfaden für das Verfassen wissenschaftlicher Arbeiten in der Wirtschaftswissenschaft (Economics)

## Fächerspezifische Merkmale
- Betont theoretische Modelle, empirische Analysen und politische Implikationen
- Betont Datenqualität, Identifikationsstrategien und Robustheitstests
- Zeitschriftenartikel als Hauptpublikationsform (Top 5: AER/QJE/JPE/Econometrica/RES)

## Themenauswahl

### Mikroökonomie
1. **Arbeitsökonomie**
   - Bildungsrendite, Qualifikationsprämie
   - Mindestlohn, Beschäftigungseffekte
   - Telearbeit, Gig-Economy

2. **Industrieorganisation**
   - Antitrust in der Plattformökonomie
   - Preisgestaltung auf digitalen Märkten
   - Markteintritt/-austritt von Unternehmen

3. **Öffentliche Finanzen**
   - Effekte der Steuerpolitik
   - Design der sozialen Sicherung
   - Steuerwettbewerb der Kommunen

### Makroökonomie
1. **Wirtschaftswachstum**
   - Totale Faktorproduktivität
   - Innovationsgetriebenes Wachstum
   - Strukturwandel

2. **Geldpolitik**
   - Effekte der quantitativen Lockerung
   - Digitale Währung (CBDC)
   - Transmissionsmechanismus des Zinssatzes

3. **Internationale Finanzen**
   - Wechselkursschwankungen
   - Kapitalflüsse
   - Globale Wertschöpfungsketten

### Entwicklungsökonomie
- Evaluierung der Effekte gezielter Armutsbekämpfung
- Digitale Finanzinklusion
- Klimawandel und Landwirtschaft
- Migration und Urbanisierung

## Strukturvorlage für wissenschaftliche Arbeiten

### Empirische Arbeit (am häufigsten)
```
1. Einleitung (Forschungsfrage, Beiträge, Überblick über die Hauptergebnisse)
2. Literaturübersicht (theoretische Entwicklung, empirische Fortschritte, Positionierung dieser Arbeit)
3. Institutioneller Hintergrund/Theoretischer Rahmen (chinesischer Kontext, theoretische Vorhersagen)
4. Daten und deskriptive Statistik (Datenquelle, Variablendefinition, Stichprobenmerkmale)
5. Empirische Strategie (Identifikationsmethode, Modellspezifikation, Behandlung von Endogenität)
6. Basisergebnisse (Hauptregression, Koeffizienteninterpretation, ökonomische Signifikanz)
7. Robustheitstests (alternative Variablen, Teilstichproben, Placebo)
8. Mechanismenanalyse (Mediationseffekte, Heterogenitätsanalyse)
9. Fazit und politische Empfehlungen
```

### Theoretische Arbeit
- Modellspezifikation (Annahmen, Spielstruktur, Gleichgewichtskonzept)
- Gleichgewichtsanalyse (Existenz, Eindeutigkeit, komparative Statik)
- Wohlfahrtsanalyse (Effizienz, Verteilungseffekte)
- Numerische Simulation (Kalibrierung, Kontrafaktisch)

## Schreibtipps

### Empirische Strategie
- **Identifikationsstrategie**:
  - RCT (Randomisiertes Experiment)
  - Natürliches Experiment (DID, RDD, IV)
  - Matching-Methoden (PSM, synthetische Kontrolle)

- **Behandlung von Endogenität**:
  - Ausgelassene Variablen (Fixeffekte, Kontrollvariablen)
  - Umgekehrte Kausalität (Instrumentalvariablen, GMM)
  - Messfehler (multiple Indikatoren, Strukturgleichungsmodelle)

### Regressionsformulare
- Schrittweise Darstellung: Basis → mit Kontrollen → Fixeffekte
- Standardfehler in Klammern (geclustert auf geeigneter Ebene)
- Signifikanzniveaus: * p<0.1, ** p<0.05, *** p<0.01
- R², Stichprobengröße, F-Statistik

### Ökonomische Signifikanz
- Nicht nur statistische Signifikanz berichten, sondern auch ökonomische Bedeutung erklären
- Vergleichsbasis: Verhältnis des Effekts zum Mittelwert
- Kosten-Nutzen-Analyse

## Datenquellen
- **Makrodaten**: Statistisches Bundesamt, Weltbank, IWF, Penn World Table
- **Mikrodaten**: CHFS, CFPS, CHARLS, CGSS, Industrieunternehmensdatenbank
- **Finanzdaten**: CSMAR, Wind, Bloomberg
- **Politische Daten**: Regierungsarbeitsbericht, Finanzministerium, Zentralbank

## Häufige Fehler
1. **Scheinregression**: Direkte Regression nicht-stationärer Zeitreihen
2. **Selektionsverzerrung**: Ungeeignete Stichprobenauswahl
3. **Übermäßige Kontrolle**: Kontrolle von Mediationsvariablen
4. **Multikollinearität**: VIF > 10
5. **Falsche Signifikanz**: P-Hacking, Nicht-Berichterstattung negativer Ergebnisse

## Empfohlene Werkzeuge
- **Datenverarbeitung**: Stata (Standard), R, Python (pandas)
- **Regressionsanalyse**: Stata (reghdfe, ivreg2), R (fixest)
- **Visualisierung**: ggplot2, Stata coefplot
- **Literaturverwaltung**: Zotero, Mendeley
- **Schreiben**: LaTeX (Overleaf) oder Word

## Einreichungsempfehlungen
- **Chinesische Zeitschriften**: "Wirtschaftsforschung", "Managementwelt", "Wirtschaftswissenschaft (Vierteljahresschrift)"
- **Englische Zeitschriften**: Auswahl nach Fachgebiet (JDE, JLE, AEJ-Serie)
- **Arbeitspapiere**: NBER, IZA, CEPR (Prioritätssetzung)

## Hinweise zur Plagiatsprüfung
- Empirische Beschreibungen (Datenquelle, Variablendefinition) können standardisiert werden
- Ableitung theoretischer Modelle in eigenen Worten
- Literaturübersicht ist am anfälligsten für Wiederholungen und muss umgeschrieben werden
- Politische Empfehlungen unter Einbeziehung aktueller Daten
