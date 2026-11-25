# Cosmos 2.5.0 et le transport MCP distant

Le moteur Python et les ressources du plugin sont conservés. Le Worker sert de passerelle Streamable HTTP sur /mcp. Il transmet les demandes au même moteur Python via remote/bridge.py, qui maintient un processus et un état distincts par session. Les vérifications du projet, la génération des fichiers et Chromium s’exécutent sur la machine qui héberge ce moteur.

## Configuration

Le moteur se lie à `127.0.0.1:8765`. Le Worker peut le joindre par un tunnel Cloudflare privé et un service VPC HTTP ciblant `127.0.0.1:8765`. Ajouter ce service à `vpc_services` sous le nom de binding `COSMOS_VPC`, puis faire tourner `cloudflared` sur la machine du moteur. La passerelle prend aussi en charge une origine HTTPS contrôlée via `COSMOS_UPSTREAM`, qui doit alors contenir l’URL complète de l’origine MCP.

Configurer deux secrets distincts, `COSMOS_CLIENT_TOKEN` et `COSMOS_ORIGIN_TOKEN`, dans le Worker via Wrangler. Fournir uniquement `COSMOS_ORIGIN_TOKEN` à `python3 remote/bridge.py` sur la machine d’origine via son environnement. Pour auditer un projet, fixer `COSMOS_PROJECT_ROOT` à un répertoire de projet dédié et installé. Les traces d’audit peuvent lire les fichiers de ce répertoire. Réserver cet accès aux utilisateurs autorisés. Le moteur doit rester en ligne.

Le Worker refuse les appels sans jeton. Pour un client qui exige une URL seule et un flux d’autorisation standard, ajouter un fournisseur OAuth avant de publier le connecteur. Ne pas mettre de jeton dans une URL ou dans un fichier suivi. Le connecteur Claude n’a pas été testé avec cette passerelle.

Aucun ZIP monolithique ni ressource privée n’est servi comme asset Cloudflare. Les ressources utiles restent dans le dépôt. Connecter le dépôt GitHub et faire un push sans forcer après inspection de sa branche existante. Pour déployer, s’authentifier avec Wrangler dans le compte autorisé, vérifier l’offre Workers Free et configurer une origine fonctionnelle avant de publier.

## Vérification locale

`node remote/test-gateway.mjs` lance un moteur 2.5.0 sur la boucle locale avec des jetons de test aléatoires. Il exécute le code du Worker et remplace uniquement la liaison réseau Cloudflare par une requête HTTP locale. Le test couvre les réponses 401 et 503, l’initialisation, les 15 outils, l’ouverture d’une page complète et de ses trois extraits dans la même session, puis la fermeture. Le déploiement Cloudflare doit être vérifié séparément avec une origine connectée.
