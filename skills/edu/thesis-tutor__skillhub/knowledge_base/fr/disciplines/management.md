# Guide de rédaction d'articles en gestion / administration des entreprises

## Caractéristiques de la discipline
- Accent sur les cadres théoriques, la validation empirique et les implications managériales
- Importance accordée aux sources de données, à la mesure des variables et au traitement de l'endogénéité
- Articles de revues principalement (revues de premier plan : AMJ/SMJ/JOM/OS/MS)
- Études de cas appréciées (construction/vérification de théories)

## Types de recherche

### 1. Étude de cas
- **Applicabilité** : exploration de nouveaux phénomènes, construction théorique, processus complexes
- **Types** :
  - Cas unique (extrême/typique/longitudinal)
  - Cas multiples (réplication/comparaison/complémentarité)
- **Points clés de conception** :
  - Sélection des cas (échantillonnage théorique, non aléatoire)
  - Collecte de données (entretiens/archives/observations/sources multiples)
  - Stratégie d'analyse (correspondance de modèles/construction d'interprétation/séquence temporelle)
  - Garantie de fiabilité (triangulation/vérification par les membres/piste d'audit)
- **Normes de rapport** :
  - Description riche du contexte (contextualisation)
  - Chaîne de preuves claire (données→graphiques→conclusions)
  - Dialogue avec la littérature (confirmation/extension/défiance)

### 2. Étude par enquête
- **Applicabilité** : vérification d'hypothèses à grande échelle, relations entre variables
- **Types** : transversale/longitudinale/panneau
- **Points clés de conception** :
  - Cadre d'échantillonnage (accessibilité de la population cible)
  - Conception du questionnaire (échelles validées + items conçus)
  - Collecte de données (en ligne/papier/mixte)
  - Biais de méthode commune (test de Harman à un facteur/contrôle procédural)
- **Méthodes d'analyse** :
  - Modèles d'équations structurelles (SEM) : AMOS/PLS/Mplus
  - Modèles linéaires hiérarchiques (HLM) : données multiniveaux
  - Modèles de croissance latente (LGM) : suivi longitudinal

### 3. Étude expérimentale
- **Applicabilité** : relations causales, mécanismes comportementaux
- **Types** : laboratoire/terrain/quasi-expérience/expérience naturelle
- **Points clés de conception** :
  - Attribution aléatoire (aléatoire simple/appariée)
  - Vérification de la manipulation (efficacité de la variable indépendante)
  - Mesure de la variable dépendante (objective/subjective/comportementale)
  - Contrôle des variables (exclusion des facteurs confondants)
- **Méthodes d'analyse** :
  - ANOVA/ANCOVA : comparaison intergroupes
  - Médiation/modération : macro PROCESS
  - Multiniveaux : HLM

### 4. Analyse de données secondaires
- **Applicabilité** : recherche macro, données de panel, études d'événements
- **Sources de données** :
  - Entreprises cotées : CSMAR, Wind, Guotaian
  - Données de brevets : Office national de la propriété intellectuelle, Derwent
  - Données de recrutement : Zhilian, 51job
  - Réseaux sociaux : Weibo, Zhihu, Maimai (web scraping)
- **Méthodes d'analyse** :
  - Modèles de données de panel : effets fixes/aléatoires/GMM
  - DID/PSM : inférence causale
  - Étude d'événements : calcul du CAR
  - Analyse textuelle : fréquence des mots, modèles thématiques, analyse de sentiment

## Cadres théoriques

### Théories courantes
- **Vue basée sur les ressources (RBV)** : ressources VRIN→avantage concurrentiel
- **Théorie institutionnelle** : pressions institutionnelles réglementaires/normatives/cognitives
- **Théorie de l'agence** : conflit principal-agent→mécanismes de gouvernance
- **Théorie des parties prenantes** : équilibre multi-acteurs
- **Capacités dynamiques** : détection/capture/reconfiguration
- **Apprentissage organisationnel** : exploration/exploitation, transformation des connaissances (SECI)
- **Théorie de l'upper echelon** : caractéristiques des dirigeants→choix stratégiques→résultats organisationnels
- **Réseaux sociaux** : trous structuraux/centralité/encastrage
- **Théorie du signal** : envoi de signaux→interprétation des signaux→résultats
- **Théorie de la légitimité** : légitimité pragmorale/morale/cognitive

### Conseils d'utilisation des théories
1. **Ne pas empiler les théories** : 1-2 théories clés suffisent
2. **Clarifier la perspective théorique** : expliquer quoi, prédire quoi
3. **Lier théorie et hypothèses** : chaque hypothèse soutenue par la théorie
4. **Dialogue théorique** : résultats cohérents/contradictoires/extension par rapport aux prédictions théoriques

## Sources de données et mesures

### Conception du questionnaire
- **Source des échelles** : privilégier les échelles validées (fiabilité et validité prouvées)
- **Traduction-retrotraduction** : échelle anglaise→chinois→retrotraduction→comparaison
- **Nombre d'items** : 3-7 items par construit (éviter la fatigue)
- **Items inversés** : inclure 2-3 items (prévenir les réponses par défaut)
- **Prétest** : 30-50 personnes, CITC<0.4 à supprimer

### Bases de données courantes
- **CSMAR** : finances, gouvernance, actionnariat des entreprises cotées
- **Wind** : finance, macroéconomie, secteurs
- **Guotaian** : économie et finance, économie régionale
- **CEIC** : macroéconomie, données sectorielles
- **Banque mondiale** : comparaisons internationales, indicateurs de développement
- **Enquête longitudinale sur les familles chinoises (CFPS)** : micro-individus
- **Enquête longitudinale sur la santé et la retraite en Chine (CHARLS)** : vieillissement

### Mesure des variables
- **Variable indépendante** : définition opérationnelle claire
- **Variable dépendante** : mesure multidimensionnelle (objective + subjective)
- **Variable médiatrice** : explication du mécanisme
- **Variable modératrice** : conditions limites
- **Variables de contrôle** : exclusion des explications alternatives

## Méthodes d'analyse

### Modèles d'équations structurelles (SEM)
- **CB-SEM (AMOS/Mplus)** :
  - Grand échantillon (>200)
  - Analyse confirmatoire
  - Ajustement strict du modèle (CFI>0.9, RMSEA<0.08, SRMR<0.08)
- **PLS-SEM (SmartPLS)** :
  - Acceptable avec petit échantillon
  - Analyse exploratoire
  - Orientation prédictive (PLSpredict)

### Modèles linéaires hiérarchiques (HLM)
- **Applicabilité** : données emboîtées (employés→équipes→organisations)
- **Logiciels** : HLM, Mplus, R (lme4)
- **Rapport** : ICC(1), ICC(2), rwg, effets inter-niveaux

### Analyse qualitative comparative (QCA)
- **Applicabilité** : complexité causale, combinaison de facteurs multiples
- **Types** : crisp-set / fuzzy-set / mvQCA
- **Logiciels** : fsQCA, R (package QCA)
- **Rapport** : table de vérité, consistence, couverture, solution intermédiaire

### Traitement de l'endogénéité
- **Sources** : variables omises, causalité inverse, erreur de mesure, sélection d'échantillon
- **Méthodes** :
  - Variables instrumentales (IV) : 2SLS
  - Différences dans les différences (DID) : choc politique
  - Appariement par score de propension (PSM) : appariement d'échantillons
  - Régression par discontinuité (RDD) : près du seuil
  - Modèle de Heckman : sélection d'échantillon

## Modèles de structure de thèse

### Recherche empirique (quantitative)
```
1. Introduction
   - Contexte pratique (phénomène managérial)
   - Lacune théorique (dialogue avec la littérature)
   - Questions de recherche
   - Contributions théoriques
   - Implications pratiques

2. Revue de littérature et hypothèses
   - Définition des construits clés
   - Littérature sur l'effet principal (A→B)
   - Mécanisme de médiation (A→M→B)
   - Limites de modération (W influence A→B)
   - Tableau récapitulatif des hypothèses

3. Conception de la recherche
   - Échantillon et procédure
   - Mesure des variables (source de l'échelle + fiabilité)
   - Stratégie d'analyse
   - Contrôle du biais de méthode commune

4. Résultats
   - Statistiques descriptives + matrice de corrélation
   - Modèle de mesure (CFA/fiabilité-validité)
   - Modèle structurel (coefficients de chemin + significativité)
   - Effet de médiation (Bootstrap)
   - Effet de modération (terme d'interaction/pente simple)
   - Tests de robustesse (mesure alternative/sous-échantillon)

5. Discussion
   - Synthèse de la vérification des hypothèses
   - Contributions théoriques (dialogue)
   - Implications managériales (opérationnelles)
   - Limites (échantillon/méthode/causalité)
   - Recherches futures (orientations spécifiques)
```

### Étude de cas (qualitative)
```
1. Introduction : phénomène→question→méthode→contribution
2. Revue de littérature : perspective théorique→lacune→cadre
3. Méthode :
   - Sélection des cas (logique d'échantillonnage théorique)
   - Collecte de données (matrice de preuves multi-sources)
   - Analyse des données (stratégie de codage)
   - Garantie de fiabilité (triangulation, etc.)
4. Description du cas : contexte→processus→événements clés
5. Analyse inter-cas : modèles→propositions→théorie
6. Discussion : contribution→implications→limites→futur
```

## Erreurs courantes
1. Cadre théorique faible (hypothèses sans soutien théorique)
2. Négligence de l'endogénéité (inférence causale non fiable)
3. Biais de méthode commune (données de même source non traitées)
4. Adaptation arbitraire des échelles (altération de la fiabilité-validité)
5. Erreur d'interprétation de l'effet de médiation (médiation complète ≠ médiation)
6. Erreur dans le graphique de modération (direction de la pente simple)
7. Biais de sélection d'échantillon (généralisation par commodité)
8. Contrôle excessif des variables (contrôle de la médiation/modération)
9. Rapport sélectif des résultats (uniquement les résultats significatifs)
10. Implications managériales vagues (manque d'opérationnalité)
