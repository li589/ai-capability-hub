# Guide de rédaction pour les articles en informatique (CS)

## Caractéristiques de la discipline
- Accent sur l'innovation algorithmique, l'implémentation système et la validation expérimentale
- Importance accordée au code open source, aux jeux de données et à la reproductibilité
- Articles de conférence > Articles de revues (conférences de premier plan : CVPR/ICML/NeurIPS/SIGCOMM/SOSP)

## Orientations de recherche

### Domaines populaires
1. **Intelligence artificielle / Apprentissage automatique**
   - Optimisation de l'efficience des grands modèles (accélération de l'inférence, compression de modèles)
   - Apprentissage multimodal (fusion vision-langage-audio)
   - Sécurité et alignement de l'IA (RLHF, tests de l'équipe rouge)
   - Apprentissage fédéré et calcul préservant la vie privée

2. **Systèmes et réseaux**
   - Systèmes natifs du cloud (Serverless, microservices)
   - Calcul en périphérie et IoT
   - Cybersécurité (architecture à confiance nulle, détection de menaces)
   - Cohérence des systèmes distribués

3. **Génie logiciel**
   - Intelligence du code (génération de code, détection de défauts)
   - DevOps et AIOps
   - Sécurité de la chaîne d'approvisionnement logicielle
   - Plateformes low-code/no-code

4. **Science des données**
   - Analyse de séries temporelles
   - Applications des réseaux de neurones graphiques
   - Gouvernance et qualité des données
   - Traitement de flux en temps réel

### Critères d'évaluation des sujets
- **Innovation** : nouveau problème ou nouvelle solution ou nouvelle perspective
- **Faisabilité** : réalisable en 6-12 mois
- **Valeur** : reconnaissance académique ou industrielle
- **Données/Code** : disponibilité de ressources publiques

## Modèle de structure de l'article

### Mémoire de licence
`
1. Introduction (contexte de recherche, définition du problème, aperçu des contributions)
2. Travaux connexes (revue par catégories, identification des lacunes)
3. Méthode/Conception du système (diagramme d'architecture, pseudo-code d'algorithme, diagramme de flux)
4. Expérimentation/Implémentation (jeux de données, métriques, expériences comparatives, expériences d'ablation)
5. Analyse des résultats (graphiques, significativité statistique, études de cas)
6. Discussion (limites, travaux futurs)
7. Conclusion
`

### Mémoire de master
Ajouter :
- Fondements théoriques (définitions formalisées, preuves de théorèmes)
- Expérimentations plus complètes (multiples jeux de données, multiples méthodes de référence, exécutions prolongées)
- Déploiement du système (tests en environnement réel, études utilisateurs)

## Points clés de rédaction

### Description des algorithmes
- Utiliser du pseudo-code (pas du code réel)
- Analyse de complexité temporelle/spatiale
- Preuve de convergence (pour les problèmes d'optimisation)

### Conception expérimentale
- Sélection des méthodes de référence : méthodes classiques + état de l'art
- Métriques d'évaluation : Accuracy/F1/Latency/Throughput
- Tests de significativité : t-test ou Wilcoxon
- Expériences d'ablation : vérifier la nécessité de chaque composant

### Normes des figures et tableaux
- Utiliser des images vectorielles (PDF/SVG)
- Couleurs adaptées aux daltoniens
- Barres d'erreur (exécutions multiples)
- Tableaux à trois lignes

## Erreurs courantes
1. **Expérimentations insuffisantes** : seulement 1-2 jeux de données, manque de comparaisons
2. **Affirmations excessives** : « première proposition », « optimal » (nécessite des preuves)
3. **Code non reproductible** : configuration d'environnement manquante, graines aléatoires
4. **Listage des travaux connexes** : doit inclure une analyse critique
5. **Introduction vide** : doit spécifier concrètement le problème résolu

## Recommandations d'outils
- **Gestion des expérimentations** : Weights & Biases, MLflow
- **Visualisation** : Matplotlib, Seaborn, Plotly
- **Versioning du code** : Git + GitHub
- **Rédaction** : Overleaf (LaTeX)
- **Références bibliographiques** : Zotero + Better BibTeX

## Conseils de soumission
- **Conférences** : attention aux dates limites, terminer 2 mois à l'avance
- **Revues** : délais de révision longs, adaptés aux travaux systématiques
- **arXiv** : publication rapide, établissement de priorité

## Précautions pour la détection de plagiat
- Les extraits de code ne sont pas comptés dans la détection (la plupart des systèmes)
- Décrire les formules avec ses propres mots
- Le pseudo-code d'algorithme peut accepter une certaine répétition
- La description des paramètres expérimentaux peut être standardisée
