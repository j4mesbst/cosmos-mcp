# Résultats vérifiés

| Configuration du cahier texte | Générations indépendantes | Recherche ciblée top 5 | Replay HeroUI | Score /100 et préférence à l’aveugle |
|---|---:|---:|---|---|
| A agent seul | 0 | Sans objet | Sans objet | Non mesuré |
| B Cosmos 2.4.1 | 0 | 0/5 | Réussi | Non mesuré |
| C Cosmos 2.5.0 | 0 | 5/5 | Réussi | Non mesuré |
| D shadcn, Playwright MCP | 0 | Sans objet | Initialisation et inventaire MCP | Non mesuré |

Les cinq requêtes ciblent des captures absentes de 2.4.1. Ce test mesure la récupération du nouveau corpus. Médiane de latence locale sur cinq requêtes : 93,85 ms pour 2.4.1, 95,07 ms pour 2.5.0. Détails et taille de chaque réponse dans `benchmarks/results/mcp-comparison.json`. Le test fonctionnel du catalogue a envoyé 98 appels dont 60 réponses images. Coût et tokens de génération non mesurés.

Le pilote `codex exec` a échoué avant génération sur un système de fichiers d’état en lecture seule. Aucun score de modèle, rappel d’activation, taux de victoire ou ablation n’a été reconstruit à partir des fixtures. Le banc de test prépare 15 scénarios et cinq cas séparés. Avec trois répétitions et quatre branches, il produit 240 feuilles anonymisables.

## Commandes et résultats

- `python3 -B skills/get-started/tests/test_references.py` baseline, sortie 0.
- Le même script 2.5.0 avec un dossier de preuves, Playwright et Chromium 153, sortie 0 après remplacement du binaire système qui échouait au lancement.
- `python3 -B skills/get-started/tests/test_heroui_benchmark.py PROJET CONFIG RAPPORT` baseline et 2.5.0, sortie 0 chaque fois sur la fixture d’origine. Les essais avec une autre fixture et la première version d’une assertion de version sont également consignés.
- `python3 -B skills/get-started/tests/test_landing_pages.py benchmarks/results/landing-mcp.json` et `test_project_style.py`, sorties 0.
- `python3 -B benchmarks/probe_tools.py --baseline … --competitors …`, sortie 0.
- `node benchmarks/browser.mjs` avec Chromium 153, sortie 0. Capture à trois tailles, navigation clavier, édition du titre, timings et mouvement réduit.
- `python3 -B benchmarks/prepare_trials.py --model to-select --host Codex --seed 250 --runs 3 --output …`, sortie 0.
