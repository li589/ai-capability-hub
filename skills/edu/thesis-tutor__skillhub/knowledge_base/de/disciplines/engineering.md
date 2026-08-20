# Allgemeiner Leitfaden für das Verfassen wissenschaftlicher Arbeiten in den Ingenieurwissenschaften

## Fächerspezifische Merkmale
- Betont problemgetriebene Forschung, Lösungsinnovation und experimentelle Validierung
- Betont Reproduzierbarkeit, vollständige Parameter und Randbedingungen
- Konferenzbeiträge + Zeitschriftenartikel gleichwertig (Top-Konferenzen: IEEE-Serie/ACM-Serie)
- Hohe Anforderungen an die Qualität von Diagrammen (technische Zeichnungen, Simulationsbilder, Referenzfotos)

## Forschungstypen

### 1. Entwurfsforschung
- **Anwendbar für**: Design neuer Systeme/neuer Strukturen/neuer Algorithmen
- **Schlüsselelemente**:
  - Anforderungsanalyse (Funktionen/Leistung/Einschränkungen)
  - Lösungsentwurf (Architektur/Module/Schnittstellen)
  - Machbarkeitsnachweis (Theorie/Simulation/Prototyp)
  - Leistungsbewertung (Vergleich/Benchmark-Tests)
- **Arbeitsstruktur**: Problem→Lösung→Implementierung→Validierung→Diskussion

### 2. Experimentelle Forschung
- **Anwendbar für**: physikalische Experimente, Leistungstests, Zuverlässigkeitsprüfung
- **Schlüsselelemente**:
  - Experimentplattform (Geräte/Umgebung/Bedingungen)
  - Experimentdesign (Variablen/Niveaus/Wiederholungen)
  - Datenerfassung (Sensoren/Abtastrate/Genauigkeit)
  - Ergebnisanalyse (Fehler/Unsicherheit/Statistik)
- **Arbeitsstruktur**: Ziel→Methode→Experiment→Ergebnisse→Analyse

### 3. Simulationsforschung
- **Anwendbar für**: numerische Simulation, Berechnungsanalyse, virtuelle Validierung
- **Schlüsselelemente**:
  - Modellerstellung (geometrisch/physikalisch/mathematisch)
  - Netzerzeugung (Typ/Dichte/Qualität)
  - Randbedingungen (Lasten/Einschränkungen/Kontakt)
  - Lösungseinstellungen (Algorithmus/Konvergenz/Genauigkeit)
  - Ergebnisvalidierung (Experimentvergleich/Literaturvergleich)
- **Arbeitsstruktur**: Problem→Modellierung→Lösung→Validierung→Anwendung

### 4. Optimierungsforschung
- **Anwendbar für**: Parameteroptimierung, Strukturoptimierung, Zeitplanoptimierung
- **Schlüsselelemente**:
  - Optimierungsziel (einzeln/mehrere Ziele)
  - Designvariablen (kontinuierlich/diskret/gemischt)
  - Einschränkungen (Gleichungen/Ungleichungen)
  - Optimierungsalgorithmus (Gradienten/heuristisch/metaheuristisch)
  - Konvergenzanalyse (Iterative Kurven/Stabilität)
- **Arbeitsstruktur**: Problem→Modellierung→Algorithmus→Experiment→Vergleich

## Strukturvorlage für wissenschaftliche Arbeiten

### Bachelorarbeit
```
1. Einleitung
   - Forschungshintergrund (technische Anforderungen, technologischer Status quo)
   - Forschungsstatus im In- und Ausland (kategorisierte Übersicht)
   - Forschungsziel und -bedeutung
   - Organisationsstruktur der Arbeit

2. Theoretische Grundlagen/Verwandte Arbeiten
   - Definition der Kernkonzepte
   - Ableitung grundlegender Theorien
   - Zusammenfassung bestehender Methoden (Vergleichstabelle der Vor- und Nachteile)

3. Lösungsentwurf/Methodenvorschlag
   - Gesamtarchitektur (Systemblockdiagramm)
   - Detaillierter Entwurf (Moduldekompositionsdiagramm)
   - Schlüsselalgorithmen (Pseudocode/Flussdiagramm)
   - Beschreibung der Innovationspunkte

4. Experiment/Simulation/Implementierung
   - Experimentplattform/Simulationsumgebung
   - Parametereinstellungen (vollständige Liste)
   - Experimentdesign (Kontrollgruppendesign)
   - Durchführungsprozess (wichtige Schritte)

5. Ergebnisse und Analyse
   - Hauptergebnisse (Diagramme bevorzugt)
   - Vergleichende Analyse (mit bestehenden Methoden)
   - Parametersensitivitätsanalyse
   - Fehler-/Unsicherheitsanalyse
   - Diskussion (Mechanismuserklärung)

6. Fazit und Ausblick
   - Hauptbeiträge (1.2.3.)
   - Einschränkungen
   - Zukünftige Arbeiten
```

### Master-/Zeitschriftenartikel
Zusätzlich:
- Detailliertere theoretische Ableitungen
- Umfassendere experimentelle Validierung (multiple Szenarien/Datensätze)
- Tiefgehendere Mechanismenanalyse
- Umfassendere Vergleiche (SOTA-Methoden)
- Komplexitätsanalyse (zeitlich/räumlich)

## Diagrammstandards

### Technische Zeichnungen
- **CAD-Zeichnungen**: Liniennormen (dicke durchgehende Linien/dünne durchgehende Linien/Strichlinien/Mittellinien)
- **Maßangaben**: vollständig, klar, keine Auslassungen
- **Toleranzen**: Angemessen gekennzeichnet (IT-Klasse)
- **Materialangaben**: Werkstoffnummer, Zustand, Wärmebehandlung
- **Technische Anforderungen**: Oberflächenrauheit, Form- und Lagetoleranzen

### Simulationsergebnisdiagramme
- **Farbdiagramme**: Farbskala klar, Bereich angemessen, Einheiten beschriftet
- **Kurven**: Achsenbeschriftungen, Einheiten, Legenden, Gitter
- **Vektorgrafik**: Pfeilrichtung, Größenverhältnis, Vergrößerung wichtiger Bereiche
- **Vergleichsdiagramme**: gleicher Maßstab, gleicher Blickwinkel, gleiche Parameter

### Referenzfotos
- **Auflösung**: 300 dpi oder höher
- **Hintergrund**: aufgeräumt, nicht ablenkend
- **Beschriftung**: Kennzeichnung wichtiger Komponenten, Maßreferenzen
- **Mehrere Perspektiven**: Gesamtansicht + Teilausschnitt + Detail

### Systemblockdiagramme/Flussdiagramme
- **Klare Hierarchie**: Systemebene→Modulebene→Einheitenebene
- **Klare Schnittstellen**: Signalfluss, Datenfluss, Steuerfluss
- **Standardsymbole**: Entspricht IEEE/GB-Normen
- **Farbnormen**: Funktionsunterscheidung (Eingabe/Verarbeitung/Ausgabe/Rückkopplung)

## Formeln und Algorithmen

### Formelstandards
- **Nummerierung**: (1), (2), (3)..., rechtsbündig
- **Zitation**: "Wie in Formel (3) dargestellt"
- **Ableitung**: Wichtige Schritte werden nicht weggelassen, zitierte Theoreme müssen gekennzeichnet werden
- **Symbole**: Bei erstmaligem Auftreten definieren, im gesamten Text einheitlich verwenden
- **Einheiten**: SI-Einheiten, konsistente Maßeinheiten

### Algorithmus-Pseudocode
- **Format**: strukturiert, eingerückt, kommentiert
- **Eingabe/Ausgabe**: Parameter klar benennen, Rückgabewerte angeben
- **Komplexität**: Zeit-/Speicherkomplexität angeben
- **Wichtige Schritte**: fettgedruckt/kommentiert

```
Algorithmus 1: XXX-Algorithmus
Eingabe: Parameter 1, Parameter 2, ...
Ausgabe: Ergebnis
1. Initialisierung...
2. für i = 1 bis n tun
3.   Berechnung...
4.   wenn Bedingung dann
5.     Aktualisierung...
6.   ende wenn
7. ende für
8. return Ergebnis
```

## Empfohlene Werkzeuge

### Modellierung und Simulation
- **MATLAB/Simulink**: Steuerung, Signale, numerische Berechnungen
- **ANSYS**: Struktur, Fluid, Elektromagnetik, Multiphysik
- **SolidWorks/CATIA**: 3D-Modellierung, Montage, technische Zeichnungen
- **AutoCAD**: 2D-technische Zeichnungen, Elektropläne
- **COMSOL**: gekoppelte Multiphysik-Simulation
- **ABAQUS**: nichtlineare Analyse, Werkstoffmechanik

### Programmierung und Algorithmen
- **Python**: Datenanalyse, maschinelles Lernen, Automatisierung
- **C/C++**: Hochleistungsberechnung, Echtzeitsysteme
- **LabVIEW**: Mess- und Steuerungssysteme, virtuelle Instrumente
- **SPS-Programmierung**: industrielle Steuerung, Automatisierung

### Datenvisualisierung
- **Origin**: wissenschaftliche Diagramme, Kurvenanpassung
- **Tecplot**: CFD-Nachbearbeitung, Farbdiagramme
- **Paraview**: Open-Source-Visualisierung, große Datenvolumen
- **MATLAB**: integrierte Diagramme, benutzerdefiniert

## Häufige Fehler
1. Unvollständige Parametereinstellungen (fehlende Schlüsselparameter)
2. Unklare Randbedingungen (beeinflusst die Reproduzierbarkeit der Ergebnisse)
3. Schlechte Diagrammqualität (niedrige Auflösung, unklare Beschriftungen)
4. Unfairer Vergleich (unterschiedliche Bedingungen, unterschiedliche Datensätze)
5. Fehlende Fehleranalyse (Unsicherheit nicht bewertet)
6. Unklare Beschreibung der Innovationspunkte (kein Vergleich mit bestehenden Methoden)
7. Lückenhafte theoretische Ableitung (wichtige Schritte weggelassen)
8. Schlechte Reproduzierbarkeit von Experimenten (Umgebung/Geräte nicht aufgezeichnet)
9. Übergeneralisierung der Schlussfolgerungen (über die Versuchsbedingungen hinaus)
10. Unregelmäßige technische Zeichnungen (Linien-/Beschriftungs-/Toleranzfehler)
