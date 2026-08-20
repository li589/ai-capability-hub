# Guide de rédaction pour les articles en économie

## Caractéristiques de la discipline
- Accent sur les modèles théoriques, l'analyse empirique et les implications politiques
- Importance accordée à la qualité des données, aux stratégies d'identification et aux tests de robustesse
- Principalement des articles de revues (Top 5 : AER/QJE/JPE/Econometrica/RES)

## Orientations de recherche

### Microéconomie
1. **Économie du travail**
   - Rendement de l'éducation, prime de compétences
   - Salaire minimum, effets sur l'emploi
   - Travail à distance, économie des petits boulots

2. **Organisation industrielle**
   - Lutte antitrust des plateformes économiques
   - Tarification des marchés numériques
   - Entrée/sortie des entreprises

3. **Économie publique**
   - Effets des politiques fiscales
   - Conception de la sécurité sociale
   - Concurrence fiscale locale

### Macroéconomie
1. **Croissance économique**
   - Productivité totale des facteurs
   - Croissance conduite par l'innovation
   - Transformation structurelle

2. **Politique monétaire**
   - Effets de l'assouplissement quantitatif
   - Monnaies numériques (MNBC)
   - Mécanismes de transmission des taux d'intérêt

3. **Finance internationale**
   - Fluctuations des taux de change
   - Flux de capitaux
   - Chaînes de valeur mondiales

### Économie du développement
- Évaluation de l'efficacité de la réduction ciblée de la pauvreté
- Inclusion financière numérique
- Changement climatique et agriculture
- Migration et urbanisation

## Modèle de structure de l'article

### Article empirique (le plus courant)
`
1. Introduction (question de recherche, contributions, aperçu des principaux résultats)
2. Revue de littérature (cadre théorique, avancées empiriques, positionnement de l'article)
3. Contexte institutionnel/cadre théorique (contexte chinois, prédictions théoriques)
4. Données et statistiques descriptives (sources de données, définitions des variables, caractéristiques de l'échantillon)
5. Stratégie empirique (méthode d'identification, spécification du modèle, traitement de l'endogénéité)
6. Résultats de base (régression principale, interprétation des coefficients, significativité économique)
7. Tests de robustesse (variables de substitution, sous-échantillons, placebos)
8. Analyse des mécanismes (effets de médiation, analyse d'hétérogénéité)
9. Conclusion et recommandations politiques
`

### Article théorique
- Spécification du modèle (hypothèses, structure de jeu, concept d'équilibre)
- Analyse d'équilibre (existence, unicité, statique comparative)
- Analyse de bien-être (efficacité, effets distributifs)
- Simulations numériques (calibration, contrefactuel)

## Points clés de rédaction

### Stratégie empirique
- **Stratégie d'identification** :
  - ECR (expérience contrôlée randomisée)
  - Expériences naturelles (DID, RDD, IV)
  - Méthodes d'appariement (PSM, contrôle synthétique)

- **Traitement de l'endogénéité** :
  - Variables omises (effets fixes, variables de contrôle)
  - Causalité inverse (variables instrumentales, GMM)
  - Erreurs de mesure (indicateurs multiples, équations structurelles)

### Normes des tableaux de régression
- Présentation étape par étape : base → ajout de contrôles → effets fixes
- Erreurs standard entre parenthèses (groupées au niveau approprié)
- Marqueurs de significativité : * p<0,1, ** p<0,05, *** p<0,01
- R², taille de l'échantillon, statistique F

### Significativité économique
- Ne pas seulement rapporter la significativité statistique, mais aussi expliquer la signification économique
- Comparaison avec la référence : ratio de l'effet par rapport à la moyenne
- Analyse coûts-bénéfices

## Sources de données
- **Macro** : Bureau national des statistiques, Banque mondiale, FMI, Penn World Table
- **Micro** : CHFS, CFPS, CHARLS, CGSS, base de données des entreprises industrielles
- **Finance** : CSMAR, Wind, Bloomberg
- **Politique** : Rapports de travail gouvernementaux, ministère des Finances, banque centrale

## Erreurs courantes
1. **Régression fallacieuse** : régression directe de séries temporelles non stationnaires
2. **Biais de sélection** : sélection inappropriée de l'échantillon
3. **Sur-contrôle** : contrôle des variables de médiation
4. **Multicolinéarité** : VIF > 10
5. **Significativité fallacieuse** : p-hacking, non-rapportage des résultats négatifs

## Recommandations d'outils
- **Traitement des données** : Stata (principal), R, Python (pandas)
- **Analyse de régression** : Stata (reghdfe, ivreg2), R (fixest)
- **Visualisation** : ggplot2, Stata coefplot
- **Gestion de la littérature** : Zotero, Mendeley
- **Rédaction** : LaTeX (Overleaf) ou Word

## Conseils de soumission
- **Revues chinoises** : « Economic Research », « Management World », « China Economic Quarterly »
- **Revues anglaises** : choisir par domaine (JDE, JLE, série AEJ)
- **Documents de travail** : NBER, IZA, CEPR (établissement de priorité)

## Précautions pour la détection de plagiat
- Les descriptions empiriques (sources de données, définitions des variables) peuvent être standardisées
- Dériver les modèles théoriques avec ses propres mots
- La partie revue de littérature est la plus sujette à la répétition, nécessite une reformulation
- Les recommandations politiques doivent intégrer les données les plus récentes
