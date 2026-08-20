# Detaillierter Leitfaden für das Exposé

## Methodische Roadmap

### 1. Was ist eine methodische Roadmap?
Die methodische Roadmap ist ein Visualisierungswerkzeug, das den vollständigen Weg der Forschung von der Problemstellung zur Lösung darstellt. Sie hilft Gutachtern, die Forschungslogik schnell zu verstehen, und hilft Ihnen, Ihre eigenen Gedanken zu ordnen.

### 2. Arten von methodischen Roadmaps

**Typ 1: Flussdiagramm-Stil (geeignet für experimentelle/technische Forschung)**
`
Forschungsfrage
    |
    v
Literaturübersicht → Theoretischer Rahmen
    |
    v
Forschungshypothese
    |
    v
Versuchsplanung / Datenerhebung
    |
    v
Datenanalyse
    |
    v
Ergebnisvalidierung
    |
    v
Fazit und Empfehlungen
`

**Typ 2: Zeitachsen-Stil (geeignet für Längsschnitt-/Entwicklungsforschung)**
`
Phase 1 (Monat 1-3)    Phase 2 (Monat 4-6)    Phase 3 (Monat 7-9)
    |                       |                       |
    v                       v                       v
Literaturrecherche      Datenerhebung           Verfassen der Arbeit
Theoriekonstruktion     Experimentdurchführung  Überarbeitung
`

**Typ 3: Zyklisch-iterativer Stil (geeignet für Aktions-/Designforschung)**
`
       Planen
          |
          v
    Umsetzen
    /        \
Prüfen       Reflektieren
    \        /
      Anpassen
          |
          v
      Neue Runde Planen
`

**Typ 4: Baumstruktur-Stil (geeignet für Multi-Methoden-/Mehrfallstudien)**
`
              Kernfrage
                 |
    +------------+------------+
    |            |            |
Quantitative  Qualitative  Mixed-Methods
Forschung     Forschung    Forschung
    |            |            |
Fragebogen    Tiefeninter- Triangulation
              views
    |            |            |
Statistische  Thematische  Integrierte
Analyse       Analyse      Analyse
`

### 3. Werkzeuge zur Erstellung methodischer Roadmaps

**Professionelle Werkzeuge**:
- Visio: Umfassendste Funktionalität, geeignet für komplexe Prozesse
- ProcessOn: Online, reichhaltige Vorlagen
- Draw.io (diagrams.net): Kostenlos, leistungsstark
- Lucidchart: Online-Zusammenarbeit, geeignet für Teams

**Allgemeine Werkzeuge**:
- PowerPoint: Ausreichend für einfache Diagramme
- Word: SmartArt-Funktion
- LaTeX: TikZ-Paket (geeignet für wissenschaftliches Satz)

**Code-Werkzeuge**:
- Python: matplotlib, graphviz
- R: DiagrammeR, ggplot2
- Mermaid: Markdown-Stil, geeignet für Dokumentationseinbettung

### 4. Designprinzipien für methodische Roadmaps

**Klarheit**:
- Jeder Knoten hat eine eindeutige Beschriftung (Verb + Substantiv)
- Pfeilrichtung eindeutig (einfach, bidirektional, zyklisch)
- Kreuzungen vermeiden (durch Schichtung oder Farbunterscheidung)

**Vollständigkeit**:
- Enthält die vollständige Kette von der Fragestellung bis zum Fazit
- Markierung von Schlüsselknoten (Meilensteine)
- Markierung von Entscheidungspunkten (z.B. „Hypothese bestätigt?")

**Hierarchie**:
- Hauptprozess: dicke Linien, große Knoten
- Teilprozesse: dünne Linien, kleine Knoten
- Anmerkungen: gestrichelte Linien, grau

**Ästhetik**:
- Einheitliche Farbgebung (3-5 Farben)
- Ausrichtung (Rasterausrichtung)
- Weißraum (nicht überfüllt)

### 5. Beispiel: Methodische Roadmap für quantitative Forschung

`
[Forschungshintergrund]
Online-Bildung entwickelt sich schnell, aber die Lernergebnisse sind uneinheitlich
         |
         v
[Literaturübersicht] → Identifikation der Forschungslücke: Fehlende systematische Studien zu Interaktionsmechanismen
         |
         v
[Theoretischer Rahmen] → Sozialer Konstruktivismus + Kognitive Lasttheorie
         |
         v
[Forschungshypothesen]
H1: Die Häufigkeit der Lehrer-Schüler-Interaktion korreliert positiv mit den Studienleistungen
H2: Die Tiefe der Schüler-Schüler-Interaktion korreliert positiv mit dem kritischen Denken
H3: Die Interaktionsqualität vermittelt zwischen Plattformfunktionen und Lernergebnissen
         |
         v
[Forschungsdesign]
  |
  +-- Experimentalgruppe: Nutzung einer neuen Interaktionsplattform (n=150)
  |
  +-- Kontrollgruppe: Nutzung einer herkömmlichen Plattform (n=150)
  |
  +-- Prätest: Lernmotivation, Vorwissen
  |
  +-- Posttest: Studienleistung, kritisches Denken, Zufriedenheit
         |
         v
[Datenerhebung]
  |
  +-- Plattformprotokolle: Interaktionshäufigkeit, Dauer, Typ
  |
  +-- Fragebogen: Wahrnehmung der Interaktionsqualität, Lernerfahrung
  |
  +-- Testergebnisse: Multiple-Choice + offene Fragen
  |
  +-- Interviews: Vertiefendes Verständnis der Mechanismen (n=20)
         |
         v
[Datenanalyse]
  |
  +-- Deskriptive Statistik: Stichprobenmerkmale, Variablenverteilung
  |
  +-- Inferenzstatistik: t-Test, Varianzanalyse, Regression
  |
  +-- Mediationsanalyse: Bootstrap-Methode
  |
  +-- Qualitative Analyse: Thematisches Kodieren
         |
         v
[Ergebnisvalidierung]
  |
  +-- Hypothesentest: Sind H1/H2/H3 bestätigt?
  |
  +-- Robustheitstest: Alternative Variablen, Teilstichproben
  |
  +-- Triangulation: Übereinstimmung quantitativer und qualitativer Ergebnisse
         |
         v
[Fazit und Empfehlungen]
  |
  +-- Theoretischer Beitrag: Verfeinerung der Online-Lerninteraktionstheorie
  |
  +-- Praktische Empfehlungen: Plattformgestaltung, Lehrstrategien
  |
  +-- Einschränkungen und zukünftige Forschung
`

## Machbarkeitsanalyse

### 1. Dimensionen der Forschungsmachbarkeit

**Theoretische Machbarkeit**:
- Hat die Forschungsfrage eine theoretische Grundlage?
- Ist der theoretische Rahmen ausgereift?
- Sind die Forschungshypothesen ableitbar?

**Methodische Machbarkeit**:
- Ist die Forschungsmethode für die Forschungsfrage geeignet?
- Sind die Daten verfügbar?
- Sind die Analysetechniken beherrscht?

**Ressourcen-Machbarkeit**:
- Zeit: Ist der Forschungszeitraum realistisch?
- Finanzierung: Wird zusätzliche Finanzierung benötigt?
- Ausrüstung: Wird spezielle Ausrüstung benötigt?
- Personal: Wird ein Mitarbeiter benötigt?
- Daten: Gibt es Zugang zu Datenquellen?

**Persönliche Machbarkeit**:
- Wissensbasis: Verfügt man über die relevanten theoretischen Grundlagen?
- Fähigkeiten: Beherrscht man die Forschungsmethoden?
- Betreuerunterstützung: Ist der Betreuer in diesem Bereich erfahren?
- Zeitaufwand: Kann ausreichend Zeit sichergestellt werden?

### 2. Rahmenwerk der Machbarkeitsanalyse

`
Machbarkeitsanalyse

1. Theoretische Machbarkeit
   - Theoretische Grundlage: [Theoriename] wurde breit in [Fachgebiet] angewandt und bietet eine solide Grundlage für diese Forschung
   - Forschungslücke: Bisherige Forschungen konzentrieren sich hauptsächlich auf X, aber es mangelt an Aufmerksamkeit für Y; diese Forschung füllt diese Lücke
   - Machbarkeitsfazit: Der theoretische Rahmen ist ausgereift, die Forschungshypothesen sind ableitbar, theoretisch machbar

2. Methodische Machbarkeit
   - Forschungsmethode: [Methodenname] ist die Standardmethode zur Lösung von [Forschungsfrage]
   - Datenerhebung: [Datenquelle] hat die Datenlieferung bestätigt, oder [Datenerhebungsmethode] wurde als durchführbar validiert
   - Analysetechnik: [Analysewerkzeug] wird beherrscht, oder [Schulungskurs] wurde geplant
   - Machbarkeitsfazit: Die Methode ist ausgereift, Daten sind verfügbar, Technik beherrschbar, methodisch machbar

3. Ressourcen-Machbarkeit
   - Zeit: Forschungszeitraum [X Monate], detaillierter Zeitplan wurde erstellt
   - Finanzierung: [Finanzierungsquelle] ist gesichert, oder keine zusätzliche Finanzierung erforderlich
   - Ausrüstung: [Ausrüstungsname] ist vorhanden, oder [Ausrüstungsquelle] wurde bestätigt
   - Personal: Betreuer [Name] ist in diesem Bereich erfahren, [Mitarbeiter] wurde kontaktiert und stimmt der Zusammenarbeit zu
   - Daten: [Datenzugangskanal] wurde bestätigt, oder [Befragungsteilnehmer] haben der Teilnahme zugestimmt
   - Machbarkeitsfazit: Ressourcen sind ausreichend, oder Alternativen sind vorhanden, ressourcenbezogen machbar

4. Persönliche Machbarkeit
   - Wissensbasis: [Kursname] wurde belegt, [theoretische Grundlage] vorhanden
   - Fähigkeiten: [Fähigkeit] wird beherrscht, [Schulung/Kurs] wurde absolviert
   - Betreuerunterstützung: Der Forschungsschwerpunkt des Betreuers ist [Richtung], eng mit dieser Forschung verknüpft
   - Zeitaufwand: Pro Woche [X Stunden] investierbar, detaillierter Zeitmanagementplan erstellt
   - Machbarkeitsfazit: Persönliche Voraussetzungen erfüllen die Forschungsanforderungen, persönlich machbar

Gesamtfazit: Diese Forschung ist in den vier Dimensionen Theorie, Methode, Ressourcen und Persönlichkeit machbar.
`

### 3. Beispiel der Machbarkeitsanalyse

**Beispiel: Forschung zur Online-Bildungsinteraktion**

`
1. Theoretische Machbarkeit
   - Theoretische Grundlage: Sozialer Konstruktivismus (Vygotsky) und Kognitive Lasttheorie (Sweller)
     wurden breit in der Bildungstechnologieforschung angewandt und bieten eine solide theoretische
     Grundlage für diese Forschung.
   - Forschungslücke: Bisherige Forschungen konzentrieren sich hauptsächlich auf das Funktionsdesign
     von Online-Lernplattformen, aber es mangelt an systematischen Studien darüber, wie
     Interaktionsmechanismen die Lernergebnisse beeinflussen.
   - Machbarkeitsfazit: Der theoretische Rahmen ist ausgereift, die Forschungshypothesen sind ableitbar,
     theoretisch machbar.

2. Methodische Machbarkeit
   - Forschungsmethode: Quasi-experimentelles Design (Experimental- vs. Kontrollgruppe) ist die
     Standardmethode zur Prüfung von Kausalzusammenhängen und für diese Forschungsfrage geeignet.
   - Datenerhebung: Eine Kooperation mit der Online-Bildungsplattform XX wurde vereinbart;
     Zugang zu Lernprotokolldaten möglich; Fragebögen werden über die Plattform verteilt,
     erwartete Rücklaufquote >70%.
   - Analysetechnik: SPSS und Mplus werden beherrscht; Schulung zu AMOS-Strukturgleichungsmodellen
     ist geplant.
   - Machbarkeitsfazit: Die Methode ist ausgereift, Daten sind verfügbar, Technik beherrschbar,
     methodisch machbar.

3. Ressourcen-Machbarkeit
   - Zeit: Forschungszeitraum 12 Monate (2023.9–2024.8), detaillierter Zeitplan wurde erstellt.
   - Finanzierung: Förderung durch den XX-Fonds (50.000 Yuan) bewilligt, deckt Kosten für
     Fragebögen, Interviews und Schulungen ab.
   - Ausrüstung: Computer und SPSS-Software vorhanden, keine zusätzliche Ausrüstung erforderlich.
   - Personal: Betreuer Professor XX ist auf Bildungstechnologie spezialisiert, über 10 einschlägige
     Publikationen; Kooperation mit der Fakultät für Erziehungswissenschaft der Universität XX
     wurde vereinbart, die Kontrollgruppenklassen zur Verfügung stellt.
   - Daten: Die Plattform hat eine Datenvereinbarung unterzeichnet, die Ethikkommission hat
     zugestimmt.
   - Machbarkeitsfazit: Ressourcen sind ausreichend, machbar.

4. Persönliche Machbarkeit
   - Wissensbasis: Bildungspsychologie, Bildungsstatistik und Bildungstechnologie wurden belegt;
     solide theoretische Grundlage vorhanden.
   - Fähigkeiten: Fortgeschrittenes SPSS-Training absolviert; deskriptive Statistik,
     Inferenzstatistik und Regressionsanalyse beherrscht; Strukturgleichungsmodelle werden
     gerade erlernt.
   - Betreuerunterstützung: Professor XX ist ein renommierter Wissenschaftler im Bereich
     Bildungstechnologie; der Forschungsschwerpunkt steht in engem Zusammenhang mit dieser
     Forschung; Betreuung wurde zugesagt.
   - Zeitaufwand: 20 Stunden pro Woche investierbar; detaillierter Zeitmanagementplan wurde erstellt.
   - Machbarkeitsfazit: Persönliche Voraussetzungen erfüllen die Forschungsanforderungen,
     persönlich machbar.

Gesamtfazit: Diese Forschung ist in den vier Dimensionen Theorie, Methode, Ressourcen und
Persönlichkeit machbar und kann planmäßig durchgeführt werden.
`

## Risikomanagement

### 1. Identifikation häufiger Risiken

**Datenrisiken**:
- Risiko: Schwierigkeiten bei der Datenerhebung (niedrige Rücklaufquote, unzureichende Stichprobe)
- Risiko: Datenqualitätsprobleme (viele fehlende Werte, viele Ausreißer)
- Risiko: Änderungen der Datenzugriffsrechte (Rückzug des Kooperationspartners, Plattformabschaltung)

**Methodische Risiken**:
- Risiko: Methode nicht anwendbar (Hypothese nicht bestätigt, schlechte Modellanpassung)
- Risiko: Technische Schwierigkeiten (Softwarefehler, Analysefehlschlag)
- Risiko: Zeitmangel (zu zeitaufwändiges Erlernen neuer Methoden)

**Ressourcenrisiken**:
- Risiko: Unzureichende Finanzierung (Budgetüberschreitung, zusätzliche Kosten)
- Risiko: Geräteausfall (Computerbeschädigung, Softwareablauf)
- Risiko: Personalveränderungen (Betreuer auf Dienstreise, Ausscheiden eines Kooperationspartners)

**Persönliche Risiken**:
- Risiko: Gesundheitsprobleme (Krankheit, Erschöpfung)
- Risiko: Zeitkonflikte (Lehrveranstaltungen, Praktika, Prüfungen)
- Risiko: Motivationsmangel (Leistungsplateau, Prokrastination)

**Externe Risiken**:
- Risiko: Politische Veränderungen (Änderungen der Hochschulanforderungen, neue ethische Vorschriften)
- Risiko: Unvorhergesehene Ereignisse (Pandemie, Naturkatastrophen)
- Risiko: Technologische Veränderungen (Plattformaktualisierungen, Änderungen des Datenformats)

### 2. Risikobewertungsmatrix

`
Risikobewertungsmatrix

Risikoposten          Eintrittswahr-  Auswirkung   Risiko-   Gegenmaßnahme
                      scheinlichkeit  (1-5)        stufe
                      (1-5)
------------------------------------------------------------
Niedrige Rücklaufquote     3            4          Hoch      Multi-Kanal-Verteilung, Anreize
Unzureichende Stichprobe   2            5          Hoch      Erweiterung des Stichprobenrahmens, Designanpassung
Methode nicht anwendbar    2            4          Mittel    Alternativmethoden, Vorversuch
Budgetüberschreitung       2            3          Mittel    Budgetpuffer, Nachfinanzierungsantrag
Betreuer auf Dienstreise   3            2          Niedrig   Online-Kommunikation, vorzeitige Terminplanung
Gesundheitsprobleme        2            3          Mittel    Gesundheitsmanagement, Zeitpuffer einplanen
Politische Veränderungen   1            4          Niedrig   Aktuelle Entwicklungen verfolgen, flexibel anpassen
`

### 3. Risikostrategien

**Präventionsstrategien (Eintrittswahrscheinlichkeit senken)**:
- Datenerhebung: Fragebogen vorab testen, Multi-Kanal-Verteilung, Erinnerungen einrichten
- Stichprobe: Stichprobenrahmen erweitern, Mindeststichprobenstandard festlegen
- Methodenanwendbarkeit: Literaturverifizierung, Vorversuch, Experten konsultieren
- Finanzierung: Detailliertes Budget, 10–20% Puffer einplanen
- Gesundheit: Regelmäßiger Tagesablauf, regelmäßige Bewegung, flexible Zeit einplanen

**Minderungsstrategien (Auswirkungen reduzieren)**:
- Niedrige Rücklaufquote: Stichprobe erhöhen, Gewichtungsanpassung verwenden
- Methode nicht anwendbar: Alternativmethoden vorbereiten, Modell vereinfachen
- Budgetüberschreitung: Kernausgaben priorieren, Zusatzfinanzierung beantragen
- Betreuer auf Dienstreise: Online-Meetings, Schlüsselfragen vorab besprechen
- Gesundheitsprobleme: Abschnittsweise vorgehen, Kommilitonen um Hilfe bitten

**Notfallstrategien (nach Risikoeintritt)**:
- Rücklaufquote <50%: Stichprobenrahmen erweitern, auf qualitative Forschung umstellen
- Unzureichende Stichprobe: Bootstrap, Bayes'sche Verfahren verwenden
- Methode vollständig gescheitert: Auf deskriptive Forschung, Fallstudien umsteigen
- Finanzierung aufgebraucht: Notfallförderung beantragen, Betreuerunterstützung suchen
- Langzeitkrankheit: Fristverlängerung beantragen, Forschungsplan anpassen

**Transferstrategien**:
- Datenerhebung: An professionelle Institutionen delegieren (Finanzierung erforderlich)
- Datenanalyse: Statistische Beratung in Anspruch nehmen (an Hochschulen meist kostenlos)
- Technische Probleme: Technischen Support-Dienst erwerben

### 4. Beispiel eines Risikomanagements

**Beispiel: Niedrige Rücklaufquote**

`
Risiko: Rücklaufquote der Befragung niedriger als erwartet (<50%)

Präventionsmaßnahmen:
- Fragebogendesign: Vorabtest mit 10 Personen, Fertigstellung innerhalb von 5 Minuten gewährleisten
- Verteilungskanäle: E-Mail + WeChat + Lehrveranstaltung + Plattform-Push, Multi-Kanal-Abdeckung
- Anreize: Die ersten 100 Teilnehmer erhalten eine Belohnung (z.B. Lernmaterialien, kleine Geschenke)
- Erinnerungsmechanismus: 3, 7 und 14 Tage nach Verteilung Erinnerungen senden

Notfallmaßnahmen:
- Rücklaufquote 40–50%: Stichprobenrahmen erweitern, 200 Personen hinzufügen
- Rücklaufquote 30–40%: Anreize erhöhen, auf Verlosung umstellen (100% Gewinnchance)
- Rücklaufquote <30%: Auf qualitative Forschung umstellen (20 Tiefeninterviews)
- Rücklaufquote <20%: Mit Betreuer besprechen, Forschungsdesign anpassen

Überwachungsindikatoren:
- Tägliche Rücklaufanzahl
- Trend der Rücklaufquote
- Repräsentativität der Stichprobe (Vergleich mit Grundgesamtheit)
`

### 5. Formulierung des Risikomanagements im Exposé

`
【Risikomanagement】

Diese Forschung identifiziert die folgenden Hauptrisiken und hat entsprechende Maßnahmen
entwickelt:

1. Risiko der Datenerhebung
   Risikobeschreibung: Die Rücklaufquote der Befragung könnte unter den Erwartungen liegen.
   Präventionsmaßnahmen: Multi-Kanal-Verteilung (E-Mail + WeChat + Lehrveranstaltung),
   Erinnerungen einrichten, Anreize bieten.
   Notfallmaßnahmen: Bei Rücklaufquote <50%: Stichprobenrahmen erweitern oder Anreize erhöhen;
   bei <30%: Umstellung auf qualitative Forschung (Tiefeninterviews).

2. Methodisches Risiko
   Risikobeschreibung: Das Strukturgleichungsmodell könnte eine schlechte Anpassung aufweisen.
   Präventionsmaßnahmen: Modell im Vorversuch validieren, Statistikexperten konsultieren.
   Notfallmaßnahmen: Bei schlechter Modellanpassung: alternative Verfahren (Regressionsanalyse,
   Varianzanalyse) verwenden oder Modell vereinfachen.

3. Zeitrisiko
   Risikobeschreibung: Die Datenerhebung könnte sich verzögern und die nachfolgende Analyse
   beeinträchtigen.
   Präventionsmaßnahmen: Detaillierter Zeitplan, 2 Monate Zeitpuffer einplanen.
   Notfallmaßnahmen: Bei Verzögerung >1 Monat: Fristverlängerung beantragen oder Analyse
   vereinfachen.

4. Ressourcenrisiko
   Risikobeschreibung: Das Budget könnte überschritten werden.
   Präventionsmaßnahmen: Detailliertes Budget, 20% Puffer einplanen, Kernausgaben priorieren.
   Notfallmaßnahmen: Bei Überschreitung: Zusatzfinanzierung beantragen oder Betreuerunterstützung
   suchen.

Durch die oben genannten Maßnahmen kann diese Forschung potenzielle Risiken wirksam bewältigen
und den erfolgreichen Abschluss der Forschung gewährleisten.
`

## Strukturvorlage für das Exposé

### Vollständige Struktur

`
1. Forschungshintergrund und -bedeutung
   1.1 Praktischer Hintergrund (woher kommt das Problem)
   1.2 Theoretischer Hintergrund (akademischer Kontext)
   1.3 Forschungsbedeutung (theoretisch + praktisch)

2. Literaturübersicht
   2.1 Definition der Kernkonzepte
   2.2 Stand der Forschung im In- und Ausland
   2.3 Forschungsbewertung (Lücke)

3. Forschungsziele und -inhalte
   3.1 Forschungsziele (konkret, messbar)
   3.2 Forschungsinhalte (Punkt für Punkt entfalten)
   3.3 Forschungshypothesen (falls zutreffend)

4. Forschungsmethodik und methodische Roadmap
   4.1 Forschungsmethode (Methodologie + konkrete Methode)
   4.2 Methodische Roadmap (Visualisierung)
   4.3 Forschungswerkzeuge (Fragebögen, Skalen, Geräte)
   4.4 Stichprobendesign (Grundgesamtheit, Stichprobe, Stichprobenmethode)

5. Machbarkeitsanalyse
   5.1 Theoretische Machbarkeit
   5.2 Methodische Machbarkeit
   5.3 Ressourcen-Machbarkeit
   5.4 Persönliche Machbarkeit

6. Risikomanagement
   6.1 Risikoidentifikation
   6.2 Risikobewertung
   6.3 Gegenstrategien

7. Forschungsplan und Zeitplan
   7.1 Phaseneinteilung
   7.2 Meilensteine
   7.3 Gantt-Diagramm

8. Erwartete Ergebnisse und Innovationspunkte
   8.1 Erwartete Ergebnisse (Arbeit, Patent, Software usw.)
   8.2 Innovationspunkte (Theorie, Methode, Anwendung)

9. Literaturverzeichnis
`

### Empfohlene Wortverteilung

| Abschnitt | Bachelor (3.000–5.000 Wörter) | Master (8.000–15.000 Wörter) | Promotion (20.000–30.000 Wörter) |
|-----------|-------------------------------|-------------------------------|----------------------------------|
| Forschungshintergrund | 500–800 | 1.000–2.000 | 2.000–3.000 |
| Literaturübersicht | 1.000–1.500 | 3.000–5.000 | 8.000–12.000 |
| Forschungsziele | 300–500 | 500–1.000 | 1.000–2.000 |
| Forschungsmethodik | 500–800 | 1.500–2.500 | 3.000–5.000 |
| Machbarkeitsanalyse | 300–500 | 500–1.000 | 1.000–2.000 |
| Risikomanagement | 200–300 | 300–500 | 500–1.000 |
| Zeitplanung | 200–300 | 300–500 | 500–1.000 |
| Erwartete Ergebnisse | 200–300 | 300–500 | 500–1.000 |

## Häufige Probleme und Lösungen

### F: Methodische Roadmap zu einfach / zu komplex?
- Zu einfach: Teilprozesse, Entscheidungspunkte, zyklische Rückkopplung hinzufügen
- Zu komplex: Gleichartiges zusammenfassen, auf hoher Ebene abstrahieren, Details in Anhänge

### F: Machbarkeitsanalyse wirkt wie Eigenlob?
- Objektive Darstellung: „ist vorhanden", „ist bestätigt" statt „ich bin sehr begabt"
- Einschränkungen anerkennen: „Obwohl in X wenig Erfahrung vorhanden ist, wurde dies durch Y ausgeglichen"
- Belege anführen: Kursnoten, Schulungszertifikate, Publikationen des Betreuers

### F: Risikomanagement wirkt wie Formsache?
- Konkretisieren: Nicht „könnte Probleme geben", sondern „Rücklaufquote könnte <50% sein"
- Quantifizieren: Eintrittswahrscheinlichkeit, Auswirkung, Schwellenwerte
- Umsetzbar: Nicht „Management verbessern", sondern „Erinnerungs-E-Mail nach 3 Tagen senden"

### F: Innovationspunkte reichen nicht?
- Neu definieren: Nicht „völlig neu", sondern „neue Kombination", „neue Anwendung", „neue Perspektive"
- Vergleichende Erläuterung: Konkrete Unterschiede zu bestehender Forschung
- Bescheidene Formulierung: „versuchen", „erkunden", „verfeinern" statt „erstmals", „revolutionär"

## Empfohlene Ressourcen

1. **Werkzeuge für methodische Roadmaps**:
   - ProcessOn: www.processon.com
   - Draw.io: app.diagrams.net
   - Lucidchart: www.lucidchart.com

2. **Projektmanagement-Werkzeuge**:
   - GanttProject: Kostenloses Gantt-Diagramm
   - Microsoft Project: Professionelles Projektmanagement
   - Excel: Einfaches Gantt-Diagramm (bedingte Formatierung)

3. **Risikobewertungswerkzeuge**:
   - Risikomatrix-Vorlage: Excel-Vorlage
   - Monte-Carlo-Simulation: @RISK, Crystal Ball

4. **Empfohlene Fachbücher**:
   - *Research Design and Methods* (Bordens & Abbott)
   - *Leitfaden für das Verfassen von Abschlussarbeiten* (Pan Maoyuan)
   - *How to Write a Research Proposal* (Locke et al.)


﻿# Leitfaden für die Überarbeitung und Überprüfung wissenschaftlicher Arbeiten

## Selbstüberarbeitung

### 1. Phasen der Überarbeitung

**Abkühlungsphase (1–3 Tage)**:
- Nach Fertigstellung des Erstentwurfs 1–3 Tage ruhen lassen
- Grund: Distanz erzeugt Objektivität, Probleme werden leichter erkannt
- Aktivitäten: Literatur lesen, Daten auswerten, ausruhen

**Erste Runde: Strukturelle Überarbeitung (makroskopisch)**
- Logikkette prüfen: Einleitung → Methode → Ergebnisse → Diskussion → Fazit
- Kapitelbalance prüfen: Ist die Wortzahl jedes Kapitels angemessen?
- Überschriftenhierarchie prüfen: Ist sie klar und einheitlich?
- Übergänge prüfen: Sind Kapitel und Abschnitte untereinander kohärent?

**Zweite Runde: Inhaltliche Überarbeitung (mesoskopisch)**
- Argumente prüfen: Hat jeder Absatz eine klare These?
- Belege prüfen: Stützen die Belege die These?
- Argumentation prüfen: Ist die Logik stringent?
- Wiederholungen prüfen: Gibt es redundante Inhalte?
- Auslassungen prüfen: Fehlen wichtige Inhalte?

**Dritte Runde: Sprachliche Überarbeitung (mikroskopisch)**
- Grammatik prüfen: Subjekt-Verb-Kongruenz, Tempus, Artikel
- Rechtschreibung prüfen: Tippfehler, Fachbegriffe
- Zeichensetzung prüfen: Mischung deutscher und englischer Satzzeichen
- Formatierung prüfen: Schriftart, Schriftgröße, Zeilenabstand
- Zitation prüfen: Einheitliches Format, Zuordnung

**Vierte Runde: Feinschliff (Verfeinerung)**
- Abbildungen und Tabellen prüfen: Nummerierung, Beschriftung, Lesbarkeit
- Daten prüfen: Zahlen, Einheiten, Prozentsätze
- Literaturverzeichnis prüfen: Vollständigkeit, Format
- Anhänge prüfen: Nummerierung, Zuordnung

### 2. Checkliste für die Selbstüberarbeitung

**Struktur-Checkliste**:
- [ ] Enthält die Zusammenfassung Forschungsziel, Methode, Ergebnisse und Fazit?
- [ ] Geht die Einleitung vom Makro- zum Mikroniveau und endet mit einer klaren Forschungsfrage?
- [ ] Ist die Literaturübersicht klar kategorisiert und verbindet Beschreibung mit Bewertung?
- [ ] Ist der Methodenabschnitt so detailliert, dass er reproduzierbar ist?
- [ ] Präsentiert der Ergebnisteil objektiv ohne Interpretation?
- [ ] Interpretiert der Diskussionsteil die Ergebnisse, vergleicht mit der Literatur und weist auf Einschränkungen hin?
- [ ] Beantwortet das Fazit die Forschungsfrage und führt keine neuen Inhalte ein?
- [ ] Ist das Verhältnis der Kapitel angemessen (Einleitung 10%, Literatur 20%, Methode 15%, Ergebnisse 20%, Diskussion 25%, Fazit 10%)?

**Inhalts-Checkliste**:
- [ ] Hat jeder Absatz einen Themensatz?
- [ ] Gibt es Übergänge zwischen den Absätzen?
- [ ] Gibt es irrelevante Inhalte?
- [ ] Gibt es wiederholte Inhalte?
- [ ] Fehlen wichtige Quellen?
- [ ] Sind die Daten aktuell?
- [ ] Sind die Schlussfolgerungen überzogen?

**Sprach-Checkliste**:
- [ ] Gibt es umgangssprachliche Ausdrücke?
- [ ] Gibt es vage Formulierungen?
- [ ] Gibt es absolute Aussagen?
- [ ] Gibt es verschachtelte Sätze (>30 Wörter)?
- [ ] Wird der Passiv zu häufig verwendet?
- [ ] Gibt es sprachliche Fehler (z.B. Germanismen)?
- [ ] Sind die Fachbegriffe einheitlich?

### 3. Lautlese-Methode

**Methode**:
- Den gesamten Text laut lesen
- Alternativ: Text-to-Speech-Werkzeug verwenden (Word-Lesefunktion, Edge-Browser)

**Erkannte Probleme**:
- Sperrige Sätze: Klingt beim Lesen unangenehm, müssen umgeschrieben werden
- Wiederholte Wörter: Gleiches Wort tritt mehrfach hintereinander auf, muss ersetzt werden
- Logische Sprünge: Nach einem Absatz ist der Zusammenhang unklar
- Tonfall-Probleme: Zu aggressiv, zu zaghaft, nicht objektiv

### 4. Umgekehrte Gliederungsmethode

**Methode**:
- Nach dem Lesen eines Absatzes den Kerninhalt in einem Satz zusammenfassen
- Auf Post-its oder am Rand notieren
- Nach Abschluss nur die Zusammenfassungssätze lesen

**Prüfung**:
- Bilden die Zusammenfassungssätze eine logische Kette?
- Gibt es Zusammenfassungssätze, die nicht zur Überschrift passen?
- Gibt es aufeinanderfolgende Absätze mit inhaltlich identischen Zusammenfassungen?
- Gibt es Absätze, die sich nicht zusammenfassen lassen (die Inhalte sind unstrukturiert)?

## Umgang mit Betreuer-Feedback

### 1. Die richtige Einstellung zum Feedback

**Positive Einstellung**:
- Der Betreuer ist ein Helfer, kein Kritiker
- Feedback ist eine kostenlose Expertenberatung
- Jede Überarbeitung verbessert die Qualität der Arbeit
- Wenn der Betreuer etwas „nicht versteht", verstehen es die Leser oft auch nicht

**Zu vermeidende Einstellungen**:
- Defensiv: „Ich habe nichts falsch gemacht, der Betreuer hat es nicht verstanden"
- Widerständig: „So viele Änderungen – dann kann ich auch neu schreiben"
- Vermeidend: „Ich kümmere mich später darum"
- Selektiv: „Nur die einfachen Änderungen, die schwierigen ignoriere ich"

### 2. Feedback-Typen und Umgang damit

**Typ 1: Inhaltliches Richtungsfeedback**
- Merkmale: „Empfehlung zur Anpassung des Forschungsrahmens", „Empfehlung zur Ergänzung der XX-Theorie"
- Vorgehensweise: Persönliches Gespräch mit dem Betreuer, genaue Richtung klären, Überarbeitungsplan erstellen
- Hinweis: Kann umfangreiches Umschreiben erfordern, frühzeitig bearbeiten

**Typ 2: Inhaltliches Detailfeedback**
- Merkmale: „Diese Argumentation ist nicht ausreichend", „Empfehlung zur Ergänzung von XX-Daten"
- Vorgehensweise: Literatur, Daten oder Fallbeispiele ergänzen, oder die These entfernen
- Hinweis: Datenquellen überprüfen, Zuverlässigkeit sicherstellen

**Typ 3: Strukturelles Feedback**
- Merkmale: „Empfehlung, Kapitel 2 und 3 zusammenzulegen", „Empfehlung zur Anpassung der Kapitelreihenfolge"
- Vorgehensweise: Plan für die Strukturanpassung erstellen, mit dem Betreuer abstimmen, dann umsetzen
- Hinweis: Gliederungsansicht verwenden, um Inhaltsverlust zu vermeiden

**Typ 4: Sprachliches Feedback**
- Merkmale: „Unklarer Ausdruck", „Empfehlung zur Straffung", „Grammatikfehler"
- Vorgehensweise: Punkt für Punkt korrigieren, ggf. Muttersprachler oder professionelle Überarbeitung hinzuziehen
- Hinweis: Einheitlichen Korrekturstil beibehalten, Inkonsistenzen vermeiden

**Typ 5: Formatierungsfeedback**
- Merkmale: „Abbildungen/Tabellen nicht normgerecht", „Zitationsfehler"
- Vorgehensweise: Nach der Hochschulvorlage prüfen, Punkt für Punkt korrigieren
- Hinweis: Formatvorlagen verwenden, manuelle Anpassungen vermeiden

### 3. Ablauf der Feedback-Bearbeitung

**Schritt 1: Feedback strukturieren**
- Feedback kategorisieren: Richtung / Inhalt / Struktur / Sprache / Format
- Priorität festlegen: Muss geändert / Sollte geändert / Kann geändert werden
- Schwierigkeit einschätzen: Einfach / Mittel / Schwierig
- Tabelle erstellen: Feedback-Inhalt | Typ | Priorität | Schwierigkeit | Änderungsplan | Status

**Schritt 2: Plan erstellen**
- Nach Priorität sortieren: Zuerst Richtung, dann Inhalt, zuletzt Format
- Schwierigkeit abwechseln: Einfach + Schwierig im Wechsel, um Überlastung zu vermeiden
- Zeit festlegen: Zeit für jeden Feedback-Typ einplanen
- Puffer einplanen: 20% der Gesamtzeit für Unvorhergesehenes

**Schritt 3: Änderungen durchführen**
- Fokussierung auf einen Typ: Nur einen Feedback-Typ gleichzeitig bearbeiten
- Abschluss markieren: Nach der Änderung als „erledigt" kennzeichnen
- Probleme dokumentieren: Was nicht geändert werden konnte, mit Grund festhalten
- Versionen sichern: Jede Überarbeitungsrunde als neue Version speichern

**Schritt 4: Überprüfung und Bestätigung**
- Abgleich mit dem Feedback: Punkt für Punkt prüfen, ob geändert
- Kreuzvalidierung: Haben die Änderungen neue Probleme verursacht?
- Gesamtprüfung: Ist der Text nach den Änderungen kohärent?
- Beim Betreuer einreichen: Mit Überarbeitungsbeschreibung

### 4. Verfassen der Überarbeitungsbeschreibung

`
Überarbeitungsbeschreibung

Sehr geehrte/r Betreuer/in,

vielen Dank für Ihre wertvollen Anmerkungen. Ich habe die folgenden Änderungen
vorgenommen:

I. Richtungsänderungen (3 Stück)
1. Zur Anpassung des Forschungsrahmens
   - Ursprüngliches Problem: Der Forschungsrahmen war zu weit gefasst
   - Änderungsplan: Fokussierung auf die Variable XX, Entfernung der Variable YY
   - Änderungsort: Kapitel 1 Abschnitt 3, Kapitel 3
   - Status: Erledigt

2. ...

II. Inhaltliche Änderungen (5 Stück)
1. Zur Ergänzung der XX-Theorie
   - Ursprüngliches Problem: In der Literaturübersicht fehlte die Perspektive der XX-Theorie
   - Änderungsplan: Ergänzung der XX-Theorie (Kapitel 2 Abschnitt 2, 500 neue Wörter)
   - Neue Quellen: Smith (2020), Jones (2021)
   - Status: Erledigt

2. ...

III. Strukturelle Änderungen (2 Stück)
...

IV. Sprachliche Änderungen (8 Stück)
...

V. Formatierungsänderungen (10 Stück)
...

Nicht geänderte Anmerkungen und Begründungen:
1. Zur Entfernung des Kapitels XX: Dieses Kapitel bildet die Grundlage für die
   nachfolgende Analyse, Beibehaltung empfohlen
   (Persönlich mit dem Betreuer besprochen, Zustimmung zur Beibehaltung erhalten)

2. ...

Der Text wurde nach den Änderungen aktualisiert. Bitte prüfen Sie ihn.

Mit freundlichen Grüßen
XXX
Datum: TT.MM.JJJJ
`

## Peer-Review

### 1. Auswahl der Gutachter

**Kriterien**:
- Gleiches Fachgebiet: Ähnliche Forschungsrichtung, kann den Inhalt verstehen
- Verschiedene Perspektiven: Unterschiedliche methodologische und theoretische Orientierung, neue Blickwinkel
- Erfahrung: Fortgeschrittene Studierende, Postdocs, Nachwuchswissenschaftler
- Vertrauenswürdig: Vertraulich, konstruktiv, keine Plagiate

**Kanäle**:
- Kommilitonen: Höheres Semester, Mitstudierende
- Akademisches Netzwerk: Konferenzkontakte, soziale Medien
- Schreibgruppen: Gruppenmitglieder mit regelmäßigem Austausch
- Professionelle Dienste: Manche Hochschulen bieten Schreibzentren an

### 2. Anfrage für das Peer-Review

**E-Mail-Vorlage**:
`
Betreff: Anfrage zur Begutachtung – [Arbeitstitel]

Sehr geehrte/r Frau/Herr XX,

ich bin Studierender im Studiengang XX an der Universität XX und verfasse
derzeit eine Master-/Doktorarbeit zum Thema [Forschungsthema].

Mir ist bekannt, dass Sie sich intensiv mit [Fachgebiet] beschäftigen, und
ich möchte Sie höflich einladen, meine Arbeit zu begutachten. Die Arbeit
befasst sich hauptsächlich mit [Kernfrage] und verwendet die Methode [Methode].
Erste Ergebnisse deuten auf [Hauptergebnis] hin.

Falls es Ihnen möglich ist, würde ich mich über Ihr Feedback bis zum [Datum]
freuen.
Der Schwerpunkt der Begutachtung liegt auf:
1. Ist der Forschungsrahmen angemessen?
2. Ist der Methodenteil klar und reproduzierbar?
3. Ist die Argumentationslogik stringent?
4. Ist der sprachliche Ausdruck präzise?

Die Arbeit umfasst ca. [X Wörter] und wird als Word-Dokument gesendet.

Vielen Dank für Ihre Zeit und Ihr Interesse!

Mit freundlichen Grüßen
XXX
[Kontaktinformationen]
`

### 3. Anleitung für Gutachter

**Hinweise für Gutachter**:
`
Vielen Dank, dass Sie sich bereit erklärt haben, meine Arbeit zu begutachten!
Nachfolgend finden Sie die Begutachtungsanleitung:

Informationen zur Arbeit:
- Titel: [Titel]
- Art: Master-/Doktorarbeit
- Stadium: Erstentwurf / Überarbeitete Fassung / Vorabgabefassung
- Umfang: ca. [X Wörter]

Schwerpunkte der Begutachtung (nach Priorität):
1. Logische Struktur: Ist die Kapitelfolge sinnvoll? Sind die Übergänge fließend?
2. Argumentationsqualität: Sind die Thesen klar? Sind die Belege ausreichend?
   Ist die Argumentation stringent?
3. Methodenbeschreibung: Ist sie so detailliert, dass sie reproduzierbar ist?
   Gibt es Lücken?
4. Literaturübersicht: Ist sie umfassend? Sind die Kategorien sinnvoll?
   Ist die kritische Bewertung ausreichend?
5. Sprachlicher Ausdruck: Gibt es Unklarheiten, Redundanzen oder Umgangssprache?
6. Formatvorgaben: Sind Abbildungen, Zitationen und Literaturverzeichnis korrekt?

Feedback-Form:
- Gesamtbewertung (200–500 Wörter)
- Punktuelle Anmerkungen (nach Kapiteln oder nach Typ)
- Prioritätskennzeichnung (hoch/mittel/niedrig)

Frist: [Datum]
Rücksendung: E-Mail / persönlich / Gespräch

Vielen Dank nochmals!
`

### 4. Umgang mit Peer-Review-Kommentaren

**Prinzipien**:
- Jede Anmerkung verdient Beachtung, auch wenn sie nicht übernommen wird
- Die meisten Anmerkungen sollten übernommen werden, besonders wenn sie von mehreren Personen stammen
- Nicht-Übernahme muss gut begründet werden und kann vermerkt werden

**Ablauf**:
1. Alle Anmerkungen sammeln und strukturieren
2. Häufigkeit notieren (von mehreren Personen genannt = wichtig)
3. Überarbeitungsplan erstellen
4. Überarbeitung durchführen
5. Rückmeldung an die Gutachter (Dank + Beschreibung der Überarbeitung)

## Sprachliche Überarbeitung

### 1. Tipps zur Selbstüberarbeitung

**Straffung**:
- Füllwörter entfernen: „sehr", „ziemlich", „eigentlich", „tatsächlich"
- Floskeln entfernen: „Es ist wichtig zu beachten, dass", „Es steht außer Zweifel, dass"
- Wiederholungen entfernen: Im selben Abschnitt Begriffe nicht erneut definieren
- Umgangssprache entfernen: „kriegen", „riesig", „super", „Ding", „Zeug"

**Verstärkung**:
- Verben statt Substantive: „eine Analyse durchführen" → „analysieren"
- Aktiv statt Passiv (angemessen): „Es wurde festgestellt, dass" → „Wir stellten fest, dass"
- Konkret statt Abstrakt: „gute Ergebnisse" → „die Ergebnisse verbesserten sich um 25 %"
- Starke Adjektive statt „sehr + Adjektiv"

**Kohärenz**:
- Übergangswörter einfügen: „Darüber hinaus", „Allerdings", „Daher", „Im Gegensatz dazu"
- Verweiswörter einfügen: „Dieses Ergebnis", „Diese Resultate", „Jener Ansatz"
- Zusammenfassungen einfügen: Satz am Absatzende, Übergangssatz am Kapitelende

### 2. Werkzeugunterstützung

**Grammatikprüfung**:
- Grammarly: Erkennt Grammatik-, Rechtschreib- und Stilfehler
- LanguageTool: Open Source, unterstützt deutsche Oberfläche
- Writefull: Speziell für wissenschaftliches Schreiben, KI-basiert

**Stilprüfung**:
- Hemingway Editor: Erkennt Lesbarkeit, markiert verschachtelte Sätze
- ProWritingAid: Umfassende Stilanalyse

**Terminologieprüfung**:
- Begriffskonsistenz: Suchen und Ersetzen, um Einheitlichkeit sicherzustellen
- Begriffsgenauigkeit: Abgleich mit maßgeblicher Literatur
- Erstmalige Verwendung: Vollständiger Name + Abkürzung

### 3. Professionelle Überarbeitungsdienste

**Anwendungsfälle**:
- Einreichung englischer Arbeiten bei internationalen Fachzeitschriften
- Viele Sprachprobleme, Selbstkorrektur führt nicht zur Verbesserung
- Zeitdruck, schnelle Überarbeitung erforderlich

**Diensttypen**:
- Sprachliche Überarbeitung: Grammatik, Rechtschreibung, Stil (0,03–0,08 €/Wort)
- Tiefenüberarbeitung: Sprache + inhaltliche Vorschläge (0,08–0,15 €/Wort)
- Wissenschaftliche Überarbeitung: Sprache + wissenschaftliche Genauigkeit (0,15–0,30 €/Wort)

**Auswahlkriterien**:
- Qualifikation der Lektoren: Muttersprachler, fachlicher Hintergrund
- Servicegarantie: Qualitätsgarantie, Nachkorrektur
- Vertraulichkeitsvereinbarung: Unterzeichnung einer NDA
- Termintreue: Pünktliche Lieferung

**Bekannte Dienste**:
- Elsevier Language Services
- Springer Nature Author Services
- Wiley Editing Services
- Editage
- Enago

### 4. Prüfung nach der Überarbeitung

**Unbedingt prüfen**:
- Wurden Fachbegriffe fehlerhaft geändert? (Fachbegriffe werden oft zu „gängigen" Wörtern „korrigiert")
- Wurden Daten fehlerhaft geändert? (Zahlen, Einheiten, Prozentsätze)
- Wurden Zitationen fehlerhaft geändert? (Autorennamen, Jahreszahlen, Seitenzahlen)
- Wurde die Logik verändert? (Konjunktionen können die Logik umkehren)
- Wurde die Formatierung geändert? (Position und Nummerierung von Abbildungen/Tabellen)

**Empfehlung**:
- Den Text nach der Überarbeitung selbst durchlesen
- Kernaussagen mit dem Originaltext abgleichen
- Kommilitonen um Gegenlesen bitten

## Versionsverwaltung der Überarbeitungen

### 1. Benennungskonvention

**Datum + Version**:
- Arbeit_20230615_v1.docx
- Arbeit_20230701_v2.docx
- Arbeit_20230715_v3_Final.docx
- Arbeit_20230720_v3_Final_Final.docx (unbedingt vermeiden!)

**Phase + Version**:
- Arbeit_Erstentwurf_v1.docx
- Arbeit_Betreuerueberarbeitung1_v2.docx
- Arbeit_Betreuerueberarbeitung2_v3.docx
- Arbeit_Vorabgaenge_v4.docx
- Arbeit_Endfassung_v5.docx

### 2. Backup-Strategie

**Lokales Backup**:
- Computerfestplatte (Arbeitsversion)
- Externe Festplatte (wöchentliches Backup)
- USB-Stick (Notfall-Backup)

**Cloud-Backup**:
- OneDrive / Google Drive / Dropbox (automatische Synchronisierung)
- Hochschul-Cloud (schnelle Verbindung über das Hochschulnetz)
- E-Mail an sich selbst

**Versionswerkzeuge**:
- Git / GitHub (geeignet für Code + Text)
- Word-Versionsverlauf (automatische Speicherung)
- Manuelle Kopie (einfach und zuverlässig)

### 3. Überarbeitungsprotokoll

**Zu protokollierende Inhalte**:
- Überarbeitungsdatum
- Überarbeitende Person (selbst / Betreuer / Gutachter)
- Überarbeitungstyp (Struktur / Inhalt / Sprache / Format)
- Überarbeitungsort (Kapitel / Seitenzahl)
- Überarbeitungsgrund (Feedback / selbst entdeckt)

**Protokollierungsmethoden**:
- Dokumenteigenschaften: Word → Datei → Informationen → Eigenschaften
- Änderungstagebuch: Separates Dokument
- Kommentare: Word-Kommentarfunktion
- Versionsvergleich: Word → Überprüfen → Vergleichen

## Häufige Probleme

### F: Die Überarbeitung verschlechtert den Text?
- Ursache: Übermäßige Überarbeitung, Verlust des Gesamtüberblicks
- Lösung: Den Text ausdrucken, offline lesen; oder den gesamten Text laut lesen
- Vorbeugung: Jede Überarbeitungsrunde konzentriert sich auf einen Problemkreis

### F: Widersprüchliche Betreuer-Kommentare?
- Lösung: Gespräch mit dem Betreuer, Prioritäten klären
- Strategie: Die eigene Forschungsfrage als Maßstab nehmen, die Auswahl erklären
- Hinweis: Gesprächsergebnis dokumentieren, um wiederholtes Überarbeiten zu vermeiden

### F: Nicht genug Zeit für eine gründliche Überarbeitung?
- Priorität: Struktur > Inhalt > Sprache > Format
- Strategie: Zuerst gravierende Fehler (Logiklücken, Sachfehler), dann Feinschliff (sprachliche Überarbeitung)
- Hilfe: Kommilitonen um Hilfe bei Formatierung und Sprachprüfung bitten

### F: Nach vielen Durchgängen immer noch nicht zufrieden?
- Akzeptanz: Keine Arbeit ist perfekt, nur gut genug
- Maßstab: Abschlussanforderungen erfüllen, Verteidigung bestehen
- Zukunft: Nach dem Abschluss weiter verfeinern, Publikation einreichen

## Empfohlene Ressourcen

1. **Überarbeitungswerkzeuge**:
   - Grammarly: grammarly.com
   - Hemingway Editor: hemingwayapp.com
   - ProWritingAid: prowritingaid.com

2. **Überarbeitungsdienste**:
   - Elsevier Language Services
   - Springer Nature Author Services
   - Editage: www.editage.com

3. **Schreibbücher**:
   - *Das Leben und das Schreiben* (Stephen King)
   - *The Sense of Style* (Steven Pinker)
   - *Stylish Academic Writing* (Helen Sword)

4. **Überarbeitungsstrategien**:
   - *Revision: Geschichte und Technik des Überarbeitens* (Wendy Bishop)
   - *Craft of Research* (Booth et al.)


﻿# Leitfaden für den Schreibprozess wissenschaftlicher Arbeiten

## Phase 1: Themendiagnose

### Prinzipien der Themenauswahl
- **Wertigkeit**: Akademischer oder praktischer Nutzen
- **Innovativität**: Neue Perspektive, neue Methode, neue Materialien, neue Ergebnisse
- **Machbarkeit**: Zeit, Ressourcen und Fähigkeiten müssen übereinstimmen
- **Klarheit**: Konkrete Fragestellung, klare Abgrenzung

### Methoden der Themenauswahl
1. **Literaturgetrieben**: Lücken, Widersprüche und Leerstellen in der Forschung entdecken
2. **Fragegetrieben**: Aus der Praxis aufgetretene Probleme
3. **Methodengetrieben**: Neue Methode auf ein bestehendes Problem anwenden
4. **Interdisziplinär**: Fächerübergreifende Perspektive

### Checkliste für die Themenauswahl
- [ ] Kann die Forschungsfrage in einem Satz klar formuliert werden?
- [ ] Gibt es unterstützende Literatur?
- [ ] Sind Daten/Materialien verfügbar?
- [ ] Ist die Arbeit innerhalb von 6–12 Monaten abschließbar?
- [ ] Stimmt der Betreuer zu?
- [ ] Entspricht das Thema der fachlichen Ausbildungsrichtung?

## Phase 2: Exposé

### Standardstruktur
1. **Forschungshintergrund**
   - Makro-Hintergrund (gesellschaftlich / akademisch)
   - Mikro-Hintergrund (konkretes Phänomen)
   - Problemstellung (vom Hintergrund zur Frage)

2. **Literaturübersicht**
   - Forschungslinien (chronologisch / thematisch / methodisch)
   - Hauptpositionen (kategorisierte Darstellung)
   - Forschungslücken (Gap-Analyse)
   - Positionierung der eigenen Arbeit (Beitragsaussage)

3. **Forschungsinhalte**
   - Forschungsziele (allgemein + spezifisch)
   - Forschungsfragen (3–5 konkrete Fragen)
   - Forschungshypothesen (falls zutreffend)
   - Methodische Roadmap (Flussdiagramm)

4. **Forschungsmethodik**
   - Methodologie (empirisch / normativ / interpretativ)
   - Konkrete Methoden (quantitativ / qualitativ / Mixed-Methods)
   - Datenquellen
   - Analysewerkzeuge

5. **Innovationspunkte**
   - Theoretische Innovation
   - Methodische Innovation
   - Materialbezogene Innovation
   - Perspektivische Innovation

6. **Forschungsplan**
   - Zeitplan (Gantt-Diagramm)
   - Erwartete Ergebnisse
   - Risiken und Gegenmaßnahmen

### Vorbereitung auf die Exposé-Verteidigung
- 10–15-minütige Präsentation
- Antworten vorbereiten: Warum dieses Thema? Warum diese Methode? Ist es machbar?
- Anmerkungen der Gutachter notieren, nach der Sitzung überarbeiten

## Phase 3: Gliederungsentwurf

### Arten von Gliederungen
- **Kapitelstruktur**: Hierarchie der Kapitelüberschriften
- **Logikstruktur**: Fortschreitende Argumentation
- **Kartenstruktur**: Kerninhalt jedes Absatzes

### Elemente der Gliederung
- Kernthese jedes Kapitels
- Belege / Materialien / Daten
- Logischer Zusammenhang mit den vorherigen und nachfolgenden Kapiteln
- Geschätzter Wortumfang

### Prüfung der Gliederung
- [ ] Ist die Logik stimmig?
- [ ] Ist die Hierarchie klar?
- [ ] Sind die Anteile ausgewogen?
- [ ] Gibt es Redundanzen?
- [ ] Werden alle Forschungsfragen abgedeckt?

## Phase 4: Kapitelweises Schreiben

### Empfohlene Schreibreihenfolge
1. **Zuerst schreiben**: Literaturübersicht, Forschungsmethodik (relativ eigenständig)
2. **Danach schreiben**: Datenanalyse, Fallstudien (Kernarbeit)
3. **Anschließend schreiben**: Einleitung, Fazit (erfordert Gesamtperspektive)
4. **Zuletzt**: Zusammenfassung, Schlüsselwörter

### Struktur jedes Kapitels
- **Einleitungsabsatz**: Kapitelziel, Zusammenhang mit der Gesamtarbeit, Vorschau der Kerninhalte
- **Hauptteil**: These + Beleg + Analyse (PEEL-Struktur)
  - Point: These
  - Evidence: Beleg
  - Explanation: Erklärung
  - Link: Rückbezug auf die These / Übergang zur nächsten These
- **Schlussabsatz**: Ergebnisse zusammenfassen, Übergang zum nächsten Kapitel

### Schreibtechniken
- **Tägliches Ritual**: Zu festen Zeiten schreiben, Gewohnheit bilden
- **Erst fertig, dann perfekt**: Der Erstentwurf muss nicht perfekt sein, zuerst aufschreiben
- **Absatzweise**: Einen Absatz nach dem anderen, um den Druck zu verringern
- **TODO-Markierungen**: Unsichere Stellen mit TODO kennzeichnen

## Phase 5: Überarbeitung und Verfeinerung

### Checkliste für die Selbstprüfung
- [ ] Sind die Thesen klar?
- [ ] Sind die Belege ausreichend?
- [ ] Ist die Logik stringent?
- [ ] Ist der sprachliche Ausdruck präzise?
- [ ] Ist die Formatierung normgerecht?
- [ ] Sind die Zitate vollständig?

### Ebenen der Überarbeitung
1. **Makroebene**: Strukturanpassung, Kapitel hinzufügen/entfernen, Logik umstrukturieren
2. **Mesoebene**: Absätze umordnen, Übergänge optimieren, Argumentation stärken
3. **Mikroebene**: Wörter und Sätze polieren, Zeichensetzung vereinheitlichen, Format angleichen

### Umgang mit Betreuer-Feedback
- Zwischen „muss geändert" und „sollte geändert werden" unterscheiden
- Unklarstellen aktiv ansprechen
- Änderungen nach der Überarbeitung markieren
- Überarbeitungsprotokoll führen

## Phase 6: Formatierung

### Häufige Formatanforderungen
- **Deckblatt**: Einheitliches Hochschulformat
- **Zusammenfassung**: Deutsch und Englisch, 300–500 Wörter
- **Inhaltsverzeichnis**: Automatisch generiert, drei Gliederungsebenen
- **Haupttext**:
  - Schriftart: Times New Roman / Arial
  - Schriftgröße: 12 Pt
  - Zeilenabstand: 1,5-fach oder 20 Pt fest
  - Seitenränder: oben/unten 2,54 cm, links/rechts 3,17 cm
- **Abbildungen und Tabellen**:
  - Abbildungsunterschrift unten, Tabellenüberschrift oben
  - Nummerierung: Abb. 1-1, Tab. 2-1
  - Quellenangabe
- **Literaturverzeichnis**:
  - Zitationsstil: APA, MLA, Chicago oder nach Fächernorm
  - Typen: Monografie [M], Zeitschrift [J], Dissertation [D], Konferenz [C], Onlinequelle [EB/OL]

### Satz- und Layoutwerkzeuge
- **Word**: Formatvorlagen, mehrstufige Listen, Beschriftungen
- **LaTeX**: Overleaf, Vorlagen
- **Literaturverwaltung**: Zotero, Mendeley, Citavi, EndNote

## Phase 7: Plagiatsprüfung und Verteidigung

### Vorbereitung auf die Plagiatsprüfung
- **Eigenprüfung**: Turnitin, iThenticate (vom Prüfungssystem der Hochschule vorgegeben)
- **Strategien zur Ähnlichkeitsreduzierung**:
  - Synonyme verwenden (akademische Genauigkeit beibehalten)
  - Satzstruktur ändern (Aktiv-Passiv-Umwandlung)
  - In Abbildungen/Tabellen umwandeln (Text in Tabelle/Diagramm)
  - Zitationen korrekt kennzeichnen (direkte Zitate ausweisen)
- **Hinweise**:
  - Fachbegriffe beibehalten
  - Formelbeschreibungen umformulieren
  - Gesetzestexte / Originalzitate werden nicht geprüft (aber gekennzeichnet)
  - Das Literaturverzeichnis wird nicht geprüft

### Vorbereitung auf die Verteidigung
- **Präsentation (PowerPoint)**:
  - 15–20 Folien
  - Forschungsfrage, Methode, Ergebnisse, Beitrag
  - Schwerpunkt auf Grafiken, Text knapp halten
  - Vortragstext vorbereiten (nicht von den Folien ablesen)

- **Typische Verteidigungsfragen**:
  - Warum haben Sie dieses Thema gewählt?
  - Worin liegt der Innovationsgehalt?
  - Welche Einschränkungen hat die Methode?
  - Wie ist ein bestimmtes Ergebnis zu interpretieren?
  - Was würden Sie bei einer Wiederholung anders machen?

- **Verhalten bei der Verteidigung**:
  - Formelle Kleidung
  - Zeitkontrolle (Vortrag 15–20 Minuten)
  - Kritik gelassen annehmen
  - Änderungswünsche notieren

### Nach der Verteidigung
- Änderungswünsche zusammenfassen
- Änderungsumfang mit dem Betreuer abstimmen
- Überarbeitete Fassung fristgerecht einreichen
- Abschließende Formatprüfung
- Elektronische und gedruckte Version einreichen
