# Leitfaden für das Verfassen wissenschaftlicher Arbeiten in der Informatik (CS)

## Fächerspezifische Merkmale
- Betont Algorithmeninnovation, Systemimplementierung und experimentelle Validierung
- Betont Open-Code, Datensätze und Reproduzierbarkeit
- Konferenzbeiträge > Zeitschriftenartikel (Top-Konferenzen: CVPR/ICML/NeurIPS/SIGCOMM/SOSP)

## Themenauswahl

### Aktuelle Forschungsfelder
1. **Künstliche Intelligenz/Maschinelles Lernen**
   - Effizienzoptimierung großer Modelle (Inferenzbeschleunigung, Modellkompression)
   - Multimodales Lernen (Vision-Sprache-Audio-Fusion)
   - KI-Sicherheit und Ausrichtung (RLHF, Red-Team-Tests)
   - Föderiertes Lernen und Datenschutzberechnung

2. **Systeme und Netzwerke**
   - Cloud-native Systeme (Serverless, Mikroservices)
   - Edge-Computing und IoT
   - Netzwerksicherheit (Zero-Trust-Architektur, Bedrohungserkennung)
   - Konsistenz verteilter Systeme

3. **Softwaretechnik**
   - Code-Intelligenz (Codegenerierung, Defekterkennung)
   - DevOps und AIOps
   - Sicherheit der Software-Lieferkette
   - Low-Code/No-Code-Plattformen

4. **Datenwissenschaft**
   - Zeitreihenanalyse
   - Anwendungen von Graph-Neuronalen Netzen
   - Datengovernance und Qualität
   - Echtzeit-Streaming-Verarbeitung

### Kriterien für die Themenauswahl
- **Innovativität**: Neues Problem oder neue Lösung oder neue Perspektive
- **Machbarkeit**: In 6-12 Monaten umsetzbar
- **Wertigkeit**: Von der akademischen Welt oder der Industrie anerkannt
- **Daten/Code**: Gibt es öffentlich zugängliche Ressourcen?

## Strukturvorlage für wissenschaftliche Arbeiten

### Bachelorarbeit
```
1. Einleitung (Forschungshintergrund, Problemdefinition, Überblick über die Beiträge)
2. Verwandte Arbeiten (Kategorisierte Übersicht, Identifikation von Forschungslücken)
3. Methodik/Systementwurf (Architekturentwurf, Algorithmus-Pseudocode, Flussdiagramme)
4. Experiment/Implementierung (Datensätze, Metriken, Vergleichsexperimente, Ablationsstudien)
5. Ergebnisanalyse (Diagramme, statistische Signifikanz, Fallstudien)
6. Diskussion (Einschränkungen, zukünftige Arbeiten)
7. Fazit
```

### Masterarbeit
Zusätzlich:
- Theoretische Grundlagen (formale Definitionen, Theorembeweise)
- Umfassendere Experimente (mehrere Datensätze, mehrere Basislinien, Langzeitläufe)
- Systembereitstellung (Tests in realen Umgebungen, Nutzerstudien)

## Schreibtipps

### Algorithmenbeschreibung
- Verwendung von Pseudocode (kein tatsächlicher Code)
- Zeit-/Speicherkomplexitätsanalyse
- Konvergenzbeweis (für Optimierungsklassen)

### Versuchsplanung
- Basislinie: Klassische Methoden + SOTA (State-of-the-Art)
- Evaluationsmetriken: Genauigkeit/F1/Latenz/Durchsatz
- Signifikanztest: t-Test oder Wilcoxon-Test
- Ablationsstudie: Notwendigkeit jeder Komponente überprüfen

### Diagrammstandards
- Verwendung von Vektorgrafiken (PDF/SVG)
- Farben, die für Farbenblinde geeignet sind
- Fehlerbalken (bei mehreren Durchläufen)
- Dreiliniertabellen

## Häufige Fehler
1. **Unzureichende Experimente**: Nur 1-2 Datensätze, fehlende Vergleiche
2. **Übertriebene Behauptungen**: "Erstmals vorgeschlagen", "optimal" (muss belegt werden)
3. **Nicht-reproduzierbarer Code**: Fehlende Umgebungskonfiguration, fehlende Zufallszahlen
4. **Aufzählung verwandter Arbeiten**: Kritische Analyse erforderlich
5. **Leere Einleitung**: Konkretisierung, welches Problem gelöst wird

## Empfohlene Werkzeuge
- **Experimentmanagement**: Weights & Biases, MLflow
- **Diagrammerstellung**: Matplotlib, Seaborn, Plotly
- **Codeversionierung**: Git + GitHub
- **Schreiben**: Overleaf (LaTeX)
- **Literaturverwaltung**: Zotero + Better BibTeX

## Einreichungsempfehlungen
- **Konferenzen**: Deadline beachten, 2 Monate vorher fertigstellen
- **Zeitschriften**: Langes Peer-Review, geeignet für systematische Arbeiten
- **arXiv**: Schnelle Veröffentlichung, Prioritätssetzung

## Hinweise zur Plagiatsprüfung
- Codefragmente werden nicht auf Plagiate überprüft (die meisten Systeme)
- Formelbeschreibungen in eigenen Worten
- Algorithmus-Pseudocode kann gewisse Wiederholungen aufweisen
- Beschreibungen der Experimenteinstellungen können standardisiert werden
