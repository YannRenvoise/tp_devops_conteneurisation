# TP 01 — CI observable et bloquante

## Expérience d'échec

- Premier contrôle en échec : `Python tests`.
- Diagnostic utile : `tests/test_pricing.py:10`, avec la comparaison
  `180.0 == 181.0`.
- Retour distant obtenu en 21 secondes lors de la première expérience.
- Le rapport JUnit `pricing-test-results` est resté téléchargeable après
  l'échec. Après refonte, l'artefact `python-test-reports` a également été
  téléversé par une étape `if: always()`.
- Le job `Python Docker image` a été bloqué par `needs` lorsque les tests ont
  échoué.

## Graphe et sécurité de publication

Chaque service possède deux portes parallèles, `tests` et `quality`. Le job
Docker dépend des deux. Une pull request construit l'image sans la publier ;
seul un push sur `main` ouvre la connexion GHCR et active `push`.

Les workflows de pull request n'utilisent pas de filtre `paths`. Un contrôle
marqué obligatoire mais ignoré par un filtre peut rester absent ou en attente,
ce qui rend la règle de protection instable. Les sept contrôles sont donc créés
sur toutes les pull requests vers `main`.

## Preuves et reproductibilité

- Pytest produit un XML JUnit.
- Gradle produit les résultats JUnit et les rapports Checkstyle XML/HTML.
- Les artefacts sont téléversés après succès ou échec et conservés 7 jours.
- `python scripts/course.py verify` exécute tests Java, tests Python,
  Checkstyle, puis Ruff. La première commande en échec arrête la séquence et
  le script retourne `1`.

## Détection et réponse aux secrets

Gitleaks analyse l'historique complet grâce à un checkout avec
`fetch-depth: 0`.

Les réponses à une fuite ne sont pas interchangeables :

1. supprimer la ligne empêche une nouvelle exposition dans la version
   courante, mais la valeur reste dans l'historique ;
2. révoquer ou faire tourner le secret invalide immédiatement la valeur
   compromise et reste obligatoire, même si le dépôt est ensuite nettoyé ;
3. réécrire l'historique retire la valeur des anciens commits, mais exige une
   coordination et un force-push, et ne remplace jamais la révocation.

Le test avec la valeur factice de l'enseignant doit être fait uniquement sur
une branche jetable, puis cette branche doit être supprimée selon ses consignes.
