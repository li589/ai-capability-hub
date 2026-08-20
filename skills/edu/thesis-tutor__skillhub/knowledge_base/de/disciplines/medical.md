# Leitfaden für das Verfassen wissenschaftlicher Arbeiten in Medizin/Life Sciences

## Fachspezifische Merkmale
- Betonung auf evidenzbasierter Medizin, experimenteller Validierung und klinischen Daten
- Wertschätzung für Ethikreview, informierte Zustimmung und Datenschutz
- Zeitschriftenartikel > Konferenzbeiträge (Top-Journals: NEJM/Lancet/JAMA/Nature Medicine/Cell)
- Strenge Schreibstandards: CONSORT, PRISMA, STROBE-Erklärungen

## Forschungstypen

### 1. Randomisierte kontrollierte Studie (RCT)
- **Anwendung**: Bewertung der Wirksamkeit von Medikamenten/Interventionen
- **Designprinzipien**:
  - Randomisierungsmethoden (einfach/stratifiziert/blockweise)
  - Verblindung (einfach/doppelt/dreifach)
  - Kontrolltypen (Placebo/aktiv/keine Kontrolle)
  - Stichprobenberechnung (Poweranalyse)
- **Berichterstattung**: CONSORT 2010-Erklärung + Flussdiagramm
- **Registrierungspflicht**: ClinicalTrials.gov oder Chinesisches Register für klinische Studien

### 2. Kohortenstudie
- **Anwendung**: Ätiologieexploration, Prognosefaktoren
- **Typen**: Prospektiv/Retrospektiv/Bidirektional
- **Designprinzipien**:
  - Klare Expositionsdefinition
  - Vollständiges Follow-up-Protokoll
  - Kontrolle der Verlustrate (<20%)
  - Kontrolle von Störvariablen
- **Berichterstattung**: STROBE-Erklärung

### 3. Fall-Kontroll-Studie
- **Anwendung**: Seltene Erkrankungen, lange Inkubationszeiten
- **Designprinzipien**:
  - Klare Falldefinition (Goldstandard)
  - Angemessene Kontrollauswahl (Krankenhaus/Bevölkerung)
  - Matching-Faktoren
  - Kontrolle von Recall Bias
- **Berichterstattung**: STROBE-Erklärung

### 4. Querschnittsstudie
- **Anwendung**: Prävalenzuntersuchung, Statusbeschreibung
- **Designprinzipien**:
  - Stichprobenverfahren (mehrstufig stratifiziert)
  - Stichprobengröße (Prävalenzschätzung)
  - Reliabilität/Validität der Erhebungsinstrumente
- **Berichterstattung**: STROBE-Erklärung (Querschnittserweiterung)

### 5. Meta-Analyse
- **Anwendung**: Evidenzsynthese, Wirksamkeitsvergleich
- **Typen**:
  - Interventions-Meta-Analyse (RCT)
  - Diagnostische Meta-Analyse
  - Netzwerk-Meta-Analyse (NMA)
  - Individual Patient Data Meta-Analyse (IPD)
- **Berichterstattung**: PRISMA 2020-Erklärung + Registrierung (PROSPERO)
- **Analyseprinzipien**:
  - Heterogenitätstest (I²-Statistik)
  - Publikationsbias (Funnel Plot, Egger-Test)
  - Sensitivitätsanalyse
  - Evidenzqualität (GRADE-Einstufung)

### 6. Systematisches Review
- **Anwendung**: Umfassende Evidenzübersicht zu einem Bereich
- **Schritte**:
  1. PICO-Frage formulieren
  2. Suchstrategie entwickeln (mindestens 3 Datenbanken)
  3. Literaturscreening (unabhängig durch Zweierteam)
  4. Datenextraktion (standardisierte Tabelle)
  5. Qualitätsbewertung (Cochrane Risk of Bias/RoB 2)
  6. Evidenzsynthese (qualitativ/quantitativ)
- **Berichterstattung**: PRISMA 2020

## Ethische Anforderungen

### Ethikreview
- **IRB/IEC-Genehmigung**: Erforderlich für alle Studien mit menschlichen Probanden
- **Prüfgegenstand**: Studienprotokoll, informierte Zustimmung, Forscherqualifikationen
- **Follow-up-Review**: Jährlich/schwere unerwünschte Ereignisse/Protokolländerungen

### Informierte Zustimmung
- **Elemente**: Studienzweck, Verfahren, Risiken, Nutzen, Alternativen, Vertraulichkeit, Freiwilligkeit, Kontaktinformationen
- **Besondere Situationen**: Notfälle, gesetzliche Vertreter für nicht einwilligungsfähige Personen
- **Dokumentation**: Unterschriebene Version + Datum + Kopie für Probanden

### Datenschutz
- **Datenanonymisierung**: Name→Nummer, ID-Nummer→teilweise verdeckt
- **Speichersicherheit**: Verschlüsselung, Zugriffskontrolle, Audit-Protokoll
- **Übertragungssicherheit**: Verschlüsselte Übertragung, Prinzip der Datenminimierung
- **Aufbewahrungsfrist**: Mindestens 5 Jahre nach Studienende

## Statistische Methoden

### Grundlegende Statistik
- **Deskriptiv**: Mittelwert ± Standardabweichung, Median (IQR), Häufigkeit (%)
- **Normalitätstest**: Shapiro-Wilk, Kolmogorov-Smirnov
- **Gruppenvergleich**: t-Test, Varianzanalyse, Chi-Quadrat-Test, Rangsummentest

### Fortgeschrittene Statistik
- **Überlebensanalyse**: Kaplan-Meier-Kurve, Log-Rank-Test, Cox-Regression
- **ROC-Analyse**: Fläche unter der Kurve, optimaler Cut-off, Sensitivität/Spezifität
- **Logistische Regression**: Einfaktoriell→Multifaktoriell, OR-Wert, 95%-KI
- **Multivariate Analyse**: Linear/Logistisch/Cox, Variablenauswahlstrategie
- **Wiederholte Messungen**: Mixed-Effects-Modell, GEE
- **Mediation/Moderation**: Bootstrap-Methode, Sobel-Test

### Stichprobenberechnung
- **Software**: G*Power, PASS, nQuery
- **Parameter**: Effektstärke, α (0.05), β (0.1 oder 0.2), Ausfallrate
- **Methoden**:
  - Zweigruppenvergleich: t-Test/Chi-Quadrat-Formel
  - Überlebensanalyse: Ereigniszahlberechnung
  - Diagnostischer Test: Sensitivitäts/Spezifitätsanforderungen
  - Äquivalenz/Non-Inferiority Design: Grenzwertbestimmung

## Gliederungsvorlagen

### Originalforschung (IMRAD-Format)
```
1. Titelseite: Titel, Autoren, Institution, Korrespondenzautor
2. Abstract: Strukturiert (Ziel, Methoden, Ergebnisse, Schlussfolgerung)
3. Einleitung: Hintergrund→Problem→Ziel→Hypothese
4. Methoden:
   - Design/Standort/Zeitraum
   - Teilnehmer (Ein-/Ausschlusskriterien)
   - Intervention/Expositionsdefinition
   - Endpunkte (primär/sekundär)
   - Statistische Methoden (Software/Version/Signifikanzniveau)
5. Ergebnisse:
   - Flussdiagramm (CONSORT)
   - Baseline-Charakteristika-Tabelle
   - Hauptergebnisse (Effektstärke+KI+p-Wert)
   - Sekundäre Ergebnisse
   - Subgruppenanalyse
   - Sensitivitätsanalyse
6. Diskussion:
   - Zusammenfassung der Hauptbefunde
   - Vergleich mit vorherigen Studien
   - Mechanismuserklärung
   - Klinische Bedeutung
   - Limitationen (ehrlich)
   - Zukünftige Richtungen
7. Fazit: Prägnant, nicht übertrieben
8. Danksagung/Erklärung: Finanzierung, Interessenkonflikte, Autorenbeitrag
9. Referenzen: Nach Zeitschriftenanforderung (Vancouver/APA)
```

### Systematisches Review/Meta-Analyse
```
1. Titel: Klar als „Systematisches Review" oder „Meta-Analyse" gekennzeichnet
2. Abstract: PRISMA-strukturiertes Abstract
3. Einleitung: Hintergrund→Problem→Ziel (PICO)
4. Methoden:
   - Protokollregistrierung (PROSPERO-Nummer)
   - Einschlusskriterien (PICOS)
   - Suchstrategie (vollständige Strategie im Anhang)
   - Screening-Prozess (unabhängig durch Zweierteam)
   - Datenextraktion (standardisierte Tabelle)
   - Qualitätsbewertung (Werkzeug+Version)
   - Statistische Methoden (Effektmaße, Heterogenität, Publikationsbias)
5. Ergebnisse:
   - Suchflussdiagramm (PRISMA)
   - Charakteristika der eingeschlossenen Studien
   - Qualitätsbewertungsergebnisdiagramm
   - Forest Plot
   - Funnel Plot
   - Subgruppenanalyse
   - Sensitivitätsanalyse
6. Diskussion: Evidenzzusammenfassung, Vertrauenswürdigkeit, Limitationen, zukünftige Forschung
7. Fazit: Implikationen für die Praxis
```

## Schreibstandards

### Berichterstattungsstandards-Checkliste
- **RCT**: CONSORT 2010 (25-Punkte-Checkliste + Flussdiagramm)
- **Systematisches Review/Meta**: PRISMA 2020 (27-Punkte-Checkliste + Flussdiagramm)
- **Beobachtungsstudien**: STROBE (22-Punkte-Checkliste)
- **Diagnostische Studien**: STARD (30-Punkte-Checkliste)
- **Fallberichte**: CARE (13-Punkte-Checkliste)
- **Tierexperimente**: ARRIVE (21-Punkte-Checkliste)
- **Qualitative Forschung**: SRQR (21-Punkte-Checkliste)
- **Gesundheitsökonomische Evaluation**: CHEERS (24-Punkte-Checkliste)

### Statistische Berichterstattungsstandards
- **Effektstärke**: Mittelwertdifferenz (MD), Standardisierte Mittelwertdifferenz (SMD), OR, RR, HR
- **Präzision**: 95%-Konfidenzintervall (KI)
- **p-Wert**: Exakter p-Wert (z.B. p=0.032), nicht „p<0.05"
- **Fehlende Daten**: Fehlrate, Behandlungsmethode
- **Software**: Name + Version (z.B. SPSS 26.0, R 4.2.1)

## Publikationsempfehlungen

### Zeitschriftenauswahl
- **Impact Factor**: JCR-Quartil (Q1-Q4), CAS-Quartil
- **Passgenauigkeit**: Scope, Leserschaft, Artikeltyp
- **Reviewzeit**: Erstgutachten, externes Review, Gesamtdauer
- **Open Access**: APC-Kosten, Förderpolitik
- **Warnliste**: CAS-Warnjournals vermeiden

### Einreichungsunterlagen
- **Cover Letter**: Innovation, klinische Bedeutung, empfohlene Gutachter
- **Autorenbeitrag**: CRediT-Klassifikation
- **Interessenkonflikte**: Keine/spezifische Erklärung
- **Datenverfügbarkeit**: Speicherort, Zugangsmethode
- **Ethikgenehmigung**: Ethiknummer, informierte Zustimmung

### Gutachterantwort
- **Haltung**: Höflich, objektiv, nicht rechtfertigend
- **Format**: Punkt-für-Punkt-Antwort (Gutachterkommentar→Antwort→Änderungsposition)
- **Strategie**: Begründete Ablehnung akzeptieren, fundierte Ablehnung, Experiment/Daten ergänzen
- **Frist**: Pünktlich antworten, Verlängerung vorab kommunizieren

## Häufige Fehler
1. Unzureichende Stichprobengröße (mangelnde Power)
2. Nicht korrigierte multiple Vergleiche (False Positives)
3. Überzogene Kausalschlussfolgerungen (Korrelation ≠ Kausalität)
4. Baseline-Ungleichgewicht (Randomisierungsversagen)
5. Unangemessene Behandlung fehlender Daten (willkürliches Löschen)
6. Zu viele Subgruppenanalysen (False Positives)
7. Ignorieren von Störvariablen (Bias)
8. Falsche statistische Methodenwahl (t-Test bei Nicht-Normalverteilung)
9. Unregelmäßige Diagramme (Achsen, Legenden, Einheiten)
10. Fehlende Ethikbeschreibung (Review nicht bestehbar)
