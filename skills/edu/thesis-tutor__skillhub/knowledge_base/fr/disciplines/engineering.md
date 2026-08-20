# Guide général de rédaction pour les articles en ingénierie

## Caractéristiques de la discipline
- Accent sur la résolution de problèmes, l'innovation des solutions et la validation expérimentale
- Importance accordée à la reproductibilité, à l'exhaustivité des paramètres et aux conditions limites
- Articles de conférence + articles de revues (conférences de premier plan : série IEEE/série ACM)
- Exigences élevées en matière de qualité des figures et tableaux (dessins techniques, figures de simulation, photos réelles)

## Types de recherche

### 1. Recherche par conception
- **Applicable à** : conception de nouveaux systèmes/nouvelles structures/nouveaux algorithmes
- **Éléments clés** :
  - Analyse des exigences (fonctionnelles/performance/contraintes)
  - Conception de la solution (architecture/modules/interfaces)
  - Démonstration de faisabilité (théorie/simulation/prototype)
  - Évaluation des performances (comparaison/tests de référence)
- **Structure de l'article** : problème → solution → implémentation → vérification → discussion

### 2. Recherche expérimentale
- **Applicable à** : expériences physiques, tests de performance, vérification de fiabilité
- **Éléments clés** :
  - Plateforme expérimentale (équipement/environnement/conditions)
  - Protocole expérimental (variables/niveaux/répétitions)
  - Acquisition de données (capteurs/taux d'échantillonnage/précision)
  - Analyse des résultats (erreurs/incertitude/statistiques)
- **Structure de l'article** : objectif → méthode → expérience → résultats → analyse

### 3. Recherche par simulation
- **Applicable à** : simulation numérique, analyse computationnelle, vérification virtuelle
- **Éléments clés** :
  - Établissement du modèle (géométrie/physique/mathématiques)
  - Maillage (type/densité/qualité)
  - Conditions limites (charges/contraintes/contacts)
  - Paramètres de résolution (algorithme/convergence/précision)
  - Vérification des résultats (comparaison expérimentale/comparaison littéraire)
- **Structure de l'article** : problème → modélisation → résolution → vérification → application

### 4. Recherche par optimisation
- **Applicable à** : optimisation de paramètres, optimisation structurelle, optimisation d'ordonnancement
- **Éléments clés** :
  - Objectif d'optimisation (mono-objectif/multi-objectifs)
  - Variables de conception (continues/discrètes/mixtes)
  - Contraintes (égalités/inégalités)
  - Algorithme d'optimisation (gradient/heuristique/métaheuristique)
  - Analyse de convergence (courbe d'itération/stabilité)
- **Structure de l'article** : problème → modélisation → algorithme → expérience → comparaison

## Modèle de structure de l'article

### Mémoire de licence
`
1. Introduction
   - Contexte de recherche (besoins techniques, état de l'art)
   - État de la recherche nationale et internationale (revue par catégories)
   - Objectifs et signification de la recherche
   - Structure de l'article

2. Fondements théoriques/travaux connexes
   - Définition des concepts clés
   - Dérivation des théories fondamentales
   - Résumé des méthodes existantes (tableau comparatif des avantages/inconvénients)

3. Conception de la solution/proposition de méthode
   - Architecture globale (diagramme système)
   - Conception détaillée (diagramme de décomposition des modules)
   - Algorithmes clés (pseudo-code/diagramme de flux)
   - Description des points d'innovation

4. Expérimentation/simulation/implémentation
   - Plateforme expérimentale/environnement de simulation
   - Paramètres (liste complète)
   - Protocole expérimental (conception du groupe de contrôle)
   - Processus de mise en œuvre (étapes clés)

5. Résultats et analyse
   - Principaux résultats (figures et tableaux prioritaires)
   - Analyse comparative (avec les méthodes existantes)
   - Analyse de sensibilité des paramètres
   - Analyse des erreurs/incertitude
   - Discussion (interprétation des mécanismes)

6. Conclusion et perspectives
   - Contributions principales (1.2.3.)
   - Limites
   - Travaux futurs
`

### Mémoire de master/article de revue
Ajouter :
- Dérivations théoriques plus détaillées
- Validations expérimentales plus complètes (scénarios multiples/jeux de données multiples)
- Analyses de mécanismes plus approfondies
- Comparaisons plus larges (méthodes état de l'art)
- Analyse de complexité (temporelle/spatiale)

## Normes des figures et tableaux

### Dessins techniques
- **Dessins CAO** : normes de type de ligne (ligne pleine épaisse/ligne pleine fine/ligne pointillée/ligne centrale)
- **Cotation** : complète, claire, sans omission
- **Tolérances et ajustements** : cotation raisonnable (grade IT)
- **Annotations de matériaux** : nuance, état, traitement thermique
- **Exigences techniques** : rugosité de surface, tolérances géométriques

### Figures de résultats de simulation
- **Cartes de contours** : échelle de couleurs claire, plage raisonnable, unités étiquetées
- **Graphiques courbes** : étiquettes des axes, unités, légende, grille
- **Champs vectoriels** : direction des flèches, échelle des tailles, zoom sur zones clés
- **Figures comparatives** : même échelle, même angle de vue, mêmes paramètres

### Photos réelles
- **Résolution** : 300 dpi ou plus
- **Arrière-plan** : simple, sans distraction du sujet principal
- **Annotations** : indication des composants clés, référence de dimensions
- **Vues multiples** : vue d'ensemble + vue partielle + détails

### Diagrammes système/diagrammes de flux
- **Hiérarchie claire** : niveau système → niveau module → niveau unité
- **Interfaces claires** : flux de signaux, flux de données, flux de contrôle
- **Symboles standard** : conformes aux normes IEEE/GB
- **Normes de couleurs** : distinction fonctionnelle (entrée/traitement/sortie/rétroaction)

## Formules et algorithmes

### Normes des formules
- **Numérotation** : (1), (2), (3)..., alignement à droite
- **Référence** : « comme le montre la formule (3) »
- **Dérivation** : les étapes clés ne sont pas omises, les références aux théorèmes doivent être indiquées
- **Symboles** : définis à leur première occurrence, cohérents dans tout le document
- **Unités** : unités SI, cohérence dimensionnelle

### Pseudo-code d'algorithmes
- **Format** : structuré, indentation, commentaires
- **Entrée/Sortie** : paramètres clairs, valeurs de retour
- **Complexité** : annotation de la complexité temporelle/spatiale
- **Étapes clés** : en gras/commentées

`
Algorithme 1 : Algorithme XXX
Entrée : paramètre1, paramètre2, ...
Sortie : résultat
1. Initialisation...
2. for i = 1 to n do
3.   Calcul...
4.   if condition then
5.     Mise à jour...
6.   end if
7. end for
8. return résultat
`

## Recommandations d'outils

### Modélisation et simulation
- **MATLAB/Simulink** : contrôle, signaux, calcul numérique
- **ANSYS** : structures, fluides, électromagnétique, multi-physique
- **SolidWorks/CATIA** : modélisation 3D, assemblage, dessins techniques
- **AutoCAD** : dessins techniques 2D, schémas électriques
- **COMSOL** : simulation couplée multi-physique
- **ABAQUS** : analyse non linéaire, mécanique des matériaux

### Programmation et algorithmes
- **Python** : analyse de données, apprentissage automatique, automatisation
- **C/C++** : calcul haute performance, systèmes temps réel
- **LabVIEW** : systèmes de mesure et contrôle, instruments virtuels
- **Programmation PLC** : contrôle industriel, automatisation

### Visualisation de données
- **Origin** : graphiques scientifiques, ajustement de courbes
- **Tecplot** : post-traitement CFD, cartes de contours
- **Paraview** : visualisation open source, données à grande échelle
- **MATLAB** : graphiques intégrés, personnalisés

## Erreurs courantes
1. Paramètres incomplets (paramètres clés manquants)
2. Conditions limites peu claires (affecte la reproductibilité des résultats)
3. Qualité médiocre des figures et tableaux (faible résolution, annotations peu claires)
4. Comparaisons injustes (conditions différentes, jeux de données différents)
5. Analyse des erreurs manquante (incertitude non évaluée)
6. Description floue des points d'innovation (pas de comparaison avec les méthodes existantes)
7. Sauts dans la dérivation théorique (étapes clés omises)
8. Faible reproductibilité des expériences (environnement/équipement non documenté)
9. Généralisation excessive des conclusions (au-delà des conditions expérimentales)
10. Dessins techniques non conformes (erreurs de type de ligne/annotation/tolérance)
