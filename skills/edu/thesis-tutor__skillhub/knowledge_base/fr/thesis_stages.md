# Guide détaillé de la proposition de recherche

## Feuille de route technique

### 1. Qu'est-ce qu'une feuille de route technique ?
La feuille de route technique est un outil de visualisation qui présente le chemin complet de la recherche, du problème à la solution. Elle aide les experts évaluateurs à comprendre rapidement votre logique de recherche et vous aide à clarifier votre pensée.

### 2. Types de feuilles de route techniques

**Type 1 : Diagramme de flux (adapté aux recherches expérimentales/ingénierie)**
`
Problématique de recherche
    |
    v
Revue de littérature → Cadre théorique
    |
    v
Hypothèses de recherche
    |
    v
Conception expérimentale/Collecte de données
    |
    v
Analyse des données
    |
    v
Validation des résultats
    |
    v
Conclusions et recommandations
`

**Type 2 : Frise chronologique (adapté aux recherches longitudinales/développementales)**
`
Phase 1 (Mois 1-3)    Phase 2 (Mois 4-6)    Phase 3 (Mois 7-9)
    |                       |                       |
    v                       v                       v
Revue de littérature    Collecte de données    Rédaction
Construction théorique  Mise en œuvre           Révision
`

**Type 3 : Itératif cyclique (adapté à la recherche-action/recherche conceptuelle)**
`
       Planifier
          |
          v
      Mettre en œuvre
    /        \
Vérifier  Réfléchir
    \        /
     Ajuster
          |
          v
    Nouveau cycle
`

**Type 4 : Arborescent (adapté aux recherches multi-méthodes/multi-cas)**
`
              Problématique centrale
                 |
    +------------+------------+
    |            |            |
Recherche      Recherche    Recherche
quantitative  qualitative   mixte
    |            |            |
Enquête       Entretiens    Triangulation
    |            |            |
Analyse       Analyse       Analyse
statistique   thématique    intégrée
`

### 3. Outils pour créer des feuilles de route techniques

**Outils professionnels** :
- Visio : le plus complet, adapté aux processus complexes
- ProcessOn : en ligne, convivial, riche en modèles
- Draw.io (diagrams.net) : gratuit, puissant
- Lucidchart : collaboration en ligne, adapté aux équipes

**Outils généraux** :
- PowerPoint : suffisant pour les processus simples
- Word : fonction SmartArt
- LaTeX : package TikZ (adapté à la mise en page académique)

**Outils de code** :
- Python : matplotlib, graphviz
- R : DiagrammeR, ggplot2
- Mermaid : style Markdown, adapté à l'intégration dans les documents

### 4. Principes de conception des feuilles de route techniques

**Clarté** :
- Chaque nœud a une étiquette claire (verbe + nom)
- Direction des flèches claire (unidirectionnelle, bidirectionnelle, cyclique)
- Éviter les lignes croisées (utiliser des couches ou des couleurs)

**Exhaustivité** :
- Inclure la chaîne complète du problème à la conclusion
- Marquer les nœuds clés (jalons)
- Marquer les points de décision (ex. : « Validation de l'hypothèse ? »)

**Hiérarchie** :
- Flux principal : lignes épaisses, grands nœuds
- Sous-flux : lignes fines, petits nœuds
- Remarques : pointillé, gris

**Esthétique** :
- Palette de couleurs cohérente (3-5 couleurs)
- Alignement (alignement sur grille)
- Espacement (ne pas surcharger)

### 5. Exemple : Feuille de route technique pour une recherche quantitative

`
[Contexte de recherche]
L'éducation en ligne se développe rapidement, mais les résultats d'apprentissage sont inégaux
         |
         v
[Revue de littérature] → Identification du manque : absence d'études systématiques sur les mécanismes d'interaction
         |
         v
[Cadre théorique] → Constructivisme social + Théorie de la charge cognitive
         |
         v
[Hypothèses de recherche]
H1 : La fréquence des interactions enseignant-étudiant est positivement corrélée aux résultats académiques
H2 : La profondeur des interactions étudiant-étudiant est positivement corrélée à la pensée critique
H3 : La qualité de l'interaction joue un rôle médiateur entre les fonctionnalités de la plateforme et les résultats d'apprentissage
         |
         v
[Conception de recherche]
  |
  +-- Groupe expérimental : utilisation d'une nouvelle plateforme d'interaction (n=150)
  |
  +-- Groupe témoin : utilisation d'une plateforme traditionnelle (n=150)
  |
  +-- Pré-test : motivation d'apprentissage, connaissances préalables
  |
  +-- Post-test : résultats académiques, pensée critique, satisfaction
         |
         v
[Collecte de données]
  |
  +-- Journaux de plateforme : fréquence, durée, type d'interactions
  |
  +-- Enquête par questionnaire : perception de la qualité des interactions, expérience d'apprentissage
  |
  +-- Résultats de tests : questions objectives + questions subjectives
  |
  +-- Entretiens : compréhension approfondie des mécanismes (n=20)
         |
         v
[Analyse des données]
  |
  +-- Statistiques descriptives : caractéristiques de l'échantillon, distribution des variables
  |
  +-- Statistiques inférentielles : test t, ANOVA, régression
  |
  +-- Analyse de médiation : méthode Bootstrap
  |
  +-- Analyse qualitative : codage thématique
         |
         v
[Validation des résultats]
  |
  +-- Test des hypothèses : H1/H2/H3 confirmées ?
  |
  +-- Test de robustesse : variables de remplacement, sous-échantillons
  |
  +-- Triangulation : cohérence entre résultats quantitatifs et qualitatifs
         |
         v
[Conclusions et recommandations]
  |
  +-- Contribution théorique : amélioration de la théorie des interactions en apprentissage en ligne
  |
  +-- Recommandations pratiques : conception de plateformes, stratégies pédagogiques
  |
  +-- Limites et recherches futures
`

## Analyse de faisabilité

### 1. Dimensions de la faisabilité de recherche

**Faisabilité théorique** :
- La problématique est-elle soutenue par la théorie ?
- Le cadre théorique est-il mature ?
- Les hypothèses sont-elles dérivables ?

**Faisabilité méthodologique** :
- La méthode de recherche est-elle adaptée à la problématique ?
- Les données sont-elles accessibles ?
- Les techniques d'analyse sont-elles maîtrisées ?

**Faisabilité des ressources** :
- Temps : le calendrier de recherche est-il raisonnable ?
- Financement : des fonds supplémentaires sont-ils nécessaires ?
- Équipement : un équipement spécial est-il nécessaire ?
- Personnel : des collaborateurs sont-ils nécessaires ?
- Données : des canaux d'accès aux données sont-ils disponibles ?

**Faisabilité personnelle** :
- Connaissances : disposez-vous des bases théoriques nécessaires ?
- Compétences : maîtrisez-vous les méthodes de recherche ?
- Soutien du directeur : le directeur est-il familier avec ce domaine ?
- Investissement en temps : pouvez-vous consacrer suffisamment de temps ?

### 2. Cadre d'analyse de faisabilité

`
Analyse de faisabilité

1. Faisabilité théorique
   - Base théorique : [Nom de la théorie] est largement appliquée dans [domaine], fournissant un soutien solide pour cette recherche
   - Lacune de recherche : les études existantes se concentrent principalement sur X, mais accordent peu d'attention à Y, cette recherche comble cette lacune
   - Conclusion de faisabilité : cadre théorique mature, hypothèses dérivables, faisabilité théorique confirmée

2. Faisabilité méthodologique
   - Méthode de recherche : [Nom de la méthode] est la méthode standard pour résoudre [problématique]
   - Accès aux données : [Source de données] a confirmé pouvoir fournir les données, ou [méthode de collecte] a été validée comme faisable
   - Techniques d'analyse : [Outil d'analyse] maîtrisé, ou [formation] planifiée
   - Conclusion de faisabilité : méthode mature, données accessibles, techniques maîtrisables, faisabilité méthodologique confirmée

3. Faisabilité des ressources
   - Temps : calendrier de recherche de [X mois], calendrier détaillé établi
   - Financement : [Source de financement] assurée, ou aucun financement supplémentaire nécessaire
   - Équipement : [Nom de l'équipement] disponible, ou [source de l'équipement] confirmée
   - Personnel : Directeur [nom] familier avec ce domaine, contact établi avec [collaborateur] qui a accepté la collaboration
   - Données : [Canal d'accès aux données] confirmé, ou [sujets d'enquête] ont accepté de participer
   - Conclusion de faisabilité : ressources suffisantes, ou alternatives déjà disponibles, faisabilité des ressources confirmée

4. Faisabilité personnelle
   - Connaissances : cours de [nom du cours] suivis, disposant de [base théorique]
   - Compétences : [compétence] maîtrisée, [formation/cours] complétée
   - Soutien du directeur : orientation de recherche du directeur : [direction], hautement pertinente pour cette recherche
   - Investissement en temps : [X heures] par semaine possibles, plan de gestion du temps établi
   - Conclusion de faisabilité : conditions personnelles répondent aux exigences de recherche, faisabilité personnelle confirmée

Conclusion générale : cette recherche est faisable sur les quatre dimensions : théorique, méthodologique, ressources et personnelle.
`

### 3. Exemple d'analyse de faisabilité

**Exemple : Recherche sur les interactions en éducation en ligne**

`
1. Faisabilité théorique
   - Base théorique : Le constructivisme social (Vygotsky) et la théorie de la charge cognitive (Sweller)
     sont largement appliqués dans la recherche en technologie éducative, fournissant un soutien théorique solide pour cette recherche.
   - Lacune de recherche : les études existantes se concentrent principalement sur la conception fonctionnelle des plateformes d'apprentissage en ligne,
     mais les études systématiques sur la manière dont les mécanismes d'interaction affectent les résultats d'apprentissage sont insuffisantes.
   - Conclusion de faisabilité : cadre théorique mature, hypothèses dérivables, faisabilité théorique confirmée.

2. Faisabilité méthodologique
   - Méthode de recherche : la conception quasi-expérimentale (groupe expérimental vs groupe témoin) est la méthode standard pour tester les relations causales,
     adaptée à cette problématique.
   - Accès aux données : collaboration établie avec la plateforme d'éducation en ligne XX, accès possible aux journaux d'apprentissage ;
     enquête par questionnaire distribuée via la plateforme, taux de réponse attendu >70%.
   - Techniques d'analyse : SPSS et Mplus maîtrisés, formation sur les modèles d'équations structurelles AMOS planifiée.
   - Conclusion de faisabilité : méthode mature, données accessibles, techniques maîtrisables, faisabilité méthodologique confirmée.

3. Faisabilité des ressources
   - Temps : calendrier de recherche de 12 mois (2023.9-2024.8), calendrier détaillé établi.
   - Financement : subvention du fonds XX obtenue (50 000 yuans), couvrant les frais d'enquête, d'entretien et de formation.
   - Équipement : ordinateur et logiciel SPSS disponibles, aucun équipement supplémentaire nécessaire.
   - Personnel : Le directeur, Professeur XX, spécialiste en technologie éducative, a publié plus de 10 articles pertinents ;
     collaboration établie avec la Faculté d'éducation de l'Université XX, qui a accepté de fournir une classe témoin.
   - Données : accord d'utilisation des données signé avec la plateforme, comité d'éthique approuvé.
   - Conclusion de faisabilité : ressources suffisantes, faisabilité des ressources confirmée.

4. Faisabilité personnelle
   - Connaissances : cours de psychologie éducative, statistiques éducatives, technologie éducative suivis,
     disposant d'une base théorique solide.
   - Compétences : formation avancée SPSS complétée, statistiques descriptives, inférentielles,
     analyse de régression maîtrisées ; apprentissage des modèles d'équations structurelles en cours.
   - Soutien du directeur : Le Professeur XX est un chercheur reconnu dans le domaine de la technologie éducative,
     orientation de recherche hautement pertinente pour cette recherche, accord de direction obtenu.
   - Investissement en temps : 20 heures par semaine possibles, plan détaillé de gestion du temps établi.
   - Conclusion de faisabilité : conditions personnelles répondent aux exigences de recherche, faisabilité personnelle confirmée.

Conclusion générale : cette recherche est faisable sur les quatre dimensions : théorique, méthodologique, ressources et personnelle,
peut être menée comme prévu.
`

## Plan de contingence

### 1. Identification des risques courants

**Risques liés aux données** :
- Risque : difficulté de collecte de données (faible taux de réponse, échantillon insuffisant)
- Risque : problèmes de qualité des données (valeurs manquantes, valeurs aberrantes)
- Risque : changement d'accès aux données (retrait du partenaire, fermeture de la plateforme)

**Risques méthodologiques** :
- Risque : méthode inadaptée (hypothèses non vérifiées, mauvais ajustement du modèle)
- Risque : difficultés techniques (erreurs logicielles, échec de l'analyse)
- Risque : manque de temps (apprentissage d'une nouvelle méthode trop long)

**Risques liés aux ressources** :
- Risque : insuffisance budgétaire (dépassement, frais supplémentaires)
- Risque : défaillance de l'équipement (ordinateur endommagé, logiciel expiré)
- Risque : changement de personnel (directeur en déplacement, collaborateur se retire)

**Risques personnels** :
- Risque : problèmes de santé (maladie, fatigue)
- Risque : conflits de temps (cours, examens, stages)
- Risque : manque de motivation (période de blocage, procrastination)

**Risques externes** :
- Risque : changements de politique (exigences de l'université, nouvelles réglementations éthiques)
- Risque : événements imprévus (pandémie, catastrophes naturelles)
- Risque : changements technologiques (mise à jour de la plateforme, changement de format de données)

### 2. Matrice d'évaluation des risques

`
Matrice d'évaluation des risques

Risque                    Probabilité(1-5)  Impact(1-5)  Niveau  Stratégie
------------------------------------------------------------
Faible taux de réponse    3                 4            Élevé   Distribution multi-canal, incitations
Échantillon insuffisant   2                 5            Élevé   Élargir l'échantillonnage, ajuster la conception
Méthode inadaptée         2                 4            Moyen   Méthode alternative, pré-test
Dépassement budgétaire    2                 3            Moyen   Marge budgétaire, demande de financement supplémentaire
Directeur en déplacement  3                 2            Faible  Communication en ligne, planification anticipée
Problèmes de santé        2                 3            Moyen   Gestion de la santé, temps de réserve
Changement de politique   1                 4            Faible  Suivi des évolutions, ajustement flexible
`

### 3. Stratégies de gestion des risques

**Stratégies de prévention (réduire la probabilité)** :
- Collecte de données : pré-test du questionnaire, distribution multi-canal, rappels programmés
- Échantillon : élargir le cadre d'échantillonnage, fixer un minimum d'échantillon
- Adéquation de la méthode : validation par la littérature, pré-test, consultation d'experts
- Budget : budget détaillé, marge de 10-20%
- Santé : routine régulière, exercice régulier, temps flexible

**Stratégies d'atténuation (réduire l'impact)** :
- Faible taux de réponse : augmenter la taille de l'échantillon, utiliser des pondérations
- Méthode inadaptée : préparer une méthode alternative, simplifier le modèle
- Dépassement budgétaire : prioriser les dépenses essentielles, rechercher un financement supplémentaire
- Directeur en déplacement : réunions en ligne, discuter des questions clés à l'avance
- Problèmes de santé : avancer par étapes, demander l'aide de collègues

**Stratégies d'urgence (après la survenance du risque)** :
- Taux de réponse <50% : élargir le cadre d'échantillonnage, passer à une recherche qualitative
- Échantillon insuffisant : utiliser Bootstrap, méthode bayésienne
- Échec complet de la méthode : passer à une recherche descriptive, étude de cas
- Épuisement budgétaire : demander un financement d'urgence, solliciter le soutien du directeur
- Maladie prolongée : demander un report, ajuster le plan de recherche

**Stratégies de transfert** :
- Collecte de données : confier à un organisme professionnel (nécessite un budget)
- Analyse des données : demander une consultation statistique (souvent gratuite à l'université)
- Problèmes techniques : acheter un service de support technique

### 4. Exemple de plan de contingence

**Exemple : Faible taux de réponse**

`
Risque : taux de réponse de l'enquête par questionnaire inférieur aux attentes (<50%)

Mesures de prévention :
- Conception du questionnaire : pré-test avec 10 personnes, s'assurer qu'il peut être complété en 5 minutes
- Canaux de distribution : email + WeChat + classe + notifications de la plateforme, couverture multi-canal
- Incitations : les 100 premiers à compléter reçoivent une récompense XX (matériel d'apprentissage, petit cadeau)
- Mécanisme de rappel : rappels à 3, 7 et 14 jours après la distribution

Mesures d'urgence :
- Taux de réponse 40-50% : élargir le cadre d'échantillonnage, ajouter 200 personnes
- Taux de réponse 30-40% : augmenter les incitations, passer à un tirage au sort (100% de chances de gagner)
- Taux de réponse <30% : passer à une recherche qualitative (20 entretiens approfondis)
- Taux de réponse <20% : discuter avec le directeur, ajuster la conception de recherche

Indicateurs de suivi :
- Nombre quotidien de réponses
- Tendance du taux de réponse
- Représentativité de l'échantillon (comparaison avec la population)
`

### 5. Rédaction du plan de contingence dans la proposition de recherche

`
【Plan de contingence】

Cette recherche identifie les principaux risques suivants et établit les plans de contingence correspondants :

1. Risque de collecte de données
   Description du risque : le taux de réponse de l'enquête par questionnaire peut être inférieur aux attentes.
   Mesures de prévention : distribution multi-canal (email + WeChat + classe), rappels programmés, incitations.
   Mesures d'urgence : si le taux de réponse <50%, élargir le cadre d'échantillonnage ou augmenter les incitations ; si <30%,
             passer à une recherche qualitative (entretiens approfondis).

2. Risque d'adéquation de la méthode
   Description du risque : le modèle d'équations structurelles peut mal s'ajuster.
   Mesures de prévention : pré-test pour valider le modèle, consultation d'un expert en statistiques.
   Mesures d'urgence : si le modèle s'ajuste mal, utiliser une méthode alternative (analyse de régression, ANOVA)
             ou simplifier le modèle.

3. Risque de temps
   Description du risque : la collecte de données peut être retardée, affectant l'analyse ultérieure.
   Mesures de prévention : établir un calendrier détaillé, prévoir 2 mois de marge.
   Mesures d'urgence : si le retard >1 mois, demander un report de la thèse ou simplifier l'analyse.

4. Risque de ressources
   Description du risque : le budget peut être dépassé.
   Mesures de prévention : budget détaillé, marge de 20%, prioriser les dépenses essentielles.
   Mesures d'urgence : si dépassement, demander un financement supplémentaire ou solliciter le soutien du directeur.

Grâce à ces plans, cette recherche peut efficacement faire face aux risques potentiels, assurant le bon déroulement de la recherche.
`

## Modèle de structure de la proposition de recherche

### Structure complète

`
1. Contexte et signification de la recherche
   1.1 Contexte pratique (origine du problème)
   1.2 Contexte théorique (contexte académique)
   1.3 Signification de la recherche (théorique + pratique)

2. Revue de littérature
   2.1 Définition des concepts clés
   2.2 État de la recherche nationale et internationale
   2.3 Évaluation de la recherche (lacunes)

3. Objectifs et contenu de la recherche
   3.1 Objectifs de recherche (spécifiques, mesurables)
   3.2 Contenu de la recherche (développement point par point)
   3.3 Hypothèses de recherche (le cas échéant)

4. Méthodologie et feuille de route technique
   4.1 Méthodologie (approche méthodologique + méthodes spécifiques)
   4.2 Feuille de route technique (visualisation)
   4.3 Outils de recherche (questionnaires, échelles, équipement)
   4.4 Plan d'échantillonnage (population, échantillon, méthode d'échantillonnage)

5. Analyse de faisabilité
   5.1 Faisabilité théorique
   5.2 Faisabilité méthodologique
   5.3 Faisabilité des ressources
   5.4 Faisabilité personnelle

6. Plan de contingence
   6.1 Identification des risques
   6.2 Évaluation des risques
   6.3 Stratégies de gestion

7. Plan de recherche et calendrier
   7.1 Phases
   7.2 Jalons
   7.3 Diagramme de Gantt

8. Résultats attendus et points d'innovation
   8.1 Résultats attendus (thèses, brevets, logiciels, etc.)
   8.2 Points d'innovation (théorie, méthodologie, applications)

9. Références
`

### Suggestions de répartition des mots

| Section | Licence (3000-5000 mots) | Master (8000-15000 mots) | Doctorat (20000-30000 mots) |
|---------|--------------------------|--------------------------|------------------------------|
| Contexte de recherche | 500-800 | 1000-2000 | 2000-3000 |
| Revue de littérature | 1000-1500 | 3000-5000 | 8000-12000 |
| Objectifs de recherche | 300-500 | 500-1000 | 1000-2000 |
| Méthodologie | 500-800 | 1500-2500 | 3000-5000 |
| Analyse de faisabilité | 300-500 | 500-1000 | 1000-2000 |
| Plan de contingence | 200-300 | 300-500 | 500-1000 |
| Calendrier | 200-300 | 300-500 | 500-1000 |
| Résultats attendus | 200-300 | 300-500 | 500-1000 |

## Questions fréquentes et solutions

### Q : La feuille de route technique est trop simple/trop complexe ?
- Simple : ajouter des sous-processus, des points de décision, des boucles de rétroaction
- Complex : fusionner les éléments similaires, abstraction à un niveau supérieur, détails en annexe

### Q : L'analyse de faisabilité ressemble à de l'autosatisfaction ?
- Énoncer objectivement : utiliser « disponible », « confirmé » plutôt que « je suis excellent »
- Reconnaître les limites : « Bien que l'expérience en X soit insuffisante, cela a été compensé par Y »
- Citer des preuves : résultats de cours, certificats de formation, articles du directeur

### Q : Le plan de contingence semble être une formalité ?
- Être spécifique : ne pas écrire « des problèmes peuvent survenir », mais « le taux de réponse peut être <50% »
- Quantifier : probabilité, impact, seuil
- Être opérationnel : ne pas écrire « renforcer la gestion », mais « envoyer un email de rappel dans 3 jours »

### Q : Les points d'innovation sont insuffisants ?
- Redéfinir : ce n'est pas « entièrement nouveau », mais « nouvelle combinaison », « nouvelle application », « nouvelle perspective »
- Comparer : différences spécifiques avec les études existantes
- Exprimer avec modération : « tenter », « explorer », « améliorer » plutôt que « pionnier », « révolutionnaire »

## Ressources recommandées

1. **Outils de feuille de route technique** :
   - ProcessOn : www.processon.com
   - Draw.io : app.diagrams.net
   - Lucidchart : www.lucidchart.com

2. **Outils de gestion de projet** :
   - GanttProject : diagramme de Gantt gratuit
   - Microsoft Project : gestion de projet professionnelle
   - Excel : diagramme de Gantt simple (mise en forme conditionnelle)

3. **Outils d'évaluation des risques** :
   - Modèle de matrice de risques : modèle Excel
   - Simulation Monte Carlo : @RISK, Crystal Ball

4. **Livres de référence** :
   - « Conception et méthodes de recherche » (Bordens & Abbott)
   - « Guide de rédaction de thèse » (Pan Maoyuan)
   - « Comment rédiger une proposition de recherche » (Locke et al.)


﻿# Guide de révision et de polissage de la thèse

## Auto-révision

### 1. Phases de révision

**Phase de repos (1-3 jours)** :
- Après avoir terminé le premier brouillon, le laisser reposer 1-3 jours avant de réviser
- Raison : la distance crée l'objectivité, facilitant la détection des problèmes
- Activités : lecture de littérature, traitement des données, repos

**Première passe : révision structurelle (macro)**
- Vérifier la chaîne logique : introduction → méthodologie → résultats → discussion → conclusion
- Vérifier l'équilibre des chapitres : nombre de mots par chapitre raisonnable
- Vérifier les niveaux de titres : clarté, cohérence
- Vérifier les transitions : continuité entre chapitres et sections

**Deuxième passe : révision du contenu (méso)**
- Vérifier les arguments : chaque paragraphe a-t-il un argument clair
- Vérifier les preuves : les preuves soutiennent-elles les arguments
- Vérifier le raisonnement : la logique est-elle rigoureuse
- Vérifier les répétitions : y a-t-il du contenu redondant
- Vérifier les omissions : y a-t-il du contenu important manquant

**Troisième passe : révision linguistique (micro)**
- Vérifier la grammaire : accord sujet-verbe, temps, articles
- Vérifier l'orthographe : fautes de frappe, terminologie spécialisée
- Vérifier la ponctuation : mélange de ponctuation chinoise et anglaise
- Vérifier le format : police, taille, interligne
- Vérifier les citations : cohérence du format, correspondances

**Quatrième passe : mise au point des détails (raffinement)**
- Vérifier les figures et tableaux : numérotation, titres, clarté
- Vérifier les données : chiffres, unités, pourcentages
- Vérifier les références : exhaustivité, format
- Vérifier les annexes : numérotation, correspondances

### 2. Liste de contrôle pour l'auto-révision

**Liste de contrôle structurelle** :
- [ ] Le résumé inclut-il l'objectif, la méthodologie, les résultats et les conclusions ?
- [ ] L'introduction va-t-elle du macro au micro, avec une problématique claire à la fin ?
- [ ] La revue de littérature est-elle clairement classée et critique ?
- [ ] La section méthodologique est-elle suffisamment détaillée pour être reproductible ?
- [ ] La section résultats présente-t-elle objectivement sans interprétation ?
- [ ] La discussion interprète-t-elle les résultats, compare-t-elle avec la littérature, identifie-t-elle les limites ?
- [ ] La conclusion répond-elle à la problématique sans introduire de nouveau contenu ?
- [ ] Les proportions sont-elles raisonnables (introduction 10%, littérature 20%, méthodologie 15%, résultats 20%, discussion 25%, conclusion 10%) ?

**Liste de contrôle du contenu** :
- [ ] Chaque paragraphe a-t-il une phrase thématique ?
- [ ] Y a-t-il des transitions entre les paragraphes ?
- [ ] Y a-t-il du contenu hors sujet ?
- [ ] Y a-t-il du contenu répétitif ?
- [ ] Y a-t-il des références importantes manquantes ?
- [ ] Les données sont-elles à jour ?
- [ ] Les conclusions sont-elles surinterprétées ?

**Liste de contrôle linguistique** :
- [ ] Y a-t-il des expressions familières ?
- [ ] Y a-t-il des formulations vagues ?
- [ ] Y a-t-il des formulations absolues ?
- [ ] Y a-t-il des phrases longues et complexes (>30 mots) ?
- [ ] Y a-t-il une surutilisation de la voix passive ?
- [ ] Y a-t-il du franglais ?
- [ ] La terminologie est-elle cohérente ?

### 3. Méthode de lecture à voix haute

**Méthode** :
- Lire l'intégralité de la thèse à voix haute
- Ou : utiliser un outil de synthèse vocale (lecture Word, navigateur Edge)

**Problèmes détectés** :
- Phrases difficiles : la lecture est laborieuse, nécessite une réécriture
- Vocabulaire répétitif : mots identiques consécutifs, nécessite un remplacement
- Sauts logiques : après la lecture d'un paragraphe, on ne comprend pas
- Problèmes de ton : trop assertif, trop hésitant, non objectif

### 4. Méthode du plan inversé

**Méthode** :
- Après la lecture d'un paragraphe, résumer le contenu principal en une phrase
- L'écrire sur un post-it ou en marge du document
- Une fois terminé, ne regarder que les phrases de résumé

**Vérification** :
- Les phrases de résumé forment-elles une chaîne logique ?
- Y a-t-il des phrases de résumé qui ne correspondent pas au titre ?
- Y a-t-il des paragraphes consécutifs dont les résumés sont répétitifs ?
- Y a-t-il des paragraphes impossibles à résumer (contenu désordonné) ?

## Traitement des retours du directeur

### 1. Attitude face aux retours

**Bonne attitude** :
- Le directeur est un aide, pas un critique
- Les retours sont des consultations gratuites d'expert
- Chaque amélioration améliore la qualité de la thèse
- Le « je ne comprends pas » du directeur est souvent le « je ne comprends pas » du lecteur

**Attitudes à éviter** :
- Défensive : « je n'ai pas tort, c'est le directeur qui n'a pas compris »
- Résistante : « autant de modifications, autant réécrire »
- Procrastinatrice : « on verra plus tard »
- Sélective : « je ne modifie que ce qui est facile, j'ignore le difficile »

### 2. Types de retours et réponses

**Type 1 : Retours directionnels**
- Caractéristiques : « suggère d'ajuster le cadre de recherche », « suggère d'ajouter la théorie XX »
- Réponse : rencontrer le directeur, confirmer la direction spécifique, établir un plan de modification
- Attention : peut impliquer une réécriture importante, traiter rapidement

**Type 2 : Retours sur le contenu**
- Caractéristiques : « les preuves sont insuffisantes ici », « suggère d'ajouter les données XX »
- Réponse : ajouter de la littérature, des données, des exemples, ou supprimer cet argument
- Attention : vérifier les sources des données, assurer leur fiabilité

**Type 3 : Retours structurels**
- Caractéristiques : « suggère de fusionner les chapitres 2 et 3 », « suggère de réorganiser les chapitres »
- Réponse : élaborer un plan de restructuration, exécuter après confirmation du directeur
- Attention : utiliser la vue plan pour éviter la perte de contenu

**Type 4 : Retours linguistiques**
- Caractéristiques : « expression peu claire », « suggère de condenser », « erreurs grammaticales »
- Réponse : modifier point par point, demander l'aide d'un locuteur natif ou d'un service de polissage
- Attention : uniformiser le style de modification, éviter les incohérences

**Type 5 : Retours sur le format**
- Caractéristiques : « figures et tableaux non conformes », « format de citation incorrect »
- Réponse : comparer avec le modèle de l'université, modifier point par point
- Attention : utiliser les styles pour éviter les ajustements manuels

### 3. Processus de traitement des retours

**Étape 1 : Organiser les retours**
- Classifier les retours : direction/contenu/structure/langue/format
- Marquer les priorités : doit être modifié/suggéré/optionnel
- Marquer la difficulté : facile/moyen/difficile
- Créer un tableau : contenu du retour | type | priorité | difficulté | plan de modification | statut

**Étape 2 : Établir un plan**
- Trier par priorité : d'abord les directionnels, puis les sur le contenu, enfin les sur le format
- Alterner par difficulté : facile + difficile, pour éviter l'épuisement
- Fixer du temps : temps prévu pour chaque type de retour
- Prévoir une marge : 20% du temps total pour les imprévus

**Étape 3 : Exécuter les modifications**
- Se concentrer sur un type : ne traiter qu'un type de retour à la fois
- Marquer les compléments : marquer « terminé » après modification
- Enregistrer les problèmes : noter les raisons pour les modifications impossibles
- Garder des versions : sauvegarder une nouvelle version à chaque série de modifications

**Étape 4 : Revérification**
- Vérifier point par point : chaque retour a-t-il été traité
- Validation croisée : les modifications n'introduisent-elles pas de nouveaux problèmes
- Vérification globale : le texte complet est-il cohérent après modification
- Soumettre au directeur : avec un rapport de modifications

### 4. Rédaction du rapport de modifications

`
Rapport de modifications

Cher directeur,

Merci pour vos précieux commentaires. J'ai effectué les modifications suivantes, détaillées ci-dessous :

I. Modifications directionnelles (3 points)
1. Concernant l'ajustement du cadre de recherche
   - Problème initial : cadre de recherche trop ambitieux
   - Plan de modification : se concentrer sur la variable XX, supprimer la variable YY
   - Emplacement : chapitre 1, section 3, chapitre 3
   - Statut : terminé

2. ...

II. Modifications du contenu (5 points)
1. Concernant l'ajout de la théorie XX
   - Problème initial : la revue de littérature manque de perspective théorique XX
   - Plan de modification : ajouter la théorie XX (chapitre 2, section 2, 500 mots supplémentaires)
   - Nouvelles références : Smith (2020), Jones (2021)
   - Statut : terminé

2. ...

III. Modifications structurelles (2 points)
...

IV. Modifications linguistiques (8 points)
...

V. Modifications du format (10 points)
...

Commentaires non modifiés et raisons :
1. Concernant la suppression du chapitre XX : ce chapitre est la base de l'analyse ultérieure, suggéré de le conserver
   (confirmé lors d'un entretien avec le directeur, accord pour le conserver)

2. ...

Le texte complet a été mis à jour après modification, veuillez réviser.

Étudiant : XXX
Date : 202X/XX/XX
`

## Évaluation par les pairs

### 1. Choisir les évaluateurs

**Critères** :
- Même domaine : direction de recherche similaire, compréhension du contenu
- Perspective différente : approche méthodologique, orientation théorique différente, offrant de nouvelles perspectives
- Expérience : étudiants de dernière année, post-doctorants, jeunes enseignants
- Fiable : confidentialité, constructivité, pas de plagiat

**Canaux** :
- Même laboratoire : collègues plus anciens, camarades de promotion
- Cercle académique : rencontres en conférences, réseaux sociaux
- Groupes d'écriture : membres de groupes d'évaluation mutuelle réguliers
- Services professionnels : certains universités proposent des centres d'écriture

### 2. Demande d'évaluation

**Modèle d'email** :
`
Objet : Demande d'évaluation de thèse - [Titre de la thèse]

Cher XX,

Bonjour ! Je suis XXX, étudiant en master/doctorat à l'Université XX, spécialité XX, actuellement en rédaction d'une thèse sur [sujet de recherche].

J'ai appris que vous avez des recherches approfondies dans [domaine spécifique], et j'aimerais vous inviter à fournir des commentaires d'évaluation sur ma thèse. La thèse se concentre principalement sur [problématique centrale], utilise [méthode], et a initialement trouvé [conclusion principale].

Si cela vous convient, j'aimerais recevoir vos commentaires avant le [date]. Les points clés d'évaluation sont :
1. Le cadre de recherche est-il raisonnable ?
2. La section méthodologique est-elle claire et reproductible ?
3. Le raisonnement est-il rigoureux ?
4. L'expression linguistique est-elle précise ?

La thèse compte environ [X milliers de mots], envoyée sous forme de document Word.

Que vous soyez disponible ou non, merci pour votre considération !

Cordialement,

XXX
[Coordonnées]
`

### 3. Fournir un guide d'évaluation

**Instructions pour les évaluateurs** :
`
Merci d'avoir accepté d'évaluer ma thèse ! Voici le guide d'évaluation :

Informations sur la thèse :
- Titre : [Titre]
- Type : thèse de master/doctorat
- Phase : premier brouillon/révision/avant version finale
- Nombre de mots : [X milliers de mots]

Points clés d'évaluation (par ordre de priorité) :
1. Structure logique : l'organisation des chapitres est-elle raisonnable ? Les transitions sont-elles naturelles ?
2. Qualité du raisonnement : les arguments sont-ils clairs ? Les preuves sont-elles suffisantes ? Le raisonnement est-il rigoureux ?
3. Description méthodologique : est-elle suffisamment détaillée pour être reproductible ? Y a-t-il des omissions ?
4. Revue de littérature : est-elle complète ? La classification est-elle raisonnable ? L'analyse critique est-elle appropriée ?
5. Expression linguistique : y a-t-il des passages obscurs, redondants, familiers ?
6. Conformité au format : figures, tableaux, citations, références sont-ils conformes ?

Forme de retour :
- Évaluation générale (200-500 mots)
- Commentaires détaillés (par chapitre ou par type)
- Priorité marquée (haute/moyenne/basse)

Date limite : avant le [date]
Moyen : email/WeChat/entretien

Merci encore !
`

### 4. Traiter les retours de l'évaluation par les pairs

**Principes** :
- Tous les commentaires méritent considération, même s'ils ne sont pas adoptés
- La plupart des commentaires doivent être adoptés, surtout ceux soulevés par plusieurs personnes
- Les non-adoptions doivent avoir des raisons suffisantes, pouvant être notées

**Processus** :
1. Collecter tous les commentaires, les classer et les organiser
2. Marquer la fréquence d'apparition (soulevé par plusieurs = important)
3. Établir un plan de modification
4. Exécuter les modifications
5. Retourner aux évaluateurs (remerciements + description des modifications)

## Polissage linguistique

### 1. Techniques d'auto-polissage

**Simplification** :
- Supprimer les redondances : « very », « quite », « rather », « really »
- Supprimer les remplissages : « it is important to note that », « there is no doubt that »
- Supprimer les répétitions : ne pas redéfinir les termes dans la même section
- Supprimer le langage familier : « get », « big », « good », « bad », « thing », « stuff »

**Renforcement** :
- Verbe au lieu de nom : « make an analysis » → « analyze »
- Actif au lieu de passif (avec modération) : « It was found that » → « We found that »
- Concret au lieu d'abstrait : « good results » → « results improved by 25% »
- Adjectif fort au lieu de « very + adjectif »

**Cohérence** :
- Ajouter des connecteurs : « Furthermore », « However », « Therefore », « In contrast »
- Ajouter des références : « This finding », « These results », « That approach »
- Ajouter des résumés : phrase de résumé en fin de paragraphe, phrase de transition en fin de chapitre

### 2. Outils d'aide

**Vérification grammaticale** :
- Grammarly : détection de la grammaire, orthographe, style
- LanguageTool : open source, interface en français
- Writefull : spécialement pour l'écriture académique, basé sur l'IA

**Vérification stylistique** :
- Hemingway Editor : détection de la lisibilité, marquage des phrases longues
- ProWritingAid : analyse stylistique complète
- Français : outils d'aide à la rédaction

**Vérification terminologique** :
- Cohérence terminologique : recherche et remplacement, assurer l'uniformité
- Précision terminologique : comparer avec la littérature de référence
- Première occurrence d'un terme : nom complet + abréviation

### 3. Services de polissage professionnel

**Situations applicables** :
- Article en anglais soumis à une revue internationale
- Problèmes linguistiques nombreux, difficile à améliorer par auto-révision
- Temps limité, besoin d'un polissage rapide

**Types de services** :
- Polissage linguistique : grammaire, orthographe, style (0,03-0,08 €/mot)
- Polissage approfondi : langue + suggestions de contenu (0,08-0,15 €/mot)
- Polissage scientifique : langue + précision scientifique (0,15-0,30 €/mot)

**Critères de sélection** :
- Qualifications des éditeurs : locuteur natif, formation disciplinaire
- Garantie de service : assurance qualité, modifications après livraison
- Accord de confidentialité : signature d'un NDA
- Engagement de délai : respect des délais

**Services connus** :
- Elsevier Language Services
- Springer Nature Author Services
- Wiley Editing Services
- Editage
- Medjaden
- Enago

### 4. Vérification après polissage

**Vérifications obligatoires** :
- Les termes techniques ont-ils été modifiés incorrectement (les termes spécialisés sont souvent « corrigés » en mots courants)
- Les données ont-elles été modifiées incorrectement (chiffres, unités, pourcentages)
- Les citations ont-elles été modifiées incorrectement (noms d'auteurs, dates, pages)
- La logique a-t-elle été modifiée incorrectement (les connecteurs modifiés inversent la logique)
- Le format a-t-il été modifié incorrectement (position des figures et tableaux, numérotation)

**Recommandations** :
- Relire soi-même après le polissage
- Comparer avec l'original, vérifier les informations clés
- Demander à un camarade de vérifier

## Gestion des versions de révision

### 1. Normes de dénomination

**Date + version** :
- These_20230615_v1.docx
- These_20230701_v2.docx
- These_20230715_v3_Final.docx
- These_20230720_v3_Final_Final.docx (à éviter !)

**Phase + version** :
- These_premier_brouillon_v1.docx
- These_revision_directeur1_v2.docx
- These_revision_directeur2_v3.docx
- These_pre-soutenance_v4.docx
- These_version_finale_v5.docx

### 2. Stratégie de sauvegarde

**Sauvegarde locale** :
- Disque dur de l'ordinateur (version de travail)
- Disque dur externe (sauvegarde hebdomadaire)
- Clé USB (sauvegarde d'urgence)

**Sauvegarde dans le cloud** :
- OneDrive/Google Drive/Dropbox (synchronisation automatique)
- Cloud de l'université (réseau éducatif rapide)
- Envoi par email (s'envoyer un email à soi-même)

**Outils de version** :
- Git/GitHub (adapté au code + texte)
- Historique des versions Word (sauvegarde automatique)
- Copie manuelle (simple et fiable)

### 3. Enregistrement des modifications

**Contenu à enregistrer** :
- Date de modification
- Auteur de la modification (soi-même/directeur/évaluateur)
- Type de modification (structure/contenu/langue/format)
- Emplacement (chapitre/page)
- Raison de la modification (retour/découverte personnelle)

**Méthode d'enregistrement** :
- Propriétés du document : Word → Fichier → Informations → Propriétés
- Journal des modifications : document séparé
- Commentaires : fonction de commentaires Word
- Comparaison de versions : Word → Révision → Comparer

## Questions fréquentes

### Q : La révision dégrade la qualité ?
- Cause : révision excessive, perte de vue d'ensemble
- Solution : imprimer le texte complet, lire hors ligne ; ou lire à voix haute
- Prévention : chaque série de révisions se concentre sur un type de problème

### Q : Les retours du directeur sont contradictoires ?
- Solution : communiquer avec le directeur, confirmer l'ordre de priorité
- Stratégie : se baser sur sa propre problématique, expliquer les choix
- Attention : enregistrer les résultats de la communication, éviter les allers-retours

### Q : Pas assez de temps pour une révision approfondie ?
- Priorité : structure > contenu > langue > format
- Stratégie : d'abord corriger les erreurs graves (failles logiques, erreurs factuelles), puis les erreurs légères (polissage linguistique)
- Aide : demander à un camarade d'aider pour la mise en forme, la vérification linguistique

### Q : Nombreuses révisions mais toujours insatisfait ?
- Accepter : une thèse n'est jamais parfaite, seulement suffisamment bonne
- Standard : atteindre les exigences de diplôme, réussir la soutenance
- Futur : continuer à améliorer après l'obtention du diplôme, soumettre pour publication

## Ressources recommandées

1. **Outils de révision** :
   - Grammarly : grammarly.com
   - Hemingway Editor : hemingwayapp.com
   - ProWritingAid : prowritingaid.com

2. **Services de polissage** :
   - Elsevier Language Services
   - Springer Nature Author Services
   - Editage : www.editage.com

3. **Livres sur l'écriture** :
   - « Écrire » (Stephen King)
   - « The Sense of Style » (Steven Pinker)
   - « Guide d'écriture académique » (Helen Sword)

4. **Stratégies de révision** :
   - « Révision : l'art de l'écriture académique » (Wendy Bishop)
   - « Comment réviser sa thèse » (Booth et al.)


﻿# Guide des étapes de rédaction de la thèse

## Étape 1 : Diagnostic du sujet

### Principes de choix du sujet
- **Valeur** : valeur académique ou pratique
- **Innovation** : nouvelle perspective, nouvelle méthode, nouveau matériel, nouvelle conclusion
- **Faisabilité** : adéquation avec le temps, les ressources et les compétences
- **Clarté** : problème spécifique, limites claires

### Méthodes de choix du sujet
1. **Littérature-driven** : identifier les lacunes, contradictions, vides
2. **Problème-driven** : problèmes rencontrés dans la pratique
3. **Méthode-driven** : application d'une nouvelle méthode à un ancien problème
4. **Interdisciplinaire** : perspective interdisciplinaire

### Liste d'évaluation du sujet
- [ ] Le problème de recherche peut-il être clairement exprimé en une phrase ?
- [ ] Y a-t-il de la littérature de soutien ?
- [ ] Les données/matériaux sont-ils accessibles ?
- [ ] La recherche peut-être achevée en 6-12 mois ?
- [ ] Le directeur approuve-t-il ?
- [ ] Le sujet correspond-il à l'orientation de la formation ?

## Étape 2 : Proposition de recherche

### Structure standard
1. **Contexte de recherche**
   - Contexte macro (social/académique)
   - Contexte micro (phénomène spécifique)
   - Problématique (du contexte au problème)

2. **Revue de littérature**
   - Évolution de la recherche (chronologique/thématique/méthodologique)
   - Points de vue principaux (classification)
   - Insuffisances de la recherche (analyse des lacunes)
   - Positionnement de l'étude (déclaration de contribution)

3. **Contenu de la recherche**
   - Objectifs de recherche (global + spécifique)
   - Questions de recherche (3-5 questions spécifiques)
   - Hypothèses de recherche (le cas échéant)
   - Feuille de route technique (diagramme de flux)

4. **Méthodologie**
   - Approche méthodologique (empirique/normative/interprétative)
   - Méthodes spécifiques (quantitatives/qualitatives/mixtes)
   - Sources de données
   - Outils d'analyse

5. **Points d'innovation**
   - Innovation théorique
   - Innovation méthodologique
   - Innovation matérielle
   - Innovation conceptuelle

6. **Plan de recherche**
   - Calendrier (diagramme de Gantt)
   - Résultats attendus
   - Risques et réponses

### Préparation à la soutenance de la proposition
- Présentation de 10-15 minutes
- Préparer les réponses : pourquoi ce sujet ? pourquoi cette méthode ? faisabilité ?
- Enregistrer les commentaires du jury, modifier après la soutenance

## Étape 3 : Construction du plan

### Types de plans
- **Plan par chapitres** : niveaux de titres des chapitres
- **Plan logique** : relation progressive des arguments
- **Plan par fiches** : contenu principal de chaque paragraphe

### Éléments du plan
- Argument principal de chaque chapitre
- Preuves/matériaux/données
- Relation logique avec les chapitres précédents et suivants
- Nombre de mots estimé

### Vérification du plan
- [ ] La logique est-elle cohérente ?
- [ ] Les niveaux sont-ils clairs ?
- [ ] Les proportions sont-elles équilibrées ?
- [ ] Y a-t-il des redondances ?
- [ ] Toutes les questions de recherche sont-elles couvertes ?

## Étape 4 : Rédaction chapitre par chapitre

### Ordre de rédaction suggéré
1. **Écrire d'abord** : revue de littérature, méthodologie (relativement indépendants)
2. **Écrire ensuite** : analyse des données, études de cas (travail principal)
3. **Écrire après** : introduction, conclusion (nécessitant une vision globale)
4. **Écrire en dernier** : résumé, mots-clés

### Structure de chaque chapitre
- **Paragraphe d'introduction** : objectif du chapitre, lien avec l'ensemble, aperçu du contenu principal
- **Paragraphes du corps** : argument + preuve + analyse (structure PEEL)
  - Point : argument
  - Evidence : preuve
  - Explanation : explication
  - Link : retour à l'argument/transition vers le prochain argument
- **Paragraphe de conclusion** : résumé des découvertes, transition

### Techniques de rédaction
- **Régularité quotidienne** : écrire à heure fixe, créer une habitude
- **D'abord terminer, puis perfectionner** : premier brouillon sans perfectionnisme, d'abord écrire
- **Par paragraphes** : écrire un paragraphe à la fois, réduire la pression
- **Marquer les points à améliorer** : utiliser TODO pour les points incertains

## Étape 5 : Révision et perfectionnement

### Liste d'auto-vérification
- [ ] Les arguments sont-ils clairs ?
- [ ] Les preuves sont-elles suffisantes ?
- [ ] La logique est-elle rigoureuse ?
- [ ] La langue est-elle précise ?
- [ ] Le format est-il conforme ?
- [ ] Les citations sont-elles complètes ?

### Niveaux de révision
1. **Macro** : restructuration, ajout/suppression de chapitres, réorganisation logique
2. **Méso** : réorganisation des paragraphes, optimisation des transitions, renforcement de l'argumentation
3. **Micro** : polissage des phrases, standardisation de la ponctuation, uniformisation du format

### Traitement des retours du directeur
- Distinguer « doit être modifié » et « suggéré de modifier »
- Communiquer activement sur les points incompréhensibles
- Marquer les modifications apportées
- Conserver les enregistrements des modifications

## Étape 6 : Conformité au format

### Exigences de format courantes
- **Page de garde** : format uniforme de l'université
- **Résumé** : en français et en anglais, 300-500 mots
- **Table des matières** : génération automatique, trois niveaux de titres
- **Corps du texte** :
  - Police : Times New Roman
  - Taille : 12pt
  - Interligne : 1,5 ou fixe 20 points
  - Marges : haut/bas 2,54 cm, gauche/droite 3,17 cm
- **Figures et tableaux** :
  - Titre des figures en bas, titre des tableaux en haut
  - Numérotation : Figure 1-1, Tableau 2-1
  - Indication de la source
- **Références** :
  - Format : APA 7e édition
  - Types : ouvrage [M], article de revue [J], thèse [D], conférence [C], ressource électronique [EB/OL]

### Outils de mise en page
- **Word** : styles, listes à niveaux, légendes
- **LaTeX** : Overleaf, modèles
- **Références** : EndNote, Zotero, Mendeley

## Étape 7 : Vérification anti-plagiat et soutenance

### Préparation à la vérification anti-plagiat
- **Auto-vérification** : logiciels de détection de plagiat (Turnitin, Compilatio)
- **Stratégies de réduction** :
  - Remplacement synonymique (maintenir la précision académique)
  - Restructuration des phrases (transformation actif/passif)
  - Conversion en graphiques (texte en tableaux/figures)
  - Conformité des citations (marquage des citations directes)
- **Précautions** :
  - Conserver la terminologie spécialisée
  - Reformuler les descriptions de formules
  - Les textes de loi/citations poétiques ne sont pas comptés (mais marqués)
  - La liste de références n'est pas comptée

### Préparation à la soutenance
- **Préparation du support** :
  - 15-20 diapositives
  - Problématique, méthodologie, résultats, contributions
  - Figures et tableaux principalement, texte concis
  - Préparer un discours (ne pas lire les diapositives)

- **Questions de soutenance** :
  - Pourquoi ce sujet ?
  - Où sont les innovations ?
  - Quelles sont les limites de la méthodologie ?
  - Comment interpréter un résultat spécifique ?
  - Comment améliorer si c'était à refaire ?

- **Éthique de soutenance** :
  - Tenue formelle
  - Maîtrise du temps (présentation 15-20 minutes)
  - Réponse humble aux critiques
  - Enregistrement des commentaires de modification

### Après la soutenance
- Organiser les commentaires de modification
- Confirmer le périmètre de modification avec le directeur
- Soumettre la version modifiée dans les délais
- Vérification finale du format
- Soumettre les versions électronique et papier
