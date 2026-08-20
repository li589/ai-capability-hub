# Guide de rédaction d'articles en médecine / sciences de la vie

## Caractéristiques de la discipline
- Accent sur la médecine fondée sur les preuves, la validation expérimentale et les données cliniques
- Importance accordée à l'éthique, au consentement éclairé et à la protection de la vie privée
- Articles de revues > articles de conférence (revues de premier plan : NEJM/Lancet/JAMA/Nature Medicine/Cell)
- Normes d'écriture strictes : déclarations CONSORT, PRISMA, STROBE, etc.

## Types de recherche

### 1. Essai contrôlé randomisé (ECR)
- **Applicabilité** : évaluation de l'efficacité d'un médicament/d'une intervention
- **Points clés de conception** :
  - Méthode de randomisation (simple/stratifiée/blocs)
  - Insu (simple/double/triple)
  - Type de comparateur (placebo/actif/absence de traitement)
  - Calcul de la taille d'échantillon (analyse de puissance)
- **Normes de rapport** : déclaration CONSORT 2010 + organigramme
- **Exigence d'enregistrement** : ClinicalTrials.gov ou registre des essais cliniques chinois

### 2. Étude de cohorte
- **Applicabilité** : exploration étiologique, facteurs pronostiques
- **Types** : prospective/rétrospective/ambispective
- **Points clés de conception** :
  - Définition claire de l'exposition
  - Protocole de suivi complet
  - Contrôle du taux de perdus de vue (<20%)
  - Contrôle des facteurs de confusion
- **Normes de rapport** : déclaration STROBE

### 3. Étude cas-témoins
- **Applicabilité** : maladies rares, maladies à longue période de latence
- **Points clés de conception** :
  - Définition claire des cas (gold standard)
  - Sélection appropriée des témoins (hôpital/communauté/population)
  - Choix des facteurs d'appariement
  - Contrôle du biais de mémoire
- **Normes de rapport** : déclaration STROBE

### 4. Étude transversale
- **Applicabilité** : enquête de prévalence, description de l'état actuel
- **Points clés de conception** :
  - Méthode d'échantillonnage (stratifié à plusieurs étapes)
  - Taille de l'échantillon (estimation de la prévalence)
  - Fiabilité et validité de l'outil d'enquête
- **Normes de rapport** : déclaration STROBE (extension transversale)

### 5. Méta-analyse
- **Applicabilité** : synthèse des preuves, comparaison d'efficacité
- **Types** :
  - Méta-analyse interventionnelle (ECR)
  - Méta-analyse diagnostique
  - Méta-analyse en réseau (NMA)
  - Méta-analyse de données individuelles (IPD)
- **Normes de rapport** : déclaration PRISMA 2020 + enregistrement (PROSPERO)
- **Points clés d'analyse** :
  - Test d'hétérogénéité (statistique I²)
  - Biais de publication (funnel plot, test d'Egger)
  - Analyse de sensibilité
  - Qualité des preuves (graduation GRADE)

### 6. Revue systématique
- **Applicabilité** : synthèse complète des preuves dans un domaine
- **Étapes** :
  1. Formuler la question PICO
  2. Élaborer la stratégie de recherche (au moins 3 bases de données)
  3. Sélectionner les articles (deux personnes indépendamment)
  4. Extraire les données (tableau standardisé)
  5. Évaluer la qualité (risque de biais Cochrane/RoB 2)
  6. Synthétiser les preuves (qualitative/quantitative)
- **Normes de rapport** : PRISMA 2020

## Exigences éthiques

### Éthique de la recherche
- **Approbation du CEI/IEC** : obligatoire pour toute recherche impliquant des humains
- **Contenu de l'évaluation** : protocole de recherche, formulaire de consentement, qualifications des chercheurs
- **Évaluation continue** : annuelle / événements indésirables graves / modifications du protocole

### Consentement éclairé
- **Éléments** : objectif de la recherche, procédure, risques, bénéfices, alternatives, confidentialité, volontariat, coordonnées
- **Situations particulières** : exception en cas d'urgence, représentant légal pour les personnes incapables
- **Documentation** : version signée + date + copie pour le participant

### Protection de la vie privée
- **Déidentification des données** : nom→numéro, numéro d'identification→masqué partiellement
- **Sécurité du stockage** : cryptage, contrôle d'accès, journal d'audit
- **Sécurité du transfert** : transfert crypté, principe de minimisation
- **Durée de conservation** : au moins 5 ans après la fin de la recherche

## Méthodes statistiques

### Statistiques de base
- **Descriptives** : moyenne ± écart-type, médiane (IQR), fréquence (%)
- **Test de normalité** : Shapiro-Wilk, Kolmogorov-Smirnov
- **Comparaison intergroupes** : test t, analyse de variance, test du chi-deux, test de rang

### Statistiques avancées
- **Analyse de survie** : courbe de Kaplan-Meier, test de Log-rank, régression de Cox
- **Analyse ROC** : aire sous la courbe, valeur seuil optimale, sensibilité/spécificité
- **Régression logistique** : univariée→multivariée, OR, IC à 95%
- **Analyse multivariée** : linéaire/logistique/Cox, stratégie de sélection de variables
- **Mesures répétées** : modèle à effets mixtes, GEE
- **Médiation/modération** : méthode Bootstrap, test de Sobel

### Calcul de la taille d'échantillon
- **Logiciels** : G*Power, PASS, nQuery
- **Paramètres** : taille d'effet, α (0.05), β (0.1 ou 0.2), taux d'abandon
- **Méthodes** :
  - Comparaison de deux groupes : formule du test t/chi-deux
  - Analyse de survie : calcul du nombre d'événements
  - Test diagnostique : exigences de sensibilité/spécificité
  - Conception d'équivalence/non-infériorité : détermination de la marge

## Modèles de structure de thèse

### Recherche originale (format IMRAD)
```
1. Page de titre : titre, auteurs, affiliation, auteur correspondant
2. Résumé : structuré (objectif, méthode, résultats, conclusion)
3. Introduction : contexte→problème→objectif→hypothèse
4. Méthodes :
   - Conception/lieu/période
   - Participants (critères d'inclusion/exclusion)
   - Intervention/définition de l'exposition
   - Critères de jugement (principal/secondaire)
   - Méthodes statistiques (logiciel/version/seuil de signification)
5. Résultats :
   - Organigramme (CONSORT)
   - Tableau des caractéristiques de base
   - Résultats principaux (taille d'effet + IC + valeur P)
   - Résultats secondaires
   - Analyse de sous-groupes
   - Analyse de sensibilité
6. Discussion :
   - Synthèse des principaux résultats
   - Comparaison avec les études antérieures
   - Explication du mécanisme
   - Signification clinique
   - Limites (en toute transparence)
   - Perspectives futures
7. Conclusion : concise, sans exagération
8. Remerciements/déclarations : financement, conflits d'intérêts, contributions des auteurs
9. Références : selon les exigences de la revue (Vancouver/APA)
```

### Revue systématique/Méta-analyse
```
1. Titre : identifier clairement « revue systématique » ou « méta-analyse »
2. Résumé : résumé structuré PRISMA
3. Introduction : contexte→problème→objectif (PICO)
4. Méthodes :
   - Enregistrement du protocole (numéro PROSPERO)
   - Critères d'inclusion (PICOS)
   - Stratégie de recherche (stratégie complète en annexe)
   - Processus de sélection (deux personnes indépendamment)
   - Extraction des données (tableau standardisé)
   - Évaluation de la qualité (outil+version)
   - Méthodes statistiques (indicateur d'effet, hétérogénéité, biais de publication)
5. Résultats :
   - Organigramme de recherche (PRISMA)
   - Tableau des caractéristiques des études incluses
   - Graphique des résultats de l'évaluation de qualité
   - Forest plot
   - Funnel plot
   - Analyse de sous-groupes
   - Analyse de sensibilité
6. Discussion : synthèse des preuves, niveau de confiance, limites, recherches futures
7. Conclusion : implications pour la pratique
```

## Normes de rédaction

### Liste de contrôle des normes de rapport
- **ECR** : CONSORT 2010 (liste de 25 items + organigramme)
- **Revue systématique/Méta** : PRISMA 2020 (liste de 27 items + organigramme)
- **Études observationnelles** : STROBE (liste de 22 items)
- **Tests diagnostiques** : STARD (liste de 30 items)
- **Rapports de cas** : CARE (liste de 13 items)
- **Expérimentation animale** : ARRIVE (liste de 21 items)
- **Recherche qualitative** : SRQR (liste de 21 items)
- **Évaluation économique** : CHEERS (liste de 24 items)

### Normes de rapport statistique
- **Taille d'effet** : différence de moyennes (DM), différence de moyennes standardisée (DMS), OR, RR, HR
- **Précision** : intervalle de confiance à 95% (IC)
- **Valeur P** : valeur P exacte (ex. P=0.032), ne pas écrire « P<0.05 »
- **Données manquantes** : rapporter le taux de données manquantes, méthode de traitement
- **Logiciel** : nom+version (ex. SPSS 26.0, R 4.2.1)

## Conseils de soumission

### Choix de la revue
- **Facteur d'impact** : classement JCR (Q1-Q4), classement de l'Académie chinoise des sciences
- **Adéquation** : périmètre, lectorat, type d'article
- **Délai de révision** : pré-sélection, évaluation externe, délai total
- **Accès ouvert** : frais APC, politique de financement
- **Liste d'avertissement** : éviter les revues sur la liste d'avertissement de l'Académie chinoise des sciences

### Documents de soumission
- **Lettre d'accompagnement** : points de nouveauté, signification clinique, réviseurs recommandés
- **Contributions des auteurs** : taxonomie CRediT
- **Conflits d'intérêts** : aucun/déclaration spécifique
- **Disponibilité des données** : lieu de stockage, modalités d'accès
- **Approbation éthique** : numéro d'approbation éthique, consentement éclairé

### Réponse aux évaluations
- **Attitude** : courtoise, objective, sans justification excessive
- **Format** : réponse point par point (commentaire du réviseur→réponse→lieu de la modification)
- **Stratégie** : accepter les commentaires raisonnables, refuser avec justification, compléter les expériences/données
- **Délai** : répondre dans les délais, communiquer à l'avance si une extension est nécessaire

## Erreurs courantes
1. Taille d'échantillon insuffisante (puissance insuffisante)
2. Comparaisons multiples non corrigées (faux positifs)
3. Inférence causale excessive (corrélation ≠ causalité)
4. Déséquilibre de base (échec de la randomisation)
5. Traitement inadéquat des données manquantes (suppression arbitraire)
6. Analyses de sous-groupes excessives (faux positifs)
7. Négligence des facteurs de confusion (biais)
8. Choix erroné de la méthode statistique (test t pour distribution non normale)
9. Graphiques non conformes (axes, légendes, unités)
10. Description éthique manquante (impossible de passer la révision)
