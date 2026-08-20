# Guide de rédaction d'articles en psychologie

## Caractéristiques de la discipline
- Accent sur la conception expérimentale, la rigueur statistique et la validation théorique
- Importance accordée à l'éthique de la recherche, au consentement éclairé et au bien-être animal
- Articles de revues principalement (revues de premier plan : Psychological Science/JPSP/JEP/Developmental Psychology)
- Le préenregistrement (preregistration) est de plus en plus important
- Tendance vers la science ouverte (Open Science) : partage des données/code/matériel

## Types de recherche

### 1. Psychologie expérimentale
- **Applicabilité** : relations causales, mécanismes cognitifs, expérimentation comportementale
- **Types de conception** :
  - Conception inter-sujets (Between-subjects) : différents participants reçoivent différents traitements
  - Conception intra-sujets (Within-subjects) : le même participant reçoit tous les traitements
  - Conception mixte (Mixed) : variables inter-sujets et intra-sujets combinées
- **Éléments clés** :
  - Manipulation de la variable indépendante (claire, efficace, reproductible)
  - Mesure de la variable dépendante (temps de réponse, taux de précision, mouvements oculaires, ERP, fMRI)
  - Contrôle des variables confondantes (randomisation, contrebalancement, masquage)
  - Analyse de puissance (G*Power : f=0.25 effet moyen, α=0.05, 1-β=0.80)
- **Normes de rapport** :
  - Préenregistrement des hypothèses (OSF, AsPredicted)
  - Description complète de la procédure expérimentale (reproductibilité)
  - Transparence des critères d'exclusion (ex. temps de réponse <200ms)
  - Complément par analyse bayésienne (BF10)

### 2. Psychologie du développement
- **Applicabilité** : développement sur la durée de vie, différences d'âge, suivi longitudinal
- **Types de conception** :
  - Conception transversale : mesure simultanée de groupes d'âge différents
  - Conception longitudinale : mesures répétées du même groupe
  - Conception séquentielle : combinaison transversale + longitudinale
- **Éléments clés** :
  - Groupes d'âge (théoriquement motivés : ex. stades de Piaget)
  - Équivalence de mesure (comparabilité des outils entre tranches d'âge)
  - Traitement de l'attrition (test MAR/MCAR, imputation multiple)
  - Effet de cohorte (différences de contexte historique)
- **Considérations spéciales** :
  - Éthique avec les enfants : consentement parental + assentiment de l'enfant (à partir de 7 ans)
  - Adaptation au développement : difficulté de la tâche, maintien de l'attention
  - Désirabilité sociale : les enfants sont plus susceptibles de complaire

### 3. Psychologie sociale
- **Applicabilité** : cognition sociale, attitudes, processus de groupe, relations interpersonnelles
- **Méthodes courantes** :
  - Questionnaires : mesures par échelle (Likert 5/7 points)
  - Méthode expérimentale : manipulation situationnelle (ex. variantes de l'expérience de conformité d'Asch)
  - Expérience de terrain : intervention en situation naturelle
  - Analyse d'archives : données historiques, contenu médiatique
- **Éléments clés** :
  - Contrôle du biais de désirabilité sociale (anonymat, mesure indirecte, IAT)
  - Représentativité de l'échantillon (problème WEIRD : occidental, éduqué, industrialisé, riche, démocratique)
  - Attention à la taille de l'effet (petit d=0.2, moyen d=0.5, grand d=0.8)
  - Réplication d'expériences (directe/conceptuelle/systématique)

### 4. Psychologie clinique
- **Applicabilité** : troubles psychologiques, effets des interventions, outils d'évaluation
- **Types de conception** :
  - ECR : gold standard, attribution aléatoire aux groupes traitement/contrôle
  - Expérience à sujet unique : conception ABA/multibaseline
  - Quasi-expérience : groupes naturels, pré-test/post-test
- **Éléments clés** :
  - Critères diagnostiques (DSM-5/CIM-11)
  - Protocole d'intervention (manualisé, vérification de la fidélité)
  - Critères de jugement (symptômes, fonctionnement, qualité de vie)
  - Traitement de l'abandon (analyse ITT/PP)
- **Éthique spécifique** :
  - Protection des populations vulnérables (patients, enfants, personnes âgées)
  - Principe de risque minimal
  - Confidentialité des données (HIPAA/loi sur la cybersécurité)

## Conception expérimentale

### Inter-sujets vs Intra-sujets
| Dimension | Inter-sujets | Intra-sujets |
|-----------|--------------|--------------|
| Avantages | Pas d'effet d'ordre, pas d'effet de pratique | Contrôle des différences individuelles, puissance statistique élevée |
| Inconvénients | Nécessite plus de participants, confusion des différences individuelles | Effet d'ordre, effet de pratique, fatigue |
| Applicabilité | Différents traitements ont un effet permanent | Traitements réversibles, nécessité de haute puissance statistique |
| Taille d'échantillon | ≥30 par groupe (grand effet) | ≥20 au total (grand effet) |

### Conception quasi-expérimentale
- **Pré-test/post-test à groupes inégaux** : sans randomisation, nécessite un contrôle statistique
- **Série temporelle interrompue** : observations multiples, comparaison avant/après intervention
- **Régression par discontinuité** : groupement basé sur le seuil d'une variable continue
- **Groupe de comparaison non équivalent** : appariement plutôt que randomisation

### Puissance statistique
- **Outils de calcul** : G*Power, package pwr, WebPower
- **Paramètres** :
  - Taille d'effet (d=0.2 petit/0.5 moyen/0.8 grand ; f=0.1 petit/0.25 moyen/0.4 grand)
  - Niveau α (0.05 ou 0.01)
  - Puissance statistique (1-β=0.80 ou 0.90)
  - Type de test (bilatéral/unilatéral)
- **Recommandations** :
  - Petit effet : ≥64 par groupe (puissance 0.80)
  - Effet moyen : ≥26 par groupe
  - Grand effet : ≥16 par groupe

## Méthodes statistiques

### Analyses de base
- **Test t** : comparaison de deux groupes (indépendants/appariés)
- **Analyse de variance (ANOVA)** : comparaison de plusieurs groupes
  - À un facteur : une variable indépendante
  - À plusieurs facteurs : plusieurs variables indépendantes + effet d'interaction
  - Mesures répétées : variable intra-sujets
  - MANOVA : plusieurs variables dépendantes
- **Test du chi-deux** : association entre variables catégorielles
- **Analyse de corrélation** : Pearson/Spearman

### Analyses avancées
- **Analyse de régression** :
  - Régression linéaire : prédicteur continu → résultat continu
  - Régression logistique : résultat catégoriel
  - Régression de Poisson : résultat de comptage
  - Régression multiniveau : données emboîtées (participants→classes→écoles)
- **Modèles d'équations structurelles (SEM)** :
  - Analyse factorielle confirmatoire (CFA) : modèle de mesure
  - Analyse de chemins : modèle structurel
  - Comparaison multi-groupes : équivalence de mesure (configural/métrique/scalaire)
- **Modèles linéaires hiérarchiques (HLM/MLM)** :
  - Modèles à intercept/slope aléatoires
  - Interaction inter-niveaux
  - Imbrication à 3 niveaux et plus
- **Modèles de croissance latente (LGM)** :
  - Croissance linéaire/non linéaire
  - Prédicteurs de la croissance
  - Modèles à processus parallèles
- **Analyse de survie** : temps jusqu'à l'événement

### Rapport de la taille d'effet
- **Cohen's d** : différence de moyennes entre deux groupes (petit 0.2/moyen 0.5/grand 0.8)
- **η² (êta-carré)** : proportion de variance expliquée (petit 0.01/moyen 0.06/grand 0.14)
- **ω² (oméga-carré)** : estimation non biaisée
- **r²** : coefficient de détermination
- **Rapport de cotes (OR)** : régression logistique
- **Intervalle de confiance** : IC à 95% plus important que la valeur P

## Utilisation des échelles

### Sources courantes d'échelles
- **APA PsycTests** : base de données officielle de tests psychologiques
- **Mental Measurements Yearbook** : évaluation des tests
- **Annexes de revues** : les articles originaux incluent souvent l'échelle complète
- **Manuels** : ex. manuel du Big Five Inventory (BFI)

### Procédure de traduction-retrotraduction
1. Anglais→langue cible (traduction par bilingue)
2. Langue cible→anglais (retrotraduction par un bilingue indépendant)
3. Comparaison de l'original avec la version retrotraduite
4. Discussion du comité d'experts sur les divergences
5. Prétest (30-50 personnes)
6. Vérification de la fiabilité et de la validité

### Exigences de fiabilité et de validité
- **Fiabilité** :
  - Alpha de Cronbach ≥ 0.70 (acceptable)
  - Fiabilité par moitié ≥ 0.70
  - Fiabilité test-retest (intervalle de 2-4 semaines) r ≥ 0.70
- **Validité** :
  - Validité de contenu : évaluation par des experts
  - Validité de construit : EFA/CFA, charges factorielles ≥ 0.50
  - Validité de critère : corrélation avec un critère externe
  - Validité discriminante : AVE > corrélation²

## Exigences éthiques

### Principes éthiques de l'APA (5 principes)
1. **Bienfaisance et non-malfaisance** : maximiser les bénéfices, minimiser les dommages
2. **Fidélité et responsabilité** : standards professionnels, responsabilité sociale
3. **Intégrité** : honnêteté, exactitude, absence de fraude
4. **Justice** : traitement équitable, éviter les préjugés
5. **Respect** : autonomie, vie privée, dignité

### Consentement éclairé
- **Éléments** : objectif de la recherche, procédure, risques, bénéfices, confidentialité, volontariat, coordonnées
- **Populations spéciales** :
  - Enfants : consentement parental + assentiment de l'enfant (à partir de 7 ans)
  - Déficience cognitive : représentant légal
  - Prisonniers : protection supplémentaire
- **Recherche avec deception** : explication a posteriori (debriefing)

### Éthique de l'expérimentation animale
- **Principe des 3R** : Remplacement (Replacement), Réduction (Reduction), Raffinement (Refinement)
- **Révision par l'IACUC** : approbation du protocole, supervision vétérinaire
- **Conditions d'élevage** : enrichissement environnemental, besoins sociaux
- **Point final** : point final humain, critères d'euthanasie

## Modèles de structure de thèse

### Recherche expérimentale
```
1. Introduction
   - Contexte théorique (concepts clés)
   - État de la recherche (lacunes dans la littérature)
   - Questions et hypothèses de recherche (H1a, H1b...)
   - Contributions théoriques et implications pratiques

2. Méthodes
   - Participants (recrutement, sélection, taille d'échantillon, rémunération)
   - Conception (conception mixte 2×3, variables indépendantes/dépendantes)
   - Matériel/stimuli (source, élaboration, prétest)
   - Procédure (étapes, randomisation, masquage)
   - Plan d'analyse des données (lien de préenregistrement)

3. Résultats
   - Statistiques descriptives (M, ÉT, n)
   - Vérification de la manipulation (efficacité de la variable indépendante)
   - Vérification des hypothèses (tableau ANOVA, taille d'effet, IC)
   - Analyses supplémentaires (exploratoires, bayésiennes)
   - Graphiques (graphique des moyennes, graphique d'interaction)

4. Discussion
   - Synthèse de la vérification des hypothèses
   - Interprétation théorique (mécanisme)
   - Comparaison avec les études antérieures
   - Limites (échantillon, méthode, généralisation)
   - Perspectives futures (hypothèses spécifiques)
   - Conclusion (concise)

5. Matériel supplémentaire (en ligne)
   - Questionnaires/stimuli complets
   - Données brutes (OSF)
   - Code d'analyse (R/Python)
```

## Pratiques de science ouverte

### Préenregistrement
- **Plateformes** : OSF, AsPredicted, ClinicalTrials.gov
- **Contenu** : hypothèses, conception, taille d'échantillon, plan d'analyse
- **Types** :
  - Préenregistrement standard : avant la collecte de données
  - Rapport enregistré : engagement de la revue à publier (quel que soit le résultat)
- **Bénéfices** : prévenir le HARKing (hypothèse a posteriori), améliorer la crédibilité

### Partage des données
- **Plateformes** : OSF, Figshare, Zenodo, GitHub
- **Contenu** :
  - Données brutes (dépersonnalisées)
  - Code d'analyse (reproductibilité)
  - Matériel de recherche (questionnaires, stimuli)
- **Licence** : CC0 (recommandé), CC-BY

### Partage du code
- **Exigences** : fonctionnel, commenté, avec README
- **Outils** : R Markdown, Jupyter Notebook
- **Contrôle de version** : Git/GitHub

## Erreurs courantes
1. Taille d'échantillon insuffisante (puissance < 0.80)
2. Comparaisons multiples non corrigées (Bonferroni/FDR)
3. Conception intra-sujets sans contrôle de l'ordre (carré latin/randomisation)
4. Taille d'effet non rapportée (uniquement la valeur P)
5. HARKing (hypothèse a posteriori)
6. Biais de méthode commune (données de même source)
7. Fiabilité faible de l'échelle (α < 0.70 mais utilisée quand même)
8. Inférence causale excessive (conception corrélationnelle)
9. Négligence des différences culturelles (échantillon WEIRD)
10. Description éthique manquante (impossible de passer la révision)
